# RSS内容存储架构升级方案（开发阶段）

## 📋 文档说明

基于当前项目开发阶段的实际情况，制定简化的存储架构升级方案。由于用户内容列表等核心功能尚未实现，可以直接采用新的存储架构，无需复杂的迁移过程。

**版本**: v1.0  
**创建时间**: 2025-01-14  
**适用场景**: 开发阶段，无存量数据  

---

## 🎯 当前项目状态

### ✅ 已实现功能
- 用户登录/登出系统
- 登录态验证
- 用户订阅源配置
- 订阅频率配置

### 🚧 待实现功能
- **用户内容列表**（核心功能）
- 内容详情展示
- 内容筛选和搜索
- AI内容处理和摘要

### 💡 关键优势
- **无存量数据**: 不需要数据迁移
- **架构灵活**: 可直接采用最优方案
- **开发效率**: 一次性实现，避免后续重构

---

## 🏗️ 直接升级方案

### 第一步：更新数据库架构（30分钟）

#### 1.1 执行新表结构
```bash
# 在现有数据库中直接创建新表
sqlite3 data/rss_subscriber.db < app/database/shared_content_schema.sql
```

#### 1.2 保留现有表（向后兼容）
```sql
-- 保留现有的 rss_contents 表作为备用
-- 新功能直接使用 shared_contents + user_content_relations
```

### 第二步：实现新存储服务（2-3小时）

#### 2.1 创建共享内容服务
```python
class SharedContentService:
    """共享内容存储服务"""
    
    async def store_rss_content(self, rss_items: List[dict], subscription_id: int, user_id: int):
        """存储RSS内容到新架构"""
        
        processed_count = 0
        new_content_count = 0
        
        for item in rss_items:
            # 1. 查找或创建共享内容
            content_id, is_new = await self._find_or_create_shared_content(item)
            
            # 2. 建立用户关系（24小时有效期）
            await self._create_user_content_relation(
                user_id=user_id,
                content_id=content_id,
                subscription_id=subscription_id,
                expires_at=datetime.now() + timedelta(hours=24)
            )
            
            # 3. 调度AI处理（仅新内容）
            if is_new:
                await self._schedule_ai_processing(content_id)
                new_content_count += 1
            
            processed_count += 1
        
        return {
            'total_processed': processed_count,
            'new_content': new_content_count,
            'reused_content': processed_count - new_content_count
        }
    
    async def get_user_contents(self, user_id: int, **filters):
        """获取用户内容列表"""
        query = """
            SELECT 
                c.id as content_id,
                c.title,
                c.author,
                c.published_at,
                c.original_link,
                c.description,
                c.summary,
                c.tags,
                c.platform,
                c.content_type,
                c.cover_image,
                r.subscription_id,
                r.is_read,
                r.is_favorited,
                r.read_at,
                us.custom_name as subscription_name
            FROM shared_contents c
            JOIN user_content_relations r ON c.id = r.content_id
            LEFT JOIN user_subscriptions us ON r.subscription_id = us.id
            WHERE r.user_id = ? 
              AND r.expires_at > datetime('now')
            ORDER BY c.published_at DESC
        """
        
        # 应用筛选条件
        params = [user_id]
        if filters.get('platform'):
            query += " AND c.platform = ?"
            params.append(filters['platform'])
        
        if filters.get('subscription_id'):
            query += " AND r.subscription_id = ?"
            params.append(filters['subscription_id'])
        
        # 分页
        limit = filters.get('limit', 20)
        offset = filters.get('offset', 0)
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        return await self._execute_query(query, params)
```

#### 2.2 更新RSS内容处理服务
```python
# 修改现有的 RSSContentService
class RSSContentService:
    def __init__(self):
        self.shared_service = SharedContentService()  # 使用新服务
    
    async def process_rss_content(self, rss_url: str, subscription_id: int, user_id: int):
        """RSS内容处理 - 使用新架构"""
        
        # 1. 拉取和解析RSS（逻辑不变）
        rss_items = await self._fetch_and_parse_rss(rss_url)
        
        # 2. 使用新存储服务处理
        result = await self.shared_service.store_rss_content(
            rss_items, subscription_id, user_id
        )
        
        logger.info(f"RSS处理完成: {result}")
        return result
```

### 第三步：实现用户内容API（1-2小时）

#### 3.1 用户内容列表接口
```python
@router.get("/users/{user_id}/content")
async def get_user_content(
    user_id: int,
    platform: Optional[str] = None,
    subscription_id: Optional[int] = None,
    page: int = 1,
    limit: int = 20
):
    """获取用户内容列表 - 新架构"""
    
    shared_service = SharedContentService()
    
    contents = await shared_service.get_user_contents(
        user_id=user_id,
        platform=platform,
        subscription_id=subscription_id,
        limit=limit,
        offset=(page - 1) * limit
    )
    
    return {
        "items": contents,
        "total": len(contents),
        "page": page,
        "limit": limit
    }
```

### 第四步：前端开发（按原计划）

由于前端用户内容列表还未开发，可以直接基于新API进行开发：

```typescript
// 前端直接调用新的API接口
const fetchUserContent = async (userId: number, filters?: ContentFilters) => {
  const response = await fetch(`/api/users/${userId}/content`, {
    method: 'GET',
    // ... 参数
  });
  
  return response.json();
};
```

---

## 📊 方案对比

| 方面 | 复杂迁移方案 | 直接升级方案 |
|------|-------------|-------------|
| **实施时间** | 6-9天 | 0.5-1天 |
| **开发复杂度** | 高（兼容层+迁移） | 低（直接实现） |
| **风险等级** | 中等 | 极低 |
| **代码质量** | 中（临时兼容代码） | 高（直接最优架构） |
| **维护成本** | 高（需清理兼容层） | 低（统一架构） |

---

## 🚀 实施步骤

### 立即可执行的步骤

1. **创建新表结构**（10分钟）
   ```bash
   cd backend
   sqlite3 data/rss_subscriber.db < app/database/shared_content_schema.sql
   ```

2. **实现SharedContentService**（2小时）
   - 内容去重逻辑
   - 用户关系管理
   - AI处理调度

3. **更新现有RSS处理服务**（30分钟）
   - 调用新的存储服务
   - 保持现有接口不变

4. **实现用户内容API**（1小时）
   - 基于新架构的查询接口
   - 支持筛选和分页

5. **前端开发**（按原计划）
   - 直接基于新API开发
   - 无需考虑兼容性

### 总时间估算：4-6小时

---

## 🎯 预期收益

### 立即收益
- **架构优雅**: 直接采用最优设计
- **开发效率**: 避免后续重构工作
- **代码质量**: 无临时兼容代码

### 长期收益
- **存储优化**: 15%存储空间节省
- **AI成本**: 30%处理成本节省
- **查询性能**: 20%性能提升
- **维护简单**: 统一架构，易于维护

---

## 🔧 技术细节

### 内容去重策略
```python
def generate_content_hash(self, title: str, link: str) -> str:
    """简化去重策略 - 适合UID定向订阅"""
    normalized_title = self._normalize_text(title)
    hash_content = f"{normalized_title}|{link}"
    return hashlib.sha256(hash_content.encode()).hexdigest()[:32]
```

### 用户关系生命周期
```python
def calculate_expires_at(self) -> datetime:
    """计算内容过期时间 - 每用户24小时"""
    return datetime.now() + timedelta(hours=24)
```

### AI处理优化
```python
async def schedule_ai_processing(self, content_id: int):
    """AI处理调度 - 仅处理新内容"""
    # 检查是否已处理
    if await self._is_content_processed(content_id):
        return
    
    # 调度AI处理任务
    await self._queue_ai_task(content_id)
```

---

## 📝 总结

在当前开发阶段，**直接采用新存储架构是最优选择**：

1. **无历史包袱**: 没有存量数据需要迁移
2. **架构最优**: 直接实现最佳设计方案
3. **开发高效**: 避免复杂的兼容和迁移逻辑
4. **质量保证**: 统一架构，代码简洁

建议立即开始实施，预计半天内可以完成核心架构升级。 