"""
订阅管理API端点 - v2版本 (集成SQLite数据库)
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query, Depends
from app.models.subscription import (
    SubscriptionTemplate,
    SubscriptionCreateRequest,
    SubscriptionResponse,
    SubscriptionListResponse
)
from app.services.subscription_service import SubscriptionService
from app.api.api_v1.endpoints.auth import get_current_user
from app.services.user_service import User

router = APIRouter()
subscription_service = SubscriptionService()

@router.get("/templates", response_model=List[SubscriptionTemplate])
async def get_subscription_templates(current_user: User = Depends(get_current_user)):
    """获取订阅模板列表"""
    try:
        templates = subscription_service.get_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板失败: {str(e)}")

@router.get("/", response_model=SubscriptionListResponse)
async def get_subscriptions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="页面大小"),
    current_user: User = Depends(get_current_user)
):
    """获取用户订阅列表"""
    try:
        result = subscription_service.get_user_subscriptions(
            user_id=current_user.user_id, 
            page=page, 
            size=size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订阅列表失败: {str(e)}")

@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    request: SubscriptionCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """创建新订阅"""
    try:
        subscription = subscription_service.create_subscription(
            request, 
            user_id=current_user.user_id
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建订阅失败: {str(e)}")

@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除订阅"""
    try:
        success = subscription_service.delete_subscription(
            subscription_id, 
            user_id=current_user.user_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="订阅不存在")
        return {"message": "订阅删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除订阅失败: {str(e)}") 

@router.put("/{subscription_id}/status")
async def update_subscription_status(
    subscription_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_user)
):
    """更新订阅状态"""
    try:
        success = subscription_service.update_subscription_status(
            subscription_id, 
            is_active, 
            user_id=current_user.user_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="订阅不存在")
        return {"message": "订阅状态更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新订阅状态失败: {str(e)}") 