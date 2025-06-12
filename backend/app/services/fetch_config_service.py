"""
订阅频率配置服务
管理用户的订阅频率配置、自动拉取开关等设置
"""

import sqlite3
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class FrequencyType(str, Enum):
    """订阅频率类型"""
    DAILY = "daily"           # 每天
    THREE_DAYS = "three_days" # 每3天  
    WEEKLY = "weekly"         # 每周

@dataclass
class FetchConfig:
    """用户拉取配置"""
    user_id: int
    auto_fetch_enabled: bool = False      # 自动拉取开关（新用户默认关闭）
    frequency: FrequencyType = FrequencyType.DAILY
    preferred_hour: int = 9               # UTC+8时区的整点时间 (0-23)
    timezone: str = "Asia/Shanghai"
    daily_limit: int = 10                 # 每日拉取次数限制
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass 
class FetchConfigUpdateRequest:
    """拉取配置更新请求"""
    auto_fetch_enabled: Optional[bool] = None
    frequency: Optional[FrequencyType] = None  
    preferred_hour: Optional[int] = None
    daily_limit: Optional[int] = None

class FetchConfigService:
    """订阅频率配置服务"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        self.db_path = db_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_user_config(self, user_id: int) -> FetchConfig:
        """
        获取用户的拉取配置
        如果用户没有配置，返回默认配置（不自动创建）
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, auto_fetch_enabled, frequency, preferred_hour, 
                       timezone, daily_limit, is_active, created_at, updated_at
                FROM user_fetch_configs
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return FetchConfig(
                    user_id=row[0],
                    auto_fetch_enabled=bool(row[1]),
                    frequency=FrequencyType(row[2]),
                    preferred_hour=row[3],
                    timezone=row[4],
                    daily_limit=row[5],
                    is_active=bool(row[6]),
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    updated_at=datetime.fromisoformat(row[8]) if row[8] else None
                )
            else:
                # 返回默认配置（不存储到数据库）
                return FetchConfig(user_id=user_id)
    
    def create_or_update_config(self, user_id: int, request: FetchConfigUpdateRequest) -> FetchConfig:
        """
        创建或更新用户拉取配置
        支持部分字段更新
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查用户是否已有配置
            cursor.execute("SELECT COUNT(*) FROM user_fetch_configs WHERE user_id = ?", (user_id,))
            exists = cursor.fetchone()[0] > 0
            
            current_time = datetime.now()
            
            if exists:
                # 更新现有配置（只更新非None字段）
                update_fields = []
                update_values = []
                
                if request.auto_fetch_enabled is not None:
                    update_fields.append("auto_fetch_enabled = ?")
                    update_values.append(request.auto_fetch_enabled)
                
                if request.frequency is not None:
                    update_fields.append("frequency = ?")
                    update_values.append(request.frequency.value)
                
                if request.preferred_hour is not None:
                    if not (0 <= request.preferred_hour <= 23):
                        raise ValueError("preferred_hour必须在0-23之间")
                    update_fields.append("preferred_hour = ?")
                    update_values.append(request.preferred_hour)
                
                if request.daily_limit is not None:
                    if not (1 <= request.daily_limit <= 100):
                        raise ValueError("daily_limit必须在1-100之间")
                    update_fields.append("daily_limit = ?")
                    update_values.append(request.daily_limit)
                
                if update_fields:
                    update_fields.append("updated_at = ?")
                    update_values.append(current_time)
                    update_values.append(user_id)
                    
                    sql = f"UPDATE user_fetch_configs SET {', '.join(update_fields)} WHERE user_id = ?"
                    cursor.execute(sql, update_values)
            else:
                # 创建新配置
                cursor.execute("""
                    INSERT INTO user_fetch_configs 
                    (user_id, auto_fetch_enabled, frequency, preferred_hour, daily_limit, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    request.auto_fetch_enabled if request.auto_fetch_enabled is not None else False,
                    request.frequency.value if request.frequency is not None else FrequencyType.DAILY.value,
                    request.preferred_hour if request.preferred_hour is not None else 9,
                    request.daily_limit if request.daily_limit is not None else 10,
                    current_time,
                    current_time
                ))
            
            conn.commit()
            
            # 返回更新后的配置
            return self.get_user_config(user_id)
    
    def get_auto_fetch_users(self) -> list[FetchConfig]:
        """获取所有开启自动拉取的用户配置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, auto_fetch_enabled, frequency, preferred_hour, 
                       timezone, daily_limit, is_active, created_at, updated_at
                FROM user_fetch_configs
                WHERE auto_fetch_enabled = 1 AND is_active = 1
                ORDER BY user_id
            """)
            
            configs = []
            for row in cursor.fetchall():
                config = FetchConfig(
                    user_id=row[0],
                    auto_fetch_enabled=bool(row[1]),
                    frequency=FrequencyType(row[2]),
                    preferred_hour=row[3],
                    timezone=row[4],
                    daily_limit=row[5],
                    is_active=bool(row[6]),
                    created_at=datetime.fromisoformat(row[7]) if row[7] else None,
                    updated_at=datetime.fromisoformat(row[8]) if row[8] else None
                )
                configs.append(config)
            
            return configs
    
    def calculate_next_fetch_time(self, config: FetchConfig, from_time: Optional[datetime] = None) -> datetime:
        """
        计算下次拉取时间
        
        Args:
            config: 用户配置
            from_time: 计算起始时间，默认为当前时间
            
        Returns:
            下次拉取的时间点
        """
        if from_time is None:
            from_time = datetime.now()
        
        # 转换到用户时区（目前固定为Asia/Shanghai，即UTC+8）
        user_tz_offset = timedelta(hours=8)
        user_time = from_time + user_tz_offset
        
        # 获取今天的目标时间点
        today_target = user_time.replace(
            hour=config.preferred_hour, 
            minute=0, 
            second=0, 
            microsecond=0
        )
        
        if config.frequency == FrequencyType.DAILY:
            # 每天：如果今天的时间点已过，则明天同一时间
            if user_time >= today_target:
                next_time = today_target + timedelta(days=1)
            else:
                next_time = today_target
                
        elif config.frequency == FrequencyType.THREE_DAYS:
            # 每3天：从今天开始，下一个3天后的时间点
            if user_time >= today_target:
                next_time = today_target + timedelta(days=3)
            else:
                next_time = today_target
                
        elif config.frequency == FrequencyType.WEEKLY:
            # 每周：从今天开始，下一个7天后的时间点  
            if user_time >= today_target:
                next_time = today_target + timedelta(days=7)
            else:
                next_time = today_target
        else:
            raise ValueError(f"不支持的频率类型: {config.frequency}")
        
        # 转换回UTC时间
        return next_time - user_tz_offset
    
    def disable_user_config(self, user_id: int) -> bool:
        """禁用用户配置（软删除）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_fetch_configs 
                SET is_active = 0, updated_at = ?
                WHERE user_id = ?
            """, (datetime.now(), user_id))
            
            return cursor.rowcount > 0 