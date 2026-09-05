import os
import django
import random
from datetime import datetime, timedelta

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from resources.models import Resource

User = get_user_model()

# 测试数据
RESOURCES = [
    # ===== 小学 =====
    {
        'title': 'Batch 2: 10分钟搞定一年级退位减法',
        'description': '一套针对一年级学生的退位减法练习册，包含20页趣味练习题，帮助孩子轻松掌握退位减法技巧。',
        'tags': ['数学', '一年级', '减法', '练习册'],
        'grade': '小学',
        'resource_type': '文档',
        'price': 3,
        'view_count': 230,
        'download_count': 45,
        'collect_count': 128,
        'upvote_count': 18,
        'downvote_count': 2,
        'avg_rating': 3.2,
    },
    {
        'title': 'Batch 2: 小学英语自然拼读全套视频课程',
        'description': '26个英文字母自然拼读视频，每个字母一个视频，包含发音示范和常见单词举例，适合幼儿园到二年级。',
        'tags': ['英语', '自然拼读', '视频', '启蒙'],
        'grade': '小学',
        'resource_type': '视频',
        'price': 5,
        'view_count': 180,
        'download_count': 32,
        'collect_count': 89,
        'upvote_count': 12,
        'downvote_count': 1,
        'avg_rating': 3.8,
    },
    {
        'title': 'Batch 2: 三年级作文思维导图模板合集',
        'description': '12个作文主题的思维导图模板，涵盖写人、写事、写景、状物等类型，帮助孩子理清写作思路。',
        'tags': ['语文', '作文', '三年级', '思维导图'],
        'grade': '小学',
        'resource_type': '文档',
        'price': 2,
        'view_count': 310,
        'download_count': 78,
        'collect_count': 156,
        'upvote_count': 25,
        'downvote_count': 3,
        'avg_rating': 3.6,
    },
    {
        'title': 'Batch 2: 小学数学思维训练100题（三年级）',
        'description': '精选100道数学思维训练题，涵盖逻辑推理、空间想象、规律探索等题型，培养孩子的数学思维能力。',
        'tags': ['数学', '思维训练', '三年级', '奥数'],
        'grade': '小学',
        'resource_type': '文档',
        'price': 4,
        'view_count': 420,
        'download_count': 95,
        'collect_count': 203,
        'upvote_count': 32,
        'downvote_count': 4,
        'avg_rating': 4.0,
    },
    {
        'title': 'Batch 2: 小学必背古诗词75首 音频+注释',
        'description': '新课标小学必背古诗词75首，每首附带音频朗读、注释赏析和思维导图，适合背诵和预习。',
        'tags': ['语文', '古诗词', '小学', '音频'],
        'grade': '小学',
        'resource_type': '视频',
        'price': 0,
        'view_count': 560,
        'download_count': 120,
        'collect_count': 280,
        'upvote_count': 45,
        'downvote_count': 2,
        'avg_rating': 4.5,
    },
    {
        'title': 'Batch 2: 一年级拼音卡片打印版',
        'description': '声母、韵母、整体认读音节全套拼音卡片，可打印裁剪，在家就能玩的拼音学习游戏。',
        'tags': ['语文', '拼音', '一年级', '卡片'],
        'grade': '小学',
        'resource_type': '文档',
        'price': 0,
        'view_count': 340,
        'download_count': 86,
        'collect_count': 145,
        'upvote_count': 20,
        'downvote_count': 1,
        'avg_rating': 4.2,
    },
    {
        'title': 'Batch 2: 小学英语词汇表（含音频）',
        'description': 'PEP小学英语3-6年级词汇表，按年级分类，包含单词、音标、中文释义和真人发音音频。',
        'tags': ['英语', '词汇', '小学', '音频'],
        'grade': '小学',
        'resource_type': '网站',
        'price': 1,
        'view_count': 280,
        'download_count': 56,
        'collect_count': 98,
        'upvote_count': 15,
        'downvote_count': 2,
        'avg_rating': 3.4,
    },
    
    # ===== 初中 =====
    {
        'title': 'Batch 2: 初中数学公式大全（可打印）',
        'description': '初中三年数学所有公式、定理汇总，按年级和章节分类，适合考前速记和日常查阅。',
        'tags': ['数学', '公式', '初中', '复习'],
        'grade': '初中',
        'resource_type': '文档',
        'price': 2,
        'view_count': 350,
        'download_count': 72,
        'collect_count': 168,
        'upvote_count': 22,
        'downvote_count': 3,
        'avg_rating': 3.7,
    },
    {
        'title': 'Batch 2: 中考英语满分作文模板',
        'description': '10种中考英语作文题型的万能模板，包含开头、结尾、过渡句和范文，轻松搞定英语作文。',
        'tags': ['英语', '作文', '中考', '模板'],
        'grade': '初中',
        'resource_type': '文档',
        'price': 3,
        'view_count': 460,
        'download_count': 98,
        'collect_count': 215,
        'upvote_count': 35,
        'downvote_count': 5,
        'avg_rating': 3.9,
    },
    {
        'title': 'Batch 2: 初中物理实验视频合集',
        'description': '初中物理全部核心实验视频，包含声、光、热、力、电五大板块，每个实验都有详细讲解。',
        'tags': ['物理', '实验', '初中', '视频'],
        'grade': '初中',
        'resource_type': '视频',
        'price': 5,
        'view_count': 190,
        'download_count': 28,
        'collect_count': 67,
        'upvote_count': 10,
        'downvote_count': 1,
        'avg_rating': 3.6,
    },
    {
        'title': 'Batch 2: 初中化学方程式汇总表',
        'description': '初中化学所有化学反应方程式汇总，按物质类型分类，附带记忆口诀和易错点提醒。',
        'tags': ['化学', '方程式', '初中', '复习'],
        'grade': '初中',
        'resource_type': '文档',
        'price': 1,
        'view_count': 220,
        'download_count': 45,
        'collect_count': 76,
        'upvote_count': 12,
        'downvote_count': 2,
        'avg_rating': 3.2,
    },
    {
        'title': 'Batch 2: 初中语文阅读理解答题技巧',
        'description': '记叙文、说明文、议论文三大文体阅读理解答题技巧，含常见题型和万能答题模板。',
        'tags': ['语文', '阅读理解', '初中', '技巧'],
        'grade': '初中',
        'resource_type': '文档',
        'price': 2,
        'view_count': 380,
        'download_count': 82,
        'collect_count': 190,
        'upvote_count': 28,
        'downvote_count': 4,
        'avg_rating': 3.8,
    },
    
    # ===== 高中 =====
    {
        'title': 'Batch 2: 高中数学导数专题精讲（含真题）',
        'description': '导数专题系统讲解，含概念、公式、题型分类和近年高考真题解析，适合高三复习冲刺。',
        'tags': ['数学', '导数', '高中', '高考'],
        'grade': '高中',
        'resource_type': '文档',
        'price': 5,
        'view_count': 290,
        'download_count': 52,
        'collect_count': 134,
        'upvote_count': 18,
        'downvote_count': 3,
        'avg_rating': 3.5,
    },
    {
        'title': 'Batch 2: 高考英语阅读理解真题精讲（2020-2025）',
        'description': '近5年高考英语阅读理解真题精讲，含文章翻译、长难句分析和解题思路。',
        'tags': ['英语', '阅读理解', '高考', '真题'],
        'grade': '高中',
        'resource_type': '文档',
        'price': 4,
        'view_count': 410,
        'download_count': 88,
        'collect_count': 210,
        'upvote_count': 30,
        'downvote_count': 5,
        'avg_rating': 3.7,
    },
    {
        'title': 'Batch 2: 高中物理力学全套解题模型',
        'description': '高中物理力学10大经典模型，每个模型含原理讲解、典型例题和解题步骤，攻克力学难题。',
        'tags': ['物理', '力学', '高中', '模型'],
        'grade': '高中',
        'resource_type': '视频',
        'price': 6,
        'view_count': 160,
        'download_count': 22,
        'collect_count': 58,
        'upvote_count': 8,
        'downvote_count': 1,
        'avg_rating': 3.4,
    },
    {
        'title': 'Batch 2: 高中化学有机推断题突破',
        'description': '有机推断题系统突破，含官能团特征反应、合成路线推断、高频考点和真题演练。',
        'tags': ['化学', '有机', '高中', '推断'],
        'grade': '高中',
        'resource_type': '文档',
        'price': 3,
        'view_count': 200,
        'download_count': 38,
        'collect_count': 72,
        'upvote_count': 11,
        'downvote_count': 2,
        'avg_rating': 3.3,
    },
    {
        'title': 'Batch 2: 高中生物必修一全套思维导图',
        'description': '高中生物必修一全部章节思维导图，知识结构清晰，适合预习、复习和考前快速回顾。',
        'tags': ['生物', '思维导图', '高中', '必修一'],
        'grade': '高中',
        'resource_type': '文档',
        'price': 2,
        'view_count': 330,
        'download_count': 70,
        'collect_count': 155,
        'upvote_count': 20,
        'downvote_count': 3,
        'avg_rating': 3.6,
    },
    {
        'title': 'Batch 2: 高中语文作文素材库（含时评）',
        'description': '2024-2025年最新时评素材、热点人物、经典名句分类整理，作文素材随时查阅。',
        'tags': ['语文', '作文', '素材', '高中'],
        'grade': '高中',
        'resource_type': '网站',
        'price': 0,
        'view_count': 450,
        'download_count': 110,
        'collect_count': 260,
        'upvote_count': 38,
        'downvote_count': 4,
        'avg_rating': 4.1,
    },
    {
        'title': 'Batch 2: 高中政治必修四哲学原理总结',
        'description': '马克思主义哲学全部原理总结，含唯物论、辩证法、认识论、历史唯物主义核心知识点。',
        'tags': ['政治', '哲学', '高中', '必修四'],
        'grade': '高中',
        'resource_type': '文档',
        'price': 1,
        'view_count': 150,
        'download_count': 25,
        'collect_count': 45,
        'upvote_count': 6,
        'downvote_count': 0,
        'avg_rating': 4.0,
    },
]

# 覆盖图（占位图片URL）
PLACEHOLDER_IMAGES = [
    '/static/images/placeholder1.jpg',
    '/static/images/placeholder2.jpg',
    '/static/images/placeholder3.jpg',
]


def create_test_data():
    # 获取第一个活跃用户作为上传者
    user = User.objects.filter(is_active=True).first()
    if not user:
        print('❌ 请先创建一个用户！')
        return
    
    print(f'👤 上传者: {user.username}')
    print(f'📦 准备生成 {len(RESOURCES)} 个资源...')
    
    created = 0
    for i, data in enumerate(RESOURCES):
        # 随机生成创建时间（最近30天内）
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        created_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
        
        # 随机选择1-3张封面图
        num_images = random.randint(1, 3)
        cover_images = random.sample(PLACEHOLDER_IMAGES, num_images)
        
        resource = Resource.objects.create(
            title=data['title'],
            description=data['description'],
            tags=data['tags'],
            grade=data['grade'],
            resource_type=data['resource_type'],
            cover_images=cover_images,
            download_url=f'https://example.com/resource_{i+1}.pdf',
            price=data['price'],
            uploader=user,
            status='published',
            view_count=data['view_count'],
            download_count=data['download_count'],
            collect_count=data['collect_count'],
            upvote_count=data['upvote_count'],
            downvote_count=data['downvote_count'],
            avg_rating=data['avg_rating'],
            created_at=created_at,
            ai_tags_generated=True,
        )
        created += 1
        print(f'  ✅ {i+1}. {data["title"][:30]}... ({data["grade"]} · {data["resource_type"]})')
    
    print(f'\n🎉 成功生成 {created} 个测试资源！')
    print('💡 访问首页查看效果')


if __name__ == '__main__':
    create_test_data()