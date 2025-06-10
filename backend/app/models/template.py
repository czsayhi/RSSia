"""
订阅模板搜索相关的数据模型
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TemplateParameter(BaseModel):
    """模板参数配置"""
    name: str = Field(..., description="参数名称")
    display_name: str = Field(..., description="参数显示名称")
    description: str = Field(..., description="参数描述")
    type: str = Field(default="string", description="参数类型")
    required: bool = Field(default=True, description="是否必填")
    placeholder: Optional[str] = Field(None, description="占位符文本")
    validation_regex: Optional[str] = Field(None, description="验证正则表达式")
    validation_message: Optional[str] = Field(None, description="验证失败提示信息")
    pre_filled: Optional[str] = Field(None, description="预填充值（URL解析时使用）")


class TemplateSearchResult(BaseModel):
    """模板搜索结果"""
    template_id: str = Field(..., description="模板唯一标识")
    template_name: str = Field(..., description="模板显示名称")
    description: str = Field(..., description="模板描述")
    icon: str = Field(..., description="模板图标文件名")
    platform: str = Field(..., description="所属平台")
    match_type: str = Field(..., description="匹配类型：keyword|url")
    match_score: float = Field(..., description="匹配分数，0-1之间")
    auto_filled_params: Optional[Dict[str, str]] = Field(
        None, description="URL解析时自动填充的参数"
    )
    required_params: List[TemplateParameter] = Field(
        default_factory=list, description="需要用户填写的参数"
    )


class TemplateSearchRequest(BaseModel):
    """模板搜索请求"""
    query: str = Field(..., min_length=1, description="搜索关键词或URL")
    limit: int = Field(default=10, ge=1, le=50, description="返回结果数量限制")


class TemplateSearchResponse(BaseModel):
    """模板搜索响应"""
    results: List[TemplateSearchResult] = Field(..., description="搜索结果列表")
    total: int = Field(..., description="结果总数")
    query: str = Field(..., description="搜索关键词")
    search_type: str = Field(..., description="搜索类型：keyword|url|mixed")


class URLParseResult(BaseModel):
    """URL解析结果"""
    success: bool = Field(..., description="解析是否成功")
    template_id: Optional[str] = Field(None, description="匹配的模板ID")
    extracted_params: Optional[Dict[str, str]] = Field(
        None, description="提取的参数"
    )
    confidence: float = Field(default=0.0, description="匹配置信度")
    error_message: Optional[str] = Field(None, description="解析失败时的错误信息")


class ValidateParametersRequest(BaseModel):
    """验证参数请求"""
    template_id: str = Field(..., description="模板ID")
    parameters: Dict[str, str] = Field(..., description="参数字典")


class ValidateParametersResponse(BaseModel):
    """验证参数响应"""
    is_valid: bool = Field(..., description="验证结果")
    message: str = Field(..., description="验证信息")
    template_id: str = Field(..., description="模板ID") 