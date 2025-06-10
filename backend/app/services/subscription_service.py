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
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        """初始化订阅服务"""
        self.db_path = db_path
        self._init_database()
        self._init_templates()
    
    def _init_database(self):
        """初始化数据库"""
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建订阅模板表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscription_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    url_template TEXT NOT NULL,
                    example_user_id TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建用户订阅表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    template_id INTEGER NOT NULL,
                    target_user_id TEXT NOT NULL,
                    custom_name TEXT,
                    rss_url TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    last_update TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_id) REFERENCES subscription_templates (id)
                )
            """)
            
            conn.commit()
    
    def _init_templates(self):
        """初始化默认模板"""
        templates = [
            {
                "platform": "bilibili",
                "content_type": "video", 
                "name": "B站用户视频",
                "description": "订阅B站用户的最新视频投稿",
                "url_template": "https://rsshub.app/bilibili/user/video/{user_id}",
                "example_user_id": "2267573"
            },
            {
                "platform": "bilibili",
                "content_type": "dynamic",
                "name": "B站用户动态", 
                "description": "订阅B站用户的最新动态",
                "url_template": "https://rsshub.app/bilibili/user/dynamic/{user_id}",
                "example_user_id": "2267573"
            },
            {
                "platform": "weibo",
                "content_type": "post",
                "name": "微博用户动态",
                "description": "订阅微博用户的最新动态",
                "url_template": "https://rsshub.app/weibo/user/{user_id}",
                "example_user_id": "1195230310"
            }
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查是否已有模板
            cursor.execute("SELECT COUNT(*) FROM subscription_templates")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # 插入默认模板
                for template in templates:
                    cursor.execute("""
                        INSERT INTO subscription_templates 
                        (platform, content_type, name, description, url_template, example_user_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        template["platform"],
                        template["content_type"], 
                        template["name"],
                        template["description"],
                        template["url_template"],
                        template["example_user_id"]
                    ))
                
                conn.commit()
    
    def get_templates(self) -> List[SubscriptionTemplate]:
        """获取所有订阅模板"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, platform, content_type, name, description, 
                       url_template, example_user_id, is_active, created_at, updated_at
                FROM subscription_templates 
                WHERE is_active = 1
                ORDER BY id
            """)
            
            templates = []
            for row in cursor.fetchall():
                template = SubscriptionTemplate(
                    id=row[0],
                    platform=PlatformType(row[1]),
                    content_type=ContentType(row[2]),
                    name=row[3],
                    description=row[4],
                    url_template=row[5],
                    example_user_id=row[6],
                    is_active=bool(row[7]),
                    created_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    updated_at=datetime.fromisoformat(row[9]) if row[9] else None
                )
                templates.append(template)
            
            return templates
    
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
                template_name=template.display_name,
                target_user_id=target_user_id,
                custom_name=request.custom_name,
                rss_url=rss_url,
                is_active=True,
                last_update=None,
                created_at=datetime.now()
            )
    
    def get_user_subscriptions(self, user_id: int = 1, page: int = 1, size: int = 20) -> SubscriptionListResponse:
        """获取用户订阅列表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute("""
                SELECT COUNT(*) FROM user_subscriptions 
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))
            total = cursor.fetchone()[0]
            
            # 获取分页数据
            offset = (page - 1) * size
            cursor.execute("""
                SELECT us.id, st.platform, st.content_type, st.name, 
                       us.target_user_id, us.custom_name, us.rss_url, 
                       us.is_active, us.last_update, us.created_at
                FROM user_subscriptions us
                JOIN subscription_templates st ON us.template_id = st.id
                WHERE us.user_id = ? AND us.is_active = 1
                ORDER BY us.created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, size, offset))
            
            subscriptions = []
            for row in cursor.fetchall():
                subscription = SubscriptionResponse(
                    id=row[0],
                    platform=PlatformType(row[1]),
                    content_type=ContentType(row[2]),
                    template_name=row[3],
                    target_user_id=row[4],
                    custom_name=row[5],
                    rss_url=row[6],
                    is_active=bool(row[7]),
                    last_update=datetime.fromisoformat(row[8]) if row[8] else None,
                    created_at=datetime.fromisoformat(row[9])
                )
                subscriptions.append(subscription)
            
            return SubscriptionListResponse(
                subscriptions=subscriptions,
                total=total,
                page=page,
                size=size
            )
    
    def delete_subscription(self, subscription_id: int, user_id: int = 1) -> bool:
        """删除订阅"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_subscriptions 
                SET is_active = 0 
                WHERE id = ? AND user_id = ?
            """, (subscription_id, user_id))
            
            conn.commit()
            return cursor.rowcount > 0 