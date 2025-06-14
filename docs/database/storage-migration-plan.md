# RSS内容存储改造迁移计划

## 📋 文档说明

本文档详细说明如何从当前的用户隔离存储方案（方案A）平滑迁移到内容去重共享方案（方案B），确保改造过程中不影响现有系统的正常运行。

**版本**: v1.0  
**创建时间**: 2025-01-14  
**迁移策略**: 渐进式改造，向后兼容  

---

## 🎯 迁移目标

### 核心目标
- ✅ **零停机迁移**: 系统持续可用，用户无感知
- ✅ **向后兼容**: 现有API和前端无需修改
- ✅ **数据完整性**: 迁移过程中数据不丢失
- ✅ **性能提升**: 逐步实现存储优化和AI成本节省

### 预期收益
- **存储成本**: 节省15%（减少重复内容存储）
- **AI成本**: 节省30%（避免重复处理相同内容）
- **查询性能**: 提升20%（优化索引和查询结构）
- **系统一致性**: AI处理结果统一，用户体验更一致

---

## 🏗️ 迁移架构设计

### 阶段1：双写模式（兼容层）
```
现有系统 ──┐
          ├─→ 兼容适配层 ──┐
新存储层 ──┘              ├─→ 统一API接口
                         ┘
```

### 阶段2：读写分离
```
写入：新存储层
读取：兼容适配层（自动选择最优数据源）
API：保持现有接口不变
```

### 阶段3：完全迁移
```
新存储层 ──→ 统一API接口
（移除兼容层和旧存储）
```

---

## 📊 详细迁移方案

### 第一阶段：建立新存储结构（1-2天）

#### 1.1 创建新表结构
```sql
-- 共享内容表
CREATE TABLE shared_contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 内容字段（与现有rss_contents兼容）
    title VARCHAR(500) NOT NULL,
    description TEXT,
    description_text TEXT,
    author VARCHAR(200),
    published_at TIMESTAMP NOT NULL,
    original_link VARCHAR(1000) NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text',
    platform VARCHAR(50) NOT NULL,
    
    -- 去重字段
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    guid VARCHAR(500),
    
    -- Feed信息
    feed_title VARCHAR(500) NOT NULL,
    feed_description TEXT,
    feed_link VARCHAR(1000),
    
    -- AI处理结果（共享）
    summary TEXT,
    tags JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- 用户内容关系表
CREATE TABLE user_content_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content_id INTEGER NOT NULL,
    subscription_id INTEGER NOT NULL,
    
    -- 用户个人状态
    is_read BOOLEAN DEFAULT FALSE,
    is_favorited BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    personal_tags JSON,
    
    -- 生命周期管理
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, content_id, subscription_id),
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(content_id) REFERENCES shared_contents(id) ON DELETE CASCADE,
    FOREIGN KEY(subscription_id) REFERENCES user_subscriptions(id) ON DELETE CASCADE
);

-- 关键索引
CREATE UNIQUE INDEX idx_shared_content_hash ON shared_contents(content_hash);
CREATE INDEX idx_shared_content_guid ON shared_contents(guid);
CREATE INDEX idx_relations_expires ON user_content_relations(expires_at);
CREATE INDEX idx_relations_user ON user_content_relations(user_id, expires_at);
CREATE INDEX idx_relations_subscription ON user_content_relations(subscription_id);
```

#### 1.2 创建兼容适配层
```python
class ContentStorageAdapter:
    """内容存储适配器 - 提供向后兼容的接口"""
    
    def __init__(self):
        self.use_new_storage = False  # 开关控制
    
    async def get_user_contents(self, user_id: int, **kwargs):
        """获取用户内容 - 兼容现有API"""
        if self.use_new_storage:
            return await self._get_user_contents_new(user_id, **kwargs)
        else:
            return await self._get_user_contents_legacy(user_id, **kwargs)
    
    async def _get_user_contents_legacy(self, user_id: int, **kwargs):
        """现有存储方案的查询逻辑"""
        # 保持现有的查询逻辑不变
        query = """
            SELECT c.*, us.custom_name as subscription_name
            FROM rss_contents c
            INNER JOIN user_subscriptions us ON c.subscription_id = us.id
            WHERE us.user_id = ?
            ORDER BY c.published_at DESC
        """
        # ... 现有逻辑
    
    async def _get_user_contents_new(self, user_id: int, **kwargs):
        """新存储方案的查询逻辑"""
        query = """
            SELECT 
                c.*,
                r.is_read,
                r.is_favorited,
                r.read_at,
                r.personal_tags,
                r.expires_at,
                s.custom_name as subscription_name
            FROM shared_contents c
            JOIN user_content_relations r ON c.id = r.content_id
            JOIN user_subscriptions s ON r.subscription_id = s.id
            WHERE r.user_id = ? 
              AND r.expires_at > datetime('now')
            ORDER BY c.published_at DESC
        """
        # ... 新逻辑
    
    async def store_content(self, content_data: dict, subscription_id: int):
        """存储内容 - 双写模式"""
        # 1. 写入现有存储（保证兼容性）
        legacy_content_id = await self._store_content_legacy(content_data, subscription_id)
        
        if self.use_new_storage:
            # 2. 同时写入新存储
            await self._store_content_new(content_data, subscription_id)
        
        return legacy_content_id
```

### 第二阶段：数据迁移和双写（3-5天）

#### 2.1 历史数据迁移
```python
class DataMigrationService:
    """数据迁移服务"""
    
    async def migrate_existing_contents(self):
        """迁移现有内容到新存储结构"""
        
        # 1. 分批迁移现有内容
        batch_size = 1000
        offset = 0
        
        while True:
            # 获取一批现有内容
            legacy_contents = await self._get_legacy_contents_batch(offset, batch_size)
            if not legacy_contents:
                break
            
            # 处理每条内容
            for content in legacy_contents:
                await self._migrate_single_content(content)
            
            offset += batch_size
            logger.info(f"已迁移 {offset} 条内容")
    
    async def _migrate_single_content(self, legacy_content):
        """迁移单条内容"""
        
        # 1. 检查是否已存在相同内容
        existing_content = await self._find_shared_content_by_hash(
            legacy_content['content_hash']
        )
        
        if existing_content:
            # 内容已存在，只需建立用户关系
            content_id = existing_content['id']
        else:
            # 创建新的共享内容
            content_id = await self._create_shared_content(legacy_content)
        
        # 2. 建立用户关系
        await self._create_user_content_relation(
            user_id=self._get_user_id_from_subscription(legacy_content['subscription_id']),
            content_id=content_id,
            subscription_id=legacy_content['subscription_id'],
            legacy_content=legacy_content
        )
```

#### 2.2 启用双写模式
```python
# 配置开关
STORAGE_CONFIG = {
    "enable_new_storage": True,
    "enable_dual_write": True,
    "migration_mode": "dual_write"
}

# RSS内容处理服务更新
class RSSContentService:
    def __init__(self):
        self.adapter = ContentStorageAdapter()
        self.adapter.use_new_storage = STORAGE_CONFIG["enable_new_storage"]
    
    async def process_rss_content(self, rss_url: str, subscription_id: int):
        """RSS内容处理 - 支持双写"""
        
        # 1. 拉取和解析RSS（逻辑不变）
        rss_items = await self._fetch_and_parse_rss(rss_url)
        
        # 2. 处理每条内容（适配新旧存储）
        for item in rss_items:
            await self.adapter.store_content(item, subscription_id)
        
        return len(rss_items)
```

### 第三阶段：切换读取源（1-2天）

#### 3.1 逐步切换读取
```python
class ContentReadStrategy:
    """内容读取策略"""
    
    def __init__(self):
        self.read_strategy = "adaptive"  # legacy/new/adaptive
    
    async def get_user_contents(self, user_id: int, **kwargs):
        """自适应读取策略"""
        
        if self.read_strategy == "legacy":
            return await self._read_from_legacy(user_id, **kwargs)
        elif self.read_strategy == "new":
            return await self._read_from_new(user_id, **kwargs)
        else:  # adaptive
            return await self._read_adaptive(user_id, **kwargs)
    
    async def _read_adaptive(self, user_id: int, **kwargs):
        """自适应读取 - 优先新存储，降级到旧存储"""
        try:
            # 尝试从新存储读取
            new_contents = await self._read_from_new(user_id, **kwargs)
            if new_contents:
                return new_contents
        except Exception as e:
            logger.warning(f"新存储读取失败，降级到旧存储: {e}")
        
        # 降级到旧存储
        return await self._read_from_legacy(user_id, **kwargs)
```

#### 3.2 数据一致性验证
```python
class DataConsistencyValidator:
    """数据一致性验证器"""
    
    async def validate_user_contents(self, user_id: int):
        """验证用户内容在新旧存储中的一致性"""
        
        # 1. 从两个存储分别获取数据
        legacy_contents = await self._get_legacy_contents(user_id)
        new_contents = await self._get_new_contents(user_id)
        
        # 2. 比较内容数量
        if len(legacy_contents) != len(new_contents):
            logger.warning(f"用户{user_id}内容数量不一致: 旧={len(legacy_contents)}, 新={len(new_contents)}")
        
        # 3. 比较内容哈希
        legacy_hashes = {c['content_hash'] for c in legacy_contents}
        new_hashes = {c['content_hash'] for c in new_contents}
        
        missing_in_new = legacy_hashes - new_hashes
        if missing_in_new:
            logger.error(f"用户{user_id}新存储缺失内容: {missing_in_new}")
        
        return len(missing_in_new) == 0
```

### 第四阶段：完全切换（1天）

#### 4.1 停止写入旧存储
```python
# 配置更新
STORAGE_CONFIG = {
    "enable_new_storage": True,
    "enable_dual_write": False,  # 停止双写
    "migration_mode": "new_only"
}
```

#### 4.2 清理旧数据和代码
```python
class MigrationCleanup:
    """迁移清理服务"""
    
    async def cleanup_legacy_storage(self):
        """清理旧存储数据"""
        
        # 1. 备份旧数据
        await self._backup_legacy_data()
        
        # 2. 删除旧表（可选，建议保留一段时间）
        # await self._drop_legacy_tables()
        
        # 3. 移除兼容代码
        logger.info("迁移完成，建议移除兼容适配层代码")
```

---

## 🔧 API兼容性保证

### 现有API接口保持不变
```python
# 现有接口：/api/users/{user_id}/content
# 返回格式完全兼容，用户无感知

@router.get("/users/{user_id}/content")
async def get_user_content(user_id: int, **kwargs):
    """用户内容接口 - 完全向后兼容"""
    
    # 内部使用适配器，外部接口不变
    adapter = ContentStorageAdapter()
    contents = await adapter.get_user_contents(user_id, **kwargs)
    
    # 返回格式与现有完全一致
    return UserContentResponse(
        content=ContentListData(
            items=[ContentItem(**item) for item in contents],
            total=len(contents),
            # ... 其他字段保持不变
        ),
        filter_tags=await adapter.get_user_tags(user_id),
        # ... 其他字段保持不变
    )
```

### 数据模型兼容性
```python
# 现有模型保持不变
class ContentItem(BaseModel):
    content_id: int          # 兼容：映射到shared_contents.id
    subscription_id: int     # 兼容：从user_content_relations获取
    title: str              # 兼容：直接映射
    link: str               # 兼容：映射到original_link
    # ... 其他字段完全兼容
```

---

## 📈 迁移监控和回滚

### 监控指标
```python
class MigrationMonitor:
    """迁移监控服务"""
    
    def __init__(self):
        self.metrics = {
            "legacy_read_count": 0,
            "new_read_count": 0,
            "dual_write_success": 0,
            "dual_write_failure": 0,
            "data_consistency_errors": 0
        }
    
    async def check_migration_health(self):
        """检查迁移健康状态"""
        
        # 1. 检查数据一致性
        consistency_rate = await self._check_data_consistency()
        
        # 2. 检查性能指标
        performance_metrics = await self._check_performance()
        
        # 3. 检查错误率
        error_rate = self.metrics["dual_write_failure"] / max(1, self.metrics["dual_write_success"])
        
        if consistency_rate < 0.99 or error_rate > 0.01:
            logger.error("迁移健康检查失败，建议回滚")
            return False
        
        return True
```

### 回滚策略
```python
class MigrationRollback:
    """迁移回滚服务"""
    
    async def rollback_to_legacy(self):
        """回滚到旧存储方案"""
        
        # 1. 停止新存储写入
        STORAGE_CONFIG["enable_new_storage"] = False
        
        # 2. 切换读取源到旧存储
        STORAGE_CONFIG["read_strategy"] = "legacy"
        
        # 3. 验证系统功能
        await self._validate_legacy_functionality()
        
        logger.info("已回滚到旧存储方案")
```

---

## ⏱️ 迁移时间表

| 阶段 | 时间 | 主要任务 | 风险等级 |
|------|------|----------|----------|
| **准备阶段** | 1天 | 创建新表结构、编写适配器 | 🟢 低 |
| **双写阶段** | 3-5天 | 历史数据迁移、启用双写 | 🟡 中 |
| **切换阶段** | 1-2天 | 逐步切换读取源、验证一致性 | 🟡 中 |
| **完成阶段** | 1天 | 停止旧存储写入、清理代码 | 🟢 低 |
| **总计** | **6-9天** | **完整迁移周期** | **🟡 中等** |

---

## 🎯 成功标准

### 技术指标
- ✅ **数据一致性**: 99.9%以上
- ✅ **API兼容性**: 100%（现有接口无需修改）
- ✅ **性能提升**: 查询速度提升20%以上
- ✅ **存储优化**: 重复内容减少15%以上

### 业务指标
- ✅ **用户体验**: 零感知迁移
- ✅ **系统稳定性**: 99.9%可用性
- ✅ **AI成本**: 节省30%处理成本
- ✅ **运维效率**: 统一内容管理

---

## 🚨 风险控制

### 主要风险点
1. **数据丢失风险**: 通过双写和备份机制控制
2. **性能下降风险**: 通过分批迁移和监控控制
3. **兼容性风险**: 通过适配器和充分测试控制
4. **回滚风险**: 通过完整的回滚策略控制

### 应急预案
- **数据备份**: 每个阶段都有完整备份
- **实时监控**: 关键指标实时监控和告警
- **快速回滚**: 5分钟内可回滚到上一个稳定状态
- **专家支持**: 迁移期间技术专家在线支持

---

## 📝 总结

这个迁移方案的核心优势：

1. **零停机**: 用户完全无感知的平滑迁移
2. **向后兼容**: 现有代码和API无需修改
3. **风险可控**: 每个阶段都有监控和回滚机制
4. **收益明确**: 存储和AI成本显著降低

通过这个渐进式迁移策略，我们可以在不影响现有系统稳定性的前提下，实现存储架构的优化升级。 