#!/usr/bin/env python3
"""
用户内容API接口
提供用户内容列表查询、状态更新、统计信息等功能
基于新的共享内容存储架构
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from app.services import shared_content_service, user_content_relation_service
from app.api.api_v1.endpoints.auth import get_current_user
from app.services.user_service import User


router = APIRouter()


# 请求/响应模型
class ContentFilter(BaseModel):
    """内容筛选条件"""
    platform: Optional[str] = Field(None, description="平台筛选")
    subscription_id: Optional[int] = Field(None, description="订阅源筛选")
    is_read: Optional[bool] = Field(None, description="已读状态筛选")
    is_favorited: Optional[bool] = Field(None, description="收藏状态筛选")
    content_type: Optional[str] = Field(None, description="内容类型筛选")
    limit: int = Field(20, ge=1, le=100, description="每页数量")
    offset: int = Field(0, ge=0, description="偏移量")


class ContentStatusUpdate(BaseModel):
    """内容状态更新"""
    is_read: Optional[bool] = Field(None, description="是否已读")
    is_favorited: Optional[bool] = Field(None, description="是否收藏")
    personal_tags: Optional[List[str]] = Field(None, description="个人标签")


class ContentSearchRequest(BaseModel):
    """内容搜索请求"""
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    platform: Optional[str] = Field(None, description="平台筛选")
    limit: int = Field(20, ge=1, le=100, description="每页数量")
    offset: int = Field(0, ge=0, description="偏移量")


class ContentListResponse(BaseModel):
    """内容列表响应"""
    contents: List[Dict[str, Any]]
    total: int
    has_more: bool
    filters_applied: Dict[str, Any]


class ContentStatsResponse(BaseModel):
    """内容统计响应"""
    total_contents: int
    read_count: int
    unread_count: int
    favorited_count: int
    read_percentage: float
    platform_distribution: Dict[str, int]
    subscription_distribution: Dict[str, int]
    system_stats: Dict[str, Any]


@router.get("/users/{user_id}/contents/stats", response_model=ContentStatsResponse)
async def get_user_content_stats(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取用户内容统计信息
    
    返回：
    - 总内容数、已读数、未读数、收藏数
    - 阅读百分比
    - 平台分布统计
    - 订阅源分布统计
    - 系统级统计信息
    """
    try:
        # 权限检查
        if current_user.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问其他用户的统计信息")
        
        # 获取统计信息
        stats = await shared_content_service.get_user_content_stats(user_id)
        
        # 确保所有必需字段都存在
        default_stats = {
            'total_contents': 0,
            'read_count': 0,
            'unread_count': 0,
            'favorited_count': 0,
            'read_percentage': 0.0,
            'platform_distribution': {},
            'subscription_distribution': {},
            'system_stats': {}
        }
        
        # 合并统计数据，确保所有字段都存在
        if stats:
            default_stats.update(stats)
        
        stats = default_stats
        
        logger.info(f"获取用户内容统计: user_id={user_id}")
        
        return ContentStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户内容统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取内容统计失败: {str(e)}")


@router.get("/users/{user_id}/contents", response_model=ContentListResponse)
async def get_user_contents(
    user_id: int,
    platform: Optional[str] = Query(None, description="平台筛选"),
    subscription_id: Optional[int] = Query(None, description="订阅源筛选"),
    is_read: Optional[bool] = Query(None, description="已读状态筛选"),
    is_favorited: Optional[bool] = Query(None, description="收藏状态筛选"),
    content_type: Optional[str] = Query(None, description="内容类型筛选"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户内容列表
    
    支持多种筛选条件：
    - platform: 平台筛选（bilibili, weibo, github等）
    - subscription_id: 订阅源筛选
    - is_read: 已读状态筛选
    - is_favorited: 收藏状态筛选
    - content_type: 内容类型筛选（video, image_text, text）
    """
    try:
        # 权限检查：只能查看自己的内容
        if current_user.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问其他用户的内容")
        
        # 构建筛选条件
        filters = {
            'platform': platform,
            'subscription_id': subscription_id,
            'is_read': is_read,
            'is_favorited': is_favorited,
            'content_type': content_type,
            'limit': limit,
            'offset': offset
        }
        
        # 移除None值
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # 获取用户内容
        contents = await shared_content_service.get_user_contents(user_id, **filters)
        
        # 计算是否还有更多内容
        has_more = len(contents) == limit
        
        logger.info(f"获取用户内容列表: user_id={user_id}, 返回{len(contents)}条")
        
        return ContentListResponse(
            contents=contents,
            total=len(contents),  # 注意：这里是当前页的数量，不是总数
            has_more=has_more,
            filters_applied=filters
        )
        
    except Exception as e:
        logger.error(f"获取用户内容列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取内容列表失败: {str(e)}")


@router.put("/users/{user_id}/contents/{content_id}")
async def update_content_status(
    user_id: int,
    content_id: int,
    update_data: ContentStatusUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    更新内容状态
    
    支持更新：
    - is_read: 已读状态
    - is_favorited: 收藏状态
    - personal_tags: 个人标签
    """
    try:
        # 权限检查
        if current_user.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权修改其他用户的内容状态")
        
        # 构建更新数据
        updates = {}
        if update_data.is_read is not None:
            updates['is_read'] = update_data.is_read
        if update_data.is_favorited is not None:
            updates['is_favorited'] = update_data.is_favorited
        if update_data.personal_tags is not None:
            updates['personal_tags'] = update_data.personal_tags
        
        if not updates:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        # 执行更新
        success = await shared_content_service.update_content_status(
            user_id, content_id, **updates
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="内容不存在或已过期")
        
        logger.info(f"更新内容状态: user_id={user_id}, content_id={content_id}, updates={updates}")
        
        return {"message": "内容状态更新成功", "updated_fields": list(updates.keys())}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新内容状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新内容状态失败: {str(e)}")


@router.get("/users/{user_id}/contents/{content_id}")
async def get_content_detail(
    user_id: int,
    content_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取内容详情
    
    返回完整的内容信息，包括：
    - 基础内容信息
    - 媒体项列表
    - 用户个人状态
    - AI处理结果
    """
    try:
        # 权限检查
        if current_user.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问其他用户的内容")
        
        # 获取内容详情
        content = await shared_content_service.get_content_detail(content_id, user_id)
        
        if not content:
            raise HTTPException(status_code=404, detail="内容不存在或已过期")
        
        logger.info(f"获取内容详情: user_id={user_id}, content_id={content_id}")
        
        return content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取内容详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取内容详情失败: {str(e)}")


@router.post("/users/{user_id}/contents/search")
async def search_user_contents(
    user_id: int,
    search_request: ContentSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    搜索用户内容
    
    支持：
    - 关键词搜索（标题、描述、作者）
    - 平台筛选
    - 分页
    """
    try:
        # 权限检查
        if current_user.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权搜索其他用户的内容")
        
        # 执行搜索
        results = await shared_content_service.search_user_contents(
            user_id=user_id,
            keyword=search_request.keyword,
            platform=search_request.platform,
            limit=search_request.limit,
            offset=search_request.offset
        )
        
        logger.info(f"搜索用户内容: user_id={user_id}, keyword={search_request.keyword}, 结果{len(results)}条")
        
        return {
            "keyword": search_request.keyword,
            "results": results,
            "total": len(results),
            "has_more": len(results) == search_request.limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索用户内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索内容失败: {str(e)}")


@router.post("/users/{user_id}/contents/{content_id}/extend")
async def extend_content_expiry(
    user_id: int,
    content_id: int,
    extend_hours: int = Query(24, ge=1, le=168, description="延长时间（小时）"),
    current_user: User = Depends(get_current_user)
):
    """
    延长内容过期时间
    
    用户可以延长感兴趣内容的查看时间
    最多可延长7天（168小时）
    """
    try:
        # 权限检查
        if current_user.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权操作其他用户的内容")
        
        # 延长过期时间
        success = await user_content_relation_service.extend_content_expiry(
            user_id, content_id, extend_hours
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="内容不存在或操作失败")
        
        logger.info(f"延长内容过期时间: user_id={user_id}, content_id={content_id}, hours={extend_hours}")
        
        return {
            "message": f"内容过期时间已延长{extend_hours}小时",
            "content_id": content_id,
            "extended_hours": extend_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"延长内容过期时间失败: {e}")
        raise HTTPException(status_code=500, detail=f"延长过期时间失败: {str(e)}")


@router.delete("/admin/contents/cleanup")
async def cleanup_expired_contents(
    current_user: User = Depends(get_current_user)
):
    """
    清理过期内容（管理员接口）
    
    清理：
    - 过期的用户内容关系
    - 孤立的共享内容
    - 相关媒体项
    """
    try:
        # 简单的管理员权限检查（实际项目中应该有更严格的权限控制）
        if not getattr(current_user, "is_admin", False):
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 执行清理
        result = await shared_content_service.cleanup_expired_content()
        
        logger.info(f"清理过期内容: {result}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理过期内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理过期内容失败: {str(e)}")


# 批量操作请求模型
class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    content_ids: List[int] = Field(..., description="内容ID列表")
    update_data: ContentStatusUpdate = Field(..., description="更新数据")


# 批量操作接口
@router.post("/users/{user_id}/contents/batch-update")
async def batch_update_content_status(
    user_id: int,
    request: BatchUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    批量更新内容状态
    
    支持批量标记已读、收藏等操作
    """
    try:
        # 权限检查
        if current_user.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权修改其他用户的内容状态")
        
        if not request.content_ids:
            raise HTTPException(status_code=400, detail="内容ID列表不能为空")
        
        # 构建更新数据
        updates = {}
        if request.update_data.is_read is not None:
            updates['is_read'] = request.update_data.is_read
        if request.update_data.is_favorited is not None:
            updates['is_favorited'] = request.update_data.is_favorited
        if request.update_data.personal_tags is not None:
            updates['personal_tags'] = request.update_data.personal_tags
        
        if not updates:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        # 批量更新
        success_count = 0
        failed_count = 0
        
        for content_id in request.content_ids:
            try:
                success = await shared_content_service.update_content_status(
                    user_id, content_id, **updates
                )
                if success:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.warning(f"批量更新单条内容失败: content_id={content_id}, error={e}")
                failed_count += 1
        
        logger.info(f"批量更新内容状态: user_id={user_id}, 成功{success_count}条, 失败{failed_count}条")
        
        return {
            "message": "批量更新完成",
            "total_requested": len(request.content_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "updated_fields": list(updates.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量更新内容状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量更新失败: {str(e)}")


# 内容统计接口（按时间范围）
@router.get("/users/{user_id}/contents/stats/timeline")
async def get_content_timeline_stats(
    user_id: int,
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户内容时间线统计
    
    返回指定天数内的内容统计趋势
    """
    try:
        # 权限检查
        if current_user.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问其他用户的统计信息")
        
        # 这里可以实现更复杂的时间线统计
        # 目前返回基础统计信息
        stats = await shared_content_service.get_user_content_stats(user_id)
        
        logger.info(f"获取用户内容时间线统计: user_id={user_id}, days={days}")
        
        return {
            "user_id": user_id,
            "days": days,
            "stats": stats,
            "message": "时间线统计功能待完善"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取内容时间线统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取时间线统计失败: {str(e)}") 