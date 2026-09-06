from django.conf import settings
import re


class TagService:
    """预设标签匹配服务"""
    
    @staticmethod
    def get_preset_tags(title, description=""):
        """
        根据标题和描述，通过关键词匹配推荐预设标签
        返回: list of tags
        """
        recommended_tags = set()
        text = (title + " " + description).lower()
        
        # 从 settings 中读取映射表
        keyword_map = getattr(settings, 'KEYWORD_TAG_MAP', {})
        
        for keyword, tags in keyword_map.items():
            # 精确匹配：确保关键词作为独立词出现，而不是部分匹配
            # 使用正则边界 \b 进行单词边界匹配
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text):
                for tag in tags:
                    recommended_tags.add(tag)
        
        return list(recommended_tags)
    
    @staticmethod
    def merge_with_ai_tags(preset_tags, ai_result):
        """
        合并预设标签和AI生成的标签，去重，限制数量
        """
        all_tags = set(preset_tags)
        
        if ai_result and 'tags' in ai_result:
            for tag in ai_result['tags']:
                all_tags.add(tag)
        
        # 限制最多5个标签
        return list(all_tags)[:5]