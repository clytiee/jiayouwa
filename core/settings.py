import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥（生产环境务必从环境变量读取）
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-please-change-in-production')

# 调试模式（生产环境必须关闭）
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# 应用注册
INSTALLED_APPS = [
    # Django 默认
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 第三方
    'django_htmx',
    
    # 自定义应用
    'users.apps.UsersConfig',
    'resources.apps.ResourcesConfig',
    'recommendations.apps.RecommendationsConfig',
    'transactions.apps.TransactionsConfig',
    'notifications.apps.NotificationsConfig',
    'shares.apps.SharesConfig',
    'contact.apps.ContactConfig',
]

# 中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',  # htmx 支持
]

ROOT_URLCONF = 'core.urls'

# 模板配置
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.unread_notification_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# 数据库（SQLite，后期可迁PostgreSQL）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 密码验证
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 国际化
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# 静态文件
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 媒体文件
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 默认主键
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 自定义用户模型
AUTH_USER_MODEL = 'users.User'

# 认证后端（支持用户名/邮箱登录）
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# 登录/登出重定向
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# 邮件配置（开发阶段用控制台输出，生产环境配置SMTP）
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# 生产环境示例（以阿里云邮件推送为例）：
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.126.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'celavi@126.com'
EMAIL_HOST_PASSWORD = 'VF85NxKT2RbLz6XB'
DEFAULT_FROM_EMAIL = 'celavi@126.com'

# Redis配置（在线推荐用）
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# 系统默认设置（可通过管理后台修改）
DEFAULT_SETTINGS = {
    'oil_daily_login': 1,
    'oil_register_bonus': 10,
    'oil_share_click': 1,
    'oil_share_register': 5,
    'oil_share_download': 1,
    'oil_upvote_reward': 1,
    'oil_collect_reward': 1,
    'oil_comment_up_reward': 1,
    'oil_price_min': 0,
    'oil_price_max': 10,
    'free_trial_enabled': True,
}

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'recommendations': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}

# ===== 用户等级配置 =====
LEVELS = [
    {'level': 1, 'title': '小蝌蚪', 'exp_required': 0},
    {'level': 2, 'title': '小青蛙', 'exp_required': 30},
    {'level': 3, 'title': '跳跳蛙', 'exp_required': 80},
    {'level': 4, 'title': '探险蛙', 'exp_required': 160},
    {'level': 5, 'title': '学霸蛙', 'exp_required': 280},
    {'level': 6, 'title': '智慧蛙', 'exp_required': 450},
    {'level': 7, 'title': '领航蛙', 'exp_required': 680},
    {'level': 8, 'title': '传奇蛙', 'exp_required': 1000},
    {'level': 9, 'title': '蛙博士', 'exp_required': 1500},
    {'level': 10, 'title': '加油蛙王', 'exp_required': 2200},
]

# ===== AI 配置 =====
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY', '')

# ===== 邀请码配置 =====
HASHIDS_SALT = 'jiayouwa_invite_salt_2024'  # 生产环境请改成一个复杂的字符串
HASHIDS_MIN_LENGTH = 6

# ===== 关键词 -> 推荐标签 映射表（预设优先，AI补充） =====
KEYWORD_TAG_MAP = {
    # ===== 英语启蒙 =====
    'phonics': ['自然拼读', '英语启蒙'],
    '自然拼读': ['自然拼读', '英语启蒙'],
    '牛津拼读': ['自然拼读', '英语启蒙'],
    '牛津树': ['分级读物', '英语启蒙'],
    'Oxford Reading Tree': ['分级读物', '原版教材'],
    'RAZ': ['分级读物', '英语阅读'],
    'raz': ['分级读物', '英语阅读'],
    '海尼曼': ['分级读物'],
    '培生': ['分级读物'],
    '红火箭': ['分级读物'],
    '大猫': ['分级读物'],
    '饼干狗': ['分级读物'],
    '分级读物': ['分级读物', '英语阅读'],
    '英语绘本': ['原版绘本', '英语阅读'],
    '绘本': ['原版绘本', '英语阅读'],
    'picture book': ['原版绘本', '英语阅读'],
    '桥梁书': ['桥梁书', '英语阅读'],
    '章节书': ['章节书', '英语阅读'],
    'Magic Tree House': ['章节书', '英语阅读'],
    '神奇树屋': ['章节书', '英语阅读'],
    '哈利波特': ['章节书', '英语阅读'],
    'Harry Potter': ['章节书', '英语阅读'],
    '原版教材': ['原版教材', '英语阅读'],
    'unlock': ['原版教材', '英语阅读'],
    'think': ['原版教材', '英语阅读'],
    'power up': ['原版教材', '英语阅读'],
    
    # ===== 英语影视 =====
    '0-3岁': ['0-3岁动画', '英语启蒙'],
    '3-6岁': ['3-6岁动画', '英语启蒙'],
    '6岁以上': ['6岁以上动画', '英语影视'],
    '儿童英语电影': ['儿童英语电影', '英语影视'],
    '英语动画': ['英语动画', '英语影视'],
    'peppa pig': ['3-6岁动画', '英语启蒙'],
    '小猪佩奇': ['3-6岁动画', '英语启蒙'],
    '蓝色小考拉': ['3-6岁动画', '英语启蒙'],
    '小鼠波波': ['3-6岁动画', '英语启蒙'],
    'maisy': ['3-6岁动画', '英语启蒙'],
    '英语纪录片': ['英语纪录片', '英语影视'],
    'bbc': ['BBC广播', '英语启蒙'],
    '英语儿歌': ['英文歌曲童谣', '英语启蒙'],
    'super simple songs': ['英文歌曲童谣', '英语启蒙'],
    
    # ===== STEM =====
    'stem': ['STEM', '科学'],
    'steam': ['STEAM', '科学'],
    '科学': ['自然科学', 'STEAM'],
    '数学': ['数学与思维', 'STEAM'],
    '数学思维': ['数学与思维', 'STEAM'],
    '奥数': ['数学与思维', '中小学教育'],
    '编程': ['儿童编程', 'STEAM'],
    'scratch': ['儿童编程', 'STEAM'],
    'python': ['儿童编程', 'STEAM'],
    '机器人': ['创意&工程', 'STEAM'],
    '乐高': ['创意&工程', 'STEAM'],
    'lego': ['创意&工程', 'STEAM'],
    '艺术': ['儿童艺术', 'STEAM'],
    '美术': ['儿童艺术', 'STEAM'],
    
    # ===== 中文阅读 =====
    '国学': ['经典国学', '中文阅读'],
    '弟子规': ['经典国学', '中文阅读'],
    '三字经': ['经典国学', '中文阅读'],
    '论语': ['经典国学', '中文阅读'],
    '古诗': ['经典国学', '中文阅读'],
    '唐诗': ['经典国学', '中文阅读'],
    '宋词': ['经典国学', '中文阅读'],
    '成语': ['经典国学', '中文阅读'],
    '中文绘本': ['中文原版阅读', '中文阅读'],
    '中文阅读': ['中文原版阅读', '中文阅读'],
    '文学': ['文学阅读', '中文阅读'],
    '小说': ['文学阅读', '中文阅读'],
    '四大名著': ['文学阅读', '中文阅读'],
    '历史': ['地理&历史', '中文阅读'],
    '地理': ['地理&历史', '中文阅读'],
    '哲学': ['哲学启蒙', '中文阅读'],
    
    # ===== 中小学教育 =====
    '幼儿园': ['幼儿园', '中小学教育'],
    '学前': ['幼儿园', '中小学教育'],
    '幼小衔接': ['幼儿园', '中小学教育'],
    '一年级': ['小学', '中小学教育'],
    '二年级': ['小学', '中小学教育'],
    '三年级': ['小学', '中小学教育'],
    '四年级': ['小学', '中小学教育'],
    '五年级': ['小学', '中小学教育'],
    '六年级': ['小学', '中小学教育'],
    '小学': ['小学', '中小学教育'],
    '初一': ['中学', '中小学教育'],
    '初二': ['中学', '中小学教育'],
    '初三': ['中学', '中小学教育'],
    '高一': ['中学', '中小学教育'],
    '高二': ['中学', '中小学教育'],
    '高三': ['中学', '中小学教育'],
    '初中': ['中学', '中小学教育'],
    '高中': ['中学', '中小学教育'],
    '中考': ['中学', '小升初'],
    '高考': ['中学', '中小学教育'],
    '小升初': ['小升初', '中小学教育'],
    
    # ===== 其他语种 =====
    '法语': ['儿童法语', '其他语种'],
    'french': ['儿童法语', '其他语种'],
    '德语': ['儿童德语', '其他语种'],
    'german': ['儿童德语', '其他语种'],
    '西班牙语': ['儿童西班牙语', '其他语种'],
    'spanish': ['儿童西班牙语', '其他语种'],
    '日语': ['儿童日语', '其他语种'],
    'japanese': ['儿童日语', '其他语种'],
    '韩语': ['儿童韩语', '其他语种'],
    'korean': ['儿童韩语', '其他语种'],
    
    # ===== 考试/考级 =====
    'ket': ['考级&大赛类', '英语启蒙'],
    'pet': ['考级&大赛类', '英语启蒙'],
    'fce': ['考级&大赛类', '英语启蒙'],
    '雅思': ['考级&大赛类', '英语启蒙'],
    'toefl': ['考级&大赛类', '英语启蒙'],
    '托福': ['考级&大赛类', '英语启蒙'],
    '剑桥': ['考级&大赛类', '英语启蒙'],
    
    # ===== 科普/百科 =====
    '科普': ['自然科普', '儿童英语阅读'],
    '百科': ['自然科普', '儿童英语阅读'],
    '动物': ['自然科普', '儿童英语阅读'],
    '植物': ['自然科普', '儿童英语阅读'],
    '宇宙': ['自然科普', '儿童英语阅读'],
    '恐龙': ['自然科普', '儿童英语阅读'],
    'dinosaur': ['自然科普', '儿童英语阅读'],
    '人体': ['自然科普', '儿童英语阅读'],
    '地理': ['地理和历史', '儿童英语阅读'],

    # ===== 新增映射 =====
    '课件': ['课件', '教学资源'],
    'PPT': ['课件', '教学资源'],
    '电子书': ['电子书', '英语阅读'],
    'ebook': ['电子书', '英语阅读'],
    '音视频': ['音视频资源', '英语启蒙'],
    '音频': ['音视频资源', '英语启蒙'],
    '视频': ['音视频资源', '英语启蒙'],
    '少儿英语': ['少儿英语', '英语启蒙'],
    '外研社': ['原版教材', '英语阅读'],
    '外研': ['原版教材', '英语阅读'],
    'Power Up': ['原版教材', '英语阅读'],
    '新动力': ['原版教材', '英语阅读'],
}
