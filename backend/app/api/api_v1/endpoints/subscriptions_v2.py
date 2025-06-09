"""
订阅管理API端点 - v2版本 (集成SQLite数据库)
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query
from app.models.subscription import (
    SubscriptionTemplate,
    SubscriptionCreateRequest,
    SubscriptionResponse,
    SubscriptionListResponse
)
from app.services.subscription_service import SubscriptionService

router = APIRouter()
subscription_service = SubscriptionService()

@router.get("/templates", response_model=List[SubscriptionTemplate])
async def get_subscription_templates():
    """获取订阅模板列表"""
    try:
        templates = subscription_service.get_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")

@router.get("/", response_model=SubscriptionListResponse)
async def get_subscriptions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="页面大小")
):
    """获取用户订阅列表"""
    try:
        result = subscription_service.get_user_subscriptions(page=page, size=size)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订阅列表失败: {str(e)}")

@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(request: SubscriptionCreateRequest):
    """创建新订阅"""
    try:
        subscription = subscription_service.create_subscription(request)
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建订阅失败: {str(e)}")

@router.delete("/{subscription_id}")
async def delete_subscription(subscription_id: int):
    """删除订阅"""
    try:
        success = subscription_service.delete_subscription(subscription_id)
        if not success:
            raise HTTPException(status_code=404, detail="订阅不存在")
        return {"message": "订阅删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除订阅失败: {str(e)}") 