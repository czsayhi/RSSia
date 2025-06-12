"""
拉取限流服务
管理用户每日拉取次数限制、可用性判断等风控功能
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class FetchQuota:
    """用户拉取配额信息"""
    user_id: int
    daily_limit: int
    current_count: int
    remaining_count: int
    can_fetch: bool
    last_fetch_at: Optional[datetime] = None
    last_fetch_success: Optional[bool] = None

@dataclass
class FetchAttemptResult:
    """拉取尝试结果"""
    success: bool
    message: str
    quota_after: Optional[FetchQuota] = None

class FetchLimitService:
    """拉取限流服务"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_user_quota(self, user_id: int) -> FetchQuota:
        """
        获取用户当日拉取配额信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户配额信息
        """
        # 获取用户配置的每日限制
        daily_limit = self._get_user_daily_limit(user_id)
        
        # 获取今日已使用的次数
        today = date.today()
        current_count = self._get_today_fetch_count(user_id, today)
        
        # 计算剩余次数
        remaining_count = max(0, daily_limit - current_count)
        can_fetch = remaining_count > 0
        
        # 获取最后拉取信息
        last_fetch_info = self._get_last_fetch_info(user_id, today)
        
        return FetchQuota(
            user_id=user_id,
            daily_limit=daily_limit,
            current_count=current_count,
            remaining_count=remaining_count,
            can_fetch=can_fetch,
            last_fetch_at=last_fetch_info.get('last_fetch_at'),
            last_fetch_success=last_fetch_info.get('last_fetch_success')
        )
    
    def check_can_fetch(self, user_id: int, fetch_type: str = 'manual') -> bool:
        """
        检查用户是否可以进行拉取
        
        Args:
            user_id: 用户ID
            fetch_type: 拉取类型 ('auto' 或 'manual')
            
        Returns:
            是否可以拉取
        """
        quota = self.get_user_quota(user_id)
        return quota.can_fetch
    
    def attempt_fetch(self, user_id: int, fetch_type: str = 'manual') -> FetchAttemptResult:
        """
        尝试进行拉取（会消耗配额）
        
        Args:
            user_id: 用户ID
            fetch_type: 拉取类型 ('auto' 或 'manual')
            
        Returns:
            拉取尝试结果
        """
        # 检查配额
        quota = self.get_user_quota(user_id)
        
        if not quota.can_fetch:
            return FetchAttemptResult(
                success=False,
                message=f"已达到每日拉取次数限制（{quota.daily_limit}次），请明天再试",
                quota_after=quota
            )
        
        # 消耗配额
        success = self._consume_fetch_quota(user_id, fetch_type)
        
        if success:
            # 获取更新后的配额信息
            updated_quota = self.get_user_quota(user_id)
            return FetchAttemptResult(
                success=True,
                message="拉取配额消耗成功",
                quota_after=updated_quota
            )
        else:
            return FetchAttemptResult(
                success=False,
                message="拉取配额消耗失败",
                quota_after=quota
            )
    
    def record_fetch_result(self, user_id: int, fetch_type: str, success: bool):
        """
        记录拉取结果（不消耗配额，仅记录结果）
        
        Args:
            user_id: 用户ID
            fetch_type: 拉取类型 ('auto' 或 'manual')
            success: 拉取是否成功
        """
        today = date.today()
        current_time = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE user_fetch_logs
                SET last_fetch_at = ?, last_fetch_success = ?, updated_at = ?
                WHERE user_id = ? AND fetch_date = ?
            """, (current_time, success, current_time, user_id, today))
    
    def get_user_fetch_history(self, user_id: int, days: int = 7) -> list[Dict[str, Any]]:
        """
        获取用户拉取历史记录
        
        Args:
            user_id: 用户ID
            days: 查询天数（默认7天）
            
        Returns:
            拉取历史记录列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT fetch_date, fetch_count, auto_fetch_count, manual_fetch_count,
                       last_fetch_at, last_fetch_success
                FROM user_fetch_logs
                WHERE user_id = ? AND fetch_date >= date('now', '-{} days')
                ORDER BY fetch_date DESC
            """.format(days), (user_id,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'fetch_date': row[0],
                    'fetch_count': row[1],
                    'auto_fetch_count': row[2],
                    'manual_fetch_count': row[3],
                    'last_fetch_at': row[4],
                    'last_fetch_success': bool(row[5]) if row[5] is not None else None
                })
            
            return history
    
    def reset_user_quota(self, user_id: int) -> bool:
        """
        重置用户当日配额（管理员功能）
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否重置成功
        """
        today = date.today()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_fetch_logs
                SET fetch_count = 0, auto_fetch_count = 0, manual_fetch_count = 0,
                    updated_at = ?
                WHERE user_id = ? AND fetch_date = ?
            """, (datetime.now(), user_id, today))
            
            return cursor.rowcount > 0
    
    # 私有方法
    def _get_user_daily_limit(self, user_id: int) -> int:
        """获取用户的每日拉取限制"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT daily_limit
                FROM user_fetch_configs
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))
            
            row = cursor.fetchone()
            return row[0] if row else 10  # 默认每日10次
    
    def _get_today_fetch_count(self, user_id: int, today: date) -> int:
        """获取用户今日已拉取次数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT fetch_count
                FROM user_fetch_logs
                WHERE user_id = ? AND fetch_date = ?
            """, (user_id, today))
            
            row = cursor.fetchone()
            return row[0] if row else 0
    
    def _get_last_fetch_info(self, user_id: int, today: date) -> Dict[str, Any]:
        """获取最后拉取信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT last_fetch_at, last_fetch_success
                FROM user_fetch_logs
                WHERE user_id = ? AND fetch_date = ?
            """, (user_id, today))
            
            row = cursor.fetchone()
            if row:
                return {
                    'last_fetch_at': datetime.fromisoformat(row[0]) if row[0] else None,
                    'last_fetch_success': bool(row[1]) if row[1] is not None else None
                }
            else:
                return {'last_fetch_at': None, 'last_fetch_success': None}
    
    def _consume_fetch_quota(self, user_id: int, fetch_type: str) -> bool:
        """消耗拉取配额"""
        today = date.today()
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
                        updated_at = ?
                    WHERE user_id = ? AND fetch_date = ?
                """, (
                    fetch_count, auto_fetch_count, manual_fetch_count,
                    current_time, user_id, today
                ))
            else:
                # 创建新记录
                cursor.execute("""
                    INSERT INTO user_fetch_logs
                    (user_id, fetch_date, fetch_count, auto_fetch_count, manual_fetch_count,
                     created_at, updated_at)
                    VALUES (?, ?, 1, ?, ?, ?, ?)
                """, (
                    user_id, today,
                    1 if fetch_type == 'auto' else 0,
                    1 if fetch_type == 'manual' else 0,
                    current_time, current_time
                ))
            
            return True 