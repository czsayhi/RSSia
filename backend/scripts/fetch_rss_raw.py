#!/usr/bin/env python3
"""
简单的RSS内容获取工具
直接获取RSS源的原始XML内容
"""

import requests
import sys
from datetime import datetime

def fetch_rss_raw(url: str) -> str:
    """获取RSS源的原始内容"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    
    try:
        print(f"🌐 正在获取RSS内容...")
        print(f"📍 URL: {url}")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"📊 HTTP状态码: {response.status_code}")
        print(f"📦 内容大小: {len(response.content)} bytes")
        print(f"📄 Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print("=" * 80)
        
        if response.status_code == 200:
            print("✅ RSS原始内容:")
            print("-" * 80)
            return response.text
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"错误内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 获取失败: {str(e)}")
        return None

def main():
    # 默认测试URL
    test_url = "https://rsshub.app/bilibili/user/video/297572288"
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    raw_content = fetch_rss_raw(test_url)
    
    if raw_content:
        print(raw_content)
        print("-" * 80)
        print("✅ 内容获取完成")
    else:
        print("❌ 无法获取内容")

if __name__ == "__main__":
    main() 