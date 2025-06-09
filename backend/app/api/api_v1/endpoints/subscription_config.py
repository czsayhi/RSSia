"""
订阅配置API端点
支持三级下拉的订阅配置交互方式
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from loguru import logger

from app.models.subscription import (
    PlatformListResponse,
    SubscriptionTypeListResponse, 
    TemplateListResponse,
    PlatformType,
    SubscriptionType
)
from app.config.subscription_config import (
    get_platform_info,
    get_subscription_types_for_platform,
    get_templates_for_platform_and_type,
    validate_subscription_parameters,
    SUBSCRIPTION_TYPE_NAMES
)

router = APIRouter()


@router.get("/platforms", response_model=PlatformListResponse, summary="获取支持的平台列表")
async def get_platforms():
    """
    获取支持的平台列表
    返回平台信息及其支持的订阅类型
    """
    try:
        platforms = get_platform_info()
        return PlatformListResponse(platforms=platforms)
    except Exception as e:
        logger.error(f"获取平台列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取平台列表失败"
        )


@router.get("/platforms/{platform}/subscription-types", 
           response_model=SubscriptionTypeListResponse, 
           summary="获取平台支持的订阅类型")
async def get_platform_subscription_types(platform: PlatformType):
    """
    获取指定平台支持的订阅类型
    """
    try:
        subscription_types = get_subscription_types_for_platform(platform)
        return SubscriptionTypeListResponse(subscription_types=subscription_types)
    except Exception as e:
        logger.error(f"获取平台订阅类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订阅类型失败"
        )


@router.get("/platforms/{platform}/subscription-types/{subscription_type}/templates",
           response_model=TemplateListResponse,
           summary="获取订阅模板列表")
async def get_subscription_templates(platform: PlatformType, subscription_type: SubscriptionType):
    """
    获取指定平台和订阅类型的模板列表
    """
    try:
        templates = get_templates_for_platform_and_type(platform, subscription_type)
        
        # 转换为响应模型
        from app.models.subscription import SubscriptionTemplate
        template_models = []
        for i, template in enumerate(templates):
            template_model = SubscriptionTemplate(
                id=i + 1,  # 临时分配ID，实际应该从数据库获取
                platform=template["platform"],
                subscription_type=template["subscription_type"],
                name=template["name"],
                description=template["description"],
                url_template=template["url_template"],
                parameters=template["parameters"]
            )
            template_models.append(template_model)
        
        return TemplateListResponse(templates=template_models)
    except Exception as e:
        logger.error(f"获取订阅模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订阅模板失败"
        )


@router.get("/subscription-types", summary="获取所有订阅类型")
async def get_all_subscription_types():
    """
    获取所有支持的订阅类型及其显示名称
    """
    try:
        subscription_types = [
            {"type": type_enum.value, "name": name}
            for type_enum, name in SUBSCRIPTION_TYPE_NAMES.items()
        ]
        return {"subscription_types": subscription_types}
    except Exception as e:
        logger.error(f"获取订阅类型列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取订阅类型列表失败"
        )


@router.post("/validate-parameters", summary="验证订阅参数")
async def validate_parameters(
    template_id: int,
    parameters: Dict[str, str]
):
    """
    验证订阅参数是否符合模板要求
    """
    try:
        is_valid, message = validate_subscription_parameters(template_id, parameters)
        
        return {
            "is_valid": is_valid,
            "message": message,
            "parameters": parameters
        }
    except Exception as e:
        logger.error(f"参数验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="参数验证失败"
        ) 