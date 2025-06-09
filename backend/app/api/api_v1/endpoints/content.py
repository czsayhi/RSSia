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


class ContentItem(BaseModel):
    """内容条目模型"""
    content_id: int
    subscription_id: int
    title: str
    link: str
    summary: Optional[str]
    published_at: str
    fetched_at: str
    is_favorited: bool = False
    tags: List[str] = []
    platform: str
    source_name: str


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
                published_at="2024-02-08T14:16:54Z",
                fetched_at=datetime.now().isoformat(),
                is_favorited=False,
                tags=["游戏", "幻兽帕鲁"],
                platform="bilibili",
                source_name="DIYgod的B站视频"
            ),
            ContentItem(
                content_id=2,
                subscription_id=2,
                title="以 LIVE 为冠，用真实卫冕。#歌手2025# 今晚开唱...",
                link="https://weibo.com/1195230310/Ps71KgDlL",
                summary="何炅关于歌手2025节目的微博分享...",
                published_at="2025-05-16T10:52:19Z",
                fetched_at=datetime.now().isoformat(),
                is_favorited=True,
                tags=["娱乐", "音乐"],
                platform="weibo",
                source_name="何炅的微博"
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


@router.get("/{content_id}", response_model=ContentItem, summary="获取内容详情")
async def get_content_detail(content_id: int) -> ContentItem:
    """
    获取指定内容的详细信息
    """
    try:
        # TODO: 从数据库查询内容详情
        
        # MVP阶段：返回模拟数据
        if content_id == 1:
            return ContentItem(
                content_id=1,
                subscription_id=1,
                title="【幻兽帕鲁】佐伊塔主暴揍佐伊塔主",
                link="https://www.bilibili.com/video/BV1eu4m1N7cL",
                summary="这是一个关于幻兽帕鲁游戏的视频，展示了佐伊塔主的游戏过程和技巧分享。视频内容包括游戏机制介绍、战斗技巧演示和娱乐解说。",
                published_at="2024-02-08T14:16:54Z",
                fetched_at=datetime.now().isoformat(),
                is_favorited=False,
                tags=["游戏", "幻兽帕鲁", "攻略"],
                platform="bilibili",
                source_name="DIYgod的B站视频"
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