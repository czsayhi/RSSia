"""
订阅模板搜索API端点
提供模板搜索、URL解析等接口
"""
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, status, Depends
from loguru import logger

from app.services.search_service import get_search_service
from app.models.template import (
    TemplateSearchResponse,
    URLParseResult,
    TemplateSearchRequest
)
from app.services.user_service import User
from app.api.api_v1.endpoints.auth import get_current_user

router = APIRouter()
search_service = get_search_service()

# 前端期望的订阅模板数据结构
class SubscriptionTemplate:
    def __init__(self, template_result, parsed_params=None):
        self.template_id = template_result.template_id
        self.template_name = template_result.template_name
        self.platform = template_result.platform
        self.description = template_result.description
        # 将 required_params 映射为 parameters
        self.parameters = []
        if hasattr(template_result, 'required_params') and template_result.required_params:
            for param in template_result.required_params:
                param_dict = {
                    "name": param.name,
                    "display_name": param.display_name,
                    "description": param.description,
                    "type": param.type,
                    "required": param.required,
                    "placeholder": param.placeholder,
                    "validation_regex": param.validation_regex,
                    "validation_message": param.validation_message
                }
                # 如果有解析出的参数，填充默认值
                if parsed_params and param.name in parsed_params:
                    param_dict["default_value"] = parsed_params[param.name]
                self.parameters.append(param_dict)
        
        # 如果有解析出的参数，保存到模板中
        self.parsed_params = parsed_params or {}

    def to_dict(self):
        return {
            "template_id": self.template_id,
            "template_name": self.template_name,
            "platform": self.platform,
            "description": self.description,
            "parameters": self.parameters,
            "parsed_params": self.parsed_params  # 添加解析参数
        }

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_templates(
    query: str = Query(..., description="搜索关键词或URL"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制"),
    current_user: User = Depends(get_current_user)
):
    """
    搜索订阅模板
    支持关键词搜索和URL解析
    """
    try:
        logger.info(f"用户 {current_user.username} 搜索订阅模板: query='{query}', limit={limit}")
        
        # 执行搜索
        search_response = search_service.search_templates(query, limit)
        
        # 检查是否为URL，如果是则尝试解析参数
        parsed_params_map = {}
        if search_service._is_valid_url(query):
            logger.info(f"检测到URL，尝试解析参数: {query}")
            parse_result = search_service.parse_url(query)
            if parse_result.success and parse_result.extracted_params:
                # 为匹配的模板保存解析参数
                parsed_params_map[parse_result.template_id] = parse_result.extracted_params
                logger.info(f"URL解析成功，提取参数: {parse_result.extracted_params}")
        
        # 转换为前端期望的格式
        subscription_templates = []
        for result in search_response.results:
            # 获取该模板的解析参数（如果有）
            parsed_params = parsed_params_map.get(result.template_id)
            template = SubscriptionTemplate(result, parsed_params)
            subscription_templates.append(template.to_dict())
        
        logger.info(f"搜索完成: 返回 {len(subscription_templates)} 个结果")
        return subscription_templates
        
    except Exception as e:
        logger.error(f"搜索订阅模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.post("/parse-url", response_model=URLParseResult, summary="解析URL并提取参数")
async def parse_url(
    url: str = Query(..., description="要解析的URL")
) -> URLParseResult:
    """
    解析URL并提取参数
    
    支持解析以下平台的URL：
    - 微博用户主页：https://weibo.com/u/123456
    - B站用户空间：https://space.bilibili.com/123456
    
    Args:
        url: 要解析的URL
        
    Returns:
        URLParseResult: 解析结果，包含提取的参数信息
        
    Example:
        `/parse-url?url=https://weibo.com/u/1195230310`
    """
    try:
        logger.info(f"收到URL解析请求: url='{url}'")
        
        # 执行URL解析
        result = search_service.parse_url(url)
        
        if result.success:
            logger.info(f"URL解析成功: template_id={result.template_id}")
        else:
            logger.warning(f"URL解析失败: {result.error_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"URL解析API失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"URL解析过程中发生错误: {str(e)}"
        )


@router.get("/template/{template_id}", response_model=Dict[str, Any], summary="获取模板详情")
async def get_template_detail(
    template_id: str
) -> Dict[str, Any]:
    """
    获取指定模板的详细信息
    
    Args:
        template_id: 模板ID
        
    Returns:
        Dict[str, Any]: 模板详细信息
        
    Raises:
        HTTPException: 当模板不存在时返回404错误
    """
    try:
        logger.info(f"获取模板详情: template_id='{template_id}'")
        
        template = search_service.get_template_by_id(template_id)
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"模板 '{template_id}' 不存在"
            )
        
        logger.info(f"模板详情获取成功: {template['display_name']}")
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模板详情API失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板详情过程中发生错误: {str(e)}"
        )


from pydantic import BaseModel

class ValidateParametersRequest(BaseModel):
    template_id: str
    parameters: Dict[str, str]

@router.post("/validate-parameters", summary="验证模板参数")
async def validate_parameters(
    request: ValidateParametersRequest
) -> Dict[str, Any]:
    """
    验证模板参数是否符合要求
    
    Args:
        request: 验证请求，包含模板ID和参数
        
    Returns:
        Dict[str, Any]: 验证结果
        
    Example:
        POST /validate-parameters
        Body: {"template_id": "weibo_user_posts", "parameters": {"uid": "1195230310"}}
    """
    try:
        logger.info(f"验证模板参数: template_id='{request.template_id}', parameters={request.parameters}")
        
        is_valid, error_message = search_service.validate_template_parameters(
            request.template_id, request.parameters
        )
        
        result = {
            "valid": is_valid,
            "message": error_message,
            "template_id": request.template_id,
            "parameters": request.parameters
        }
        
        if is_valid:
            logger.info(f"参数验证通过: template_id={request.template_id}")
        else:
            logger.warning(f"参数验证失败: template_id={request.template_id}, error={error_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"验证参数API失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"参数验证过程中发生错误: {str(e)}"
        )


@router.get("/platforms", response_model=List[Dict[str, Any]], summary="获取支持的平台列表")
async def get_supported_platforms() -> List[Dict[str, Any]]:
    """
    获取系统支持的所有平台列表
    
    Returns:
        List[Dict[str, Any]]: 平台信息列表，包含每个平台的模板数量
    """
    try:
        logger.info("获取支持的平台列表")
        
        platforms = search_service.get_supported_platforms()
        
        logger.info(f"平台列表获取成功: 共 {len(platforms)} 个平台")
        return platforms
        
    except Exception as e:
        logger.error(f"获取平台列表API失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取平台列表过程中发生错误: {str(e)}"
        ) 