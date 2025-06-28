#!/usr/bin/env python3
"""
统一向量搜索服务
专注于向量化技术实现，提供简化的标准接口
- 内容预处理场景：接收标准字段，直接向量化存储
- 对话场景：接收用户输入，直接向量化查询
"""

import sys
import os
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

class VectorSearchService:
    """统一向量搜索服务 - 纯技术实现"""
    
    def __init__(self, persist_directory: str = "data/chroma_db"):
        """初始化向量搜索服务"""
        print("🔍 正在初始化统一向量搜索服务...")
        
        self.persist_directory = persist_directory
        self.collection_name = "rss_contents_unified"
        
        # 初始化ChromaDB客户端
        self._init_chromadb_client()
        
        # 加载向量模型
        print("📦 正在加载sentence-transformers模型...")
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        
        print("✅ 统一向量搜索服务初始化完成！")
        print("💡 支持场景:")
        print("   - 内容预处理：直接存储标准字段")
        print("   - 用户对话：直接向量化查询")
        print("=" * 60)
    
    def _init_chromadb_client(self):
        """初始化ChromaDB客户端和集合"""
        try:
            # 确保持久化目录存在
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            # 创建ChromaDB客户端
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name
                )
                print(f"📂 使用现有ChromaDB集合: {self.collection_name}")
            except Exception:
                # 集合不存在，创建新集合
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "RSS内容统一向量化存储"}
                )
                print(f"🆕 创建新ChromaDB集合: {self.collection_name}")
                
            print(f"🗄️ ChromaDB持久化路径: {self.persist_directory}")
            
        except Exception as e:
            print(f"❌ ChromaDB初始化失败: {e}")
            raise

    # ===========================================
    # 内容预处理场景：直接接收标准字段
    # ===========================================
    
    def add_content_vector(self, content_id: int, title: str, summary: str, 
                          topics: str, tags: List[str], platform: str = "", 
                          publish_date: str = "", original_link: str = ""):
        """
        内容预处理场景：添加内容到向量数据库
        
        Args:
            content_id: 内容ID（数据库主键）
            title: 标题
            summary: 摘要
            topics: 单个主题字符串
            tags: 纯标签数组
            platform: 平台
            publish_date: 发布日期
            original_link: 原始链接
        """
        try:
            # 1. 组装向量化文本（四个核心元素）
            vectorization_text = self._prepare_vectorization_text(
                title, summary, topics, tags
            )
            
            # 2. 准备元数据
            metadata = {
                'content_id': content_id,
                'title': title[:100],  # ChromaDB字符串长度限制
                'summary': summary[:200],
                'topics': topics[:50],
                'tags': json.dumps(tags, ensure_ascii=False)[:300],
                'platform': platform,
                'publish_date': publish_date,
                'original_link': original_link,
                'created_at': datetime.now().isoformat(),
                'vector_type': 'content'  # 标识向量类型
            }
            
            # 3. 生成文档ID
            doc_id = f"content_{content_id}"
            
            # 4. 添加到ChromaDB（自动向量化）
            self.collection.add(
                documents=[vectorization_text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            print(f"✅ 内容向量存储成功: {title[:30]}... (ID: {content_id})")
            
        except Exception as e:
            print(f"❌ 内容向量存储失败: {e}")
            raise
    
    def _prepare_vectorization_text(self, title: str, summary: str, 
                                   topics: str, tags: List[str]) -> str:
        """
        组装向量化文本（四个核心元素）
        
        Args:
            title: 标题
            summary: 摘要
            topics: 单个主题字符串
            tags: 纯标签数组
            
        Returns:
            str: 组合后的向量化文本
        """
        components = []
        
        # 1. 标题（必需）
        if title and title.strip():
            components.append(f"标题: {title.strip()}")
        
        # 2. 摘要
        if summary and summary.strip():
            components.append(f"摘要: {summary.strip()}")
        
        # 3. 主题（单个字符串）
        if topics and topics.strip() and topics != '其他':
            components.append(f"主题: {topics.strip()}")
        
        # 4. 标签（数组）
        if tags and isinstance(tags, list):
            valid_tags = [tag.strip() for tag in tags if tag and isinstance(tag, str) and tag.strip()]
            if valid_tags:
                components.append(f"标签: {', '.join(valid_tags)}")
        
        vectorization_text = " | ".join(components)
        print(f"🔤 向量化文本: {vectorization_text[:100]}...")
        
        return vectorization_text
    
    # ===========================================
    # 对话场景：用户输入向量化和检索
    # ===========================================
    
    def encode_user_query(self, query_text: str) -> List[float]:
        """
        对话场景：将用户输入向量化
        
        Args:
            query_text: 用户查询文本
            
        Returns:
            List[float]: 查询向量
        """
        try:
            print(f"🔤 用户查询向量化: {query_text[:50]}...")
            vector = self.model.encode([query_text])[0]
            print(f"✅ 查询向量生成成功: {len(vector)}维")
            return vector.tolist()
        except Exception as e:
            print(f"❌ 查询向量化失败: {e}")
            raise
    
    def search_similar_content(self, query_text: str, top_k: int = 5, 
                              platform_filter: Optional[str] = None,
                              topics_filter: Optional[str] = None) -> List[Dict]:
        """
        对话场景：基于用户查询检索相似内容
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            platform_filter: 平台过滤
            topics_filter: 主题过滤
            
        Returns:
            List[Dict]: 相似内容列表
        """
        try:
            # 构建过滤条件
            where_filter = {"vector_type": "content"}  # 只检索内容向量
            
            if platform_filter:
                where_filter["platform"] = platform_filter
            if topics_filter:
                where_filter["topics"] = topics_filter
            
            # ChromaDB查询
            results = self.collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_filter,
                include=['metadatas', 'documents', 'distances']
            )
            
            # 处理结果
            formatted_results = []
            if results and results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    # 转换相似度
                    similarity = max(0, 1 - distance)
                    
                    formatted_results.append({
                        'content_id': metadata.get('content_id'),
                        'title': metadata.get('title', ''),
                        'summary': metadata.get('summary', ''),
                        'topics': metadata.get('topics', ''),
                        'tags': json.loads(metadata.get('tags', '[]')),
                        'platform': metadata.get('platform', ''),
                        'publish_date': metadata.get('publish_date', ''),
                        'similarity': similarity,
                        'distance': distance,
                        'vectorization_text': doc
                    })
            
            # 按相似度排序
            formatted_results.sort(key=lambda x: x['similarity'], reverse=True)
            print(f"🔍 检索到 {len(formatted_results)} 条相似内容")
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 内容检索失败: {e}")
            return []
    
    # ===========================================
    # 通用工具方法
    # ===========================================
    
    def get_vector_stats(self) -> Dict[str, Any]:
        """获取向量数据库统计信息"""
        try:
            count = self.collection.count()
            
            # 获取最近添加的内容
            recent_results = self.collection.get(
                limit=10,
                include=['metadatas'],
                where={"vector_type": "content"}
            )
            
            recent_items = []
            platform_stats = {}
            topics_stats = {}
            
            if recent_results and recent_results['metadatas']:
                for metadata in recent_results['metadatas']:
                    # 最近内容
                    recent_items.append({
                        'content_id': metadata.get('content_id'),
                        'title': metadata.get('title', 'Unknown'),
                        'topics': metadata.get('topics', ''),
                        'created_at': metadata.get('created_at', '')
                    })
                    
                    # 平台统计
                    platform = metadata.get('platform', 'unknown')
                    platform_stats[platform] = platform_stats.get(platform, 0) + 1
                    
                    # 主题统计
                    topics = metadata.get('topics', '其他')
                    topics_stats[topics] = topics_stats.get(topics, 0) + 1
            
            return {
                'total_vectors': count,
                'platform_distribution': platform_stats,
                'topics_distribution': topics_stats,
                'recent_items': recent_items[:5],
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory,
                'model_name': 'paraphrase-multilingual-MiniLM-L12-v2'
            }
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {'error': str(e)}
    
    def delete_content_vector(self, content_id: int):
        """删除指定内容的向量"""
        try:
            doc_id = f"content_{content_id}"
            self.collection.delete(ids=[doc_id])
            print(f"🗑️ 已删除内容向量: content_id={content_id}")
        except Exception as e:
            print(f"❌ 删除向量失败: {e}")
            raise
    
    def reset_collection(self):
        """重置向量集合（用于测试）"""
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"🗑️ 已删除ChromaDB集合: {self.collection_name}")
            
            # 重新创建集合
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "RSS内容统一向量化存储"}
            )
            print(f"🆕 重新创建ChromaDB集合: {self.collection_name}")
            
        except Exception as e:
            print(f"❌ 重置集合失败: {e}")


# ===========================================
# 全局实例和便捷函数
# ===========================================

# 创建全局实例
vector_service = VectorSearchService()

def add_content_to_vectors(content_id: int, title: str, summary: str, 
                          topics: str, tags: List[str], **kwargs):
    """便捷函数：添加内容到向量数据库"""
    return vector_service.add_content_vector(
        content_id, title, summary, topics, tags, **kwargs
    )

def search_content_by_query(query_text: str, **kwargs):
    """便捷函数：根据查询检索内容"""
    return vector_service.search_similar_content(query_text, **kwargs)


# ===========================================
# 命令行测试入口
# ===========================================

if __name__ == "__main__":
    print("🚀 统一向量搜索服务测试")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "stats":
            # 显示统计信息
            stats = vector_service.get_vector_stats()
            print("\n📊 向量数据库统计:")
            print(json.dumps(stats, indent=2, ensure_ascii=False))
            
        elif sys.argv[1] == "search" and len(sys.argv) > 2:
            # 搜索测试
            query = " ".join(sys.argv[2:])
            results = vector_service.search_similar_content(query, top_k=3)
            print(f"\n🔍 搜索结果 (查询: {query}):")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']} (相似度: {result['similarity']:.3f})")
                
        elif sys.argv[1] == "reset":
            # 重置集合
            vector_service.reset_collection()
            
        else:
            print("❌ 未知命令")
    else:
        print("💡 使用示例:")
        print("  python vector_search.py stats          # 显示统计")
        print("  python vector_search.py search 查询内容  # 搜索测试")
        print("  python vector_search.py reset          # 重置集合") 