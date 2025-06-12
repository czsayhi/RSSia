#!/usr/bin/env python3
"""
创建测试用户脚本
用于初始化测试数据，方便前后端集成测试
"""

import sys
from pathlib import Path

# 添加app路径
sys.path.append(str(Path(__file__).parent))

from app.services.user_service import user_service
from loguru import logger


def create_test_users():
    """创建测试用户"""
    logger.info("🚀 开始创建测试用户...")
    
    try:
        # 创建管理员用户
        admin_user = user_service.create_test_user()
        logger.info(f"✅ 管理员用户创建成功: {admin_user.username} (ID: {admin_user.user_id})")
        logger.info(f"   邮箱: {admin_user.email}")
        logger.info(f"   密码: admin123")
        logger.info(f"   Token: {admin_user.access_token}")
        
        # 创建普通测试用户
        try:
            test_user = user_service.create_user(
                username="testuser",
                email="test@example.com",
                password="123456"
            )
            logger.info(f"✅ 测试用户创建成功: {test_user.username} (ID: {test_user.user_id})")
            logger.info(f"   邮箱: {test_user.email}")
            logger.info(f"   密码: 123456")
            logger.info(f"   Token: {test_user.access_token}")
        except ValueError as e:
            if "已存在" in str(e):
                logger.info("⚠️  测试用户已存在，跳过创建")
            else:
                raise
        
        logger.info("\n🎉 测试用户创建完成！")
        logger.info("\n📋 登录测试信息:")
        logger.info("管理员账号:")
        logger.info("  用户名: admin")
        logger.info("  密码: admin123")
        logger.info("\n普通用户账号:")
        logger.info("  用户名: testuser 或 test@example.com")
        logger.info("  密码: 123456")
        
    except Exception as e:
        logger.error(f"❌ 创建测试用户失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_test_users() 