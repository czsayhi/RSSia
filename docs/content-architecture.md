##业务流程图 - 完整的内容处理流程
graph TD
    A["用户订阅配置"] --> B["订阅源管理"]
    A --> C["订阅频率设置"]
    
    B --> D["模板搜索与匹配"]
    D --> E["RSS URL生成"]
    
    C --> F["定时调度器"]
    F --> G["自动拉取触发"]
    
    H["手动拉取触发"] --> I["RSS内容获取"]
    G --> I
    E --> I
    
    I --> J["XML内容解析"]
    J --> K["内容标准化"]
    K --> L["内容哈希计算"]
    
    L --> M{"内容去重检查"}
    M -->|"已存在"| N["复用共享内容"]
    M -->|"新内容"| O["创建共享内容"]
    
    N --> P["用户-内容关系映射"]
    O --> Q["存储到共享内容表"]
    Q --> P
    
    P --> R["建立用户关系"]
    R --> S["内容入库完成"]
    
    S --> T["AI增强处理"]
    T --> U["内容摘要生成"]
    T --> V["标签提取"]
    T --> W["情感分析"]
    
    U --> X["增强内容存储"]
    V --> X
    W --> X
    
    X --> Y["用户内容消费"]
    Y --> Z["个性化推荐"]
    Y --> AA["内容筛选"]
    Y --> BB["阅读状态管理"]
    
    subgraph "订阅配置层"
        A
        B
        C
        D
        E
    end
    
    subgraph "触发调度层"
        F
        G
        H
    end
    
    subgraph "内容获取层"
        I
        J
        K
        L
    end
    
    subgraph "去重存储层"
        M
        N
        O
        Q
        P
        R
        S
    end
    
    subgraph "AI增强层（架构预留，未实现）"
        T
        U
        V
        W
        X
    end
    
    subgraph "用户消费层"
        Y
        Z
        AA
        BB
    end
    
    style A fill:#e1f5fe
    style M fill:#fff3e0
    style T fill:#f3e5f5
    style Y fill:#e8f5e8

##时序图 - 详细的技术实现流程
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端界面
    participant SearchAPI as 搜索API
    participant SubAPI as 订阅API
    participant Scheduler as 定时调度器
    participant RSSService as RSS内容服务
    participant DedupeService as 去重服务
    participant SharedService as 共享内容服务
    participant RelationService as 用户关系服务
    participant AIService as AI增强服务
    participant Database as 数据库

    Note over User,Database: 1. 用户订阅配置阶段
    User->>Frontend: 搜索订阅源
    Frontend->>SearchAPI: 模板搜索请求
    SearchAPI-->>Frontend: 返回匹配模板
    User->>Frontend: 配置订阅参数
    Frontend->>SubAPI: 创建订阅配置
    SubAPI->>Database: 保存订阅配置
    
    Note over User,Database: 2. 定时/手动拉取阶段
    Scheduler->>RSSService: 定时触发拉取
    User->>Frontend: 手动触发拉取
    Frontend->>RSSService: 手动拉取请求
    
    Note over RSSService,Database: 3. 内容获取与解析阶段
    RSSService->>RSSService: 获取RSS XML
    RSSService->>RSSService: 解析XML内容
    RSSService->>RSSService: 内容标准化
    RSSService->>DedupeService: 计算内容哈希
    
    Note over DedupeService,Database: 4. 去重与存储阶段
    DedupeService->>Database: 检查内容哈希
    alt 内容已存在
        DedupeService-->>RSSService: 返回已存在内容ID
        RSSService->>RelationService: 建立用户关系
    else 新内容
        DedupeService-->>RSSService: 确认新内容
        RSSService->>SharedService: 创建共享内容
        SharedService->>Database: 存储共享内容
        SharedService-->>RSSService: 返回内容ID
        RSSService->>RelationService: 建立用户关系
    end
    
    RelationService->>Database: 保存用户-内容关系
    
    Note over AIService,Database: 5. AI增强处理阶段（架构预留，当前未实现）
    RSSService->>AIService: 触发AI增强（预留接口）
    AIService->>AIService: 生成内容摘要（待实现）
    AIService->>AIService: 提取标签（待实现）
    AIService->>AIService: 情感分析（待实现）
    AIService->>Database: 更新增强内容（预留字段：summary, tags）
    
    Note over User,Database: 6. 用户消费阶段
    User->>Frontend: 查看内容列表
    Frontend->>SubAPI: 获取用户内容
    SubAPI->>Database: 查询用户关联内容
    Database-->>SubAPI: 返回内容数据
    SubAPI-->>Frontend: 返回个性化内容
    Frontend-->>User: 展示内容列表