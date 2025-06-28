"""
订阅频率配置和拉取控制API接口
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

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
from app.services.subscription_service import SubscriptionService
from app.services import rss_content_service
from app.services.user_service import UserService

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

class FetchQuotaResponse(BaseModel):
    """拉取配额响应"""
    user_id: int
    date: str
    total_quota: int
    used_quota: int
    remaining_quota: int
    auto_fetch_count: int
    manual_fetch_count: int
    last_fetch_at: Optional[str] = None

class ManualFetchRequest(BaseModel):
    """手动拉取请求"""
    user_id: int = Field(..., description="用户ID")

class ManualFetchResponse(BaseModel):
    """手动拉取响应"""
    success: bool
    message: str
    total_subscriptions: int = 0
    success_count: int = 0
    failed_count: int = 0
    processed_contents: List[Dict[str, Any]] = []
    quota_after: Optional[FetchQuotaResponse] = None
    should_refresh_content: bool = False  # 新增：是否需要刷新内容列表

# 依赖注入函数
def get_config_service() -> FetchConfigService:
    return FetchConfigService()

def get_limit_service() -> FetchLimitService:
    return FetchLimitService()

def get_subscription_service() -> SubscriptionService:
    return SubscriptionService()

# API端点
@router.get("/config/{user_id}", response_model=FetchConfigResponse)
async def get_fetch_config(
    user_id: int,
    config_service: FetchConfigService = Depends(get_config_service)
):
    """获取用户拉取配置"""
    try:
        config = config_service.get_user_config(user_id)
        if not config:
            raise HTTPException(status_code=404, detail="用户配置不存在")
        
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.put("/config/{user_id}", response_model=FetchConfigResponse)
async def update_fetch_config(
    user_id: int,
    request: FetchConfigUpdateRequest,
    config_service: FetchConfigService = Depends(get_config_service)
):
    """更新用户拉取配置"""
    try:
        updated_config = config_service.update_user_config(user_id, request)
        
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@router.get("/quota/{user_id}", response_model=FetchQuotaResponse)
async def get_fetch_quota(
    user_id: int,
    limit_service: FetchLimitService = Depends(get_limit_service)
):
    """获取用户拉取配额"""
    try:
        quota = limit_service.get_user_quota(user_id)
        
        return FetchQuotaResponse(
            user_id=quota.user_id,
            date=quota.date.strftime('%Y-%m-%d'),
            total_quota=quota.total_quota,
            used_quota=quota.used_quota,
            remaining_quota=quota.remaining_quota,
            auto_fetch_count=quota.auto_fetch_count,
            manual_fetch_count=quota.manual_fetch_count,
            last_fetch_at=quota.last_fetch_at.isoformat() if quota.last_fetch_at else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配额失败: {str(e)}")

@router.post("/manual-fetch", response_model=ManualFetchResponse)
async def manual_fetch_rss(
    request: ManualFetchRequest,
    config_service: FetchConfigService = Depends(get_config_service),
    limit_service: FetchLimitService = Depends(get_limit_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """
    手动拉取RSS内容
    包含完整的拉取次数限制、配额管理、内容存储功能
    """
    try:
        from loguru import logger
        import asyncio
        user_id = request.user_id
        
        # 1. 检查用户拉取权限和配额
        attempt_result = limit_service.attempt_fetch(user_id, 'manual')
        
        if not attempt_result.success:
            return ManualFetchResponse(
                success=False,
                message=attempt_result.message,
                            quota_after=FetchQuotaResponse(
                user_id=attempt_result.quota_after.user_id,
                date=datetime.now().strftime('%Y-%m-%d'),
                total_quota=attempt_result.quota_after.daily_limit,
                used_quota=attempt_result.quota_after.current_count,
                remaining_quota=attempt_result.quota_after.remaining_count,
                auto_fetch_count=0,  # 需要从数据库获取，暂时设为0
                manual_fetch_count=0,  # 需要从数据库获取，暂时设为0
                last_fetch_at=attempt_result.quota_after.last_fetch_at.isoformat() if attempt_result.quota_after.last_fetch_at else None
            )
            )
        
        # 2. 获取用户订阅列表
        subscriptions = subscription_service.get_user_subscriptions(user_id)
        total_count = len(subscriptions.subscriptions)
        
        if total_count == 0:
            return ManualFetchResponse(
                success=False,
                message="用户没有活跃的订阅",
                total_subscriptions=0
            )
        
        # 3. 执行统一的RSS拉取流程
        result = await _perform_unified_fetch(user_id, subscriptions.subscriptions)
        
        # 4. 记录拉取结果
        limit_service.record_fetch_result(
            user_id=user_id,
            fetch_type='manual',
            success=result['success_count'] > 0
        )
        
        # 5. 获取更新后的配额信息
        updated_quota = limit_service.get_user_quota(user_id)
        
        return ManualFetchResponse(
            success=result['success_count'] > 0,
            message=f"手动拉取完成，成功处理 {result['success_count']}/{total_count} 个订阅源",
            total_subscriptions=total_count,
            success_count=result['success_count'],
            failed_count=total_count - result['success_count'],
            processed_contents=result['processed_contents'],
            should_refresh_content=result['success_count'] > 0,  # 有新内容时需要刷新
            quota_after=FetchQuotaResponse(
                user_id=updated_quota.user_id,
                date=datetime.now().strftime('%Y-%m-%d'),
                total_quota=updated_quota.daily_limit,
                used_quota=updated_quota.current_count,
                remaining_quota=updated_quota.remaining_count,
                auto_fetch_count=0,  # 需要从数据库获取，暂时设为0
                manual_fetch_count=0,  # 需要从数据库获取，暂时设为0
                last_fetch_at=updated_quota.last_fetch_at.isoformat() if updated_quota.last_fetch_at else None
            )
        )
        
    except Exception as e:
        logger.error(f"手动拉取失败: {e}")
        raise HTTPException(status_code=500, detail=f"手动拉取失败: {str(e)}")

# 统一的拉取执行函数
async def _perform_unified_fetch(user_id: int, subscriptions: list) -> Dict[str, Any]:
    """
    执行统一的RSS拉取流程
    使用RSSContentService进行完整的拉取→解析→存储流程
    """
    try:
        from loguru import logger
        
        # 使用全局统一的RSS内容服务实例
        
        total_count = len(subscriptions)
        success_count = 0
        failed_subscriptions = []
        processed_contents = []
        
        logger.info(f"开始批量拉取RSS内容: {total_count}个订阅源, user_id={user_id}")
        
        for i, subscription in enumerate(subscriptions, 1):
            try:
                logger.info(f"处理订阅 {i}/{total_count}: {subscription.custom_name or subscription.rss_url}")
                
                # 检查订阅源是否处于活跃状态
                if not subscription.is_active:
                    logger.info(f"⏸️ 跳过非活跃订阅源: {subscription.custom_name or subscription.rss_url}")
                    failed_subscriptions.append({
                        'subscription_id': subscription.id,
                        'name': subscription.custom_name or subscription.rss_url,
                        'error': '订阅源已禁用'
                    })
                    continue
                
                # 使用RSSContentService进行完整的拉取→解析→存储流程
                result = await rss_content_service.fetch_and_store_rss_content(
                    subscription_id=subscription.id,
                    rss_url=subscription.rss_url,
                    user_id=user_id
                )
                
                if result.get('success', False):
                    success_count += 1
                    processed_contents.extend(result.get('processed_items', []))
                    logger.info(f"✅ 订阅拉取成功: {subscription.custom_name or subscription.rss_url}")
                else:
                    failed_subscriptions.append({
                        'subscription_id': subscription.id,
                        'name': subscription.custom_name or subscription.rss_url,
                        'error': result.get('error', '未知错误')
                    })
                    logger.warning(f"❌ 订阅拉取失败: {subscription.custom_name or subscription.rss_url}, 错误: {result.get('error')}")
                
            except Exception as e:
                failed_subscriptions.append({
                    'subscription_id': subscription.id,
                    'name': subscription.custom_name or subscription.rss_url,
                    'error': str(e)
                })
                logger.error(f"❌ 订阅处理异常: {subscription.custom_name or subscription.rss_url}, 异常: {str(e)}")
        
        logger.info(f"批量拉取完成: 成功 {success_count}/{total_count}")
        
        return {
            'success_count': success_count,
            'total_count': total_count,
            'failed_subscriptions': failed_subscriptions,
            'processed_contents': processed_contents
        }
        
    except Exception as e:
        logger.error(f"批量拉取过程异常: {str(e)}")
        return {
            'success_count': 0,
            'total_count': len(subscriptions),
            'failed_subscriptions': [{'error': f'批量拉取异常: {str(e)}'}],
            'processed_contents': []
        } 