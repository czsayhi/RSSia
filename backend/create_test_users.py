#!/usr/bin/env python3
"""
创建测试用户脚本
用于验证新的共享内容存储架构
"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.user_service import user_service

async def create_test_users():
    """创建两个测试用户"""
    
    print("🔧 创建测试用户...")
    print("=" * 50)
    
    # 测试用户1
    user1_username = "alice"
    user1_email = "alice@test.com"
    user1_password = "password123"
    
    # 测试用户2
    user2_username = "bob"
    user2_email = "bob@test.com"
    user2_password = "password456"
    
    try:
        # 创建用户1
        try:
            user1 = user_service.create_user(user1_username, user1_email, user1_password)
            print(f"✅ 用户1创建成功:")
            print(f"   - 用户名: {user1_username}")
            print(f"   - 密码: {user1_password}")
            print(f"   - 邮箱: {user1_email}")
            print(f"   - 用户ID: {user1.user_id}")
        except ValueError as e:
            if "已存在" in str(e):
                print(f"ℹ️  用户1已存在: {user1_username}")
                # 获取现有用户信息
                user1 = user_service.authenticate_user(user1_username, user1_password)
                if user1:
                    print(f"   - 用户名: {user1_username}")
                    print(f"   - 密码: {user1_password}")
                    print(f"   - 用户ID: {user1.user_id}")
                else:
                    print(f"   - 密码可能不是: {user1_password}")
            else:
                raise
        
        print()
        
        # 创建用户2
        try:
            user2 = user_service.create_user(user2_username, user2_email, user2_password)
            print(f"✅ 用户2创建成功:")
            print(f"   - 用户名: {user2_username}")
            print(f"   - 密码: {user2_password}")
            print(f"   - 邮箱: {user2_email}")
            print(f"   - 用户ID: {user2.user_id}")
        except ValueError as e:
            if "已存在" in str(e):
                print(f"ℹ️  用户2已存在: {user2_username}")
                # 获取现有用户信息
                user2 = user_service.authenticate_user(user2_username, user2_password)
                if user2:
                    print(f"   - 用户名: {user2_username}")
                    print(f"   - 密码: {user2_password}")
                    print(f"   - 用户ID: {user2.user_id}")
                else:
                    print(f"   - 密码可能不是: {user2_password}")
            else:
                raise
        
        print()
        print("🎯 测试账号信息总结:")
        print("=" * 50)
        print(f"账号1: {user1_username} / {user1_password}")
        print(f"账号2: {user2_username} / {user2_password}")
        print()
        print("📋 测试建议:")
        print("1. 为两个用户创建部分重复的RSS订阅源")
        print("2. 验证内容去重功能是否正常工作")
        print("3. 检查用户关系映射是否正确")
        print("4. 测试24小时生命周期管理")
        print()
        print("🔗 推荐测试RSS源:")
        print("- 阮一峰的网络日志: http://www.ruanyifeng.com/blog/atom.xml")
        print("- 少数派: https://sspai.com/feed")
        print("- V2EX: https://www.v2ex.com/index.xml")
        print("- GitHub Trending: https://github.com/trending.atom")
        
    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(create_test_users())
    if success:
        print("\n🎉 测试用户创建完成！")
    else:
        print("\n❌ 测试用户创建失败！")
        sys.exit(1) 