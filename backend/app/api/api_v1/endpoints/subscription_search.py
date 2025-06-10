"""
订阅模板搜索API端点
提供模板搜索、URL解析等接口
"""
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger

from app.services.search_service import get_search_service
from app.models.template import (
    TemplateSearchResponse,
    URLParseResult,
    TemplateSearchRequest
)

router = APIRouter()
search_service = get_search_service()


@router.get("/search", response_model=TemplateSearchResponse, summary="搜索订阅模板")
async def search_templates(
    query: str = Query(..., min_length=1, description="搜索关键词或URL"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制")
) -> TemplateSearchResponse:
    """
    搜索订阅模板
    
    支持两种搜索方式：
    1. **关键词搜索**：如"微博"、"用户"、"视频"等
    2. **URL解析**：如"https://weibo.com/u/123456"，会自动解析参数
    
    Args:
        query: 搜索关键词或URL
        limit: 返回结果数量限制（1-50）
        
    Returns:
        TemplateSearchResponse: 搜索结果，包含匹配的模板列表
        
    Example:
        关键词搜索：`/search?query=微博&limit=5`
        URL解析：`/search?query=https://weibo.com/u/1195230310`
    """
    try:
        logger.info(f"收到搜索请求: query='{query}', limit={limit}")
        
        # 执行搜索
        result = search_service.search_templates(query, limit)
        
        logger.info(f"搜索完成: 返回 {result.total} 个结果")
        return result
        
    except Exception as e:
        logger.error(f"搜索模板API失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索过程中发生错误: {str(e)}"
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