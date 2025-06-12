#!/usr/bin/env python3
"""
数据库初始化脚本
手动创建所有必需的数据库表
"""

def init_database():
    """初始化所有数据库表"""
    try:
        from app.services.subscription_service import subscription_service
        from app.services.database_service import database_service
        
        print('🚀 开始初始化数据库...')
        
        print('📋 初始化订阅服务表...')
        subscription_service._init_database()
        
        print('📋 初始化数据库服务表...')
        database_service._init_database()
        
        print('✅ 数据库初始化完成!')
        
        # 验证表是否创建成功
        import sqlite3
        conn = sqlite3.connect('data/rss_subscriber.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        conn.close()
        
        print(f'📊 已创建的表: {table_names}')
        
    except Exception as e:
        print(f'❌ 数据库初始化失败: {e}')
        raise

if __name__ == "__main__":
    init_database() 