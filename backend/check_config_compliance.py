#!/usr/bin/env python3
"""
RSSHub订阅源配置合规性检查脚本
基于规范文档检查 subscription_config.py 的配置是否正确
"""

import re
from typing import Dict, List, Any

# 从规范文档中提取的标准配置
STANDARD_ROUTES = {
    "weibo": {
        "user": {
            "route": "/weibo/user/:uid/:routeParams?",
            "url_template": "https://rsshub.app/weibo/user/{uid}",
            "required_params": ["uid"],
            "optional_params": ["routeParams"],
            "param_patterns": {
                "uid": r"^[0-9]+$"
            }
        },
        "keyword": {
            "route": "/weibo/keyword/:keyword/:routeParams?", 
            "url_template": "https://rsshub.app/weibo/keyword/{keyword}",
            "required_params": ["keyword"],
            "optional_params": ["routeParams"],
            "param_patterns": {
                "keyword": None  # 关键词无固定格式限制
            }
        }
    },
    "jike": {
        "user": {
            "route": "/jike/user/:id",
            "url_template": "https://rsshub.app/jike/user/{id}",
            "required_params": ["id"],
            "optional_params": [],
            "param_patterns": {
                "id": None  # UUID格式，但规范中未明确
            }
        },
        "topic": {
            "route": "/jike/topic/:id/:showUid?",
            "url_template": "https://rsshub.app/jike/topic/{id}",
            "required_params": ["id"],
            "optional_params": ["showUid"],
            "param_patterns": {
                "id": None
            }
        }
    },
    "bilibili": {
        "user_video": {
            "route": "/bilibili/user/video/:uid/:embed?",
            "url_template": "https://rsshub.app/bilibili/user/video/{uid}",
            "required_params": ["uid"],
            "optional_params": ["embed"],
            "param_patterns": {
                "uid": r"^[0-9]+$"
            }
        },
        "user_dynamic": {
            "route": "/bilibili/user/dynamic/:uid/:routeParams?",
            "url_template": "https://rsshub.app/bilibili/user/dynamic/{uid}",
            "required_params": ["uid"],
            "optional_params": ["routeParams"],
            "param_patterns": {
                "uid": r"^[0-9]+$"
            }
        }
    }
}

def load_current_config():
    """加载当前的配置"""
    try:
        from app.config.subscription_config import (
            PLATFORM_CONFIG, 
            SUBSCRIPTION_TEMPLATES,
            SUBSCRIPTION_TYPE_NAMES
        )
        return {
            "platform_config": PLATFORM_CONFIG,
            "templates": SUBSCRIPTION_TEMPLATES,
            "type_names": SUBSCRIPTION_TYPE_NAMES
        }
    except ImportError as e:
        print(f"❌ 无法导入配置模块: {e}")
        return None

def check_platform_config(platform_config):
    """检查平台配置"""
    print("🔍 检查平台配置...")
    issues = []
    
    standard_platforms = {"bilibili", "weibo", "jike"}
    configured_platforms = set()
    
    for platform_enum, config in platform_config.items():
        platform_name = platform_enum.value
        configured_platforms.add(platform_name)
        
        # 检查平台名称
        if platform_name not in standard_platforms:
            issues.append(f"⚠️  未知平台: {platform_name}")
        
        # 检查必需字段
        required_fields = ["name", "description", "supported_types"]
        for field in required_fields:
            if field not in config:
                issues.append(f"❌ 平台 {platform_name} 缺少必需字段: {field}")
    
    # 检查缺失的平台
    missing_platforms = standard_platforms - configured_platforms
    for platform in missing_platforms:
        issues.append(f"⚠️  缺少平台配置: {platform}")
    
    return issues

def check_subscription_templates(templates):
    """检查订阅模板配置"""
    print("🔍 检查订阅模板配置...")
    issues = []
    url_templates = []
    template_names = []
    
    for i, template in enumerate(templates):
        template_id = i + 1
        platform = template.get("platform")
        subscription_type = template.get("subscription_type")
        
        if not platform or not subscription_type:
            issues.append(f"❌ 模板 {template_id} 缺少平台或订阅类型")
            continue
            
        platform_name = platform.value if hasattr(platform, 'value') else str(platform)
        type_name = subscription_type.value if hasattr(subscription_type, 'value') else str(subscription_type)
        
        # 检查URL模板重复
        url_template = template.get("url_template", "")
        if url_template in url_templates:
            issues.append(f"❌ 模板 {template_id} URL模板重复: {url_template}")
        else:
            url_templates.append(url_template)
        
        # 检查模板名称重复
        template_name = f"{platform_name}_{template.get('name', '')}"
        if template_name in template_names:
            issues.append(f"❌ 模板 {template_id} 名称重复: {template_name}")
        else:
            template_names.append(template_name)
        
        # 检查URL模板格式
        if not url_template.startswith("https://rsshub.app/"):
            issues.append(f"❌ 模板 {template_id} URL模板格式错误: {url_template}")
        
        # 检查参数配置
        parameters = template.get("parameters", [])
        if not parameters:
            issues.append(f"⚠️  模板 {template_id} 没有参数配置")
        else:
            param_names = []
            for param in parameters:
                param_name = param.name if hasattr(param, 'name') else param.get('name', '') if hasattr(param, 'get') else ''
                if param_name in param_names:
                    issues.append(f"❌ 模板 {template_id} 参数名重复: {param_name}")
                else:
                    param_names.append(param_name)
        
        # 与标准配置对比
        issues.extend(check_template_against_standard(template_id, platform_name, type_name, template))
    
    return issues

def check_template_against_standard(template_id, platform, subscription_type, template):
    """检查模板是否符合标准配置"""
    issues = []
    
    # 映射订阅类型
    type_mapping = {
        "user": "user",
        "keyword": "keyword", 
        "topic": "topic"
    }
    
    mapped_type = type_mapping.get(subscription_type)
    if not mapped_type:
        issues.append(f"⚠️  模板 {template_id} 使用了非标准订阅类型: {subscription_type}")
        return issues
    
    # 特殊处理B站的两种用户订阅
    if platform == "bilibili" and subscription_type == "user":
        url_template = template.get("url_template", "")
        if "video" in url_template:
            standard_key = "user_video"
        elif "dynamic" in url_template:
            standard_key = "user_dynamic"
        else:
            issues.append(f"❌ 模板 {template_id} B站用户订阅类型不明确")
            return issues
    else:
        standard_key = mapped_type
    
    # 检查是否存在标准配置
    if platform not in STANDARD_ROUTES:
        issues.append(f"⚠️  模板 {template_id} 平台 {platform} 不在标准配置中")
        return issues
    
    if standard_key not in STANDARD_ROUTES[platform]:
        issues.append(f"⚠️  模板 {template_id} 订阅类型 {standard_key} 不在标准配置中")
        return issues
    
    standard = STANDARD_ROUTES[platform][standard_key]
    
    # 检查URL模板
    expected_url = standard["url_template"]
    actual_url = template.get("url_template", "")
    
    # 提取参数部分进行比较
    expected_params = re.findall(r'\{([^}]+)\}', expected_url)
    actual_params = re.findall(r'\{([^}]+)\}', actual_url)
    
    if set(expected_params) != set(actual_params):
        issues.append(f"⚠️  模板 {template_id} URL参数不匹配。期望: {expected_params}, 实际: {actual_params}")
    
    # 检查参数配置
    parameters = template.get("parameters", [])
    param_names = [p.name if hasattr(p, 'name') else p.get('name', '') if hasattr(p, 'get') else '' for p in parameters]
    
    # 检查必需参数
    for required_param in standard["required_params"]:
        if required_param not in param_names:
            issues.append(f"❌ 模板 {template_id} 缺少必需参数: {required_param}")
    
    # 检查参数验证规则
    for param in parameters:
        param_name = param.name if hasattr(param, 'name') else param.get('name', '') if hasattr(param, 'get') else ''
        if param_name in standard["param_patterns"]:
            expected_pattern = standard["param_patterns"][param_name]
            
            # 获取实际的验证规则
            if hasattr(param, 'validation_regex'):
                actual_pattern = param.validation_regex
            elif hasattr(param, 'validation'):
                actual_pattern = param.validation
            elif hasattr(param, 'get'):
                actual_pattern = param.get('validation')
            else:
                actual_pattern = None
            
            if expected_pattern and actual_pattern != expected_pattern:
                issues.append(f"⚠️  模板 {template_id} 参数 {param_name} 验证规则不匹配。期望: {expected_pattern}, 实际: {actual_pattern}")
    
    return issues

def check_missing_templates():
    """检查缺失的模板"""
    print("🔍 检查缺失的模板...")
    issues = []
    
    # 根据标准配置检查缺失的模板
    expected_templates = []
    for platform, types in STANDARD_ROUTES.items():
        for type_key, config in types.items():
            expected_templates.append(f"{platform}_{type_key}")
    
    # 加载当前配置检查
    try:
        from app.config.subscription_config import SUBSCRIPTION_TEMPLATES
        
        current_templates = []
        for template in SUBSCRIPTION_TEMPLATES:
            platform = template.get("platform")
            subscription_type = template.get("subscription_type")
            url_template = template.get("url_template", "")
            
            if platform and subscription_type:
                platform_name = platform.value if hasattr(platform, 'value') else str(platform)
                type_name = subscription_type.value if hasattr(subscription_type, 'value') else str(subscription_type)
                
                # 特殊处理B站
                if platform_name == "bilibili" and type_name == "user":
                    if "video" in url_template:
                        current_templates.append("bilibili_user_video")
                    elif "dynamic" in url_template:
                        current_templates.append("bilibili_user_dynamic")
                else:
                    current_templates.append(f"{platform_name}_{type_name}")
        
        # 检查缺失的模板
        missing = set(expected_templates) - set(current_templates)
        for template in missing:
            issues.append(f"⚠️  缺少模板配置: {template}")
            
    except ImportError as e:
        issues.append(f"❌ 无法检查模板: {e}")
    
    return issues

def main():
    """主检查函数"""
    print("🚀 RSSHub订阅源配置合规性检查")
    print("=" * 60)
    
    # 加载配置
    config = load_current_config()
    if not config:
        print("❌ 无法加载配置，检查终止")
        return
    
    all_issues = []
    
    # 1. 检查平台配置
    platform_issues = check_platform_config(config["platform_config"])
    all_issues.extend(platform_issues)
    
    # 2. 检查订阅模板
    template_issues = check_subscription_templates(config["templates"])
    all_issues.extend(template_issues)
    
    # 3. 检查缺失的模板
    missing_issues = check_missing_templates()
    all_issues.extend(missing_issues)
    
    # 结果汇总
    print(f"\n📊 检查结果汇总")
    print("=" * 60)
    
    if not all_issues:
        print("🎉 恭喜！配置完全符合规范，没有发现问题")
        return
    
    # 按严重程度分类
    errors = [issue for issue in all_issues if issue.startswith("❌")]
    warnings = [issue for issue in all_issues if issue.startswith("⚠️")]
    
    print(f"总问题数: {len(all_issues)}")
    print(f"错误: {len(errors)}")
    print(f"警告: {len(warnings)}")
    
    print(f"\n📋 详细问题列表:")
    for issue in all_issues:
        print(f"   {issue}")
    
    # 修复建议
    print(f"\n🔧 修复建议:")
    if errors:
        print("   1. 优先修复错误项，这些会影响功能正常运行")
    if warnings:
        print("   2. 考虑修复警告项，提升配置的标准化程度")
    if missing_issues:
        print("   3. 根据规范文档补充缺失的模板配置")

if __name__ == "__main__":
    main() 