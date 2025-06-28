#!/usr/bin/env python3
"""
AI内容预处理服务
实现完整的7步预处理流程：
1. RSS内容获取 (已有)
2. 解析为标准字段、去重、用户映射 (已有)  
3. 按照prompt模版注入交付给大模型补充标签、主题、摘要
4. 大模型生成失败，用规则兜底补充进行补充
5. 标准内容完整入库
6. 向量化处理
7. 存入向量数据库
"""
import json
import asyncio
import sqlite3
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
from loguru import logger

from app.models.content import RSSContent
from app.services.ai_service_manager import ai_service_manager
from app.services.content_processing_utils import ContentProcessingUtils


class AIContentProcessor:
    """AI内容预处理核心服务 - 使用统一的AIServiceManager"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        # 数据库路径
        self.db_path = db_path
        # 使用全局AI服务管理器
        self.ai_manager = ai_service_manager
        
        # 记录AI服务状态
        status = self.ai_manager.get_service_status()
        logger.info(f"🧠 AI内容处理器初始化完成: LLM可用={status['llm_available']}, 向量服务可用={status['vector_available']}")
    
    @property
    def llm_service(self):
        """兼容性属性：LLM服务"""
        return self.ai_manager.llm_service
    
    @property  
    def vector_service(self):
        """兼容性属性：向量服务"""
        return self.ai_manager.vector_service
    
    async def process_content_intelligence(self, entries: List[RSSContent]) -> List[RSSContent]:
        """
        第3-7步：完整的AI内容处理流程
        
        Args:
            entries: RSS内容列表（已去重）
            
        Returns:
            List[RSSContent]: AI处理后的内容列表
        """
        logger.info(f"🧠 开始AI内容处理，共{len(entries)}条")
        
        processed_entries = []
        skipped_count = 0
        
        for i, entry in enumerate(entries, 1):
            logger.debug(f"🔄 处理第{i}/{len(entries)}条: {entry.title[:50]}...")
            
            # 第1步：内容有效性验证 - 获取内容失败直接跳过
            if not self._validate_content_availability(entry):
                logger.warning(f"⚠️ 内容不可用，跳过处理: {getattr(entry, 'title', 'Unknown')[:30]}...")
                skipped_count += 1
                continue
            
            try:
                # 第3步：AI智能处理
                ai_result = await self._process_with_ai(entry)
                
                if ai_result:
                    # AI处理成功（字段分离处理）
                    entry.smart_summary = ai_result.get('summary', entry.title)
                    entry.topics = ai_result.get('topics', '其他')  # 新增：设置topics字段
                    entry.tags = ai_result.get('tags', '[]')  # 纯标签数组JSON
                    entry.content_type = ai_result.get('content_type', entry.content_type)
                    logger.debug(f"✅ AI处理成功: {entry.title[:30]}... | topics='{entry.topics}'")
                else:
                    # 第4步：AI失败，规则兜底
                    fallback_result = self._process_with_fallback(entry)
                    entry.smart_summary = fallback_result.get('summary', '')
                    entry.topics = fallback_result.get('topics', '其他')  # 新增：兜底topics
                    entry.tags = fallback_result.get('tags', '[]')  # 纯标签数组JSON
                    
                    logger.debug(f"🔄 兜底处理完成: {entry.title[:30]}... | topics='{entry.topics}'")
                
                # 第5步：更新数据库AI处理结果
                try:
                    await self._update_ai_results_to_database(entry)
                    logger.debug(f"💾 数据库更新完成: {entry.title[:30]}...")
                except Exception as e:
                    logger.warning(f"⚠️ 数据库更新失败: {e}")
                
                # 第6-7步：向量化处理
                if self.vector_service:
                    try:
                        logger.info(f"🔮 开始向量化处理: {entry.title[:30]}...")
                        await self._process_vectorization(entry)
                        logger.success(f"✅ 向量化完成: {entry.title[:30]}...")
                    except Exception as e:
                        logger.warning(f"⚠️ 向量化失败: {e}")
                else:
                    logger.info("🔮 向量服务不可用，跳过向量化处理")
                
                processed_entries.append(entry)
                
            except Exception as e:
                logger.error(f"❌ 内容处理失败，跳过此条目: {getattr(entry, 'title', 'Unknown')[:50]}... | 错误: {e}")
                skipped_count += 1
                # 按照用户要求：处理失败直接跳过，等下次轮询再尝试
                continue
        
        logger.info(f"✅ AI内容处理完成: 成功{len(processed_entries)}条，跳过{skipped_count}条")
        return processed_entries
    
    async def _process_with_ai(self, entry: RSSContent) -> Optional[Dict[str, Any]]:
        """
        第3步：使用AI处理内容
        
        Args:
            entry: RSS内容项
            
        Returns:
            Optional[Dict]: AI处理结果或None
        """
        if not self.llm_service:
            logger.info("🤖 LLM服务不可用，跳过AI处理")
            return None
        
        try:
            # 准备prompt输入
            logger.info(f"📝 开始准备Prompt - 标题: {getattr(entry, 'title', '')[:50]}...")
            prompt_input = self._prepare_prompt_input(entry)
            
            # 记录组装的prompt（截取前500字符避免日志过长）
            logger.info(f"📋 Prompt组装完成，长度: {len(prompt_input)}字符")
            logger.debug(f"📋 Prompt内容预览: {prompt_input[:500]}...")
            
            # 调用LLM
            logger.info(f"🤖 发送请求到LLM服务 (Normal模式)")
            response = await self._call_llm(prompt_input)
            
            if response:
                logger.info(f"✅ LLM响应成功，长度: {len(response)}字符")
                logger.debug(f"🤖 LLM原始响应: {response}")
                
                # 解析JSON响应
                logger.info("🔍 开始解析AI响应JSON")
                ai_result = self._parse_ai_response(response)
                
                if ai_result:
                    logger.success(f"✅ AI处理成功 - 摘要长度: {len(ai_result.get('summary', ''))}字符")
                    logger.debug(f"🎯 AI处理结果: {ai_result}")
                    return ai_result
                else:
                    logger.warning("⚠️ AI响应JSON解析失败，将使用兜底处理")
            else:
                logger.warning("⚠️ LLM响应为空，将使用兜底处理")
            
        except Exception as e:
            logger.warning(f"⚠️ AI处理异常: {e}")
            
        return None
    
    def _validate_content_availability(self, entry: RSSContent) -> bool:
        """
        验证内容是否可用于处理
        
        Args:
            entry: RSS内容项
            
        Returns:
            bool: True表示内容可用，False表示应跳过
        """
        try:
            # 获取关键字段
            title = getattr(entry, 'title', '') or ""
            description = getattr(entry, 'description', '') or ""
            description_text = getattr(entry, 'description_text', '') or ""
            
            # 判断是否有可用的核心内容
            has_title = bool(title.strip())
            has_description = bool(description.strip() or description_text.strip())
            
            # 业务逻辑：如果title和description都为空，则认为内容获取失败
            if not has_title and not has_description:
                logger.debug(f"🚫 内容验证失败：标题和描述都为空")
                return False
            
            # 有任一核心字段可用，则认为可以处理（即使其他字段不完整）
            logger.debug(f"✅ 内容验证通过：title={has_title}, description={has_description}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ 内容验证异常: {e}")
            return False
    
    def _prepare_prompt_input(self, entry: RSSContent) -> str:
        """
        准备prompt输入
        注意：此方法调用前已通过_validate_content_availability验证
        因此可以安全地处理字段不完整的情况
        """
        prompt = self.ai_manager.prepare_prompt(
            template_name="content_analysis",
            title=getattr(entry, 'title', '') or "",
            description=getattr(entry, 'description', '') or "",
            description_text=getattr(entry, 'description_text', '') or "",
            author=getattr(entry, 'author', '') or "",
            platform=getattr(entry, 'platform', '') or "",
            feed_title=getattr(entry, 'feed_title', '') or ""
        )
        return prompt
    
    def _prepare_prompt_input_for_terminal(self, entry: RSSContent) -> str:
        """
        准备适合终端输入的prompt（移除换行符，优化格式）
        
        Args:
            entry: RSS内容项
            
        Returns:
            str: 优化格式的单行prompt，适合终端直接使用
        """
        # 先获取完整prompt
        full_prompt = self._prepare_prompt_input(entry)
        
        # 移除换行符，用空格替代
        terminal_prompt = full_prompt.replace('\n', ' ').replace('\r', ' ')
        
        # 清理多余的空格，保持JSON格式的可读性
        import re
        # 第一步：清理连续的空格
        terminal_prompt = re.sub(r'\s+', ' ', terminal_prompt)
        
        # 第二步：优化JSON格式中的空格（如果有的话）
        terminal_prompt = terminal_prompt.replace('{ ', '{').replace(' }', '}')
        terminal_prompt = terminal_prompt.replace('[ ', '[').replace(' ]', ']')
        
        # 第三步：清理首尾空格
        terminal_prompt = terminal_prompt.strip()
        
        return terminal_prompt
    
    async def _call_llm(self, prompt: str) -> Optional[str]:
        """调用LLM服务"""
        try:
            # 使用AIServiceManager的统一接口
            response = await self.ai_manager.call_llm(prompt)
            return response
            
        except Exception as e:
            logger.warning(f"⚠️ LLM调用失败: {e}")
            return None
    
    def _parse_ai_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析AI响应（适配字段分离结构）"""
        try:
            # 提取JSON部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            logger.debug(f"🔍 JSON查找: start_idx={start_idx}, end_idx={end_idx}")
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                logger.debug(f"📋 提取的JSON字符串: {json_str}")
                
                result = json.loads(json_str)
                logger.info(f"✅ JSON解析成功: {result}")
                
                # 验证必需字段
                if self._validate_ai_result(result):
                    logger.info("✅ AI结果字段验证通过")
                    
                    # 字段分离处理：兼容原有prompt格式
                    separated_result = self._convert_ai_result_to_separated_fields(result)
                    
                    logger.debug(f"🏷️ 字段分离完成: {separated_result}")
                    
                    return separated_result
                else:
                    logger.warning(f"⚠️ AI结果字段验证失败，缺少必需字段: {result}")
            else:
                logger.warning("⚠️ 在AI响应中未找到有效的JSON格式")
                    
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ AI响应JSON解析失败: {e}")
            logger.debug(f"❌ 无法解析的响应内容: {response}")
        except Exception as e:
            logger.warning(f"⚠️ AI响应处理失败: {e}")
            
        return None
    
    def _validate_ai_result(self, result: Dict[str, Any]) -> bool:
        """验证AI结果格式"""
        required_fields = ['topics', 'tags', 'summary']
        return all(field in result for field in required_fields)
    
    def _convert_ai_result_to_separated_fields(self, ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """将AI结果转换为字段分离格式（兼容原有prompt格式）"""
        try:
            # 提取基础字段
            summary = ai_result.get('summary', '')
            
            # 处理topics字段（原有prompt返回单个主题字符串）
            topics = ai_result.get('topics', '其他')
            if isinstance(topics, list) and topics:
                topics = topics[0]  # 兼容：如果返回数组取第一个
            elif not isinstance(topics, str):
                topics = "其他"
            
            # 处理tags字段（原有prompt返回标签数组）
            tags = ai_result.get('tags', [])
            if not isinstance(tags, list):
                tags = []
            
            # 其他字段保持不变
            content_type = ai_result.get('content_type', 'text')
            
            return {
                'summary': summary,
                'topics': topics,  # 单个主题字符串
                'tags': json.dumps(tags, ensure_ascii=False),  # 纯标签数组转JSON
                'content_type': content_type
            }
            
        except Exception as e:
            logger.error(f"❌ AI结果字段分离转换失败: {e}")
            return {
                'summary': ai_result.get('summary', ''),
                'topics': '其他',
                'tags': '[]',
                'content_type': 'text'
            }
    
    def _process_with_fallback(self, entry: RSSContent) -> Dict[str, str]:
        """
        第4步：兜底处理（简化版）- 直接返回新格式
        
        Args:
            entry: RSS内容项（已通过内容有效性验证）
            
        Returns:
            Dict[str, str]: 兜底处理结果（新格式）
        """
        # 使用简化的兜底服务（直接输出新格式）
        result = ContentProcessingUtils.process_content_with_fallback(
            title=getattr(entry, 'title', '') or "",
            description=getattr(entry, 'description', '') or "",
            description_text=getattr(entry, 'description_text', '') or "",
            author=getattr(entry, 'author', '') or "",
            platform=getattr(entry, 'platform', '') or "",
            feed_title=getattr(entry, 'feed_title', '') or "",
            link=getattr(entry, 'original_link', '') or ""
        )
        
        # 新版本兜底服务直接返回字段分离格式，无需转换
        logger.debug(f"🔄 兜底处理完成: summary={len(result.get('summary', ''))}, topics='{result.get('topics', '')}', tags={len(result.get('tags', '[]'))}")
        return result
    

    
    async def _update_ai_results_to_database(self, entry: RSSContent):
        """
        第5步：更新AI处理结果到数据库（适配字段分离结构）
        
        Args:
            entry: 已处理的RSS内容项（包含AI结果和content_id）
        """
        try:
            # 直接使用content_id - 新架构下已包含在entry中
            content_id = entry.content_id
            if not content_id:
                logger.warning(f"⚠️ 内容缺少content_id，跳过数据库更新: {entry.title[:30]}...")
                return

            # 准备字段分离的数据
            summary = entry.smart_summary
            topics = getattr(entry, 'topics', '其他')  # 单个主题字符串
            tags = entry.tags if hasattr(entry, 'tags') else '[]'  # 标签JSON数组
            
            # 更新数据库中的AI字段（字段分离）
            await asyncio.to_thread(self._update_shared_content_ai_fields_v2, 
                                  content_id, summary, topics, tags)
            
            logger.debug(f"💾 AI结果已更新到数据库: content_id={content_id}")
            
        except Exception as e:
            logger.error(f"❌ 更新AI结果到数据库失败: {e}")
            raise

    def _update_shared_content_ai_fields_v2(self, content_id: int, summary: str, topics: str, tags: str):
        """同步方法：更新共享内容的AI字段（字段分离版本）"""
        try:
            from ..core.database_manager import get_db_transaction
            with get_db_transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE shared_contents 
                    SET summary = ?, topics = ?, tags = ?, updated_at = ?
                    WHERE id = ?
                """, (summary, topics, tags, datetime.now(), content_id))
                
                if cursor.rowcount > 0:
                    logger.debug(f"💾 数据库更新成功: content_id={content_id}, topics='{topics}'")
                else:
                    logger.warning(f"⚠️ 数据库更新无影响: content_id={content_id}")
                    
        except Exception as e:
            logger.error(f"❌ 数据库更新失败: {e}")
            raise
    
    async def _get_content_id_by_hash(self, content_hash: str) -> Optional[int]:
        """通过content_hash获取内容ID"""
        try:
            from ..core.database_manager import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM shared_contents WHERE content_hash = ?", (content_hash,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ 查询内容ID失败: {e}")
            return None
    
    async def _process_vectorization(self, entry: RSSContent):
        """
        第6-7步：向量化处理和存储（统一向量服务）
        
        Args:
            entry: RSS内容项
        """
        if not self.vector_service:
            logger.info("🔮 向量服务不可用，跳过向量化处理")
            return
        
        try:
            logger.info(f"🔮 开始向量化处理: {entry.title[:30]}...")
            
            # 准备标准化数据（直接从entry提取）
            content_id = getattr(entry, 'content_id', None)
            if not content_id:
                logger.warning(f"⚠️ 内容缺少content_id，跳过向量化: {entry.title[:30]}...")
                return
            
            title = entry.title or ""
            summary = entry.smart_summary or ""
            topics = getattr(entry, 'topics', '其他')  # 单个主题字符串
            
            # 解析标签数组
            tags_list = []
            try:
                tags_json = entry.tags if hasattr(entry, 'tags') else '[]'
                if isinstance(tags_json, str):
                    tags_list = json.loads(tags_json)
                elif isinstance(tags_json, list):
                    tags_list = tags_json
            except:
                tags_list = []
            
            # 调用统一向量服务（新接口）
            platform = getattr(entry, 'platform', '')
            publish_date = str(getattr(entry, 'published_at', ''))
            original_link = getattr(entry, 'original_link', '')
            
            # 使用新的向量服务接口
            await asyncio.to_thread(
                self.vector_service.add_content_vector,
                content_id=content_id,  # 直接传递content_id
                title=title,
                summary=summary,
                topics=topics,
                tags=tags_list,
                platform=platform,
                publish_date=publish_date,
                original_link=original_link
            )
            
            logger.success(f"✅ 向量化存储成功: {entry.title[:30]}... (content_id={content_id})")
            
        except Exception as e:
            logger.warning(f"⚠️ 向量化处理失败: {e}")
            raise
    

    
    def get_service_status(self) -> Dict[str, bool]:
        """获取服务状态"""
        # 直接使用AIServiceManager的状态
        status = self.ai_manager.get_service_status()
        status['fallback_available'] = True  # 兜底服务总是可用
        return status


# 创建全局实例
ai_content_processor = AIContentProcessor() 