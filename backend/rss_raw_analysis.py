#!/usr/bin/env python3
"""
RSS原始内容分析工具
对比RSS原始内容和后端处理后内容
"""

import feedparser
import requests
import json
from datetime import datetime

def analyze_rss_content(url, name):
    """分析RSS原始内容"""
    print(f"\n{'='*60}")
    print(f"分析 {name}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            
            print(f"✅ HTTP状态: {response.status_code}")
            print(f"📰 Feed标题: {feed.feed.get('title', '无标题')}")
            print(f"📝 Feed描述: {feed.feed.get('description', '无描述')}")
            print(f"📊 总条目数: {len(feed.entries)}")
            
            print(f"\n📋 前5条原始内容详情:")
            for i, entry in enumerate(feed.entries[:5]):
                print(f"\n--- 条目 {i+1} ---")
                print(f"标题: {entry.get('title', '无标题')}")
                print(f"链接: {entry.get('link', '无链接')}")
                print(f"发布时间: {entry.get('published', '无时间')}")
                print(f"更新时间: {entry.get('updated', '无更新时间')}")
                print(f"作者: {entry.get('author', '无作者')}")
                print(f"描述: {entry.get('summary', '无描述')[:150]}...")
                
                # 显示所有可用字段
                print("原始字段列表:")
                for key in entry.keys():
                    if key not in ['title', 'link', 'published', 'updated', 'author', 'summary']:
                        value = str(entry.get(key, ''))[:50]
                        print(f"  {key}: {value}...")
                        
            return True
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def get_backend_content():
    """获取后端处理后的内容"""
    print(f"\n{'='*60}")
    print("获取后端处理后内容")
    print('='*60)
    
    try:
        response = requests.get("http://localhost:8001/api/v1/content/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 后端API状态: {response.status_code}")
            print(f"📊 后端内容数量: {len(data)}")
            
            for item in data:
                print(f"\n--- 后端内容 {item['content_id']} ---")
                print(f"subscription_id: {item['subscription_id']}")
                print(f"title: {item['title']}")
                print(f"link: {item['link']}")
                print(f"summary: {item['summary']}")
                print(f"published_at: {item['published_at']}")
                print(f"fetched_at: {item['fetched_at']}")
                print(f"tags: {item['tags']}")
                print(f"platform: {item['platform']}")
                print(f"source_name: {item['source_name']}")
                print(f"is_favorited: {item['is_favorited']}")
            
            return data
        else:
            print(f"❌ 后端API请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 后端API异常: {e}")
        return None

if __name__ == "__main__":
    print("🔍 RSS原始内容 vs 后端处理内容对比分析")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试用例列表
    test_cases = [
        {
            "name": "B站DIYgod视频",
            "url": "https://rsshub.app/bilibili/user/video/2267573"
        },
        {
            "name": "微博何炅动态", 
            "url": "https://rsshub.app/weibo/user/1195230310"
        }
    ]
    
    # 分析原始RSS内容
    for case in test_cases:
        analyze_rss_content(case["url"], case["name"])
    
    # 获取后端处理后内容
    backend_data = get_backend_content()
    
    print(f"\n{'='*60}")
    print("分析总结")
    print('='*60)
    print("1. subscription_id 和 source_name 字段来源分析:")
    print("   - subscription_id: 这是后端生成的数据库主键，不是RSS原生字段")
    print("   - source_name: 这是后端根据订阅配置生成的展示名称，不是RSS原生字段")
    print("\n2. 内容过滤情况:")
    print("   - 后端返回的内容数量可能少于RSS原始内容")
    print("   - 这可能是因为去重、过滤或模拟数据的原因") 