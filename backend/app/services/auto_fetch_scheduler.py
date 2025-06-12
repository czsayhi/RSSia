"""
自动拉取调度服务
基于APScheduler实现用户订阅内容的自动拉取调度
包含重试机制和任务记录管理
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from .fetch_config_service import FetchConfigService, FetchConfig, FrequencyType
from .enhanced_rss_service import EnhancedRSSService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 执行中
    SUCCESS = "success"       # 成功
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消

@dataclass
class FetchTask:
    """拉取任务"""
    user_id: int
    task_type: str              # 'auto' 或 'manual'
    task_key: str               # 任务唯一标识
    scheduled_at: datetime      # 计划执行时间
    executed_at: Optional[datetime] = None
    attempt_count: int = 0
    max_attempts: int = 3
    status: TaskStatus = TaskStatus.PENDING
    success_count: int = 0      # 成功拉取的订阅数量
    total_count: int = 0        # 总订阅数量
    error_message: Optional[str] = None
    next_retry_at: Optional[datetime] = None

class AutoFetchScheduler:
    """自动拉取调度器"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        self.db_path = db_path
        self.config_service = FetchConfigService(db_path)
        self.rss_service = EnhancedRSSService()
        
        # 配置APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        
        executors = {
            'default': ThreadPoolExecutor(max_workers=5)  # 最多5个并发拉取任务
        }
        
        job_defaults = {
            'coalesce': True,           # 合并错过的任务
            'max_instances': 1,         # 每个任务最多1个实例
            'misfire_grace_time': 300   # 任务错过5分钟内仍可执行
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def start(self):
        """启动调度器"""
        logger.info("启动RSS自动拉取调度器...")
        
        # 启动调度器
        if not self.scheduler.running:
            self.scheduler.start()
        
        # 设置定期检查任务（每分钟检查一次需要调度的用户）
        self.scheduler.add_job(
            self._check_and_schedule_users,
            trigger=CronTrigger(minute='*'),  # 每分钟执行一次
            id='check_users',
            replace_existing=True
        )
        
        # 设置重试任务检查（每5分钟检查一次需要重试的任务）
        self.scheduler.add_job(
            self._check_retry_tasks,
            trigger=CronTrigger(minute='*/5'),  # 每5分钟执行一次
            id='check_retries',
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
            # 获取所有开启自动拉取的用户
            users = self.config_service.get_auto_fetch_users()
            current_time = datetime.now()
            
            for config in users:
                # 计算该用户的下次拉取时间
                next_fetch_time = self.config_service.calculate_next_fetch_time(config, current_time)
                
                # 检查是否需要立即执行（允许1分钟的误差）
                time_diff = abs((next_fetch_time - current_time).total_seconds())
                if time_diff <= 60:  # 1分钟内
                    self._schedule_user_fetch(config, next_fetch_time)
                    
        except Exception as e:
            logger.error(f"检查用户调度时出错: {e}")
    
    def _schedule_user_fetch(self, config: FetchConfig, scheduled_time: datetime):
        """为用户调度拉取任务"""
        task_key = f"auto_{config.user_id}_{scheduled_time.strftime('%Y%m%d_%H')}"
        
        # 检查任务是否已存在
        if self._task_exists(task_key):
            return
        
        # 创建任务记录
        task = FetchTask(
            user_id=config.user_id,
            task_type='auto',
            task_key=task_key,
            scheduled_at=scheduled_time
        )
        
        self._save_task(task)
        
        # 调度任务执行
        self.scheduler.add_job(
            self._execute_user_fetch,
            trigger=DateTrigger(run_date=scheduled_time),
            args=[task_key],
            id=task_key,
            replace_existing=True
        )
        
        logger.info(f"已调度用户 {config.user_id} 的自动拉取任务，执行时间: {scheduled_time}")
    
    def _execute_user_fetch(self, task_key: str):
        """执行用户拉取任务"""
        try:
            # 获取任务信息
            task = self._get_task(task_key)
            if not task or task.status != TaskStatus.PENDING:
                return
            
            # 更新任务状态为执行中
            self._update_task_status(task_key, TaskStatus.RUNNING, executed_at=datetime.now())
            
            # 检查用户是否还开启自动拉取
            config = self.config_service.get_user_config(task.user_id)
            if not config.auto_fetch_enabled:
                self._update_task_status(task_key, TaskStatus.CANCELLED, error_message="用户已关闭自动拉取")
                return
            
            # 检查用户当日拉取次数限制
            if not self._check_daily_limit(task.user_id, config.daily_limit):
                self._update_task_status(task_key, TaskStatus.FAILED, error_message="已达到当日拉取次数限制")
                return
            
            # 执行拉取任务
            success_count, total_count = self._perform_user_fetch(task.user_id)
            
            if success_count > 0:
                # 任务成功
                self._update_task_status(
                    task_key, 
                    TaskStatus.SUCCESS,
                    success_count=success_count,
                    total_count=total_count
                )
                # 记录拉取日志
                self._record_fetch_log(task.user_id, 'auto', True)
                logger.info(f"用户 {task.user_id} 自动拉取成功: {success_count}/{total_count}")
            else:
                # 任务失败，检查是否需要重试
                self._handle_task_failure(task_key, "拉取失败，没有成功获取任何内容")
                
        except Exception as e:
            logger.error(f"执行拉取任务 {task_key} 时出错: {e}")
            self._handle_task_failure(task_key, str(e))
    
    def _handle_task_failure(self, task_key: str, error_message: str):
        """处理任务失败"""
        task = self._get_task(task_key)
        if not task:
            return
        
        attempt_count = task.attempt_count + 1
        
        if attempt_count >= task.max_attempts:
            # 达到最大重试次数，标记为失败
            self._update_task_status(
                task_key,
                TaskStatus.FAILED,
                error_message=error_message,
                attempt_count=attempt_count
            )
            # 记录失败日志
            self._record_fetch_log(task.user_id, 'auto', False)
            logger.warning(f"任务 {task_key} 达到最大重试次数，标记为失败")
        else:
            # 安排重试
            next_retry = datetime.now() + timedelta(minutes=10)  # 10分钟后重试
            self._update_task_status(
                task_key,
                TaskStatus.PENDING,
                error_message=error_message,
                attempt_count=attempt_count,
                next_retry_at=next_retry
            )
            logger.info(f"任务 {task_key} 将于 {next_retry} 重试（第{attempt_count}次尝试）")
    
    def _check_retry_tasks(self):
        """检查需要重试的任务"""
        try:
            current_time = datetime.now()
            retry_tasks = self._get_retry_tasks(current_time)
            
            for task_key in retry_tasks:
                self.scheduler.add_job(
                    self._execute_user_fetch,
                    trigger=DateTrigger(run_date=current_time),
                    args=[task_key],
                    id=f"retry_{task_key}",
                    replace_existing=True
                )
                logger.info(f"已调度重试任务: {task_key}")
                
        except Exception as e:
            logger.error(f"检查重试任务时出错: {e}")
    
    def _perform_user_fetch(self, user_id: int) -> tuple[int, int]:
        """
        执行用户的RSS拉取
        
        Returns:
            tuple: (成功数量, 总数量)
        """
        try:
            # 获取用户的所有活跃订阅
            from .subscription_service import SubscriptionService
            subscription_service = SubscriptionService(self.db_path)
            
            # 这里需要获取用户订阅列表的方法
            subscriptions = subscription_service.get_user_subscriptions(user_id)
            total_count = len(subscriptions.subscriptions)
            success_count = 0
            
            for subscription in subscriptions.subscriptions:
                try:
                    # 调用RSS服务拉取内容
                    result = self.rss_service.fetch_and_process_rss(subscription.rss_url, user_id)
                    if result.get('success', False):
                        success_count += 1
                        # 更新订阅的最后更新时间
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
    
    # 数据库操作方法
    def _task_exists(self, task_key: str) -> bool:
        """检查任务是否存在"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fetch_task_logs WHERE task_key = ?", (task_key,))
            return cursor.fetchone()[0] > 0
    
    def _save_task(self, task: FetchTask):
        """保存任务到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fetch_task_logs 
                (user_id, task_type, task_key, scheduled_at, status, max_attempts)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                task.user_id,
                task.task_type,
                task.task_key,
                task.scheduled_at,
                task.status.value,
                task.max_attempts
            ))
    
    def _get_task(self, task_key: str) -> Optional[FetchTask]:
        """获取任务信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, task_type, task_key, scheduled_at, executed_at,
                       attempt_count, max_attempts, status, success_count, total_count,
                       error_message, next_retry_at
                FROM fetch_task_logs
                WHERE task_key = ?
            """, (task_key,))
            
            row = cursor.fetchone()
            if row:
                return FetchTask(
                    user_id=row[0],
                    task_type=row[1],
                    task_key=row[2],
                    scheduled_at=datetime.fromisoformat(row[3]),
                    executed_at=datetime.fromisoformat(row[4]) if row[4] else None,
                    attempt_count=row[5],
                    max_attempts=row[6],
                    status=TaskStatus(row[7]),
                    success_count=row[8],
                    total_count=row[9],
                    error_message=row[10],
                    next_retry_at=datetime.fromisoformat(row[11]) if row[11] else None
                )
            return None
    
    def _update_task_status(self, task_key: str, status: TaskStatus, **kwargs):
        """更新任务状态"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            update_fields = ["status = ?", "updated_at = ?"]
            update_values = [status.value, datetime.now()]
            
            # 处理可选参数
            if 'executed_at' in kwargs:
                update_fields.append("executed_at = ?")
                update_values.append(kwargs['executed_at'])
            
            if 'attempt_count' in kwargs:
                update_fields.append("attempt_count = ?")
                update_values.append(kwargs['attempt_count'])
            
            if 'success_count' in kwargs:
                update_fields.append("success_count = ?")
                update_values.append(kwargs['success_count'])
            
            if 'total_count' in kwargs:
                update_fields.append("total_count = ?")
                update_values.append(kwargs['total_count'])
            
            if 'error_message' in kwargs:
                update_fields.append("error_message = ?")
                update_values.append(kwargs['error_message'])
            
            if 'next_retry_at' in kwargs:
                update_fields.append("next_retry_at = ?")
                update_values.append(kwargs['next_retry_at'])
            
            update_values.append(task_key)
            
            sql = f"UPDATE fetch_task_logs SET {', '.join(update_fields)} WHERE task_key = ?"
            cursor.execute(sql, update_values)
    
    def _get_retry_tasks(self, current_time: datetime) -> List[str]:
        """获取需要重试的任务"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT task_key
                FROM fetch_task_logs
                WHERE status = 'pending' 
                  AND next_retry_at IS NOT NULL 
                  AND next_retry_at <= ?
                  AND attempt_count < max_attempts
            """, (current_time,))
            
            return [row[0] for row in cursor.fetchall()]
    
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
            
            # 尝试获取今日记录
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