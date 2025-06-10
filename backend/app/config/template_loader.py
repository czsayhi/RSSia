"""
订阅模板加载器
支持JSON配置文件的热更新和模板搜索功能
"""
import json
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field


class TemplateParameter(BaseModel):
    """模板参数配置"""
    name: str
    display_name: str
    description: str
    type: str = "string"
    required: bool = True
    placeholder: Optional[str] = None
    validation_regex: Optional[str] = None
    validation_message: Optional[str] = None


class URLPattern(BaseModel):
    """URL解析模式"""
    pattern: str
    param_mapping: Dict[str, int]


class SubscriptionTemplate(BaseModel):
    """订阅模板"""
    id: str
    display_name: str
    description: str
    icon: str
    platform: str
    search_keywords: List[str]
    url_patterns: List[URLPattern]
    url_template: str
    parameters: List[TemplateParameter]
    example_url: Optional[str] = None
    enabled: bool = True


class TemplateSearchResult(BaseModel):
    """模板搜索结果"""
    template_id: str
    display_name: str
    description: str
    icon: str
    platform: str
    match_type: str  # "keyword" | "url"
    match_score: float
    auto_filled_params: Optional[Dict[str, str]] = None
    required_params: List[TemplateParameter]


class TemplateLoader:
    """模板加载器 - 支持热更新"""
    
    def __init__(self, config_path: str = "app/config/subscription_templates.json"):
        self.config_path = Path(config_path)
        self._templates: List[SubscriptionTemplate] = []
        self._templates_dict: Dict[str, SubscriptionTemplate] = {}
        self._last_modified: Optional[float] = None
        
        # 首次加载
        self.reload_if_changed()
    
    def reload_if_changed(self) -> bool:
        """如果配置文件有变化则重新加载"""
        try:
            if not self.config_path.exists():
                logger.error(f"配置文件不存在: {self.config_path}")
                return False
            
            current_mtime = self.config_path.stat().st_mtime
            
            if self._last_modified is None or current_mtime > self._last_modified:
                logger.info("检测到配置文件变化，重新加载模板配置")
                self._load_templates()
                self._last_modified = current_mtime
                return True
            
            return False
        except Exception as e:
            logger.error(f"检查配置文件变化失败: {e}")
            return False
    
    def _load_templates(self) -> None:
        """从JSON文件加载模板配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            templates = []
            for template_data in config_data.get('templates', []):
                # 转换参数格式
                parameters = []
                for param_data in template_data.get('parameters', []):
                    parameters.append(TemplateParameter(**param_data))
                
                # 转换URL模式格式
                url_patterns = []
                for pattern_data in template_data.get('url_patterns', []):
                    url_patterns.append(URLPattern(**pattern_data))
                
                template = SubscriptionTemplate(
                    id=template_data['id'],
                    display_name=template_data['display_name'],
                    description=template_data['description'],
                    icon=template_data['icon'],
                    platform=template_data['platform'],
                    search_keywords=template_data['search_keywords'],
                    url_patterns=url_patterns,
                    url_template=template_data['url_template'],
                    parameters=parameters,
                    example_url=template_data.get('example_url'),
                    enabled=template_data.get('enabled', True)
                )
                
                if template.enabled:
                    templates.append(template)
            
            self._templates = templates
            self._templates_dict = {t.id: t for t in templates}
            
            logger.info(f"成功加载 {len(templates)} 个启用的模板配置")
            
        except Exception as e:
            logger.error(f"加载模板配置失败: {e}")
            raise
    
    def get_all_templates(self) -> List[SubscriptionTemplate]:
        """获取所有启用的模板"""
        self.reload_if_changed()
        return self._templates.copy()
    
    def get_template(self, template_id: str) -> Optional[SubscriptionTemplate]:
        """根据ID获取模板"""
        self.reload_if_changed()
        return self._templates_dict.get(template_id)
    
    def search_templates(self, query: str, limit: int = 10) -> List[TemplateSearchResult]:
        """搜索模板"""
        self.reload_if_changed()
        
        if not query.strip():
            return []
        
        query = query.strip().lower()
        results = []
        
        # 1. 检查是否为URL
        url_results = self._parse_url(query)
        if url_results:
            results.extend(url_results)
        
        # 2. 关键词搜索
        keyword_results = self._search_by_keywords(query)
        results.extend(keyword_results)
        
        # 3. 去重并按分数排序
        seen_template_ids = set()
        unique_results = []
        for result in results:
            if result.template_id not in seen_template_ids:
                seen_template_ids.add(result.template_id)
                unique_results.append(result)
        
        unique_results.sort(key=lambda x: x.match_score, reverse=True)
        return unique_results[:limit]
    
    def _search_by_keywords(self, query: str) -> List[TemplateSearchResult]:
        """根据关键词搜索模板"""
        results = []
        
        for template in self._templates:
            score = self._calculate_match_score(template, query)
            if score > 0:
                results.append(TemplateSearchResult(
                    template_id=template.id,
                    display_name=template.display_name,
                    description=template.description,
                    icon=template.icon,
                    platform=template.platform,
                    match_type="keyword",
                    match_score=score,
                    auto_filled_params=None,
                    required_params=template.parameters
                ))
        
        return results
    
    def _parse_url(self, url: str) -> List[TemplateSearchResult]:
        """解析URL并匹配模板"""
        results = []
        
        for template in self._templates:
            for url_pattern in template.url_patterns:
                match = re.search(url_pattern.pattern, url, re.IGNORECASE)
                if match:
                    # 提取参数
                    auto_filled_params = {}
                    for param_name, group_index in url_pattern.param_mapping.items():
                        if group_index <= len(match.groups()):
                            auto_filled_params[param_name] = match.group(group_index)
                    
                    results.append(TemplateSearchResult(
                        template_id=template.id,
                        display_name=template.display_name,
                        description=template.description,
                        icon=template.icon,
                        platform=template.platform,
                        match_type="url",
                        match_score=1.0,  # URL匹配给最高分
                        auto_filled_params=auto_filled_params,
                        required_params=template.parameters
                    ))
        
        return results
    
    def _calculate_match_score(self, template: SubscriptionTemplate, query: str) -> float:
        """计算模板匹配分数"""
        score = 0.0
        query_lower = query.lower()
        
        # 精确匹配 (权重: 1.0)
        for keyword in template.search_keywords:
            if query_lower == keyword.lower():
                score += 1.0
                break
        
        # 包含匹配 (权重: 0.6)
        if score == 0:
            for keyword in template.search_keywords:
                if query_lower in keyword.lower() or keyword.lower() in query_lower:
                    score += 0.6
                    break
        
        # 平台匹配 (权重: 0.4)
        if query_lower in template.platform.lower():
            score += 0.4
        
        # 显示名称匹配 (权重: 0.3)
        if query_lower in template.display_name.lower():
            score += 0.3
        
        return min(score, 1.0)  # 最高分1.0
    
    def validate_template_parameters(self, template_id: str, parameters: Dict[str, str]) -> Tuple[bool, str]:
        """验证模板参数"""
        template = self.get_template(template_id)
        if not template:
            return False, f"模板 {template_id} 不存在"
        
        # 验证必填参数
        for param in template.parameters:
            if param.required and param.name not in parameters:
                return False, f"缺少必填参数: {param.display_name}"
            
            if param.name in parameters:
                value = parameters[param.name]
                
                # 验证正则表达式
                if param.validation_regex and value:
                    if not re.match(param.validation_regex, value):
                        error_msg = param.validation_message or f"参数 {param.display_name} 格式不正确"
                        return False, error_msg
        
        return True, "验证通过"
    
    def generate_rss_url(self, template_id: str, parameters: Dict[str, str]) -> Optional[str]:
        """生成RSS URL"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        try:
            return template.url_template.format(**parameters)
        except KeyError as e:
            logger.error(f"生成RSS URL失败，缺少参数: {e}")
            return None


# 全局实例
template_loader = TemplateLoader()


def get_template_loader() -> TemplateLoader:
    """获取模板加载器实例"""
    return template_loader 