"""
RSS自动拉取调度服务
基于APScheduler实现用户订阅内容的自动拉取调度
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from .fetch_config_service import FetchConfigService, FetchConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class FetchScheduler:
    """RSS拉取调度器"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        self.db_path = db_path
        self.config_service = FetchConfigService(db_path)
        
        # 配置APScheduler
        self.scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': ThreadPoolExecutor(max_workers=5)},
            job_defaults={'coalesce': True, 'max_instances': 1},
            timezone='Asia/Shanghai'
        )
        
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def start(self):
        """启动调度器"""
        logger.info("启动RSS自动拉取调度器...")
        
        if not self.scheduler.running:
            self.scheduler.start()
        
        # 每分钟检查需要调度的用户
        self.scheduler.add_job(
            self._check_and_schedule_users,
            trigger=CronTrigger(minute='*'),
            id='check_users',
            replace_existing=True
        )
        
        logger.info("RSS自动拉取调度器启动完成")
    
    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("RSS自动拉取调度器已停止")
    
    def _check_and_schedule_users(self):
        """检查并调度需要自动拉取的用户"""
        try:
            users = self.config_service.get_auto_fetch_users()
            current_time = datetime.now()
            
            for config in users:
                next_fetch_time = self.config_service.calculate_next_fetch_time(config, current_time)
                
                # 检查是否需要立即执行（允许1分钟误差）
                time_diff = abs((next_fetch_time - current_time).total_seconds())
                if time_diff <= 60:
                    self._execute_user_fetch(config.user_id)
                    
        except Exception as e:
            logger.error(f"检查用户调度时出错: {e}")
    
    def _execute_user_fetch(self, user_id: int):
        """执行用户拉取任务"""
        try:
            logger.info(f"开始执行用户 {user_id} 的自动拉取任务")
            
            # 检查用户配置
            config = self.config_service.get_user_config(user_id)
            if not config.auto_fetch_enabled:
                logger.info(f"用户 {user_id} 已关闭自动拉取")
                return
            
            # 检查每日限制
            if not self._check_daily_limit(user_id, config.daily_limit):
                logger.warning(f"用户 {user_id} 已达到当日拉取次数限制")
                return
            
            # 执行拉取
            success_count, total_count = self._perform_user_fetch(user_id)
            
            # 记录结果
            self._record_fetch_log(user_id, 'auto', success_count > 0)
            
            logger.info(f"用户 {user_id} 自动拉取完成: {success_count}/{total_count}")
            
        except Exception as e:
            logger.error(f"执行用户 {user_id} 拉取任务时出错: {e}")
    
    def _perform_user_fetch(self, user_id: int) -> tuple[int, int]:
        """执行用户的RSS拉取"""
        try:
            from .subscription_service import SubscriptionService
            from .enhanced_rss_service import EnhancedRSSService
            
            subscription_service = SubscriptionService(self.db_path)
            rss_service = EnhancedRSSService()
            
            subscriptions = subscription_service.get_user_subscriptions(user_id)
            total_count = len(subscriptions.subscriptions)
            success_count = 0
            
            for subscription in subscriptions.subscriptions:
                try:
                    result = rss_service.fetch_and_process_rss(subscription.rss_url, user_id)
                    if result.get('success', False):
                        success_count += 1
                        self._update_subscription_last_update(subscription.id)
                except Exception as e:
                    logger.error(f"拉取订阅 {subscription.id} 失败: {e}")
                    continue
            
            return success_count, total_count
            
        except Exception as e:
            logger.error(f"执行用户 {user_id} 拉取时出错: {e}")
            return 0, 0
    
    def _update_subscription_last_update(self, subscription_id: int):
        """更新订阅的最后更新时间"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_subscriptions 
                SET last_update = ?
                WHERE id = ?
            """, (datetime.now(), subscription_id))
    
    def _check_daily_limit(self, user_id: int, daily_limit: int) -> bool:
        """检查用户当日拉取次数是否超限"""
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT fetch_count
                FROM user_fetch_logs
                WHERE user_id = ? AND fetch_date = ?
            """, (user_id, today))
            
            row = cursor.fetchone()
            current_count = row[0] if row else 0
            
            return current_count < daily_limit
    
    def _record_fetch_log(self, user_id: int, fetch_type: str, success: bool):
        """记录拉取日志"""
        today = datetime.now().date()
        current_time = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT fetch_count, auto_fetch_count, manual_fetch_count
                FROM user_fetch_logs
                WHERE user_id = ? AND fetch_date = ?
            """, (user_id, today))
            
            row = cursor.fetchone()
            
            if row:
                # 更新现有记录
                fetch_count = row[0] + 1
                auto_fetch_count = row[1] + (1 if fetch_type == 'auto' else 0)
                manual_fetch_count = row[2] + (1 if fetch_type == 'manual' else 0)
                
                cursor.execute("""
                    UPDATE user_fetch_logs
                    SET fetch_count = ?, auto_fetch_count = ?, manual_fetch_count = ?,
                        last_fetch_at = ?, last_fetch_success = ?, updated_at = ?
                    WHERE user_id = ? AND fetch_date = ?
                """, (
                    fetch_count, auto_fetch_count, manual_fetch_count,
                    current_time, success, current_time, user_id, today
                ))
            else:
                # 创建新记录
                cursor.execute("""
                    INSERT INTO user_fetch_logs
                    (user_id, fetch_date, fetch_count, auto_fetch_count, manual_fetch_count,
                     last_fetch_at, last_fetch_success)
                    VALUES (?, ?, 1, ?, ?, ?, ?)
                """, (
                    user_id, today,
                    1 if fetch_type == 'auto' else 0,
                    1 if fetch_type == 'manual' else 0,
                    current_time, success
                )) 