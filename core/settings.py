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
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# 生产环境示例（以阿里云邮件推送为例）：
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.aliyun.com'
# EMAIL_PORT = 465
# EMAIL_USE_SSL = True
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

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
