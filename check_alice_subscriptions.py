import sqlite3

# 连接数据库
conn = sqlite3.connect('data/rss_subscriber.db')
cursor = conn.cursor()

# 查询alice的所有订阅源
cursor.execute('''
    SELECT id, rss_url, custom_name, is_active, created_at 
    FROM subscriptions 
    WHERE user_id = 1 
    ORDER BY created_at DESC
''')

subscriptions = cursor.fetchall()

print(f"Alice的订阅源总数: {len(subscriptions)}")
print("\n订阅源详情:")
print("-" * 80)

for i, sub in enumerate(subscriptions, 1):
    print(f"{i}. ID: {sub[0]}")
    print(f"   URL: {sub[1]}")
    print(f"   名称: {sub[2] if sub[2] else '未设置'}")
    print(f"   激活状态: {'✅ 激活' if sub[3] else '❌ 未激活'}")
    print(f"   创建时间: {sub[4]}")
    print()

# 统计激活状态
active_count = sum(1 for sub in subscriptions if sub[3])
inactive_count = len(subscriptions) - active_count

print(f"激活的订阅源: {active_count}")
print(f"未激活的订阅源: {inactive_count}")

conn.close() 