"""
内容管理端点
提供RSS内容的查询、筛选、收藏等功能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from loguru import logger

router = APIRouter()


class MediaItem(BaseModel):
    """媒体项模型"""
    url: str
    type: str  # image/video/audio
    description: Optional[str] = None
    duration: Optional[int] = None  # 视频时长（秒）


class ContentItem(BaseModel):
    """内容条目模型"""
    content_id: int
    subscription_id: int
    title: str
    link: str
    summary: Optional[str]
    description: Optional[str] = None  # HTML内容描述
    published_at: str
    fetched_at: str
    is_favorited: bool = False
    tags: List[str] = []
    platform: str
    source_name: str
    # 新增字段
    author: Optional[str] = None
    cover_image: Optional[str] = None
    media_items: List[MediaItem] = []
    content_type: str = "text"  # video/image_text/text


class RelatedContentItem(BaseModel):
    """相关内容条目模型（用于详情页推荐）"""
    content_id: int
    title: str
    cover_image: Optional[str] = None
    content_type: str = "text"  # video/image_text/text
    published_at: str
    duration: Optional[int] = None  # 视频时长（秒），仅video类型使用


class ContentDetailResponse(BaseModel):
    """内容详情响应模型（包含相关内容推荐）"""
    # 主要内容信息
    content: ContentItem
    
    # 相关内容推荐（同一订阅源的其他内容）
    related_contents: List[RelatedContentItem] = []
    
    # 元信息
    subscription_info: Dict[str, Any] = {}


class ContentFilter(BaseModel):
    """内容筛选模型"""
    subscription_id: Optional[int] = None
    platform: Optional[str] = None
    is_favorited: Optional[bool] = None
    tags: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@router.get("/", response_model=List[ContentItem], summary="获取内容列表")
async def get_content_list(
    subscription_id: Optional[int] = Query(None, description="订阅ID筛选"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    is_favorited: Optional[bool] = Query(None, description="收藏状态筛选"),
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(20, ge=1, le=100, description="返回条数")
) -> List[ContentItem]:
    """
    获取RSS内容列表
    支持多种筛选条件和分页
    """
    try:
        # TODO: 从数据库查询内容列表
        # TODO: 应用筛选条件
        # TODO: 实现分页
        
        # MVP阶段：返回模拟数据
        mock_content = [
            ContentItem(
                content_id=1,
                subscription_id=1,
                title="【幻兽帕鲁】佐伊塔主暴揍佐伊塔主",
                link="https://www.bilibili.com/video/BV1eu4m1N7cL",
                summary="幻兽帕鲁游戏视频，佐伊塔主相关内容...",
                description="<p>这是一个关于幻兽帕鲁游戏的视频内容，包含游戏机制介绍和战斗技巧演示。</p>",
                published_at="2024-02-08T14:16:54Z",
                fetched_at=datetime.now().isoformat(),
                is_favorited=False,
                tags=["游戏", "幻兽帕鲁"],
                platform="bilibili",
                source_name="DIYgod的B站视频",
                author="DIYgod",
                cover_image="https://i0.hdslb.com/bfs/archive/example_cover.jpg",
                media_items=[
                    MediaItem(
                        url="https://www.bilibili.com/video/BV1eu4m1N7cL",
                        type="video",
                        description="幻兽帕鲁游戏视频",
                        duration=720
                    )
                ],
                content_type="video"
            ),
            ContentItem(
                content_id=2,
                subscription_id=2,
                title="以 LIVE 为冠，用真实卫冕。#歌手2025# 今晚开唱...",
                link="https://weibo.com/1195230310/Ps71KgDlL",
                summary="何炅关于歌手2025节目的微博分享...",
                description="<p>以 LIVE 为冠，用真实卫冕。#歌手2025# 今晚开唱，期待精彩表演！</p>",
                published_at="2025-05-16T10:52:19Z",
                fetched_at=datetime.now().isoformat(),
                is_favorited=True,
                tags=["娱乐", "音乐"],
                platform="weibo",
                source_name="何炅的微博",
                author="何炅",
                cover_image="https://wx1.sinaimg.cn/mw2000/example_weibo_image.jpg",
                media_items=[
                    MediaItem(
                        url="https://wx1.sinaimg.cn/mw2000/singer2025_poster.jpg",
                        type="image",
                        description="歌手2025节目海报"
                    ),
                    MediaItem(
                        url="https://wx2.sinaimg.cn/mw2000/backstage_photo.jpg",
                        type="image",
                        description="后台准备照片"
                    )
                ],
                content_type="image_text"
            )
        ]
        
        # 应用筛选
        filtered_content = mock_content
        if subscription_id:
            filtered_content = [c for c in filtered_content if c.subscription_id == subscription_id]
        if platform:
            filtered_content = [c for c in filtered_content if c.platform == platform]
        if is_favorited is not None:
            filtered_content = [c for c in filtered_content if c.is_favorited == is_favorited]
        
        # 应用分页
        paginated_content = filtered_content[skip:skip+limit]
        
        return paginated_content
    except Exception as e:
        logger.error(f"获取内容列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取内容列表过程中发生错误"
        )


@router.get("/{content_id}", response_model=ContentDetailResponse, summary="获取内容详情")
async def get_content_detail(
    content_id: int,
    include_related: bool = Query(True, description="是否包含相关内容推荐"),
    related_limit: int = Query(6, ge=1, le=20, description="相关内容数量限制")
) -> ContentDetailResponse:
    """
    获取指定内容的详细信息，包含同一订阅源的其他内容推荐
    
    相关内容推荐规则：
    - 来自同一个订阅源（subscription_id相同）
    - 排除当前内容
    - 按发布时间倒序排列
    - 只返回简化信息：content_id、title、cover_image、content_type、published_at
    """
    try:
        # TODO: 从数据库查询内容详情
        
        # MVP阶段：返回模拟数据
        if content_id == 1:
            main_content = ContentItem(
                content_id=1,
                subscription_id=1,
                title="【幻兽帕鲁】佐伊塔主暴揍佐伊塔主",
                link="https://www.bilibili.com/video/BV1eu4m1N7cL",
                summary="这是一个关于幻兽帕鲁游戏的视频，展示了佐伊塔主的游戏过程和技巧分享。视频内容包括游戏机制介绍、战斗技巧演示和娱乐解说。",
                description="<div><p>这是一个关于幻兽帕鲁游戏的详细视频内容。</p><p>视频主要包含以下内容：</p><ul><li>游戏机制详细介绍</li><li>佐伊塔主角色分析</li><li>战斗技巧演示</li><li>游戏攻略分享</li></ul><p>适合所有幻兽帕鲁玩家观看学习。</p></div>",
                published_at="2024-02-08T14:16:54Z",
                fetched_at=datetime.now().isoformat(),
                is_favorited=False,
                tags=["游戏", "幻兽帕鲁", "攻略"],
                platform="bilibili",
                source_name="DIYgod的B站视频",
                author="DIYgod",
                cover_image="https://i0.hdslb.com/bfs/archive/palu_video_cover.jpg",
                media_items=[
                    MediaItem(
                        url="https://www.bilibili.com/video/BV1eu4m1N7cL",
                        type="video",
                        description="幻兽帕鲁游戏视频 - 佐伊塔主攻略",
                        duration=720
                    ),
                    MediaItem(
                        url="https://i0.hdslb.com/bfs/archive/palu_screenshot1.jpg",
                        type="image",
                        description="游戏截图1 - 佐伊塔主形象"
                    ),
                    MediaItem(
                        url="https://i0.hdslb.com/bfs/archive/palu_screenshot2.jpg",
                        type="image",
                        description="游戏截图2 - 战斗场景"
                    )
                ],
                content_type="video"
            )
            
            # 模拟相关内容推荐（同一订阅源的其他内容）
            related_contents = []
            if include_related:
                related_contents = [
                    RelatedContentItem(
                        content_id=3,
                        title="【技术分享】如何构建现代化的RSS订阅器",
                        cover_image="https://i0.hdslb.com/bfs/archive/tech_cover.jpg",
                        content_type="video",
                        published_at="2024-02-06T10:30:00Z",
                        duration=1280  # 21分20秒
                    ),
                    RelatedContentItem(
                        content_id=4,
                        title="开源项目RSSHub使用指南",
                        cover_image="https://i0.hdslb.com/bfs/archive/rsshub_cover.jpg",
                        content_type="image_text",
                        published_at="2024-02-04T15:20:00Z"
                    ),
                    RelatedContentItem(
                        content_id=5,
                        title="前端开发最佳实践分享",
                        cover_image=None,  # 纯文本内容没有封面
                        content_type="text",
                        published_at="2024-02-02T09:15:00Z"
                    ),
                    RelatedContentItem(
                        content_id=6,
                        title="JavaScript异步编程深度解析",
                        cover_image="https://i0.hdslb.com/bfs/archive/js_async.jpg",
                        content_type="video",
                        published_at="2024-01-30T16:45:00Z",
                        duration=2145  # 35分45秒
                    ),
                    RelatedContentItem(
                        content_id=7,
                        title="Vue3组件设计模式",
                        cover_image="https://i0.hdslb.com/bfs/archive/vue3_pattern.jpg",
                        content_type="image_text",
                        published_at="2024-01-28T11:20:00Z"
                    ),
                    RelatedContentItem(
                        content_id=8,
                        title="Docker容器化部署实战",
                        cover_image="https://i0.hdslb.com/bfs/archive/docker_deploy.jpg",
                        content_type="video",
                        published_at="2024-01-25T13:30:00Z",
                        duration=1650  # 27分30秒
                    )
                ]
            
            return ContentDetailResponse(
                content=main_content,
                related_contents=related_contents[:related_limit],
                subscription_info={
                    "subscription_id": 1,
                    "name": "DIYgod的B站视频",
                    "platform": "bilibili",
                    "description": "关注DIYgod的技术分享和开源项目",
                    "total_contents": 15  # 该订阅源总共有15篇内容
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="内容不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取内容详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取内容详情过程中发生错误"
        )


@router.post("/{content_id}/favorite", summary="收藏内容")
async def favorite_content(content_id: int) -> Dict[str, Any]:
    """
    收藏指定的内容
    """
    try:
        # TODO: 更新数据库中的收藏状态
        
        logger.info(f"收藏内容: {content_id}")
        
        return {
            "message": "收藏成功",
            "content_id": content_id,
            "is_favorited": True,
            "favorited_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"收藏内容失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="收藏内容过程中发生错误"
        )


@router.delete("/{content_id}/favorite", summary="取消收藏")
async def unfavorite_content(content_id: int) -> Dict[str, Any]:
    """
    取消收藏指定的内容
    """
    try:
        # TODO: 更新数据库中的收藏状态
        
        logger.info(f"取消收藏内容: {content_id}")
        
        return {
            "message": "取消收藏成功",
            "content_id": content_id,
            "is_favorited": False,
            "unfavorited_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"取消收藏失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消收藏过程中发生错误"
        )


@router.get("/search/", response_model=List[ContentItem], summary="搜索内容")
async def search_content(
    query: str = Query(..., description="搜索关键词"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(20, ge=1, le=100, description="返回条数")
) -> List[ContentItem]:
    """
    根据关键词搜索内容
    """
    try:
        # TODO: 实现全文搜索功能
        
        logger.info(f"搜索内容: {query}")
        
        # MVP阶段：返回模拟搜索结果
        if "帕鲁" in query:
            return [
                ContentItem(
                    content_id=1,
                    subscription_id=1,
                    title="【幻兽帕鲁】佐伊塔主暴揍佐伊塔主",
                    link="https://www.bilibili.com/video/BV1eu4m1N7cL",
                    summary="幻兽帕鲁游戏视频，佐伊塔主相关内容...",
                    published_at="2024-02-08T14:16:54Z",
                    fetched_at=datetime.now().isoformat(),
                    is_favorited=False,
                    tags=["游戏", "幻兽帕鲁"],
                    platform="bilibili",
                    source_name="DIYgod的B站视频"
                )
            ]
        else:
            return []
    except Exception as e:
        logger.error(f"搜索内容失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索内容过程中发生错误"
        )


@router.get("/subscription/{subscription_id}", response_model=List[RelatedContentItem], summary="获取订阅源内容列表")
async def get_subscription_contents(
    subscription_id: int,
    exclude_content_id: Optional[int] = Query(None, description="排除的内容ID"),
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(20, ge=1, le=100, description="返回条数")
) -> List[RelatedContentItem]:
    """
    获取指定订阅源的内容列表（简化信息）
    
    主要用于：
    - 订阅源详情页展示所有内容
    - 内容详情页的"查看更多"功能
    - 支持排除指定内容（避免重复显示当前内容）
    """
    try:
        # TODO: 从数据库查询指定订阅源的内容列表
        
        # MVP阶段：返回模拟数据
        mock_contents = [
            RelatedContentItem(
                content_id=1,
                title="【幻兽帕鲁】佐伊塔主暴揍佐伊塔主",
                cover_image="https://i0.hdslb.com/bfs/archive/palu_cover.jpg",
                content_type="video",
                published_at="2024-02-08T14:16:54Z"
            ),
            RelatedContentItem(
                content_id=3,
                title="【技术分享】如何构建现代化的RSS订阅器",
                cover_image="https://i0.hdslb.com/bfs/archive/tech_cover.jpg",
                content_type="video",
                published_at="2024-02-06T10:30:00Z"
            ),
            RelatedContentItem(
                content_id=4,
                title="开源项目RSSHub使用指南",
                cover_image="https://i0.hdslb.com/bfs/archive/rsshub_cover.jpg",
                content_type="image_text",
                published_at="2024-02-04T15:20:00Z"
            ),
            RelatedContentItem(
                content_id=5,
                title="前端开发最佳实践分享",
                cover_image=None,
                content_type="text",
                published_at="2024-02-02T09:15:00Z"
            ),
            RelatedContentItem(
                content_id=6,
                title="JavaScript异步编程深度解析",
                cover_image="https://i0.hdslb.com/bfs/archive/js_async.jpg",
                content_type="video",
                published_at="2024-01-30T16:45:00Z"
            ),
            RelatedContentItem(
                content_id=7,
                title="Vue3组件设计模式",
                cover_image="https://i0.hdslb.com/bfs/archive/vue3_pattern.jpg",
                content_type="image_text",
                published_at="2024-01-28T11:20:00Z"
            ),
            RelatedContentItem(
                content_id=8,
                title="Docker容器化部署实战",
                cover_image="https://i0.hdslb.com/bfs/archive/docker_deploy.jpg",
                content_type="video",
                published_at="2024-01-25T13:30:00Z"
            )
        ]
        
        # 过滤指定订阅源的内容
        filtered_contents = mock_contents  # 这里假设mock数据都属于subscription_id=1
        
        # 排除指定内容
        if exclude_content_id:
            filtered_contents = [c for c in filtered_contents if c.content_id != exclude_content_id]
        
        # 应用分页
        paginated_contents = filtered_contents[skip:skip+limit]
        
        logger.info(f"获取订阅源{subscription_id}内容: {len(paginated_contents)}条")
        return paginated_contents
        
    except Exception as e:
        logger.error(f"获取订阅源内容失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订阅源内容过程中发生错误"
        ) 