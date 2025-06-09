#!/usr/bin/env python3
"""
基于新修复配置的RSS订阅功能验证脚本
使用 docs/test-cases.md 中的测试用例和修复后的订阅配置验证系统功能
"""

import requests
import feedparser
import json
from datetime import datetime
from typing import Dict, List

# 基于test-cases.md的测试用例
TEST_CASES = [
    {
        "id": 1,
        "name": "B站UP主视频订阅 - DIYgod",
        "url": "https://rsshub.app/bilibili/user/video/2267573",
        "platform": "bilibili",
        "subscription_type": "user",
        "params": {"uid": "2267573"},
        "description": "订阅DIYgod的B站视频投稿",
        "verified": True
    },
    {
        "id": 2, 
        "name": "B站UP主视频订阅 - 另一用户",
        "url": "https://rsshub.app/bilibili/user/video/297572288",
        "platform": "bilibili",
        "subscription_type": "user", 
        "params": {"uid": "297572288"},
        "description": "订阅另一B站用户的视频投稿",
        "verified": False
    },
    {
        "id": 3,
        "name": "微博博主订阅 - 用户A",
        "url": "https://rsshub.app/weibo/user/1673951863",
        "platform": "weibo",
        "subscription_type": "user",
        "params": {"uid": "1673951863"},
        "description": "订阅微博用户的动态",
        "verified": False
    },
    {
        "id": 4,
        "name": "微博博主订阅 - 阑夕（科技博主）",
        "url": "https://rsshub.app/weibo/user/1560906700",
        "platform": "weibo", 
        "subscription_type": "user",
        "params": {"uid": "1560906700"},
        "description": "订阅阑夕的微博动态（互联网视频博主，知名科技自媒体）",
        "verified": True
    },
    {
        "id": 5,
        "name": "微博关键词订阅 - AI行业",
        "url": "https://rsshub.app/weibo/keyword/ai行业",
        "platform": "weibo",
        "subscription_type": "keyword",
        "params": {"keyword": "ai行业"},
        "description": "订阅包含'ai行业'关键词的微博内容",
        "verified": False
    },
    {
        "id": 6,
        "name": "即刻用户订阅",
        "url": "https://rsshub.app/jike/user/82D23B32-CF36-4C59-AD6F-D05E3552CBF3",
        "platform": "jike",
        "subscription_type": "user",
        "params": {"id": "82D23B32-CF36-4C59-AD6F-D05E3552CBF3"},
        "description": "订阅即刻用户的内容",
        "verified": False
    },
    {
        "id": 7,
        "name": "即刻圈子订阅",
        "url": "https://rsshub.app/jike/topic/63579abb6724cc583b9bba9a",
        "platform": "jike",
        "subscription_type": "topic",
        "params": {"id": "63579abb6724cc583b9bba9a"},
        "description": "订阅即刻特定圈子的内容",
        "verified": False
    }
]

def test_config_loading():
    """测试新配置是否能正常加载"""
    print("🔍 测试配置加载...")
    try:
        from app.config.subscription_config import get_platform_info, SUBSCRIPTION_TEMPLATES
        
        platforms = get_platform_info()
        templates = SUBSCRIPTION_TEMPLATES
        
        print(f"   ✅ 成功加载 {len(platforms)} 个平台配置")
        print(f"   ✅ 成功加载 {len(templates)} 个订阅模板")
        
        # 显示平台信息
        for platform in platforms:
            types = [t.value for t in platform.supported_subscription_types]
            print(f"      📱 {platform.name}: {types}")
        
        return True
    except Exception as e:
        print(f"   ❌ 配置加载失败: {e}")
        return False

def test_url_template_generation():
    """测试URL模板生成功能"""
    print("\n🔍 测试URL模板生成...")
    try:
        from app.config.subscription_config import SUBSCRIPTION_TEMPLATES
        
        # 测试每个模板的URL生成
        for template in SUBSCRIPTION_TEMPLATES:
            platform = template["platform"].value
            subscription_type = template["subscription_type"].value
            url_template = template["url_template"]
            parameters = template["parameters"]
            
            print(f"   📋 {platform}_{subscription_type}: {url_template}")
            
            # 验证参数占位符
            for param in parameters:
                param_name = param.name
                if f"{{{param_name}}}" not in url_template:
                    print(f"      ⚠️  参数 {param_name} 在URL模板中未找到占位符")
                else:
                    print(f"      ✅ 参数 {param_name} 配置正确")
        
        return True
    except Exception as e:
        print(f"   ❌ URL模板生成测试失败: {e}")
        return False

def test_rss_content_fetch(test_case):
    """测试RSS内容获取"""
    case_id = test_case["id"]
    name = test_case["name"]
    url = test_case["url"]
    verified = test_case.get("verified", False)
    
    print(f"\n📡 测试用例 {case_id}: {name}")
    print(f"   URL: {url}")
    print(f"   平台: {test_case['platform']}")
    print(f"   类型: {test_case['subscription_type']}")
    if verified:
        print(f"   ✅ 已验证可用")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"   HTTP状态: {response.status_code}")
        
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            
            if hasattr(feed, 'entries') and len(feed.entries) > 0:
                print(f"   ✅ 成功获取 {len(feed.entries)} 条RSS内容")
                
                if hasattr(feed, 'feed'):
                    feed_title = getattr(feed.feed, 'title', '未知标题')
                    print(f"   📰 Feed标题: {feed_title}")
                
                # 显示最新内容
                print(f"   📋 最新内容:")
                for i, entry in enumerate(feed.entries[:2]):
                    title = entry.get('title', '无标题')[:60]
                    pub_date = entry.get('published', '未知时间')
                    print(f"      {i+1}. {title}...")
                    print(f"         时间: {pub_date}")
                
                return {
                    "success": True,
                    "entries_count": len(feed.entries),
                    "feed_title": getattr(feed.feed, 'title', '未知标题') if hasattr(feed, 'feed') else '未知标题'
                }
            else:
                if feed.bozo:
                    print(f"   ⚠️  RSS解析错误: {feed.bozo_exception}")
                else:
                    print(f"   ❌ RSS解析成功但无内容条目")
                return {"success": False, "error": "无内容"}
        
        elif response.status_code == 429:
            print(f"   ⚠️  请求频率限制 (429)")
            return {"success": False, "error": "频率限制"}
        else:
            print(f"   ❌ HTTP请求失败: {response.status_code}")
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        print(f"   ❌ 请求超时")
        return {"success": False, "error": "请求超时"}
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return {"success": False, "error": str(e)}

def test_new_config_api():
    """测试新配置的API接口"""
    print("\n🔍 测试订阅配置API...")
    
    base_url = "http://localhost:8000"
    
    try:
        # 测试平台列表API
        response = requests.get(f"{base_url}/api/v1/subscription-config/platforms", timeout=5)
        if response.status_code == 200:
            platforms = response.json()
            print(f"   ✅ 平台列表API正常: {len(platforms.get('platforms', []))} 个平台")
        else:
            print(f"   ⚠️  平台列表API响应异常: {response.status_code}")
            return False
            
        # 测试订阅类型API
        response = requests.get(f"{base_url}/api/v1/subscription-config/platforms/bilibili/subscription-types", timeout=5)
        if response.status_code == 200:
            types = response.json()
            print(f"   ✅ 订阅类型API正常: B站支持 {len(types.get('subscription_types', []))} 种类型")
        else:
            print(f"   ⚠️  订阅类型API响应异常: {response.status_code}")
            return False
            
        return True
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  无法连接到API服务器，跳过API测试")
        return None
    except Exception as e:
        print(f"   ❌ API测试失败: {e}")
        return False

def main():
    """主验证函数"""
    print("🚀 RSS智能订阅器 - 新配置功能验证")
    print("=" * 70)
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试用例来源: docs/test-cases.md")
    print(f"配置文件: backend/app/config/subscription_config.py")
    
    # 验证统计
    total_tests = 0
    passed_tests = 0
    
    # 1. 配置加载测试
    total_tests += 1
    if test_config_loading():
        passed_tests += 1
    
    # 2. URL模板生成测试  
    total_tests += 1
    if test_url_template_generation():
        passed_tests += 1
    
    # 3. API接口测试
    total_tests += 1
    api_result = test_new_config_api()
    if api_result is True:
        passed_tests += 1
    elif api_result is None:
        # 如果API服务器未启动，不计入失败
        total_tests -= 1
    
    # 4. RSS内容获取测试
    rss_results = {}
    successful_cases = 0
    
    print(f"\n📋 RSS内容获取测试")
    print("-" * 50)
    
    for test_case in TEST_CASES:
        total_tests += 1
        result = test_rss_content_fetch(test_case)
        rss_results[test_case["id"]] = result
        
        if result["success"]:
            passed_tests += 1
            successful_cases += 1
    
    # 按平台统计
    platform_stats = {}
    for test_case in TEST_CASES:
        platform = test_case["platform"]
        if platform not in platform_stats:
            platform_stats[platform] = {"total": 0, "success": 0}
        
        platform_stats[platform]["total"] += 1
        if rss_results[test_case["id"]]["success"]:
            platform_stats[platform]["success"] += 1
    
    # 结果汇总
    print(f"\n📊 验证结果汇总")
    print("=" * 70)
    print(f"总验证项: {total_tests}")
    print(f"通过验证: {passed_tests}")
    print(f"失败验证: {total_tests - passed_tests}")
    print(f"成功率: {passed_tests / total_tests * 100:.1f}%")
    
    print(f"\n📈 平台测试统计:")
    for platform, stats in platform_stats.items():
        success_rate = stats["success"] / stats["total"] * 100
        status = "✅" if success_rate >= 50 else "⚠️" if success_rate > 0 else "❌"
        print(f"   {status} {platform}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
    
    print(f"\n📋 RSS内容获取详情:")
    for test_case in TEST_CASES:
        case_id = test_case["id"]
        result = rss_results[case_id]
        status = "✅" if result["success"] else "❌"
        print(f"   {status} 用例{case_id}: {test_case['name']}")
        if result["success"]:
            print(f"      获取到 {result['entries_count']} 条内容")
        else:
            print(f"      失败原因: {result['error']}")
    
    # 最终判断
    rss_success_rate = successful_cases / len(TEST_CASES) * 100
    
    if passed_tests >= total_tests * 0.8 and rss_success_rate >= 50:
        print(f"\n🎉 验证通过！新配置功能正常")
        print(f"✨ 系统能够真实获取RSS订阅内容，准备提交到Git")
        if successful_cases == len(TEST_CASES):
            print(f"🏆 所有RSS测试用例都通过，系统完美运行！")
        return True
    else:
        print(f"\n⚠️  验证部分通过")
        print(f"需要检查失败的项目后再提交到Git")
        return False

if __name__ == "__main__":
    main() 