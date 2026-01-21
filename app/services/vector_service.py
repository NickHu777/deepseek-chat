# app/services/vector_service.py
"""
向量服务：负责文本向量化和向量搜索
"""
import logging
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    """向量服务"""

    def __init__(self):
        """初始化向量服务（延迟加载模型）"""
        self.dimension = settings.EMBEDDING_DIMENSION
        self.model = None
        self._model_load_attempted = False  # 是否已尝试加载
        self._use_lazy_loading = True  # 使用延迟加载

        logger.info(f"✅ 向量服务初始化完成 (维度: {self.dimension}, 延迟加载模式)")

    def _try_load_model(self, force_reload: bool = False):
        """尝试加载向量模型（带超时和快速失败）"""
        # 如果已经尝试过且不强制重新加载，直接返回
        if self._model_load_attempted and not force_reload:
            return
        
        self._model_load_attempted = True
        
        try:
            logger.info(f"⏳ 开始加载向量模型: {settings.VECTOR_MODEL}")
            
            # 检查环境变量，允许跳过模型加载
            import os
            if os.getenv("SKIP_VECTOR_MODEL", "false").lower() == "true":
                logger.info("🚫 环境变量 SKIP_VECTOR_MODEL=true，跳过模型加载")
                self.model = None
                return

            # 尝试导入 sentence-transformers
            try:
                from sentence_transformers import SentenceTransformer
                import socket
                
                # 设置超时（避免长时间等待）
                socket.setdefaulttimeout(5)  # 5秒超时
                
                try:
                    # 使用本地缓存优先
                    import os
                    cache_folder = os.path.expanduser("~/.cache/huggingface/hub")
                    
                    logger.info(f"📥 加载模型（本地缓存优先）: {settings.VECTOR_MODEL}")
                    
                    # 加载模型（会先检查本地缓存）
                    self.model = SentenceTransformer(
                        settings.VECTOR_MODEL,
                        cache_folder=cache_folder
                    )
                    
                    logger.info("✅ 向量模型加载成功")

                    # 验证模型维度
                    test_embedding = self.model.encode("test")
                    actual_dim = len(test_embedding)
                    
                    if actual_dim != self.dimension:
                        logger.warning(f"⚠️  配置维度({self.dimension})与模型实际维度({actual_dim})不匹配")
                        self.dimension = actual_dim  # 自动更新维度
                        logger.info(f"✅ 已自动更新向量维度为 {actual_dim}")

                except Exception as e:
                    error_msg = str(e)
                    if "Max retries" in error_msg or "Network is unreachable" in error_msg:
                        logger.warning(f"⚠️  网络连接失败，无法下载模型（将使用占位向量）")
                        logger.info("💡 提示：如需使用真实向量，请确保网络畅通或设置 HF_ENDPOINT 镜像")
                    else:
                        logger.error(f"❌ 加载向量模型失败: {error_msg}")
                    
                    self.model = None
                finally:
                    # 恢复默认超时
                    socket.setdefaulttimeout(None)

            except ImportError as e:
                logger.warning(f"⚠️  未安装 sentence-transformers: {e}")
                logger.info("💡 安装命令: pip install sentence-transformers")
                self.model = None

        except Exception as e:
            logger.error(f"❌ 初始化向量模型时出错: {e}")
            self.model = None

    def get_embedding(self, text: str) -> List[float]:
        """获取单个文本的向量表示（首次调用时加载模型）"""
        try:
            if not text or not text.strip():
                logger.debug("文本为空，返回零向量")
                return self._get_zero_vector()

            # 延迟加载：首次使用时才加载模型
            if self._use_lazy_loading and not self._model_load_attempted:
                logger.info("🔄 首次调用向量服务，开始加载模型...")
                self._try_load_model()

            # 如果模型已加载，使用真实模型
            if self.model is not None:
                try:
                    embedding = self.model.encode(text)
                    return embedding.tolist()
                except Exception as e:
                    logger.error(f"使用模型生成向量失败，使用伪随机向量替代: {e}")
                    return self._get_random_vector(text)

            # 否则返回伪随机向量（用于测试）
            logger.debug("向量模型未加载，使用伪随机向量")
            return self._get_random_vector(text)

        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            return self._get_zero_vector()

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """批量获取向量（更高效，首次调用时加载模型）"""
        try:
            if not texts:
                return []

            # 延迟加载：首次使用时才加载模型
            if self._use_lazy_loading and not self._model_load_attempted:
                logger.info("🔄 首次批量调用向量服务，开始加载模型...")
                self._try_load_model()

            # 如果模型已加载，使用真实模型批量处理
            if self.model is not None:
                try:
                    embeddings = self.model.encode(texts)
                    return embeddings.tolist()
                except Exception as e:
                    logger.error(f"使用模型批量生成向量失败，使用逐条生成替代: {e}")
                    # 降级到逐条生成
                    pass

            # 逐条生成向量（支持模型和随机向量）
            embeddings = []
            for text in texts:
                embedding = self.get_embedding(text)
                embeddings.append(embedding)

            return embeddings

        except Exception as e:
            logger.error(f"批量生成向量失败: {e}")
            return [self._get_zero_vector() for _ in range(len(texts))]

    def calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        try:
            # 转换为numpy数组
            a = np.array(vec1)
            b = np.array(vec2)

            # 计算点积
            dot_product = np.dot(a, b)

            # 计算模长
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            # 避免除以零
            if norm_a == 0 or norm_b == 0:
                return 0.0

            # 计算余弦相似度
            similarity = dot_product / (norm_a * norm_b)

            # 确保在[-1, 1]范围内
            similarity = max(-1.0, min(1.0, similarity))

            return float(similarity)

        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
            return 0.0

    def search_similar(
            self,
            db,
            query: str,
            limit: int = None,
            threshold: float = None,
            collection_name: str = "documents"
    ) -> List:
        """
        搜索相似的文档块

        Args:
            db: 数据库会话
            query: 查询文本
            limit: 返回结果数量
            threshold: 相似度阈值
            collection_name: 集合名称

        Returns:
            List[DocumentSearchResult]: 搜索结果列表
        """
        if limit is None:
            limit = settings.SEARCH_LIMIT
        if threshold is None:
            threshold = settings.SIMILARITY_THRESHOLD

        # 生成查询向量
        query_embedding = self.get_embedding(query)

        logger.info(f"向量搜索: query='{query[:50]}...', limit={limit}, threshold={threshold}")

        try:
            from app.models.document import DocumentChunk, Document
            from app.schemas.document import DocumentSearchResult
            
            # 查询所有文档分块（未来使用 pgvector 优化）
            chunks = db.query(DocumentChunk).join(Document).filter(
                DocumentChunk.embedding.isnot(None)
            ).all()
            
            if not chunks:
                logger.warning("数据库中没有已向量化的文档分块")
                return []
            
            # 计算相似度
            results_with_scores = []
            for chunk in chunks:
                if chunk.embedding:
                    try:
                        similarity = self.cosine_similarity(query_embedding, chunk.embedding)
                        
                        # 过滤低于阈值的结果
                        if similarity >= threshold:
                            results_with_scores.append({
                                "chunk": chunk,
                                "similarity": float(similarity)
                            })
                    except Exception as e:
                        logger.debug(f"计算相似度失败 (chunk_id={chunk.id}): {e}")
            
            # 按相似度排序并限制数量
            results_with_scores.sort(key=lambda x: x["similarity"], reverse=True)
            results_with_scores = results_with_scores[:limit]
            
            # 转换为响应格式
            search_results = []
            for item in results_with_scores:
                chunk = item["chunk"]
                search_results.append(
                    DocumentSearchResult(
                        chunk_id=chunk.id,
                        chunk_text=chunk.chunk_text,
                        filename=chunk.document.filename,
                        document_id=chunk.document_id,
                        similarity=item["similarity"],
                        metadata=chunk.chunk_metadata or {}
                    )
                )
            
            logger.info(f"找到 {len(search_results)} 个相关结果")
            return search_results

        except Exception as e:
            logger.error(f"向量搜索失败: {e}", exc_info=True)
            return []

    def calculate_batch_similarities(
            self,
            query_vec: List[float],
            vectors: List[List[float]]
    ) -> List[float]:
        """批量计算相似度"""
        try:
            if not vectors:
                return []

            # 转换为numpy数组
            query_np = np.array(query_vec)
            vectors_np = np.array(vectors)

            # 批量计算点积
            dot_products = np.dot(vectors_np, query_np)

            # 计算查询向量的模长
            query_norm = np.linalg.norm(query_np)

            # 计算所有向量的模长
            vectors_norms = np.linalg.norm(vectors_np, axis=1)

            # 避免除以零
            with np.errstate(divide='ignore', invalid='ignore'):
                similarities = dot_products / (vectors_norms * query_norm)
                similarities = np.nan_to_num(similarities, nan=0.0, posinf=0.0, neginf=0.0)

            # 确保在[-1, 1]范围内
            similarities = np.clip(similarities, -1.0, 1.0)

            return similarities.tolist()

        except Exception as e:
            logger.error(f"批量计算相似度失败: {e}")
            return [0.0] * len(vectors)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = {
            "model_name": settings.VECTOR_MODEL,
            "dimension": self.dimension,
            "model_loaded": self.model is not None,
            "model_type": "sentence-transformers" if self.model is not None else "placeholder",
        }

        if self.model is not None:
            info.update({
                "model_device": str(getattr(self.model, 'device', 'unknown')),
                "model_max_length": getattr(self.model, 'max_seq_length', 'unknown'),
            })

        return info

    def _get_zero_vector(self) -> List[float]:
        """获取零向量"""
        return [0.0] * self.dimension

    def _get_random_vector(self, text: str) -> List[float]:
        """获取伪随机向量（基于文本哈希，用于测试）"""
        try:
            # 使用文本的哈希值生成可重复的"随机"向量
            text_hash = hashlib.md5(text.encode()).hexdigest()
            seed = int(text_hash[:8], 16)

            # 设置随机种子以确保可重复性
            np.random.seed(seed)

            # 生成随机向量
            vector = np.random.randn(self.dimension).tolist()

            # 归一化到单位长度
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = (np.array(vector) / norm).tolist()

            return vector

        except Exception as e:
            logger.error(f"生成随机向量失败: {e}")
            return self._get_zero_vector()

    def normalize_vector(self, vector: List[float]) -> List[float]:
        """归一化向量到单位长度"""
        try:
            vec_np = np.array(vector)
            norm = np.linalg.norm(vec_np)

            if norm == 0:
                return vector

            normalized = (vec_np / norm).tolist()
            return normalized

        except Exception as e:
            logger.error(f"归一化向量失败: {e}")
            return vector

    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self.model is not None

    def reload_model(self, model_name: Optional[str] = None) -> bool:
        """重新加载模型"""
        try:
            old_model = self.model

            if model_name:
                settings.VECTOR_MODEL = model_name

            logger.info(f"重新加载向量模型: {settings.VECTOR_MODEL}")
            self.model = None

            # 尝试加载新模型
            self._try_load_model()

            success = self.model is not None

            if success:
                logger.info("✅ 模型重新加载成功")
                if old_model:
                    # 清理旧模型（如果需要）
                    del old_model
            else:
                logger.warning("❌ 模型重新加载失败")

            return success

        except Exception as e:
            logger.error(f"重新加载模型失败: {e}")
            return False


# 创建全局实例
vector_service = VectorService()


# 添加模块级别的便捷函数
def get_vector_service() -> VectorService:
    """获取向量服务实例"""
    return vector_service