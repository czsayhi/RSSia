#!/usr/bin/env python3
"""
AI服务管理器
统一管理LLM服务、向量服务和prompt模版
提供标准化的AI调用接口，避免服务间直接依赖
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
import asyncio


class AIServiceManager:
    """AI服务统一管理器"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        """
        初始化AI服务管理器
        
        Args:
            db_path: 数据库路径（向量服务可能需要）
        """
        self.db_path = db_path
        
        # AI服务实例
        self.llm_service = None
        self.vector_service = None
        
        # Prompt模版缓存
        self.prompt_templates = {}
        
        # 初始化服务
        self._init_services()
        self._load_prompt_templates()
    
    def _init_services(self):
        """初始化AI服务"""
        # 初始化LLM服务
        try:
            self.llm_service = self._init_llm_service()
            if self.llm_service:
                logger.info("🤖 LLM服务初始化成功")
            else:
                logger.warning("⚠️ LLM服务不可用，将使用规则兜底")
        except Exception as e:
            logger.warning(f"⚠️ LLM服务初始化失败: {e}")
            self.llm_service = None
        
        # 初始化向量服务
        try:
            self.vector_service = self._init_vector_service()
            if self.vector_service:
                logger.info("🔮 向量服务初始化成功")
            else:
                logger.warning("⚠️ 向量服务不可用，跳过向量化处理")
        except Exception as e:
            logger.warning(f"⚠️ 向量服务初始化失败: {e}")
            self.vector_service = None
    
    def _init_llm_service(self):
        """初始化LLM服务"""
        try:
            from scripts.qwen3_chat import Qwen3Chat
            llm = Qwen3Chat()
            return llm
        except ImportError as e:
            logger.warning(f"🤖 Qwen3Chat模块不可用: {e}")
            return None
        except Exception as e:
            logger.warning(f"🤖 LLM初始化失败: {e}")
            return None
    
    def _init_vector_service(self):
        """初始化向量搜索服务"""
        try:
            from scripts.vector_search import VectorSearchService
            vector_service = VectorSearchService()
            return vector_service
        except ImportError as e:
            logger.warning(f"🔮 VectorSearchService模块不可用: {e}")
            return None
        except Exception as e:
            logger.warning(f"🔮 向量服务初始化失败: {e}")
            return None
    
    def _load_prompt_templates(self):
        """加载prompt模版"""
        try:
            # 当前主要的prompt模版文件
            template_path = Path(__file__).parent.parent.parent / "optimized_prompt_template.txt"
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    self.prompt_templates["content_analysis"] = f.read()
                logger.info("📝 Prompt模版加载成功")
            else:
                # 使用兜底模版
                self.prompt_templates["content_analysis"] = self._get_fallback_prompt_template()
                logger.warning("⚠️ 主prompt模版文件不存在，使用兜底模版")
                
        except Exception as e:
            logger.error(f"❌ 加载prompt模版失败: {e}")
            self.prompt_templates["content_analysis"] = self._get_fallback_prompt_template()
    
    def _get_fallback_prompt_template(self) -> str:
        """获取兜底的prompt模版"""
        return """你是一名内容分析专家。基于以下内容生成主题、标签和摘要：

输入内容：
{title}
{description}
{description_text}
{author}
{platform}
{feed_title}

请按JSON格式输出：
{
  "topics": "主题",
  "tags": ["标签1", "标签2"],
  "summary": "摘要"
}"""
    
    # =================
    # 公开调用接口
    # =================
    
    async def call_llm(self, prompt: str) -> Optional[str]:
        """
        调用LLM服务
        
        Args:
            prompt: 输入prompt
            
        Returns:
            Optional[str]: LLM响应结果，失败返回None
        """
        if not self.llm_service:
            logger.warning("🤖 LLM服务不可用")
            return None
        
        try:
            # 调用LLM生成结果
            response = await self._execute_llm_call(prompt)
            return response
        except Exception as e:
            logger.error(f"❌ LLM调用失败: {e}")
            return None
    
    async def _execute_llm_call(self, prompt: str) -> Optional[str]:
        """执行LLM调用（可能需要根据具体LLM服务调整）"""
        # 这里需要根据实际的LLM服务接口进行调用
        # 目前基于qwen3_chat的接口设计
        if hasattr(self.llm_service, 'generate_response'):
            # generate_response是同步方法，不需要await
            return self.llm_service.generate_response(prompt)
        elif hasattr(self.llm_service, 'chat'):
            # chat方法如果是同步的，不需要await
            if asyncio.iscoroutinefunction(self.llm_service.chat):
                return await self.llm_service.chat(prompt)
            else:
                return self.llm_service.chat(prompt)
        else:
            logger.error("❌ LLM服务接口不匹配")
            return None
    
    async def call_vector_service(self, text: str) -> Optional[List[float]]:
        """
        调用向量服务
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[List[float]]: 向量结果，失败返回None
        """
        if not self.vector_service:
            logger.warning("🔮 向量服务不可用")
            return None
        
        try:
            # 调用向量服务生成向量
            vector = await self._execute_vector_call(text)
            return vector
        except Exception as e:
            logger.error(f"❌ 向量服务调用失败: {e}")
            return None
    
    async def _execute_vector_call(self, text: str) -> Optional[List[float]]:
        """执行向量化调用"""
        if hasattr(self.vector_service, 'get_embedding'):
            # 检查是否为async方法
            if asyncio.iscoroutinefunction(self.vector_service.get_embedding):
                return await self.vector_service.get_embedding(text)
            else:
                return self.vector_service.get_embedding(text)
        elif hasattr(self.vector_service, 'encode_text'):
            # encode_text是同步方法
            return self.vector_service.encode_text(text)
        elif hasattr(self.vector_service, 'encode'):
            # encode方法如果是同步的，不需要await
            if asyncio.iscoroutinefunction(self.vector_service.encode):
                return await self.vector_service.encode(text)
            else:
                return self.vector_service.encode(text)
        else:
            logger.error("❌ 向量服务接口不匹配")
            return None
    
    async def store_vector(self, content_id: int, vector: List[float], metadata: Dict[str, Any] = None):
        """
        存储向量数据
        
        Args:
            content_id: 内容ID
            vector: 向量数据
            metadata: 元数据
        """
        if not self.vector_service:
            logger.warning("🔮 向量服务不可用，跳过存储")
            return
        
        try:
            if hasattr(self.vector_service, 'add_vector'):
                await self.vector_service.add_vector(
                    id=str(content_id),
                    vector=vector,
                    metadata=metadata or {}
                )
                logger.debug(f"🔮 向量存储成功: content_id={content_id}")
            else:
                logger.warning("⚠️ 向量服务不支持存储功能")
        except Exception as e:
            logger.error(f"❌ 向量存储失败: {e}")
    
    def get_prompt_template(self, template_name: str) -> str:
        """
        获取prompt模版
        
        Args:
            template_name: 模版名称
            
        Returns:
            str: prompt模版内容
        """
        return self.prompt_templates.get(template_name, self._get_fallback_prompt_template())
    
    def prepare_prompt(self, template_name: str, **kwargs) -> str:
        """
        准备prompt输入
        
        Args:
            template_name: 模版名称
            **kwargs: 模版参数
            
        Returns:
            str: 格式化后的prompt
        """
        template = self.get_prompt_template(template_name)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"⚠️ Prompt模版参数缺失: {e}")
            # 不要返回原始模板！用安全默认值填充缺失参数
            safe_kwargs = {
                'title': kwargs.get('title', ''),
                'description': kwargs.get('description', ''),
                'description_text': kwargs.get('description_text', ''),
                'author': kwargs.get('author', ''),
                'platform': kwargs.get('platform', ''),
                'feed_title': kwargs.get('feed_title', '')
            }
            return template.format(**safe_kwargs)
    
    def get_service_status(self) -> Dict[str, bool]:
        """
        获取服务状态
        
        Returns:
            Dict[str, bool]: 各服务的可用状态
        """
        return {
            "llm_available": self.llm_service is not None,
            "vector_available": self.vector_service is not None,
            "prompt_loaded": len(self.prompt_templates) > 0
        }
    
    def is_llm_available(self) -> bool:
        """检查LLM服务是否可用"""
        return self.llm_service is not None
    
    def is_vector_available(self) -> bool:
        """检查向量服务是否可用"""
        return self.vector_service is not None


# 创建全局实例
ai_service_manager = AIServiceManager() 