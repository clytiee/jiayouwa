import json
import os
import numpy as np
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class VectorSearch:
    """向量语义搜索"""
    
    EMBEDDING_URL = 'https://open.bigmodel.cn/api/paas/v4/embeddings'
    CACHE_KEY = 'resource_embeddings'
    CACHE_FILE = 'resource_embeddings.json'
    
    @classmethod
    def _get_headers(cls):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.ZHIPU_API_KEY}'
        }
    
    @classmethod
    def _get_embedding(cls, text):
        """获取文本的向量"""
        if not settings.ZHIPU_API_KEY:
            logger.warning('ZHIPU_API_KEY 未配置')
            return None
        
        try:
            response = requests.post(
                cls.EMBEDDING_URL,
                headers=cls._get_headers(),
                json={
                    'model': 'embedding-2',
                    'input': text[:2000]  # 限制长度
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get('data', [{}])[0].get('embedding', [])
                return np.array(embedding) if embedding else None
            else:
                logger.error(f'Embedding API 失败: {response.status_code}')
                return None
        except Exception as e:
            logger.error(f'获取向量失败: {e}')
            return None
    
    @classmethod
    def _cosine_similarity(cls, a, b):
        """计算余弦相似度"""
        if a is None or b is None:
            return 0
        if len(a) == 0 or len(b) == 0:
            return 0
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
    
    @classmethod
    def _get_resource_text(cls, resource):
        """构建资源的文本表示"""
        parts = [resource.title]
        if resource.description:
            parts.append(resource.description)
        if resource.tags:
            parts.append(' '.join(resource.tags))
        if resource.grade:
            parts.append(resource.grade)
        if resource.resource_type:
            parts.append(resource.resource_type)
        return ' '.join(parts)
    
    @classmethod
    def build_index(cls, force=False):
        """构建向量索引"""
        from .models import Resource
        
        # 检查缓存
        if not force:
            cached = cache.get(cls.CACHE_KEY)
            if cached:
                return cached
        
        resources = Resource.objects.filter(status='published').select_related('uploader')
        if not resources.exists():
            return []
        
        index_data = []
        for resource in resources:
            text = cls._get_resource_text(resource)
            embedding = cls._get_embedding(text)
            if embedding is not None:
                index_data.append({
                    'id': resource.id,
                    'title': resource.title,
                    'embedding': embedding.tolist(),
                    'price': resource.price,
                    'tags': resource.tags,
                    'grade': resource.grade,
                    'resource_type': resource.resource_type,
                    'uploader_name': resource.uploader.first_name or resource.uploader.username,
                    'cover_image': resource.cover_images[0] if resource.cover_images else None,
                    'download_count': resource.download_count,
                    'collect_count': resource.collect_count,
                    'avg_rating': resource.avg_rating,
                })
        
        # 保存到缓存（5分钟）
        cache.set(cls.CACHE_KEY, index_data, 300)
        
        # 保存到文件（持久化）
        try:
            file_path = os.path.join(settings.BASE_DIR, cls.CACHE_FILE)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'保存向量索引失败: {e}')
        
        return index_data
    
    @classmethod
    def search(cls, query, limit=20):
        """语义搜索"""
        if not query:
            return []
        
        # 获取查询向量
        query_embedding = cls._get_embedding(query)
        if query_embedding is None:
            return []
        
        # 加载索引
        index_data = cache.get(cls.CACHE_KEY)
        if not index_data:
            # 尝试从文件加载
            try:
                file_path = os.path.join(settings.BASE_DIR, cls.CACHE_FILE)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
            except Exception as e:
                logger.error(f'加载索引文件失败: {e}')
        
        if not index_data:
            # 实时构建
            index_data = cls.build_index()
        
        if not index_data:
            return []
        
        # 计算相似度
        results = []
        for item in index_data:
            embedding = np.array(item['embedding'])
            similarity = cls._cosine_similarity(query_embedding, embedding)
            if similarity > 0.1:  # 阈值过滤
                results.append({
                    'id': item['id'],
                    'title': item['title'],
                    'similarity': similarity,
                    'price': item['price'],
                    'tags': item['tags'],
                    'grade': item['grade'],
                    'resource_type': item['resource_type'],
                    'uploader_name': item['uploader_name'],
                    'cover_image': item['cover_image'],
                    'download_count': item['download_count'],
                    'collect_count': item['collect_count'],
                    'avg_rating': item['avg_rating'],
                })
        
        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    @classmethod
    def rebuild_index(cls):
        """重建索引（后台管理用）"""
        cache.delete(cls.CACHE_KEY)
        return cls.build_index(force=True)