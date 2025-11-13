"""
Django settings for project project.
"""

from pathlib import Path
import os

# -------------------------------------------------------------------
# 基础路径
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------
# 安全 & 调试
# -------------------------------------------------------------------
# 本地开发使用你原来的 key 即可；上线务必放到环境变量里
SECRET_KEY = "django-insecure-e6m8$pc-^#owrn)_26u5e5@n&)x%$gj%rm*&=+0e#@un^zx05#"

# 本地开发打开 DEBUG，上线请改为 False
DEBUG = True

# 本地仅允许本机访问；若需要局域网调试可加上机器内网 IP
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# -------------------------------------------------------------------
# 应用
# -------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 第三方
    "corsheaders",
    "rest_framework",

    # 你的应用
    "chatbot",
]

# -------------------------------------------------------------------
# 中间件（corsheaders 需置于 CommonMiddleware 之前）
# -------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",   # 位置必须在这里
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"

# -------------------------------------------------------------------
# 模板
# -------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

# -------------------------------------------------------------------
# 数据库：本地默认 SQLite；如需连远端 MySQL，设置环境变量 DJANGO_USE_SQLITE=0
# -------------------------------------------------------------------
USE_SQLITE = os.getenv("DJANGO_USE_SQLITE", "1") == "1"

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DJANGO_DB_NAME", "cyber_doctor"),
            "USER": os.getenv("DJANGO_DB_USER", "root"),
            "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", "123456"),
            "HOST": os.getenv("DJANGO_DB_HOST", "114.215.183.142"),
            "PORT": os.getenv("DJANGO_DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }

# -------------------------------------------------------------------
# 密码校验
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------------------------------------------------
# 国际化
# -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tokyo"   # 你在日本，本地开发更直观；需要可改回 UTC
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# 静态文件
# -------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
# 若需要 collectstatic，可设置：
# STATIC_ROOT = BASE_DIR / "staticfiles"

# -------------------------------------------------------------------
# 默认主键类型
# -------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------
# CORS（开发期全放开，生产请按域名精确配置）
# -------------------------------------------------------------------
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = ["*"]

# -------------------------------------------------------------------
# DRF（可按需调整）
# -------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

# -------------------------------------------------------------------
# 缓存：本地用内存缓存，避免未启动 Redis 报错
# -------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "local-cache",
    }
}