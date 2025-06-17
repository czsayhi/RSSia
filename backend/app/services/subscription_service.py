"""
订阅管理服务
"""
from typing import List, Optional
from datetime import datetime
import sqlite3
import os
from ..models.subscription import (
    SubscriptionTemplate,
    UserSubscription,
    SubscriptionCreateRequest,
    SubscriptionResponse,
    SubscriptionListResponse,
    PlatformType,
    ContentType
)


class SubscriptionService:
    """订阅管理服务"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 使用backend目录下的数据库
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(backend_dir, "data", "rss_subscriber.db")
        """初始化订阅服务"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            

            
            # 创建用户订阅表（简化版本，频率配置统一管理）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    template_id TEXT NOT NULL,               -- 现在使用字符串ID（JSON模板）
                    target_user_id TEXT NOT NULL,
                    custom_name TEXT,
                    rss_url TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    last_update TIMESTAMP,                   -- 最后拉取时间
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 执行新的数据库架构（风控和频率配置）
            self._init_fetch_control_tables(cursor)
            
            conn.commit()
    
    def _init_fetch_control_tables(self, cursor):
        """初始化订阅频率配置和风控表"""
        # 用户拉取记录表（每日限流控制）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_fetch_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                fetch_date DATE NOT NULL,
                fetch_count INTEGER DEFAULT 0,
                auto_fetch_count INTEGER DEFAULT 0,
                manual_fetch_count INTEGER DEFAULT 0,
                last_fetch_at TIMESTAMP,
                last_fetch_success BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_user_fetch_date ON user_fetch_logs (user_id, fetch_date)")
        
        # 拉取任务记录表（重试逻辑控制）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fetch_task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_type VARCHAR(20) NOT NULL,
                task_key VARCHAR(100) NOT NULL,
                scheduled_at TIMESTAMP NOT NULL,
                executed_at TIMESTAMP,
                attempt_count INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                status VARCHAR(20) DEFAULT 'pending',
                success_count INTEGER DEFAULT 0,
                total_count INTEGER DEFAULT 0,
                error_message TEXT,
                next_retry_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_task_key ON fetch_task_logs (task_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_task_status ON fetch_task_logs (user_id, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_at ON fetch_task_logs (scheduled_at)")
        
        # 订阅频率配置表（用户维度配置）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_fetch_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                auto_fetch_enabled BOOLEAN DEFAULT 0,
                frequency VARCHAR(20) DEFAULT 'daily',
                preferred_hour INTEGER DEFAULT 9,
                timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
                daily_limit INTEGER DEFAULT 10,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_auto_fetch ON user_fetch_configs (user_id, auto_fetch_enabled)")
    

    
    def get_templates(self) -> List[SubscriptionTemplate]:
        """获取所有订阅模板（现在从JSON配置文件获取）"""
        from app.config.template_loader import get_template_loader
        
        template_loader = get_template_loader()
        return template_loader.get_all_templates()
    
    def create_subscription(self, request: SubscriptionCreateRequest, user_id: int = 1) -> SubscriptionResponse:
        """创建新订阅"""
        from app.config.template_loader import get_template_loader
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 使用新的模板加载器获取模板信息
            template_loader = get_template_loader()
            template = template_loader.get_template(request.template_id)
            
            if not template:
                raise ValueError(f"订阅模板 {request.template_id} 不存在")
            
            # 验证参数
            is_valid, error_message = template_loader.validate_template_parameters(
                request.template_id, request.parameters
            )
            if not is_valid:
                raise ValueError(f"参数验证失败: {error_message}")
            
            # 生成RSS URL
            rss_url = template_loader.generate_rss_url(request.template_id, request.parameters)
            if not rss_url:
                raise ValueError("生成RSS URL失败")
            
            # 获取主要参数值作为target_user_id（向后兼容）
            target_user_id = list(request.parameters.values())[0] if request.parameters else ""
            
            # 插入订阅记录
            cursor.execute("""
                INSERT INTO user_subscriptions 
                (user_id, template_id, target_user_id, custom_name, rss_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                request.template_id,  # 现在使用字符串ID
                target_user_id,
                request.custom_name,
                rss_url,
                datetime.now()
            ))
            
            subscription_id = cursor.lastrowid
            conn.commit()
            
            # 返回订阅信息
            return SubscriptionResponse(
                id=subscription_id,
                platform=PlatformType(template.platform),
                content_type=ContentType("dynamic"),  # 默认类型
                template_name=template.template_name,
                target_user_id=target_user_id,
                custom_name=request.custom_name,
                rss_url=rss_url,
                is_active=True,
                last_update=None,
                created_at=datetime.now()
            )
    
    def get_user_subscriptions(self, user_id: int = 1, page: int = 1, size: int = 20) -> SubscriptionListResponse:
        """获取用户订阅列表"""
        from app.config.template_loader import get_template_loader
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取总数（包含所有订阅源，不过滤is_active状态）
            cursor.execute("""
                SELECT COUNT(*) FROM user_subscriptions 
                WHERE user_id = ?
            """, (user_id,))
            total = cursor.fetchone()[0]
            
            # 获取分页数据（包含所有订阅源，不过滤is_active状态）
            offset = (page - 1) * size
            cursor.execute("""
                SELECT id, template_id, target_user_id, custom_name, rss_url, 
                       is_active, last_update, created_at
                FROM user_subscriptions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, size, offset))
            
            # 获取模板加载器
            template_loader = get_template_loader()
            
            subscriptions = []
            for row in cursor.fetchall():
                # 从JSON配置文件获取模板信息
                template = template_loader.get_template(row[1])  # template_id
                
                if template:
                    subscription = SubscriptionResponse(
                        id=row[0],
                        platform=PlatformType(template.platform),
                        content_type=ContentType("dynamic"),  # 默认类型
                        template_name=template.template_name,
                        target_user_id=row[2],
                        custom_name=row[3],
                        rss_url=row[4],
                        is_active=bool(row[5]),
                        last_update=datetime.fromisoformat(row[6]) if row[6] else None,
                        created_at=datetime.fromisoformat(row[7])
                    )
                    subscriptions.append(subscription)
            
            return SubscriptionListResponse(
                subscriptions=subscriptions,
                total=total,
                page=page,
                size=size
            )
    
    def delete_subscription(self, subscription_id: int, user_id: int = 1) -> bool:
        """删除订阅（真正删除记录）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM user_subscriptions 
                WHERE id = ? AND user_id = ?
            """, (subscription_id, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def update_subscription_status(self, subscription_id: int, is_active: bool, user_id: int = 1) -> bool:
        """更新订阅状态"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_subscriptions 
                SET is_active = ? 
                WHERE id = ? AND user_id = ?
            """, (is_active, subscription_id, user_id))
            
            conn.commit()
            return cursor.rowcount > 0


# 创建全局实例
subscription_service = SubscriptionService()