"""
Django settings for project project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]

# -------------------------------------------------------------------
# 基础路径
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
# 加载根目录 .env，确保数据库等环境变量在 manage.py 运行时可见
load_dotenv(BASE_DIR / ".env", override=False)

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
    "chatbot.middleware.JWTAuthMiddleware",
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
# 数据库：固定使用 MySQL（移除 SQLite 分支）
# -------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DJANGO_DB_NAME", "cyber_doctor"),
        "USER": os.getenv("DJANGO_DB_USER", "root"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", ""),
        "HOST": os.getenv("DJANGO_DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DJANGO_DB_PORT", "3306"),
        "OPTIONS": {"charset": os.getenv("DJANGO_DB_CHARSET", "utf8mb4")},
        "CONN_MAX_AGE": int(os.getenv("DJANGO_DB_CONN_MAX_AGE", "60")),
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
CSRF_TRUSTED_ORIGINS = _split_csv(os.getenv("CSRF_TRUSTED_ORIGINS")) or [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
]

CORS_ALLOW_CREDENTIALS = True
_allowed_origins = _split_csv(os.getenv("CORS_ALLOWED_ORIGINS"))
if _allowed_origins:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = _allowed_origins
else:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = []
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

# -------------------------------------------------------------------
# Session/Cookie 设置，保证与 AuthServer 同步
# -------------------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "sessionid")
SESSION_COOKIE_DOMAIN = os.getenv("SESSION_COOKIE_DOMAIN") or None
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

AUTH_SERVER_BASE_URL = os.getenv("AUTH_SERVER_BASE_URL", "http://127.0.0.1:8000")

# -------------------------------------------------------------------
# JWT （与 AuthServer 共用配置）
# -------------------------------------------------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "replace-me-with-a-secure-jwt-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_LIFETIME_MINUTES = int(os.getenv("ACCESS_TOKEN_LIFETIME_MINUTES", "60"))
REFRESH_TOKEN_LIFETIME_DAYS = int(os.getenv("REFRESH_TOKEN_LIFETIME_DAYS", "7"))
