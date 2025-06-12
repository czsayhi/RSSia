-- RSS订阅频率配置和风控相关数据库表结构
-- 创建时间: 2024年
-- 用途: 订阅频率管理、自动调度、风控限流

-- 用户拉取记录表（每日限流控制）
CREATE TABLE IF NOT EXISTS user_fetch_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fetch_date DATE NOT NULL,                -- 自然日维度 (YYYY-MM-DD)
    fetch_count INTEGER DEFAULT 0,          -- 当日总拉取次数
    auto_fetch_count INTEGER DEFAULT 0,     -- 自动拉取次数
    manual_fetch_count INTEGER DEFAULT 0,   -- 手动拉取次数
    last_fetch_at TIMESTAMP,                -- 最后拉取时间
    last_fetch_success BOOLEAN,             -- 最后拉取是否成功
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, fetch_date),             -- 确保每个用户每天只有一条记录
    INDEX idx_user_fetch_date (user_id, fetch_date)
);

-- 拉取任务记录表（重试逻辑控制）
CREATE TABLE IF NOT EXISTS fetch_task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_type VARCHAR(20) NOT NULL,         -- 'auto' 或 'manual'
    task_key VARCHAR(100) NOT NULL,         -- 任务唯一标识 (user_id + date + hour)
    scheduled_at TIMESTAMP NOT NULL,        -- 计划执行时间
    executed_at TIMESTAMP,                  -- 实际执行时间
    attempt_count INTEGER DEFAULT 0,        -- 尝试次数
    max_attempts INTEGER DEFAULT 3,         -- 最大尝试次数
    status VARCHAR(20) DEFAULT 'pending',   -- pending, running, success, failed, cancelled
    success_count INTEGER DEFAULT 0,        -- 成功拉取的订阅数量
    total_count INTEGER DEFAULT 0,          -- 总订阅数量
    error_message TEXT,                     -- 错误信息
    next_retry_at TIMESTAMP,                -- 下次重试时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(task_key),                       -- 防止重复任务
    INDEX idx_user_task_status (user_id, status),
    INDEX idx_scheduled_at (scheduled_at),
    INDEX idx_next_retry (next_retry_at)
);

-- 订阅频率配置表（用户维度配置）
CREATE TABLE IF NOT EXISTS user_fetch_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,        -- 用户ID（唯一）
    auto_fetch_enabled BOOLEAN DEFAULT 0,   -- 自动拉取开关（新用户默认关闭）
    frequency VARCHAR(20) DEFAULT 'daily',  -- 频率: daily, three_days, weekly
    preferred_hour INTEGER DEFAULT 9,       -- 首选时间（24小时制，UTC+8）
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',  -- 时区
    daily_limit INTEGER DEFAULT 10,         -- 每日拉取次数限制
    is_active BOOLEAN DEFAULT 1,            -- 配置是否生效
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_auto_fetch (user_id, auto_fetch_enabled),
    CHECK (preferred_hour >= 0 AND preferred_hour <= 23),
    CHECK (frequency IN ('daily', 'three_days', 'weekly')),
    CHECK (daily_limit > 0 AND daily_limit <= 100)
); 