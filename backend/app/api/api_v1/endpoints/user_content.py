"""
用户内容管理端点
提供用户维度的内容列表、分页、标签筛选和推荐功能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import sqlite3
import json

from fastapi import APIRouter, HTTPException, status, Query, Path
from pydantic import BaseModel
from loguru import logger

from app.services.tag_cache_service import tag_cache_service

router = APIRouter()


class MediaItem(BaseModel):
    """媒体项模型"""
    url: str
    type: str  # image/video/audio
    description: Optional[str] = None
    duration: Optional[int] = None  # 视频时长（秒）


class ContentItem(BaseModel):
    """用户内容项模型"""
    content_id: int
    subscription_id: int
    title: str
    link: str
    summary: Optional[str] = None
    description: Optional[str] = None  # HTML内容描述
    published_at: str
    fetched_at: str
    is_favorited: bool = False
    tags: List[str] = []
    platform: str
    source_name: str
    author: Optional[str] = None
    cover_image: Optional[str] = None
    media_items: List[MediaItem] = []
    content_type: str = "text"  # video/image_text/text


class TagItem(BaseModel):
    """标签项模型"""
    name: str
    count: int


class ContentListData(BaseModel):
    """内容列表数据模型"""
    items: List[ContentItem]
    total: int
    page: int
    limit: int
    has_next: bool


class UserContentResponse(BaseModel):
    """用户内容响应模型"""
    content: ContentListData
    filter_tags: List[TagItem]
    tags_updated_at: Optional[str] = None
    content_updated_at: Optional[str] = None


class UserContentService:
    """用户内容服务"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        self.db_path = db_path
    
    def get_user_content_list(
        self, 
        user_id: int, 
        tag: Optional[str] = None, 
        page: int = 1, 
        limit: int = 20
    ) -> UserContentResponse:
        """获取用户内容列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 1. 获取用户的推荐标签（使用缓存服务）
                cached_tags = tag_cache_service.get_user_tags_with_cache(user_id)
                filter_tags = [TagItem(name=tag["name"], count=tag["count"]) for tag in cached_tags]
                
                # 2. 构建内容查询SQL（使用新的shared_contents架构）
                base_query = """
                    SELECT 
                        c.id, r.subscription_id, c.title, c.original_link,
                        c.description, c.published_at, c.created_at,
                        r.is_favorited, c.tags, c.platform, c.feed_title,
                        c.author, c.cover_image, c.content_type, c.summary,
                        r.is_read, r.read_at, r.personal_tags
                    FROM shared_contents c
                    JOIN user_content_relations r ON c.id = r.content_id
                    JOIN user_subscriptions us ON r.subscription_id = us.id
                    WHERE r.user_id = ? AND r.expires_at > datetime('now')
                """
                
                params = [user_id]
                
                # 添加标签筛选
                if tag and tag != "全部":
                    base_query += " AND json_extract(c.tags, '$') LIKE ?"
                    params.append(f'%"{tag}"%')
                
                # 3. 获取总数
                count_query = f"SELECT COUNT(*) FROM ({base_query})"
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                
                # 4. 添加排序和分页
                content_query = base_query + " ORDER BY c.published_at DESC LIMIT ? OFFSET ?"
                offset = (page - 1) * limit
                params.extend([limit, offset])
                
                cursor.execute(content_query, params)
                rows = cursor.fetchall()
                
                # 5. 处理内容数据（适配新架构字段）
                content_items = []
                for row in rows:
                    # 获取媒体项（使用shared_content_media_items表）
                    media_items = self._get_content_media_items(cursor, row[0])
                    
                    # 解析标签
                    tags = json.loads(row[8]) if row[8] else []
                    
                    content_item = ContentItem(
                        content_id=row[0],         # c.id
                        subscription_id=row[1],    # r.subscription_id  
                        title=row[2],              # c.title
                        link=row[3],               # c.original_link
                        description=row[4],        # c.description
                        published_at=row[5],       # c.published_at
                        fetched_at=row[6],         # c.created_at
                        is_favorited=bool(row[7]), # r.is_favorited
                        tags=tags,                 # c.tags (row[8])
                        platform=row[9],           # c.platform
                        source_name=row[10],       # c.feed_title
                        author=row[11],            # c.author
                        cover_image=row[12],       # c.cover_image
                        content_type=row[13],      # c.content_type
                        summary=row[14],           # c.summary
                        media_items=media_items    # 关联查询结果
                    )
                    content_items.append(content_item)
                
                # 6. 构建响应
                content_data = ContentListData(
                    items=content_items,
                    total=total,
                    page=page,
                    limit=limit,
                    has_next=offset + len(content_items) < total
                )
                
                return UserContentResponse(
                    content=content_data,
                    filter_tags=filter_tags,
                    tags_updated_at=datetime.now().isoformat(),
                    content_updated_at=datetime.now().isoformat()
                )
                
        except Exception as e:
            logger.error(f"获取用户内容列表失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取用户内容列表失败: {str(e)}"
            )
    
    def _get_user_recommended_tags(self, cursor: sqlite3.Cursor, user_id: int) -> List[TagItem]:
        """获取用户推荐标签（基于用户订阅内容统计）"""
        try:
            # 查询用户所有内容的标签统计（使用新架构）
            query = """
                SELECT 
                    tag_value,
                    COUNT(*) as tag_count
                FROM (
                    SELECT json_each.value as tag_value
                    FROM shared_contents c
                    JOIN user_content_relations r ON c.id = r.content_id
                    JOIN json_each(c.tags) 
                    WHERE r.user_id = ? 
                    AND r.expires_at > datetime('now')
                    AND c.tags IS NOT NULL 
                    AND c.tags != 'null'
                    AND c.tags != '[]'
                )
                GROUP BY tag_value
                ORDER BY tag_count DESC
                LIMIT 10
            """
            
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            tags = []
            for row in rows:
                if row[0] and row[0].strip():  # 过滤空标签
                    tags.append(TagItem(name=row[0], count=row[1]))
            
            return tags
            
        except Exception as e:
            logger.warning(f"获取用户推荐标签失败: {e}")
            return []
    
    def _get_content_media_items(self, cursor: sqlite3.Cursor, content_id: int) -> List[MediaItem]:
        """获取内容的媒体项（使用新架构的shared_content_media_items表）"""
        try:
            cursor.execute("""
                SELECT url, media_type, description, duration
                FROM shared_content_media_items
                WHERE content_id = ?
                ORDER BY sort_order
            """, (content_id,))
            
            rows = cursor.fetchall()
            media_items = []
            
            for row in rows:
                media_item = MediaItem(
                    url=row[0],
                    type=row[1],
                    description=row[2],
                    duration=row[3]
                )
                media_items.append(media_item)
            
            return media_items
            
        except Exception as e:
            logger.warning(f"获取媒体项失败: {e}")
            return []


# 创建服务实例
user_content_service = UserContentService()


@router.get("/users/{user_id}/content", response_model=UserContentResponse, summary="获取用户内容列表")
async def get_user_content(
    user_id: int = Path(..., description="用户ID"),
    tag: Optional[str] = Query(None, description="标签筛选"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量")
) -> UserContentResponse:
    """
    获取用户内容列表，支持分页和标签筛选
    
    功能特性：
    - 用户维度的内容查询（基于用户订阅）
    - 分页支持
    - 标签筛选（单选模式）
    - 推荐标签（基于用户内容统计）
    - 实时内容更新
    """
    try:
        logger.info(f"获取用户{user_id}内容列表: tag={tag}, page={page}, limit={limit}")
        
        result = user_content_service.get_user_content_list(
            user_id=user_id,
            tag=tag,
            page=page,
            limit=limit
        )
        
        logger.info(f"返回内容: {len(result.content.items)}条, 总计: {result.content.total}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户内容列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户内容列表过程中发生错误"
        )


@router.get("/users/{user_id}/tags", response_model=List[TagItem], summary="获取用户推荐标签")
async def get_user_tags(
    user_id: int = Path(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50, description="标签数量限制")
) -> List[TagItem]:
    """
    获取用户推荐标签列表
    
    基于用户订阅内容的标签使用频次统计，返回最热门的标签
    """
    try:
        logger.info(f"获取用户{user_id}推荐标签")
        
        with sqlite3.connect(user_content_service.db_path) as conn:
            cursor = conn.cursor()
            tags = user_content_service._get_user_recommended_tags(cursor, user_id)
            
        return tags[:limit]
        
    except Exception as e:
        logger.error(f"获取用户推荐标签失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户推荐标签过程中发生错误"
        ) 