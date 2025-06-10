"""
订阅模板搜索服务
提供模板搜索、URL解析等功能
"""
import re
from typing import List, Optional
from urllib.parse import urlparse

from loguru import logger

from app.config.template_loader import get_template_loader, TemplateLoader
from app.models.template import (
    TemplateSearchResult,
    TemplateSearchResponse,
    TemplateParameter,
    URLParseResult
)


class SearchService:
    """搜索服务类"""
    
    def __init__(self):
        self.template_loader: TemplateLoader = get_template_loader()
    
    def search_templates(self, query: str, limit: int = 10) -> TemplateSearchResponse:
        """
        搜索订阅模板
        
        Args:
            query: 搜索关键词或URL
            limit: 返回结果数量限制
            
        Returns:
            TemplateSearchResponse: 搜索结果响应
        """
        logger.info(f"开始搜索模板: query='{query}', limit={limit}")
        
        try:
            # 检测搜索类型
            search_type = self._detect_search_type(query)
            
            # 执行搜索
            search_results = self.template_loader.search_templates(query, limit)
            
            # 转换为API响应格式
            results = []
            for result in search_results:
                # 为URL解析结果设置预填充参数
                required_params = []
                for param in result.required_params:
                    template_param = TemplateParameter(
                        name=param.name,
                        display_name=param.display_name,
                        description=param.description,
                        type=param.type,
                        required=param.required,
                        placeholder=param.placeholder,
                        validation_regex=param.validation_regex,
                        validation_message=param.validation_message,
                        pre_filled=(
                            result.auto_filled_params.get(param.name) 
                            if result.auto_filled_params else None
                        )
                    )
                    required_params.append(template_param)
                
                api_result = TemplateSearchResult(
                    template_id=result.template_id,
                    display_name=result.display_name,
                    description=result.description,
                    icon=result.icon,
                    platform=result.platform,
                    match_type=result.match_type,
                    match_score=result.match_score,
                    auto_filled_params=result.auto_filled_params,
                    required_params=required_params
                )
                results.append(api_result)
            
            response = TemplateSearchResponse(
                total=len(results),
                results=results,
                query=query,
                search_type=search_type
            )
            
            logger.info(f"搜索完成: 找到 {len(results)} 个匹配结果")
            return response
            
        except Exception as e:
            logger.error(f"搜索模板失败: {e}")
            # 返回空结果而不是抛出异常
            return TemplateSearchResponse(
                total=0,
                results=[],
                query=query,
                search_type="error"
            )
    
    def parse_url(self, url: str) -> URLParseResult:
        """
        解析URL并提取参数
        
        Args:
            url: 要解析的URL
            
        Returns:
            URLParseResult: URL解析结果
        """
        logger.info(f"开始解析URL: {url}")
        
        try:
            # 验证URL格式
            if not self._is_valid_url(url):
                return URLParseResult(
                    success=False,
                    error_message="不是有效的URL格式"
                )
            
            # 使用模板加载器解析URL
            search_results = self.template_loader._parse_url(url)
            
            if not search_results:
                return URLParseResult(
                    success=False,
                    error_message="未找到匹配的模板"
                )
            
            # 取第一个匹配结果（通常只有一个）
            best_match = search_results[0]
            
            result = URLParseResult(
                success=True,
                template_id=best_match.template_id,
                extracted_params=best_match.auto_filled_params,
                confidence=best_match.match_score
            )
            
            logger.info(f"URL解析成功: template_id={result.template_id}")
            return result
            
        except Exception as e:
            logger.error(f"URL解析失败: {e}")
            return URLParseResult(
                success=False,
                error_message=f"解析过程发生错误: {str(e)}"
            )
    
    def validate_template_parameters(self, template_id: str, parameters: dict) -> tuple[bool, str]:
        """
        验证模板参数
        
        Args:
            template_id: 模板ID
            parameters: 参数字典
            
        Returns:
            tuple: (是否验证通过, 错误信息)
        """
        logger.debug(f"验证模板参数: template_id={template_id}, parameters={parameters}")
        
        try:
            return self.template_loader.validate_template_parameters(template_id, parameters)
        except Exception as e:
            logger.error(f"参数验证失败: {e}")
            return False, f"参数验证过程发生错误: {str(e)}"
    
    def get_template_by_id(self, template_id: str) -> Optional[dict]:
        """
        根据ID获取模板信息
        
        Args:
            template_id: 模板ID
            
        Returns:
            Optional[dict]: 模板信息，如果不存在则返回None
        """
        try:
            template = self.template_loader.get_template(template_id)
            if not template:
                return None
            
            # 转换为字典格式，隐藏RSS URL等敏感信息
            return {
                "id": template.id,
                "display_name": template.display_name,
                "description": template.description,
                "icon": template.icon,
                "platform": template.platform,
                "parameters": [
                    {
                        "name": param.name,
                        "display_name": param.display_name,
                        "description": param.description,
                        "type": param.type,
                        "required": param.required,
                        "placeholder": param.placeholder,
                        "validation_regex": param.validation_regex,
                        "validation_message": param.validation_message
                    }
                    for param in template.parameters
                ]
            }
        except Exception as e:
            logger.error(f"获取模板信息失败: {e}")
            return None
    
    def _detect_search_type(self, query: str) -> str:
        """
        检测搜索类型
        
        Args:
            query: 搜索关键词或URL
            
        Returns:
            str: 搜索类型 - keyword|url|mixed
        """
        if self._is_valid_url(query):
            return "url"
        elif any(keyword in query.lower() for keyword in ["http", "www", ".com", ".cn"]):
            return "mixed"
        else:
            return "keyword"
    
    def _is_valid_url(self, url: str) -> bool:
        """
        验证URL格式是否有效
        
        Args:
            url: 要验证的URL
            
        Returns:
            bool: 是否为有效URL
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def get_supported_platforms(self) -> List[dict]:
        """
        获取支持的平台列表
        
        Returns:
            List[dict]: 平台信息列表
        """
        try:
            templates = self.template_loader.get_all_templates()
            platforms = {}
            
            for template in templates:
                if template.platform not in platforms:
                    platforms[template.platform] = {
                        "platform": template.platform,
                        "template_count": 0,
                        "templates": []
                    }
                
                platforms[template.platform]["template_count"] += 1
                platforms[template.platform]["templates"].append({
                    "id": template.id,
                    "display_name": template.display_name
                })
            
            return list(platforms.values())
            
        except Exception as e:
            logger.error(f"获取平台列表失败: {e}")
            return []


# 全局搜索服务实例
search_service = SearchService()


def get_search_service() -> SearchService:
    """获取搜索服务实例"""
    return search_service 