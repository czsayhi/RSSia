#!/usr/bin/env python3
"""
创建测试数据脚本
包括用户和订阅配置数据，用于前后端集成测试
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# 添加app路径
sys.path.append(str(Path(__file__).parent))

from app.services.subscription_service import SubscriptionService
from app.models.subscription import SubscriptionCreateRequest


def create_test_data():
    """创建测试数据"""
    print("🚀 开始创建测试数据...")
    
    # 初始化订阅服务
    service = SubscriptionService()
    
    # 1. 创建测试用户
    print("\n👤 创建测试用户...")
    
    # 删除已存在的测试用户（如果有）
    db_path = "data/rss_subscriber.db"
    if os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = 'test_user'")
            cursor.execute("DELETE FROM user_subscriptions WHERE user_id = 1")
            conn.commit()
    
    # 创建新的测试用户
    user_id = service.create_user(
        username="test_user",
        wechat_id="wx_test_123456",
        display_name="测试用户"
    )
    print(f"✅ 创建测试用户成功: ID={user_id}, 用户名=test_user, 微信=wx_test_123456")
    
    # 2. 创建测试订阅配置
    print("\n📺 创建测试订阅配置...")
    
    test_subscriptions = [
        {
            "template_id": "bilibili_user_videos",
            "parameters": {"uid": "2267573"},  # 老番茄
            "custom_name": "老番茄的视频"
        },
        {
            "template_id": "bilibili_user_dynamics", 
            "parameters": {"uid": "297572288"},  # 某科学的超电磁炮
            "custom_name": "某科学的超电磁炮动态"
        },
        {
            "template_id": "weibo_user_posts",
            "parameters": {"uid": "1195230310"},  # 头条新闻
            "custom_name": "头条新闻微博"
        },
        {
            "template_id": "weibo_keyword_search",
            "parameters": {"keyword": "人工智能"},
            "custom_name": "AI相关话题"
        },
        {
            "template_id": "jike_user_posts",
            "parameters": {"id": "82D23B32-CF36-4C59-AD6F-D05E3552CBF3"},
            "custom_name": "即刻用户动态"
        }
    ]
    
    created_subscriptions = []
    
    for i, sub_data in enumerate(test_subscriptions, 1):
        try:
            request = SubscriptionCreateRequest(
                template_id=sub_data["template_id"],
                parameters=sub_data["parameters"],
                custom_name=sub_data["custom_name"]
            )
            
            subscription = service.create_subscription(request, user_id=1)  # 使用用户ID=1
            created_subscriptions.append(subscription)
            
            print(f"✅ 订阅 {i}: {subscription.template_name}")
            print(f"   - ID: {subscription.id}")
            print(f"   - 自定义名称: {subscription.custom_name}")
            print(f"   - RSS URL: {subscription.rss_url}")
            print(f"   - 状态: {'启用' if subscription.is_active else '禁用'}")
            
        except Exception as e:
            print(f"❌ 创建订阅 {i} 失败: {e}")
    
    # 3. 创建一些不同状态的订阅用于测试
    print("\n🔄 设置不同状态的订阅...")
    
    if len(created_subscriptions) >= 2:
        # 将第2个订阅设为inactive状态
        service.update_subscription_status(created_subscriptions[1].id, "inactive")
        print(f"✅ 订阅 {created_subscriptions[1].id} 状态设置为: inactive")
    
    # 4. 验证数据创建结果
    print("\n📊 验证创建结果...")
    
    # 获取用户订阅列表
    subscription_list = service.get_user_subscriptions(user_id=1)
    
    print(f"✅ 总共创建了 {subscription_list.total} 个订阅配置")
    print(f"✅ 订阅列表:")
    
    for sub in subscription_list.subscriptions:
        status_emoji = "🟢" if sub.is_active else "🔴"
        print(f"   {status_emoji} {sub.template_name} - {sub.custom_name}")
    
    # 5. 输出API测试命令
    print("\n🧪 API测试命令:")
    print("# 搜索模版:")
    print("curl 'http://127.0.0.1:8001/api/v1/subscription-search/search?query=bilibili'")
    print("\n# 获取用户订阅列表:")
    print("curl 'http://127.0.0.1:8001/api/v1/subscriptions'")
    print("\n# 创建新订阅:")
    print("curl -X POST 'http://127.0.0.1:8001/api/v1/subscriptions' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"template_id\":\"bilibili_user_videos\",\"parameters\":{\"uid\":\"123456\"},\"custom_name\":\"测试订阅\"}'")
    
    print("\n🎉 测试数据创建完成！")


def show_database_info():
    """显示数据库信息"""
    db_path = "data/rss_subscriber.db"
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    print("\n📋 数据库信息:")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"👤 用户数量: {user_count}")
        
        # 订阅表
        cursor.execute("SELECT COUNT(*) FROM user_subscriptions WHERE is_active = 1")
        active_sub_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_subscriptions WHERE is_active = 0")
        inactive_sub_count = cursor.fetchone()[0]
        
        print(f"📺 活跃订阅: {active_sub_count}")
        print(f"🔴 已删除订阅: {inactive_sub_count}")
        
        # 订阅状态分布
        cursor.execute("SELECT status, COUNT(*) FROM user_subscriptions WHERE is_active = 1 GROUP BY status")
        status_counts = cursor.fetchall()
        print("📊 订阅状态分布:")
        for status, count in status_counts:
            print(f"   - {status}: {count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RSS订阅器测试数据管理")
    parser.add_argument("--info", action="store_true", help="显示数据库信息")
    parser.add_argument("--create", action="store_true", help="创建测试数据")
    
    args = parser.parse_args()
    
    if args.info:
        show_database_info()
    elif args.create:
        create_test_data()
    else:
        print("使用方式:")
        print("  python create_test_data.py --create  # 创建测试数据")
        print("  python create_test_data.py --info    # 显示数据库信息") 