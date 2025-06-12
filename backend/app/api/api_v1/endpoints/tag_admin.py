"""
标签管理端点
提供标签缓存的监控、手动触发和管理功能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query, Path
from pydantic import BaseModel
from loguru import logger

from app.services.tag_cache_service import tag_cache_service
from app.scheduler.tag_scheduler import tag_scheduler

router = APIRouter()


class TagCacheStatus(BaseModel):
    """标签缓存状态"""
    user_id: int
    tags_count: int
    last_updated: str
    content_count: int
    cache_age_minutes: int


class SchedulerJobStatus(BaseModel):
    """调度器任务状态"""
    id: str
    name: str
    next_run: Optional[str]
    trigger: str


class TagAdminResponse(BaseModel):
    """标签管理响应"""
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/admin/tags/status", response_model=List[TagCacheStatus], summary="获取标签缓存状态")
async def get_tag_cache_status() -> List[TagCacheStatus]:
    """
    获取所有用户的标签缓存状态
    用于监控缓存健康度和性能
    """
    try:
        import sqlite3
        
        with sqlite3.connect(tag_cache_service.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    user_id, 
                    tags_json,
                    content_count,
                    last_updated,
                    created_at
                FROM user_tag_cache
                ORDER BY last_updated DESC
            """)
            
            rows = cursor.fetchall()
            cache_status = []
            
            for row in rows:
                user_id, tags_json, content_count, last_updated, created_at = row
                
                # 计算缓存年龄
                cache_time = datetime.fromisoformat(last_updated)
                cache_age = (datetime.now() - cache_time).total_seconds() / 60
                
                # 解析标签数量
                import json
                tags = json.loads(tags_json) if tags_json else []
                
                status_item = TagCacheStatus(
                    user_id=user_id,
                    tags_count=len(tags),
                    last_updated=last_updated,
                    content_count=content_count,
                    cache_age_minutes=int(cache_age)
                )
                cache_status.append(status_item)
            
            return cache_status
            
    except Exception as e:
        logger.error(f"获取标签缓存状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取标签缓存状态失败"
        )


@router.get("/admin/tags/jobs", response_model=List[SchedulerJobStatus], summary="获取调度器任务状态")
async def get_scheduler_job_status() -> List[SchedulerJobStatus]:
    """
    获取标签缓存调度器的任务状态
    用于监控定时任务运行情况
    """
    try:
        job_status = tag_scheduler.get_job_status()
        
        scheduler_jobs = []
        for job in job_status:
            scheduler_job = SchedulerJobStatus(
                id=job["id"],
                name=job["name"],
                next_run=job["next_run"],
                trigger=job["trigger"]
            )
            scheduler_jobs.append(scheduler_job)
        
        return scheduler_jobs
        
    except Exception as e:
        logger.error(f"获取调度器任务状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取调度器任务状态失败"
        )


@router.post("/admin/tags/update", response_model=TagAdminResponse, summary="手动触发标签更新")
async def trigger_tag_update(
    user_id: Optional[int] = Query(None, description="指定用户ID，不指定则更新所有需要更新的用户")
) -> TagAdminResponse:
    """
    手动触发标签缓存更新
    可以指定用户ID或更新所有需要更新的用户
    """
    try:
        result = tag_scheduler.trigger_manual_update(user_id)
        
        if user_id:
            message = f"用户{user_id}标签缓存更新成功"
        else:
            message = f"批量标签缓存更新完成: 成功{result['success']}个, 失败{result['error']}个"
        
        return TagAdminResponse(
            message=message,
            data=result
        )
        
    except Exception as e:
        logger.error(f"手动触发标签更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"手动触发标签更新失败: {str(e)}"
        )


@router.delete("/admin/tags/cache", response_model=TagAdminResponse, summary="清理过期缓存")
async def cleanup_expired_cache(
    days: int = Query(7, ge=1, le=30, description="清理几天前的缓存")
) -> TagAdminResponse:
    """
    手动清理过期的标签缓存
    """
    try:
        deleted_count = tag_cache_service.cleanup_expired_cache(days)
        
        return TagAdminResponse(
            message=f"过期缓存清理完成，删除{deleted_count}条记录",
            data={"deleted_count": deleted_count, "days": days}
        )
        
    except Exception as e:
        logger.error(f"清理过期缓存失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理过期缓存失败: {str(e)}"
        )


@router.get("/admin/tags/stats", response_model=TagAdminResponse, summary="获取标签统计信息")
async def get_tag_stats() -> TagAdminResponse:
    """
    获取标签系统的统计信息
    包括缓存命中率、用户数量、平均标签数等
    """
    try:
        import sqlite3
        
        with sqlite3.connect(tag_cache_service.db_path) as conn:
            cursor = conn.cursor()
            
            # 统计信息
            stats = {}
            
            # 1. 缓存用户总数
            cursor.execute("SELECT COUNT(*) FROM user_tag_cache")
            stats["cached_users"] = cursor.fetchone()[0]
            
            # 2. 活跃用户总数（有订阅的用户）
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_subscriptions WHERE is_active = 1")
            stats["active_users"] = cursor.fetchone()[0]
            
            # 3. 平均标签数
            cursor.execute("""
                SELECT AVG(json_array_length(tags_json)) 
                FROM user_tag_cache 
                WHERE tags_json IS NOT NULL
            """)
            avg_tags = cursor.fetchone()[0]
            stats["avg_tags_per_user"] = float(avg_tags) if avg_tags else 0
            
            # 4. 最近更新的缓存数量（1小时内）
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_tag_cache 
                WHERE last_updated > datetime('now', '-1 hour')
            """)
            stats["recently_updated"] = cursor.fetchone()[0]
            
            # 5. 需要更新的用户数量
            users_need_update = tag_cache_service.get_users_need_cache_update()
            stats["users_need_update"] = len(users_need_update)
            
            # 6. 缓存命中率（估算）
            cache_coverage = stats["cached_users"] / max(stats["active_users"], 1) * 100
            stats["cache_coverage_percent"] = round(cache_coverage, 2)
            
            return TagAdminResponse(
                message="标签统计信息获取成功",
                data=stats
            )
            
    except Exception as e:
        logger.error(f"获取标签统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取标签统计信息失败: {str(e)}"
        )


@router.get("/admin/tags/user/{user_id}", response_model=TagAdminResponse, summary="获取指定用户标签详情")
async def get_user_tag_details(
    user_id: int = Path(..., description="用户ID")
) -> TagAdminResponse:
    """
    获取指定用户的标签详细信息
    包括标签列表、缓存状态、内容统计等
    """
    try:
        # 获取缓存的标签
        cached_tags = tag_cache_service.get_user_tags_from_cache(user_id)
        
        # 获取实时计算的标签（用于对比）
        fresh_tags = tag_cache_service.update_user_tags_cache(user_id)
        
        # 统计用户内容
        import sqlite3
        with sqlite3.connect(tag_cache_service.db_path) as conn:
            cursor = conn.cursor()
            content_count = tag_cache_service._get_user_content_count(cursor, user_id)
        
        data = {
            "user_id": user_id,
            "content_count": content_count,
            "cached_tags": cached_tags,
            "fresh_tags": fresh_tags,
            "cache_available": cached_tags is not None,
            "tags_match": cached_tags == fresh_tags if cached_tags else False
        }
        
        return TagAdminResponse(
            message=f"用户{user_id}标签详情获取成功",
            data=data
        )
        
    except Exception as e:
        logger.error(f"获取用户标签详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户标签详情失败: {str(e)}"
        )