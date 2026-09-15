# -*- coding: utf-8 -*-
"""评论表情包（自定义表情）解析与渲染服务。

评论内容中的自定义表情以 ``[sticker:<id>]`` 占位标记存储，
展示时统一通过 :func:`render_comment_html` 渲染为 <img>。
"""
import re
import time

from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

# 单条评论允许的最大自定义表情数量
MAX_STICKERS_PER_COMMENT = 9
# 表情包列表缓存时长（秒）
_STICKER_CACHE_TTL = 60

STICKER_TOKEN_RE = re.compile(r'\[sticker:(\d+)\]')

_sticker_cache = {'ts': 0, 'data': {}}


def get_sticker_map(force=False):
    """返回 {sticker_id: Sticker} 映射，带 60 秒进程内缓存。"""
    now = time.time()
    if not force and _sticker_cache['data'] and now - _sticker_cache['ts'] < _STICKER_CACHE_TTL:
        return _sticker_cache['data']

    from .models import Sticker

    data = {
        s.id: s
        for s in Sticker.objects.filter(is_active=True, pack__is_active=True).select_related('pack')
        if s.image
    }
    _sticker_cache['ts'] = now
    _sticker_cache['data'] = data
    return data


def clear_sticker_cache():
    """表情包变更后调用，立即失效缓存。"""
    _sticker_cache['ts'] = 0
    _sticker_cache['data'] = {}


def extract_sticker_ids(content):
    """提取内容中用到的自定义表情 id（去重，保持出现顺序）。"""
    if not content:
        return []
    ids = []
    for raw in STICKER_TOKEN_RE.findall(str(content)):
        sid = int(raw)
        if sid not in ids:
            ids.append(sid)
    return ids


def strip_sticker_tokens(content):
    """去掉表情占位标记，得到纯文本内容。"""
    if not content:
        return ''
    return re.sub(r'\s{2,}', ' ', STICKER_TOKEN_RE.sub(' ', str(content))).strip()


def plain_content(content, fallback='[表情]'):
    """用于通知/短信等纯文本场景的内容。"""
    text = strip_sticker_tokens(content)
    if text:
        return text
    return fallback if extract_sticker_ids(content) else ''


def render_comment_html(content):
    """把评论内容渲染为安全的 HTML（转义文本 + 表情图片 + 换行）。"""
    if not content:
        return ''

    content = str(content)
    sticker_ids = extract_sticker_ids(content)
    stickers = get_sticker_map() if sticker_ids else {}

    parts = []
    last = 0
    for match in STICKER_TOKEN_RE.finditer(content):
        parts.append(escape(content[last:match.start()]))
        sticker = stickers.get(int(match.group(1)))
        if sticker is not None:
            try:
                url = sticker.image.url
            except ValueError:
                url = ''
            if url:
                parts.append(format_html(
                    '<img class="comment-sticker" src="{}" alt="{}" title="{}" loading="lazy">',
                    url, sticker.name, sticker.name,
                ))
            else:
                parts.append(escape(match.group(0)))
        else:
            # 表情已被删除/停用，保留原文避免内容丢失
            parts.append(escape(match.group(0)))
        last = match.end()
    parts.append(escape(content[last:]))

    html = ''.join(parts).replace('\n', '<br>')
    return mark_safe(html)


def serialize_sticker_packs():
    """序列化启用中的表情包，供前端选择器使用。"""
    from .models import StickerPack

    packs = []
    for pack in StickerPack.objects.filter(is_active=True).order_by('sort_order', 'id'):
        stickers = []
        for sticker in pack.stickers.filter(is_active=True).order_by('sort_order', 'id'):
            if not sticker.image:
                continue
            try:
                url = sticker.image.url
            except ValueError:
                continue
            stickers.append({
                'id': sticker.id,
                'name': sticker.name,
                'url': url,
                'token': sticker.token,
            })
        if stickers:
            packs.append({
                'id': pack.id,
                'name': pack.name,
                'icon': pack.icon,
                'stickers': stickers,
            })
    return packs
