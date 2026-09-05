import os
import sys
from django.core.management.base import BaseCommand
from resources.vector_search import VectorSearch


class Command(BaseCommand):
    help = '手动重建向量索引'

    def handle(self, *args, **options):
        self.stdout.write('🔄 开始重建向量索引...')
        try:
            result = VectorSearch.rebuild_index()
            count = len(result) if result else 0
            self.stdout.write(self.style.SUCCESS(f'✅ 重建完成！共 {count} 个资源'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 重建失败: {e}'))