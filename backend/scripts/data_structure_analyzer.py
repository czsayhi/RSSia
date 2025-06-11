#!/usr/bin/env python3
"""
RSS订阅源原生数据结构分析工具
用于深度分析6种订阅源的数据结构和字段特征
"""

import json
import time
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Any, Optional
import feedparser
from pathlib import Path
import hashlib

class RSSDataStructureAnalyzer:
    """RSS数据结构分析器"""
    
    def __init__(self):
        self.results = {
            "analysis_time": datetime.now().isoformat(),
            "platforms": {},
            "unified_schema": {},
            "field_statistics": {},
            "recommendations": {}
        }
        
        # 从订阅模板配置加载测试用例
        self.templates = self._load_templates()
        
        # 请求配置：突破429限制
        self.request_config = {
            "timeout": 30,
            "retry_count": 3,
            "retry_delay": 2,  # 秒
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/rss+xml, application/xml, text/xml",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache"
            }
        }
    
    def _load_templates(self) -> Dict:
        """加载订阅模板配置"""
        template_path = Path(__file__).parent.parent / "app/config/subscription_templates.json"
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def analyze_all_platforms(self):
        """分析所有平台的数据结构"""
        print(f"🚀 开始分析6种订阅源的原生数据结构...")
        
        # 定义测试用例，优先处理能访问的源
        test_cases = [
            # B站 - 优先测试（已知可用）
            {
                "template_id": "bilibili_user_videos",
                "test_params": [
                    {"uid": "2267573", "name": "DIYgod"},
                    {"uid": "297572288", "name": "德州扑克木头哟"},
                    {"uid": "946974", "name": "影视飓风"}  # 新增测试用例
                ]
            },
            {
                "template_id": "bilibili_user_dynamics", 
                "test_params": [
                    {"uid": "297572288", "name": "德州扑克木头哟"},
                    {"uid": "2267573", "name": "DIYgod"}
                ]
            },
            
            # 微博 - 使用多种策略突破限制
            {
                "template_id": "weibo_user_posts",
                "test_params": [
                    {"uid": "1195230310", "name": "测试用户1"},
                    {"uid": "1560906700", "name": "测试用户2"}
                ]
            },
            {
                "template_id": "weibo_keyword_search",
                "test_params": [
                    {"keyword": "人工智能"},
                    {"keyword": "程序员"}
                ]
            },
            
            # 即刻 - 多实例测试
            {
                "template_id": "jike_user_posts",
                "test_params": [
                    {"id": "82D23B32-CF36-4C59-AD6F-D05E3552CBF3", "name": "测试用户1"}
                ]
            },
            {
                "template_id": "jike_topic_posts", 
                "test_params": [
                    {"id": "556688fae4b00c57d9dd46ee", "name": "测试圈子1"}
                ]
            }
        ]
        
        # 并发分析，但控制并发数避免429
        semaphore = asyncio.Semaphore(2)  # 最多2个并发请求
        tasks = []
        
        for test_case in test_cases:
            for params in test_case["test_params"]:
                task = self._analyze_single_source(
                    semaphore, test_case["template_id"], params
                )
                tasks.append(task)
        
        # 执行分析
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for result in results:
            if isinstance(result, dict) and not isinstance(result, Exception):
                platform = result.get("platform")
                if platform:
                    if platform not in self.results["platforms"]:
                        self.results["platforms"][platform] = {
                            "templates": {},
                            "common_fields": set(),
                            "unique_fields": set()
                        }
                    
                    template_id = result.get("template_id")
                    self.results["platforms"][platform]["templates"][template_id] = result
        
        # 生成统一数据模式
        self._generate_unified_schema()
        
        # 生成字段统计
        self._generate_field_statistics()
        
        # 生成建议
        self._generate_recommendations()
        
        return self.results
    
    async def _analyze_single_source(self, semaphore: asyncio.Semaphore, 
                                   template_id: str, params: Dict) -> Dict:
        """分析单个订阅源"""
        async with semaphore:
            try:
                # 获取模板配置
                template = next(
                    t for t in self.templates["templates"] 
                    if t["template_id"] == template_id
                )
                
                # 构建RSS URL
                url_template = template["url_template"]
                rss_url = url_template.format(**params)
                
                print(f"📡 分析 {template['platform']} - {template['template_name']}")
                print(f"   URL: {rss_url}")
                
                # 获取RSS数据
                rss_data = await self._fetch_rss_with_retry(rss_url)
                if not rss_data:
                    return {"error": f"无法获取RSS数据: {rss_url}"}
                
                # 解析数据结构
                parsed_data = feedparser.parse(rss_data)
                
                # 分析结构
                analysis = self._analyze_rss_structure(parsed_data, template, params)
                
                # 添加请求间隔，避免429
                await asyncio.sleep(1)
                
                return analysis
                
            except Exception as e:
                return {"error": str(e), "template_id": template_id, "params": params}
    
    async def _fetch_rss_with_retry(self, url: str) -> Optional[str]:
        """带重试机制的RSS获取"""
        for attempt in range(self.request_config["retry_count"]):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.request_config["timeout"]),
                    headers=self.request_config["headers"]
                ) as session:
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 429:
                            wait_time = (2 ** attempt) * self.request_config["retry_delay"]
                            print(f"   ⚠️  HTTP 429，等待 {wait_time}s 后重试...")
                            await asyncio.sleep(wait_time)
                        else:
                            print(f"   ❌ HTTP {response.status}: {await response.text()}")
                            return None
                            
            except Exception as e:
                print(f"   ❌ 请求异常: {str(e)}")
                if attempt < self.request_config["retry_count"] - 1:
                    await asyncio.sleep(self.request_config["retry_delay"])
        
        return None
    
    def _analyze_rss_structure(self, parsed_data: Any, template: Dict, params: Dict) -> Dict:
        """分析RSS数据结构"""
        feed = parsed_data.feed
        entries = parsed_data.entries[:5]  # 分析前5条内容
        
        analysis = {
            "template_id": template["template_id"],
            "platform": template["platform"],
            "template_name": template["template_name"],
            "test_params": params,
            "analysis_time": datetime.now().isoformat(),
            
            # Feed级别信息
            "feed_info": {
                "title": getattr(feed, 'title', ''),
                "description": getattr(feed, 'description', ''),
                "link": getattr(feed, 'link', ''),
                "language": getattr(feed, 'language', ''),
                "generator": getattr(feed, 'generator', ''),
                "updated": getattr(feed, 'updated', ''),
                "total_entries": len(parsed_data.entries)
            },
            
            # 内容字段结构
            "content_schema": {},
            "field_types": {},
            "field_examples": {},
            "unique_fields": set(),
            "common_fields": set()
        }
        
        if entries:
            # 分析第一条内容的完整结构
            first_entry = entries[0]
            analysis["content_schema"] = self._extract_entry_fields(first_entry)
            
            # 分析所有字段的类型和示例
            for entry in entries:
                for field_name in dir(entry):
                    if not field_name.startswith('_'):
                        try:
                            field_value = getattr(entry, field_name)
                            if field_value and not callable(field_value):
                                # 记录字段类型
                                field_type = type(field_value).__name__
                                if field_name not in analysis["field_types"]:
                                    analysis["field_types"][field_name] = field_type
                                
                                # 记录字段示例（截取前100字符）
                                if field_name not in analysis["field_examples"]:
                                    example = str(field_value)[:100]
                                    analysis["field_examples"][field_name] = example
                        except:
                            pass
        
        # 转换set为list以便JSON序列化
        analysis["unique_fields"] = list(analysis["unique_fields"])
        analysis["common_fields"] = list(analysis["common_fields"])
        
        return analysis
    
    def _extract_entry_fields(self, entry) -> Dict:
        """提取条目的所有字段"""
        fields = {}
        
        for field_name in dir(entry):
            if not field_name.startswith('_'):
                try:
                    field_value = getattr(entry, field_name)
                    if field_value and not callable(field_value):
                        # 特殊处理一些复杂字段
                        if hasattr(field_value, '__dict__'):
                            fields[field_name] = str(field_value)
                        elif isinstance(field_value, (list, tuple)):
                            fields[field_name] = list(field_value)
                        else:
                            fields[field_name] = field_value
                except:
                    pass
        
        return fields
    
    def _generate_unified_schema(self):
        """生成统一的数据模式"""
        all_fields = {}
        
        for platform_name, platform_data in self.results["platforms"].items():
            for template_id, template_data in platform_data["templates"].items():
                if "field_types" in template_data:
                    for field_name, field_type in template_data["field_types"].items():
                        if field_name not in all_fields:
                            all_fields[field_name] = {
                                "type": field_type,
                                "platforms": [platform_name],
                                "count": 1
                            }
                        else:
                            if platform_name not in all_fields[field_name]["platforms"]:
                                all_fields[field_name]["platforms"].append(platform_name)
                            all_fields[field_name]["count"] += 1
        
        # 识别核心字段（出现在多个平台的字段）
        core_fields = {
            field_name: field_info 
            for field_name, field_info in all_fields.items()
            if field_info["count"] >= 2
        }
        
        self.results["unified_schema"] = {
            "all_fields": all_fields,
            "core_fields": core_fields,
            "mvp_display_fields": [
                "title", "link", "description", "published", "author"
            ]
        }
    
    def _generate_field_statistics(self):
        """生成字段统计信息"""
        total_platforms = len(self.results["platforms"])
        total_templates = sum(
            len(p["templates"]) for p in self.results["platforms"].values()
        )
        
        field_frequency = {}
        for platform_data in self.results["platforms"].values():
            for template_data in platform_data["templates"].values():
                if "field_types" in template_data:
                    for field_name in template_data["field_types"]:
                        field_frequency[field_name] = field_frequency.get(field_name, 0) + 1
        
        # 按频率排序
        sorted_fields = sorted(
            field_frequency.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        self.results["field_statistics"] = {
            "total_platforms": total_platforms,
            "total_templates": total_templates,
            "total_unique_fields": len(field_frequency),
            "high_frequency_fields": sorted_fields[:10],
            "universal_fields": [
                field for field, count in sorted_fields 
                if count >= total_templates * 0.8
            ]
        }
    
    def _generate_recommendations(self):
        """生成MVP阶段建议"""
        self.results["recommendations"] = {
            "mvp_display_fields": {
                "essential": ["title", "link", "published"],
                "recommended": ["description", "author"],
                "optional": ["tags", "updated", "id"]
            },
            
            "ui_design_suggestions": {
                "title": "主标题，支持链接跳转",
                "published": "相对时间显示（如'2小时前'）",
                "description": "摘要，截取200字符，支持展开",
                "author": "作者信息，可选显示",
                "platform_icon": "根据template.platform显示对应icon"
            },
            
            "data_processing_priorities": [
                "实现RSS源访问频率控制",
                "统一时间格式处理（published字段）",
                "HTML标签清理（description字段）",
                "内容去重机制（基于link或id）",
                "错误处理和降级策略"
            ],
            
            "technical_implementation": {
                "backend_field_mapping": {
                    "title": "entry.title",
                    "link": "entry.link", 
                    "description": "clean_html(entry.description)",
                    "published_at": "parse_datetime(entry.published)",
                    "author": "entry.author or extract_from_title()",
                    "content_hash": "generate_hash(entry.link + entry.title)"
                },
                
                "frontend_display_props": {
                    "title": "string",
                    "link": "string", 
                    "description": "string (max 200 chars)",
                    "published_at": "Date object",
                    "author": "string | null",
                    "platform": "string",
                    "template_name": "string"
                }
            }
        }
    
    def save_results(self, output_file: str = None):
        """保存分析结果"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"rss_data_structure_analysis_{timestamp}.json"
        
        output_path = Path(__file__).parent.parent / "docs/analysis" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 处理set类型以便JSON序列化
        def serialize_sets(obj):
            if isinstance(obj, set):
                return list(obj)
            return obj
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=serialize_sets)
        
        print(f"📄 分析结果已保存至: {output_path}")
        return output_path

async def main():
    """主函数"""
    analyzer = RSSDataStructureAnalyzer()
    
    print("=" * 60)
    print("🔍 RSS订阅源原生数据结构深度分析")
    print("=" * 60)
    
    # 执行分析
    results = await analyzer.analyze_all_platforms()
    
    # 保存结果
    output_path = analyzer.save_results()
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("📊 分析摘要")
    print("=" * 60)
    
    platforms = results.get("platforms", {})
    print(f"✅ 成功分析平台数: {len(platforms)}")
    
    for platform_name, platform_data in platforms.items():
        successful_templates = len(platform_data.get("templates", {}))
        print(f"   📱 {platform_name}: {successful_templates}个模板")
    
    if "field_statistics" in results:
        stats = results["field_statistics"]
        print(f"🔢 发现字段总数: {stats.get('total_unique_fields', 0)}")
        print(f"🌟 通用字段数量: {len(stats.get('universal_fields', []))}")
    
    print(f"\n📄 详细报告: {output_path}")
    print("🚀 建议下一步: 基于分析结果优化用户界面和数据处理逻辑")

if __name__ == "__main__":
    asyncio.run(main()) 