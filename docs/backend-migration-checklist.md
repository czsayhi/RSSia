# 后端存储架构改造检查清单

## 📋 改造范围确认

### ✅ 本次实施内容

#### 1. 数据库架构升级
- [x] 创建 `shared_contents` 表
- [x] 创建 `user_content_relations` 表  
- [x] 创建 `shared_content_media_items` 表
- [x] 创建必要的索引
- [x] 创建自动清理触发器
- [x] 创建查询视图

#### 2. 内容入库流程改造
- [x] RSS内容解析和标准化
- [x] 内容去重逻辑（基于content_hash）
- [x] 共享内容存储服务
- [x] 媒体项处理和存储
- [x] 用户关系建立逻辑

#### 3. 用户关系管理
- [x] 用户-内容关系映射
- [x] 24小时生命周期管理
- [x] 个人状态管理（is_read, is_favorited）
- [x] 个人标签支持（personal_tags字段）

#### 4. API接口实现
- [x] 用户内容列表查询接口
- [x] 内容筛选（平台、订阅源、状态）
- [x] 分页支持
- [x] 内容状态更新接口（标记已读、收藏）
- [x] 用户标签统计接口

#### 5. 服务层重构
- [x] SharedContentService 实现
- [x] 更新现有 RSSContentService
- [x] 内容去重服务
- [x] 用户关系管理服务

### 🔄 预留功能（后续实施）

#### AI处理模块
- [ ] summary 字段处理逻辑
- [ ] tags 字段AI生成
- [ ] 内容智能分类
- [ ] 个性化推荐

#### 前端兼容
- [ ] API响应格式兼容性分析
- [ ] 前端数据模型适配
- [ ] 接口字段映射

---

## 🔧 技术实施细节

### 关键服务接口设计

#### SharedContentService
```python
class SharedContentService:
    async def store_rss_content(self, rss_items, subscription_id, user_id) -> dict
    async def get_user_contents(self, user_id, **filters) -> List[dict]
    async def update_content_status(self, user_id, content_id, **updates) -> bool
    async def get_user_content_stats(self, user_id) -> dict
```

#### ContentDeduplicationService  
```python
class ContentDeduplicationService:
    async def find_or_create_content(self, content_data) -> Tuple[int, bool]
    def generate_content_hash(self, title, link) -> str
    async def check_content_exists(self, content_hash) -> Optional[int]
```

#### UserContentRelationService
```python
class UserContentRelationService:
    async def create_relation(self, user_id, content_id, subscription_id) -> int
    async def update_relation_status(self, relation_id, **updates) -> bool
    async def cleanup_expired_relations(self) -> int
```

### API端点设计

```python
# 用户内容相关
GET    /api/users/{user_id}/content              # 获取用户内容列表
PUT    /api/users/{user_id}/content/{content_id} # 更新内容状态
GET    /api/users/{user_id}/content/stats        # 获取用户内容统计

# 内容管理相关  
GET    /api/content/{content_id}                 # 获取内容详情
GET    /api/content/{content_id}/media           # 获取内容媒体项
```

### 数据模型兼容性

#### 现有模型保持
```python
class ContentItem(BaseModel):
    content_id: int          # 映射到 shared_contents.id
    subscription_id: int     # 从 user_content_relations 获取
    title: str              # shared_contents.title
    link: str               # shared_contents.original_link
    # ... 其他字段保持兼容
```

---

## ⚠️ 注意事项

### 1. 数据完整性
- 确保外键约束正确设置
- 验证级联删除逻辑
- 测试数据清理触发器

### 2. 性能优化
- 验证关键查询的索引效果
- 测试大数据量下的查询性能
- 监控数据库存储空间变化

### 3. 向后兼容
- 保留现有 rss_contents 表结构
- 确保现有API接口响应格式不变
- 验证现有订阅功能正常工作

### 4. 错误处理
- 内容去重冲突处理
- 用户关系创建失败处理
- 数据库连接异常处理

---

## 🧪 测试计划

### 单元测试
- [ ] 内容去重逻辑测试
- [ ] 用户关系管理测试
- [ ] API接口功能测试

### 集成测试  
- [ ] RSS内容完整流程测试
- [ ] 多用户内容隔离测试
- [ ] 数据清理机制测试

### 性能测试
- [ ] 大量内容存储性能
- [ ] 用户内容查询性能
- [ ] 并发访问压力测试

---

## 📊 验收标准

### 功能验收
- ✅ RSS内容可以正常拉取和存储
- ✅ 内容去重机制工作正常
- ✅ 用户可以查看个人内容列表
- ✅ 内容状态更新功能正常
- ✅ 数据自动清理机制有效

### 性能验收
- ✅ 内容查询响应时间 < 500ms
- ✅ 存储空间相比旧方案节省 > 10%
- ✅ 支持并发用户数 > 100

### 兼容性验收
- ✅ 现有订阅功能不受影响
- ✅ API响应格式保持兼容
- ✅ 数据库迁移无数据丢失 