# -*- coding: utf-8 -*-
"""生成一批内置示例表情包，便于首次体验评论表情包功能。

用法：
    python manage.py seed_stickers
    python manage.py seed_stickers --pack 加油蛙 --overwrite
"""
import io
import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from resources.models import Sticker, StickerPack
from resources.sticker_service import clear_sticker_cache

# (表情名称, 用于绘制的 emoji 字形)
DEFAULT_STICKERS = [
    ('加油', '💪'),
    ('真棒', '👍'),
    ('学到了', '📚'),
    ('谢谢', '🙏'),
    ('开心', '😄'),
    ('点赞', '🔥'),
    ('抱抱', '🤗'),
    ('加油哇', '🐸'),
    ('笔芯', '❤️'),
    ('收到', '👌'),
    ('鼓掌', '👏'),
    ('收藏', '⭐'),
]

BACKGROUNDS = [
    (240, 253, 244),
    (254, 249, 195),
    (239, 246, 255),
    (253, 242, 248),
]

EMOJI_FONT_CANDIDATES = [
    r'C:\Windows\Fonts\seguiemj.ttf',
    '/System/Library/Fonts/Apple Color Emoji.ttc',
    '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',
]
FALLBACK_FONT_CANDIDATES = [
    r'C:\Windows\Fonts\msyhbd.ttc',
    r'C:\Windows\Fonts\msyh.ttc',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
]

SIZE = 240


def _first_existing(paths):
    for path in paths:
        if os.path.exists(path):
            return path
    return None


class Command(BaseCommand):
    help = '生成内置示例表情包（画成 PNG 并写入数据库）'

    def add_arguments(self, parser):
        parser.add_argument('--pack', default='加油蛙表情', help='表情包分组名称')
        parser.add_argument('--overwrite', action='store_true', help='同名表情重新生成图片')

    def handle(self, *args, **options):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            self.stderr.write(self.style.ERROR('需要安装 Pillow：pip install Pillow'))
            return

        emoji_font_path = _first_existing(EMOJI_FONT_CANDIDATES)
        text_font_path = _first_existing(FALLBACK_FONT_CANDIDATES)

        pack, _ = StickerPack.objects.get_or_create(
            name=options['pack'],
            defaults={'icon': '🐸', 'sort_order': 0},
        )

        created, skipped = 0, 0
        with transaction.atomic():
            for index, (name, glyph) in enumerate(DEFAULT_STICKERS):
                existing = pack.stickers.filter(name=name).first()
                if existing and not options['overwrite']:
                    skipped += 1
                    continue

                buffer = self._render(Image, ImageDraw, ImageFont, glyph, name,
                                      BACKGROUNDS[index % len(BACKGROUNDS)],
                                      emoji_font_path, text_font_path, index)
                if buffer is None:
                    self.stderr.write(self.style.WARNING(f'跳过「{name}」：没有可用字体'))
                    continue

                sticker = existing or Sticker(pack=pack, name=name)
                sticker.pack = pack
                sticker.sort_order = index
                sticker.is_active = True
                sticker.image.save(f'seed_{index}.png', ContentFile(buffer.getvalue()), save=False)
                sticker.save()
                created += 1

        clear_sticker_cache()
        self.stdout.write(self.style.SUCCESS(
            f'✅ 表情包「{pack.name}」生成完成：新增/更新 {created} 个，跳过 {skipped} 个'
        ))

    def _render(self, Image, ImageDraw, ImageFont, glyph, name, background,
                emoji_font_path, text_font_path, index):
        canvas = Image.new('RGB', (SIZE, SIZE), background)
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle([8, 8, SIZE - 8, SIZE - 8], radius=36,
                               outline=(203, 213, 225), width=3)

        if emoji_font_path:
            try:
                font = ImageFont.truetype(emoji_font_path, 120)
                draw.text((SIZE // 2, SIZE // 2 - 24), glyph, font=font,
                          anchor='mm', embedded_color=True)
                self._draw_label(draw, ImageFont, name, text_font_path)
                return self._to_png(Image, canvas)
            except Exception:
                pass

        # 降级：用普通字体绘制文字
        if text_font_path:
            try:
                font = ImageFont.truetype(text_font_path, 72)
                label = name[:2]
                draw.text((SIZE // 2, SIZE // 2 - 20), label, font=font,
                          anchor='mm', fill=(21, 128, 61))
                self._draw_label(draw, ImageFont, name, text_font_path)
                return self._to_png(Image, canvas)
            except Exception:
                return None
        return None

    def _draw_label(self, draw, ImageFont, name, text_font_path):
        if not text_font_path:
            return
        try:
            small = ImageFont.truetype(text_font_path, 28)
            draw.text((SIZE // 2, SIZE - 40), name, font=small,
                      anchor='mm', fill=(107, 114, 128))
        except Exception:
            pass

    def _to_png(self, Image, canvas):
        buffer = io.BytesIO()
        canvas.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        return buffer
