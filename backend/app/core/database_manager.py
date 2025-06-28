#!/usr/bin/env python3
"""
统一数据库连接管理器
解决项目中60+个独立sqlite3.connect()调用点的问题
提供连接池、事务管理、自动清理等功能
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Optional, Generator, Any, Dict, List
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass

from loguru import logger


@dataclass
class ConnectionInfo:
    """连接信息"""
    connection: sqlite3.Connection
    created_at: datetime
    last_used: datetime
    thread_id: int
    is_active: bool = True


class DatabaseConnectionManager:
    """
    统一数据库连接管理器
    
    Features:
    - 单例模式，全局唯一实例
    - 连接池管理，避免频繁建立/销毁连接
    - 线程安全的连接分配
    - 自动连接清理和超时处理
    - 统一的事务管理
    - 连接状态监控和统计
    """
    
    _instance: Optional['DatabaseConnectionManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = "data/rss_subscriber.db") -> 'DatabaseConnectionManager':
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        """初始化数据库连接管理器"""
        if hasattr(self, '_initialized'):
            return
        
        self.db_path = Path(db_path).resolve()
        self._connections: Dict[int, ConnectionInfo] = {}
        self._pool_lock = threading.Lock()
        self._max_connections = 10  # 最大连接数
        self._connection_timeout = 300  # 连接超时时间（秒）
        self._cleanup_interval = 60  # 清理间隔（秒）
        self._last_cleanup = time.time()
        self._stats = {
            'total_created': 0,
            'total_closed': 0,
            'current_active': 0,
            'peak_connections': 0
        }
        
        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置SQLite连接参数
        self._connection_config = {
            'timeout': 30.0,  # 数据库锁等待超时
            'check_same_thread': False,  # 允许多线程使用
            'isolation_level': None,  # 自动提交模式
        }
        
        self._initialized = True
        logger.info(f"🔧 数据库连接管理器初始化完成: {self.db_path}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """创建新的数据库连接"""
        try:
            conn = sqlite3.connect(str(self.db_path), **self._connection_config)
            
            # 配置SQLite优化参数
            conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
            conn.execute("PRAGMA journal_mode = WAL")  # 使用WAL模式提升并发性
            conn.execute("PRAGMA synchronous = NORMAL")  # 平衡性能和安全性
            conn.execute("PRAGMA cache_size = 10000")  # 增加缓存大小
            conn.execute("PRAGMA temp_store = MEMORY")  # 临时文件存储在内存
            
            # 设置行工厂，返回字典格式结果
            conn.row_factory = sqlite3.Row
            
            self._stats['total_created'] += 1
            self._stats['current_active'] += 1
            self._stats['peak_connections'] = max(
                self._stats['peak_connections'], 
                self._stats['current_active']
            )
            
            logger.debug(f"📊 创建新数据库连接: {id(conn)} (活跃: {self._stats['current_active']})")
            return conn
            
        except Exception as e:
            logger.error(f"❌ 数据库连接创建失败: {e}")
            raise
    
    def _get_thread_connection(self) -> sqlite3.Connection:
        """获取当前线程的连接"""
        thread_id = threading.get_ident()
        
        with self._pool_lock:
            # 清理过期连接
            self._cleanup_expired_connections()
            
            # 检查是否已有当前线程的连接
            if thread_id in self._connections:
                conn_info = self._connections[thread_id]
                if conn_info.is_active:
                    # 更新最后使用时间
                    conn_info.last_used = datetime.now()
                    logger.debug(f"🔄 复用线程连接: {thread_id}")
                    return conn_info.connection
                else:
                    # 连接已失效，移除
                    del self._connections[thread_id]
            
            # 检查连接池是否已满
            if len(self._connections) >= self._max_connections:
                logger.warning(f"⚠️ 连接池已满 ({self._max_connections})，清理旧连接")
                self._cleanup_least_used_connection()
            
            # 创建新连接
            conn = self._create_connection()
            conn_info = ConnectionInfo(
                connection=conn,
                created_at=datetime.now(),
                last_used=datetime.now(),
                thread_id=thread_id,
                is_active=True
            )
            self._connections[thread_id] = conn_info
            
            return conn
    
    def _cleanup_expired_connections(self):
        """清理过期连接"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = current_time
        expired_threshold = datetime.now() - timedelta(seconds=self._connection_timeout)
        expired_threads = []
        
        for thread_id, conn_info in self._connections.items():
            if conn_info.last_used < expired_threshold:
                expired_threads.append(thread_id)
        
        for thread_id in expired_threads:
            self._close_connection(thread_id)
        
        if expired_threads:
            logger.debug(f"🧹 清理过期连接: {len(expired_threads)}个")
    
    def _cleanup_least_used_connection(self):
        """清理最久未使用的连接"""
        if not self._connections:
            return
        
        # 找到最久未使用的连接
        least_used_thread = min(
            self._connections.keys(),
            key=lambda tid: self._connections[tid].last_used
        )
        self._close_connection(least_used_thread)
    
    def _close_connection(self, thread_id: int):
        """关闭指定线程的连接"""
        if thread_id in self._connections:
            conn_info = self._connections[thread_id]
            try:
                conn_info.connection.close()
                self._stats['total_closed'] += 1
                self._stats['current_active'] -= 1
                logger.debug(f"🔒 关闭数据库连接: {thread_id}")
            except Exception as e:
                logger.warning(f"⚠️ 连接关闭失败: {e}")
            finally:
                del self._connections[thread_id]
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取数据库连接的上下文管理器
        
        Usage:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
                return cursor.fetchall()
        """
        conn = self._get_thread_connection()
        try:
            yield conn
        except Exception as e:
            # 发生异常时回滚事务（如果有的话）
            try:
                conn.rollback()
            except:
                pass
            logger.error(f"❌ 数据库操作异常: {e}")
            raise
        finally:
            # 连接由池管理，不在这里关闭
            pass
    
    @contextmanager
    def get_transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取数据库事务的上下文管理器
        
        Usage:
            with db_manager.get_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users ...")
                cursor.execute("UPDATE subscriptions ...")
                # 自动提交事务
        """
        conn = self._get_thread_connection()
        try:
            # 开始事务
            conn.execute("BEGIN")
            yield conn
            # 提交事务
            conn.commit()
            logger.debug("✅ 事务提交成功")
        except Exception as e:
            # 回滚事务
            try:
                conn.rollback()
                logger.warning(f"🔄 事务回滚: {e}")
            except:
                logger.error("❌ 事务回滚失败")
            raise
    
    def execute_query(self, query: str, params: tuple = None) -> List[sqlite3.Row]:
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            List[sqlite3.Row]: 查询结果
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        执行更新语句
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            int: 受影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        with self._pool_lock:
            active_connections = len([
                conn for conn in self._connections.values() 
                if conn.is_active
            ])
            
            return {
                **self._stats,
                'current_active': active_connections,
                'pool_size': len(self._connections),
                'max_connections': self._max_connections,
                'db_path': str(self.db_path)
            }
    
    def close_all_connections(self):
        """关闭所有连接"""
        with self._pool_lock:
            thread_ids = list(self._connections.keys())
            for thread_id in thread_ids:
                self._close_connection(thread_id)
            logger.info(f"🔒 已关闭所有数据库连接: {len(thread_ids)}个")
    
    def __del__(self):
        """析构函数，确保连接被正确关闭"""
        try:
            self.close_all_connections()
        except:
            pass


# 全局数据库管理器实例
db_manager = DatabaseConnectionManager()


def get_db_manager() -> DatabaseConnectionManager:
    """获取全局数据库管理器实例"""
    return db_manager


# 便捷函数
def execute_query(query: str, params: tuple = None) -> List[sqlite3.Row]:
    """执行查询的便捷函数"""
    return db_manager.execute_query(query, params)


def execute_update(query: str, params: tuple = None) -> int:
    """执行更新的便捷函数"""
    return db_manager.execute_update(query, params)


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """获取数据库连接的便捷函数"""
    with db_manager.get_connection() as conn:
        yield conn


@contextmanager  
def get_db_transaction() -> Generator[sqlite3.Connection, None, None]:
    """获取数据库事务的便捷函数"""
    with db_manager.get_transaction() as conn:
        yield conn


if __name__ == "__main__":
    # 连接管理器测试
    print("🧪 测试数据库连接管理器...")
    
    # 测试基本连接
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 数据库表数量: {len(tables)}")
    
    # 测试事务
    try:
        with get_db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)")
            cursor.execute("INSERT INTO test_table (id) VALUES (1)")
            print("✅ 事务测试成功")
    except Exception as e:
        print(f"❌ 事务测试失败: {e}")
    
    # 打印连接统计
    stats = db_manager.get_stats()
    print(f"📈 连接统计: {stats}") 