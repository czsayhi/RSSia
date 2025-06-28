#!/usr/bin/env python3
"""
RSS内容拉取和处理服务演示版
展示完整的RSS处理流程，不依赖额外的第三方库
"""

import hashlib
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

import feedparser
import requests


class RSSContentDemo:
    """RSS内容处理演示服务"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'RSS-Subscriber-Demo/1.0',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        }
    
    def demo_rss_processing(self, rss_url: str) -> Dict[str, Any]:
        """
        演示RSS内容处理的完整流程
        
        Args:
            rss_url: RSS URL
            
        Returns:
            Dict: 处理结果统计
        """
        print(f"\n🚀 开始RSS内容处理演示")
        print(f"📡 目标URL: {rss_url}")
        print("="*60)
        
        # 第1步：HTTP请求拉取RSS原始数据
        print("\n第1步：HTTP请求拉取RSS原始数据")
        print("-" * 30)
        raw_data = self._step1_fetch_raw(rss_url)
        if not raw_data:
            return {"error": "HTTP请求失败"}
        
        # 第2步：feedparser解析RSS/Atom格式
        print("\n第2步：feedparser解析RSS/Atom格式")
        print("-" * 30)
        feed_data = self._step2_parse_feed(raw_data)
        if not feed_data:
            return {"error": "RSS解析失败"}
        
        # 第3步：提取和清洗内容数据
        print("\n第3步：提取和清洗内容数据")
        print("-" * 30)
        raw_entries = self._step3_extract_entries(feed_data)
        
        # 第4步：内容去重处理
        print("\n第4步：内容去重处理")
        print("-" * 30)
        unique_entries = self._step4_deduplicate(raw_entries)
        
        # 第5步：智能内容处理
        print("\n第5步：智能内容处理（标签提取、摘要生成）")
        print("-" * 30)
        processed_entries = self._step5_intelligent_processing(unique_entries)
        
        # 第6步：显示处理结果
        print("\n第6步：处理结果展示")
        print("-" * 30)
        self._step6_display_results(processed_entries)
        
        return {
            "success": True,
            "feed_title": feed_data.feed.get('title', ''),
            "raw_count": len(feed_data.entries),
            "extracted_count": len(raw_entries),
            "unique_count": len(unique_entries),
            "processed_count": len(processed_entries)
        }
    
    def _step1_fetch_raw(self, rss_url: str) -> Optional[bytes]:
        """第1步：HTTP请求拉取RSS原始数据"""
        try:
            print(f"📡 发送HTTP请求到: {rss_url}")
            response = requests.get(rss_url, headers=self.headers, timeout=15)
            
            print(f"✅ HTTP状态码: {response.status_code}")
            print(f"📦 响应大小: {len(response.content)} bytes")
            print(f"📄 Content-Type: {response.headers.get('content-type', '未知')}")
            
            if response.status_code == 200:
                return response.content
            else:
                print(f"❌ HTTP请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ HTTP请求异常: {e}")
            return None
    
    def _step2_parse_feed(self, raw_data: bytes) -> Optional[Any]:
        """第2步：feedparser解析RSS/Atom格式"""
        try:
            print("🔍 使用feedparser解析RSS内容...")
            feed = feedparser.parse(raw_data)
            
            print(f"📰 Feed标题: {feed.feed.get('title', '无标题')}")
            print(f"📝 Feed描述: {feed.feed.get('description', '无描述')[:100]}...")
            print(f"📊 解析到的条目数: {len(feed.entries)}")
            
            if hasattr(feed, 'bozo') and feed.bozo:
                print(f"⚠️ RSS格式警告: {feed.bozo_exception}")
            
            if feed.entries:
                print("✅ RSS解析成功")
                return feed
            else:
                print("❌ 没有找到RSS条目")
                return None
                
        except Exception as e:
            print(f"❌ RSS解析异常: {e}")
            return None
    
    def _step3_extract_entries(self, feed: Any) -> List[Dict]:
        """第3步：提取和清洗内容数据"""
        print(f"📝 开始提取 {len(feed.entries)} 条RSS条目...")
        
        extracted_entries = []
        
        for i, entry in enumerate(feed.entries, 1):
            try:
                # 提取基础字段
                title = self._clean_text(entry.get('title', '无标题'))
                link = entry.get('link', '')
                
                # 处理描述内容
                description = self._extract_description(entry)
                
                # 处理发布时间
                pub_date = self._parse_date(entry)
                
                # 生成内容哈希
                content_hash = self._generate_hash(title, link, description)
                
                extracted_entry = {
                    'title': title,
                    'link': link,
                    'description': description,
                    'pub_date': pub_date,
                    'content_hash': content_hash,
                    'raw_entry': entry  # 保留原始数据用于调试
                }
                
                extracted_entries.append(extracted_entry)
                print(f"📄 {i}. {title[:50]}...")
                
            except Exception as e:
                print(f"⚠️ 条目 {i} 提取失败: {e}")
                continue
        
        print(f"✅ 成功提取 {len(extracted_entries)} 条内容")
        return extracted_entries
    
    def _step4_deduplicate(self, entries: List[Dict]) -> List[Dict]:
        """第4步：内容去重处理"""
        print(f"🔄 开始去重处理，原始条目数: {len(entries)}")
        
        seen_hashes = set()
        unique_entries = []
        
        for entry in entries:
            if entry['content_hash'] not in seen_hashes:
                seen_hashes.add(entry['content_hash'])
                unique_entries.append(entry)
            else:
                print(f"🔄 发现重复内容: {entry['title'][:30]}...")
        
        print(f"✅ 去重完成: {len(entries)} → {len(unique_entries)} 条")
        return unique_entries
    
    def _step5_intelligent_processing(self, entries: List[Dict]) -> List[Dict]:
        """第5步：智能内容处理"""
        print(f"🧠 开始智能处理 {len(entries)} 条内容...")
        
        # 使用ContentProcessingUtils统一处理
        from app.services.content_processing_utils import ContentProcessingUtils
        
        processed_entries = []
        
        for entry in entries:
            try:
                # 使用ContentProcessingUtils的完整处理
                fallback_result = ContentProcessingUtils.process_content_with_fallback(
                    title=entry['title'],
                    description=entry['description'],
                    description_text=entry['description'],  # 使用相同的描述
                    author="",  # demo中没有作者信息
                    platform=ContentProcessingUtils.detect_platform(entry['link']),
                    feed_title=""  # demo中没有feed标题
                )
                
                # 应用处理结果
                entry['smart_summary'] = fallback_result['summary']
                entry['tags'] = fallback_result['tags']  # JSON格式
                
                # 识别平台
                entry['platform'] = ContentProcessingUtils.detect_platform(entry['link'])
                
                processed_entries.append(entry)
                
                print(f"🏷️  标签提取: {entry['tags']}")
                
            except Exception as e:
                print(f"⚠️ 智能处理失败: {e}")
                processed_entries.append(entry)  # 保留原始内容
        
        print(f"✅ 智能处理完成: {len(processed_entries)} 条")
        return processed_entries
    
    def _step6_display_results(self, entries: List[Dict]):
        """第6步：显示处理结果"""
        print(f"📋 最终处理结果展示 (前3条):")
        
        for i, entry in enumerate(entries[:3], 1):
            print(f"\n--- 内容 {i} ---")
            print(f"📄 标题: {entry['title']}")
            print(f"🔗 链接: {entry['link']}")
            print(f"📝 智能摘要: {entry['smart_summary']}")
            print(f"🏷️  标签: {entry['tags']}")
            print(f"📱 平台: {entry['platform']}")
            print(f"📅 发布时间: {entry['pub_date']}")
            print(f"🔒 内容哈希: {entry['content_hash'][:16]}...")
    
    def _clean_text(self, text: str) -> str:
        """清洗文本内容"""
        if not text:
            return ""
        
        # 简单的HTML标签移除
        text = re.sub(r'<[^>]+>', '', text)
        
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_description(self, entry: Any) -> str:
        """提取描述内容"""
        # 尝试多个字段
        for field in ['summary', 'description', 'content']:
            if hasattr(entry, field) and entry.get(field):
                desc = entry[field]
                if isinstance(desc, list) and desc:
                    desc = desc[0].get('value', '')
                
                clean_desc = self._clean_text(str(desc))
                if clean_desc:
                    return clean_desc[:300] + "..." if len(clean_desc) > 300 else clean_desc
        
        return "无描述内容"
    
    def _parse_date(self, entry: Any) -> str:
        """解析发布时间"""
        time_fields = ['published_parsed', 'updated_parsed']
        
        for field in time_fields:
            if hasattr(entry, field) and entry.get(field):
                try:
                    time_struct = entry[field]
                    dt = datetime(*time_struct[:6])
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    continue
        
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _generate_hash(self, title: str, link: str, description: str) -> str:
        """生成内容哈希"""
        content = f"{title}{link}{description}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    



def main():
    """主演示程序"""
    print("🔍 RSS内容拉取和处理完整流程演示")
    print("=" * 60)
    
    # 创建演示服务
    demo = RSSContentDemo()
    
    # 测试URL列表
    test_urls = [
        "https://rsshub.app/bilibili/user/video/2267573",
        "https://rsshub.app/weibo/user/1195230310"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n\n{'='*80}")
        print(f"演示 {i}: {url}")
        print('='*80)
        
        result = demo.demo_rss_processing(url)
        
        print(f"\n📊 处理统计:")
        print(f"- Feed标题: {result.get('feed_title', 'N/A')}")
        print(f"- 原始条目数: {result.get('raw_count', 0)}")
        print(f"- 提取条目数: {result.get('extracted_count', 0)}")
        print(f"- 去重后条目数: {result.get('unique_count', 0)}")
        print(f"- 最终处理条目数: {result.get('processed_count', 0)}")


if __name__ == "__main__":
    main() 