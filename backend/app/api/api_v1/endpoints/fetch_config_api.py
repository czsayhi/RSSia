"""
订阅频率配置和拉取控制API接口
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.services.fetch_config_service import (
    FetchConfigService, 
    FetchConfig,
    FetchConfigUpdateRequest,
    FrequencyType
)
from app.services.fetch_limit_service import (
    FetchLimitService,
    FetchQuota,
    FetchAttemptResult
)
from app.services.enhanced_rss_service import EnhancedRSSService

router = APIRouter()

# Pydantic模型定义
class FetchConfigResponse(BaseModel):
    """拉取配置响应"""
    user_id: int
    auto_fetch_enabled: bool
    frequency: str
    preferred_hour: int
    timezone: str
    daily_limit: int
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class FetchConfigUpdateModel(BaseModel):
    """拉取配置更新请求"""
    auto_fetch_enabled: Optional[bool] = None
    frequency: Optional[str] = Field(None, pattern="^(daily|three_days|weekly)$")
    preferred_hour: Optional[int] = Field(None, ge=0, le=23)
    daily_limit: Optional[int] = Field(None, ge=1, le=100)

class FetchQuotaResponse(BaseModel):
    """拉取配额响应"""
    user_id: int
    daily_limit: int
    current_count: int
    remaining_count: int
    can_fetch: bool
    last_fetch_at: Optional[str] = None
    last_fetch_success: Optional[bool] = None

class ManualFetchRequest(BaseModel):
    """手动拉取请求"""
    user_id: int = Field(default=1, description="用户ID")

class ManualFetchResponse(BaseModel):
    """手动拉取响应"""
    success: bool
    message: str
    quota_after: Optional[FetchQuotaResponse] = None
    fetch_results: Optional[Dict[str, Any]] = None

# 依赖注入
def get_config_service():
    return FetchConfigService()

def get_limit_service():
    return FetchLimitService()

def get_rss_service():
    return EnhancedRSSService()

# API端点

@router.get("/config/{user_id}", response_model=FetchConfigResponse)
async def get_user_fetch_config(
    user_id: int,
    config_service: FetchConfigService = Depends(get_config_service)
):
    """获取用户订阅频率配置"""
    try:
        config = config_service.get_user_config(user_id)
        
        return FetchConfigResponse(
            user_id=config.user_id,
            auto_fetch_enabled=config.auto_fetch_enabled,
            frequency=config.frequency.value,
            preferred_hour=config.preferred_hour,
            timezone=config.timezone,
            daily_limit=config.daily_limit,
            is_active=config.is_active,
            created_at=config.created_at.isoformat() if config.created_at else None,
            updated_at=config.updated_at.isoformat() if config.updated_at else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.post("/config/{user_id}", response_model=FetchConfigResponse)
async def update_user_fetch_config(
    user_id: int,
    config_update: FetchConfigUpdateModel,
    config_service: FetchConfigService = Depends(get_config_service)
):
    """更新用户订阅频率配置"""
    try:
        # 转换请求模型
        request = FetchConfigUpdateRequest(
            auto_fetch_enabled=config_update.auto_fetch_enabled,
            frequency=FrequencyType(config_update.frequency) if config_update.frequency else None,
            preferred_hour=config_update.preferred_hour,
            daily_limit=config_update.daily_limit
        )
        
        # 更新配置
        updated_config = config_service.create_or_update_config(user_id, request)
        
        return FetchConfigResponse(
            user_id=updated_config.user_id,
            auto_fetch_enabled=updated_config.auto_fetch_enabled,
            frequency=updated_config.frequency.value,
            preferred_hour=updated_config.preferred_hour,
            timezone=updated_config.timezone,
            daily_limit=updated_config.daily_limit,
            is_active=updated_config.is_active,
            created_at=updated_config.created_at.isoformat() if updated_config.created_at else None,
            updated_at=updated_config.updated_at.isoformat() if updated_config.updated_at else None
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@router.get("/quota/{user_id}", response_model=FetchQuotaResponse)
async def get_user_fetch_quota(
    user_id: int,
    limit_service: FetchLimitService = Depends(get_limit_service)
):
    """获取用户拉取配额信息"""
    try:
        quota = limit_service.get_user_quota(user_id)
        
        return FetchQuotaResponse(
            user_id=quota.user_id,
            daily_limit=quota.daily_limit,
            current_count=quota.current_count,
            remaining_count=quota.remaining_count,
            can_fetch=quota.can_fetch,
            last_fetch_at=quota.last_fetch_at.isoformat() if quota.last_fetch_at else None,
            last_fetch_success=quota.last_fetch_success
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配额信息失败: {str(e)}")

@router.get("/can-fetch/{user_id}")
async def check_can_fetch(
    user_id: int,
    limit_service: FetchLimitService = Depends(get_limit_service)
):
    """检查用户是否可以进行手动拉取"""
    try:
        can_fetch = limit_service.check_can_fetch(user_id, 'manual')
        quota = limit_service.get_user_quota(user_id)
        
        return {
            "can_fetch": can_fetch,
            "remaining_count": quota.remaining_count,
            "daily_limit": quota.daily_limit,
            "message": "可以拉取" if can_fetch else f"已达到每日拉取次数限制（{quota.daily_limit}次）"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查拉取权限失败: {str(e)}")

@router.post("/manual-fetch", response_model=ManualFetchResponse)
async def manual_fetch_rss(
    request: ManualFetchRequest,
    limit_service: FetchLimitService = Depends(get_limit_service),
    rss_service: EnhancedRSSService = Depends(get_rss_service)
):
    """手动拉取RSS内容"""
    try:
        user_id = request.user_id
        
        # 尝试消耗配额
        attempt_result = limit_service.attempt_fetch(user_id, 'manual')
        
        if not attempt_result.success:
            return ManualFetchResponse(
                success=False,
                message=attempt_result.message,
                quota_after=FetchQuotaResponse(
                    user_id=attempt_result.quota_after.user_id,
                    daily_limit=attempt_result.quota_after.daily_limit,
                    current_count=attempt_result.quota_after.current_count,
                    remaining_count=attempt_result.quota_after.remaining_count,
                    can_fetch=attempt_result.quota_after.can_fetch,
                    last_fetch_at=attempt_result.quota_after.last_fetch_at.isoformat() if attempt_result.quota_after.last_fetch_at else None,
                    last_fetch_success=attempt_result.quota_after.last_fetch_success
                ) if attempt_result.quota_after else None
            )
        
        # 执行实际的RSS拉取
        fetch_results = await _perform_manual_fetch(user_id, rss_service)
        
        # 记录拉取结果
        limit_service.record_fetch_result(user_id, 'manual', fetch_results.get('success', False))
        
        return ManualFetchResponse(
            success=True,
            message="手动拉取完成",
            quota_after=FetchQuotaResponse(
                user_id=attempt_result.quota_after.user_id,
                daily_limit=attempt_result.quota_after.daily_limit,
                current_count=attempt_result.quota_after.current_count,
                remaining_count=attempt_result.quota_after.remaining_count,
                can_fetch=attempt_result.quota_after.can_fetch,
                last_fetch_at=attempt_result.quota_after.last_fetch_at.isoformat() if attempt_result.quota_after.last_fetch_at else None,
                last_fetch_success=attempt_result.quota_after.last_fetch_success
            ),
            fetch_results=fetch_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"手动拉取失败: {str(e)}")

@router.get("/history/{user_id}")
async def get_fetch_history(
    user_id: int,
    days: int = 7,
    limit_service: FetchLimitService = Depends(get_limit_service)
):
    """获取用户拉取历史记录"""
    try:
        history = limit_service.get_user_fetch_history(user_id, days)
        return {
            "user_id": user_id,
            "days": days,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取拉取历史失败: {str(e)}")

# 辅助函数
async def _perform_manual_fetch(user_id: int, rss_service: EnhancedRSSService) -> Dict[str, Any]:
    """执行手动拉取"""
    try:
        from app.services.subscription_service import SubscriptionService
        
        subscription_service = SubscriptionService()
        subscriptions = subscription_service.get_user_subscriptions(user_id)
        
        total_count = len(subscriptions.subscriptions)
        success_count = 0
        failed_subscriptions = []
        
        for subscription in subscriptions.subscriptions:
            try:
                result = rss_service.fetch_and_process_rss(subscription.rss_url, user_id)
                if result.get('success', False):
                    success_count += 1
                else:
                    failed_subscriptions.append({
                        'subscription_id': subscription.id,
                        'error': result.get('error', '未知错误')
                    })
            except Exception as e:
                failed_subscriptions.append({
                    'subscription_id': subscription.id,
                    'error': str(e)
                })
        
        return {
            'success': success_count > 0,
            'total_subscriptions': total_count,
            'success_count': success_count,
            'failed_count': len(failed_subscriptions),
            'failed_subscriptions': failed_subscriptions,
            'message': f"成功拉取 {success_count}/{total_count} 个订阅源"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': '拉取过程中发生错误'
        } 