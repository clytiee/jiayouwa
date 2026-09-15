# -*- coding: utf-8 -*-
"""评论相关的模板过滤器 / 标签。"""
from django import template

from ..sticker_service import plain_content, render_comment_html

register = template.Library()


@register.filter(name='render_comment', is_safe=True)
def render_comment(content):
    """渲染评论内容：转义文本 + 自定义表情图片 + 换行。"""
    return render_comment_html(content)


@register.filter(name='comment_plain')
def comment_plain(content):
    """评论的纯文本形式（去掉表情标记），用于 title / 摘要。"""
    return plain_content(content, fallback='[表情]')
