#!/usr/bin/env python3
"""
数据库初始化脚本
手动创建所有必需的数据库表
"""

def init_database():
    """初始化所有数据库表"""
    try:
        from app.services.subscription_service import subscription_service
        
        print('🚀 开始初始化数据库...')
        
        print('📋 初始化订阅服务表...')
        subscription_service._init_database()
        
        # 🆕 统一使用共享内容架构
        print('📋 初始化共享内容架构（新架构）...')
        init_shared_content_schema()
        
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
        
        # 特别检查关键表（新架构）
        required_tables = ['shared_contents', 'user_content_relations', 'shared_content_media_items']
        missing_tables = [table for table in required_tables if table not in table_names]
        if missing_tables:
            print(f'⚠️ 缺失关键表: {missing_tables}')
        else:
            print('✅ 所有关键表都已创建（新架构）')
        
    except Exception as e:
        print(f'❌ 数据库初始化失败: {e}')
        raise

def init_shared_content_schema():
    """初始化共享内容架构"""
    import sqlite3
    from pathlib import Path
    
    try:
        # 读取共享内容架构SQL
        schema_path = Path(__file__).parent / 'app' / 'database' / 'shared_content_schema.sql'
        if not schema_path.exists():
            print(f'⚠️ 共享内容架构文件不存在: {schema_path}')
            return
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # 执行架构创建
        with sqlite3.connect('data/rss_subscriber.db') as conn:
            # 分割SQL语句执行（处理多个CREATE语句）
            sql_statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in sql_statements:
                if statement:
                    try:
                        conn.execute(statement)
                    except sqlite3.Error as e:
                        # 跳过已存在的表错误
                        if 'already exists' not in str(e).lower():
                            print(f'⚠️ SQL执行警告: {e}')
            
            conn.commit()
            print('✅ 共享内容架构初始化完成')
            
    except Exception as e:
        print(f'❌ 共享内容架构初始化失败: {e}')
        raise

if __name__ == "__main__":
    init_database() 