"""
用户管理服务
提供用户注册、登录验证、用户信息管理等功能
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class User:
    """用户信息"""
    user_id: int
    username: str
    email: str
    password_hash: str
    access_token: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserService:
    """用户管理服务"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 使用backend目录下的数据库
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(backend_dir, "data", "rss_subscriber.db")
        self.db_path = db_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """初始化用户表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    access_token VARCHAR(255) UNIQUE,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_token ON users (access_token)")
            
            conn.commit()
            logger.info("用户表初始化完成")
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        # 使用SHA-256进行密码哈希（生产环境建议使用bcrypt）
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_token(self) -> str:
        """生成访问令牌"""
        return secrets.token_urlsafe(32)
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """创建新用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查用户名是否已存在
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
                if cursor.fetchone()[0] > 0:
                    raise ValueError("用户名已存在")
                
                # 检查邮箱是否已存在
                cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
                if cursor.fetchone()[0] > 0:
                    raise ValueError("邮箱已被注册")
                
                # 创建用户
                password_hash = self._hash_password(password)
                access_token = self._generate_token()
                current_time = datetime.now()
                
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, access_token, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, email, password_hash, access_token, current_time, current_time))
                
                user_id = cursor.lastrowid
                
                # 为新用户创建默认拉取配置
                cursor.execute("""
                    INSERT INTO user_fetch_configs 
                    (user_id, auto_fetch_enabled, frequency, preferred_hour, daily_limit, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    False,  # 默认关闭自动拉取
                    'daily',  # 默认每天
                    8,  # 默认8:00拉取
                    10,  # 默认每日10次限制
                    current_time,
                    current_time
                ))
                
                conn.commit()
                
                logger.info(f"用户创建成功: {username} (ID: {user_id})，已创建默认拉取配置")
                
                return User(
                    user_id=user_id,
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    access_token=access_token,
                    is_active=True,
                    created_at=current_time,
                    updated_at=current_time
                )
                
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查找用户（支持用户名或邮箱登录）
                cursor.execute("""
                    SELECT user_id, username, email, password_hash, access_token, is_active, created_at, updated_at
                    FROM users 
                    WHERE (username = ? OR email = ?) AND is_active = 1
                """, (username, username))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # 验证密码
                stored_password_hash = row[3]
                if self._hash_password(password) != stored_password_hash:
                    return None
                
                # 更新访问令牌
                new_token = self._generate_token()
                cursor.execute("""
                    UPDATE users SET access_token = ?, updated_at = ?
                    WHERE user_id = ?
                """, (new_token, datetime.now(), row[0]))
                
                conn.commit()
                
                logger.info(f"用户认证成功: {row[1]} (ID: {row[0]})")
                
                return User(
                    user_id=row[0],
                    username=row[1],
                    email=row[2],
                    password_hash=row[3],
                    access_token=new_token,
                    is_active=bool(row[5]),
                    created_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    updated_at=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return None
    
    def get_user_by_token(self, token: str) -> Optional[User]:
        """通过令牌获取用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT user_id, username, email, password_hash, access_token, is_active, created_at, updated_at
                    FROM users 
                    WHERE access_token = ? AND is_active = 1
                """, (token,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return User(
                    user_id=row[0],
                    username=row[1],
                    email=row[2],
                    password_hash=row[3],
                    access_token=row[4],
                    is_active=bool(row[5]),
                    created_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    updated_at=datetime.fromisoformat(row[7]) if row[7] else None
                )
                
        except Exception as e:
            logger.error(f"通过令牌获取用户失败: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """通过ID获取用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT user_id, username, email, password_hash, access_token, is_active, created_at, updated_at
                    FROM users 
                    WHERE user_id = ? AND is_active = 1
                """, (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return User(
                    user_id=row[0],
                    username=row[1],
                    email=row[2],
                    password_hash=row[3],
                    access_token=row[4],
                    is_active=bool(row[5]),
                    created_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    updated_at=datetime.fromisoformat(row[7]) if row[7] else None
                )
                
        except Exception as e:
            logger.error(f"通过ID获取用户失败: {e}")
            return None
    
    def invalidate_token(self, token: str) -> bool:
        """使令牌失效（登出）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users SET access_token = NULL, updated_at = ?
                    WHERE access_token = ?
                """, (datetime.now(), token))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"令牌失效失败: {e}")
            return False
    
    def create_test_user(self) -> User:
        """创建测试用户（用于开发测试）"""
        try:
            # 先尝试删除已存在的测试用户
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username = 'admin'")
                conn.commit()
            
            # 创建新的测试用户
            return self.create_user(
                username="admin",
                email="admin@example.com", 
                password="admin123"
            )
            
        except Exception as e:
            logger.error(f"创建测试用户失败: {e}")
            raise


# 创建全局用户服务实例
user_service = UserService() 