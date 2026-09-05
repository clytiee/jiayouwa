import json
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class AIService:
    """AI 服务（智谱 GLM）"""
    
    API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
    
    @classmethod
    def _get_headers(cls):
        """获取请求头"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.ZHIPU_API_KEY}'
        }
    
    @classmethod
    def generate_resource_tags(cls, title, description=''):
        """
        根据资源标题和描述，生成标签、年级、资源类型
        返回: {'tags': [...], 'grade': '...', 'resource_type': '...'}
        """
        if not settings.ZHIPU_API_KEY:
            logger.warning('ZHIPU_API_KEY 未配置，跳过 AI 标签生成')
            return None
        
        prompt = f"""
你是一个教育学习资源分类专家。请根据以下资源信息，生成分类标签。

资源标题：{title}
资源描述：{description}

请按以下 JSON 格式返回：
{{
    "tags": ["标签1", "标签2", "标签3"],  // 3-5个关键词标签
    "grade": "小学" | "初中" | "高中",    // 根据内容判断
    "resource_type": "视频" | "文档" | "网站" | "APP" | "教具" | "其他"
}}

只返回 JSON，不要有其他内容。
"""
        
        try:
            response = requests.post(
                cls.API_URL,
                headers=cls._get_headers(),
                json={
                    'model': 'glm-4-flash',
                    'messages': [
                        {'role': 'system', 'content': '你是一个教育学习资源分类专家，请根据资源信息生成准确的分类标签。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 200,
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                # 提取 JSON
                content = content.strip()
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                data = json.loads(content)
                # 验证必填字段
                if 'tags' in data and 'grade' in data and 'resource_type' in data:
                    # 限制标签数量
                    data['tags'] = data['tags'][:5]
                    # 验证 grade 取值范围
                    valid_grades = ['小学', '初中', '高中']
                    if data['grade'] not in valid_grades:
                        data['grade'] = ''
                    # 验证 resource_type
                    valid_types = ['视频', '文档', '网站', 'APP', '教具', '其他']
                    if data['resource_type'] not in valid_types:
                        data['resource_type'] = ''
                    return data
                else:
                    logger.error(f'AI 返回格式不正确: {data}')
                    return None
            else:
                logger.error(f'AI API 请求失败: {response.status_code}, {response.text}')
                return None
                
        except requests.exceptions.Timeout:
            logger.error('AI API 请求超时')
            return None
        except json.JSONDecodeError as e:
            logger.error(f'AI 返回 JSON 解析失败: {e}, content: {content}')
            return None
        except Exception as e:
            logger.error(f'AI 服务异常: {e}')
            return None