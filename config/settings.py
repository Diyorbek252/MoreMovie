"""
MORE-MOVIE — Django sozlamalari.

Maxfiy qiymatlar (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_URL) kodda emas,
loyiha ildizidagi `.env` faylida saqlanadi. Namuna uchun `.env.example` ga qarang.

Django 6.1 / Python 3.14
"""

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# .env faylini o'qiymiz. Fayl bo'lmasa ham xato bermaydi — u holda qiymatlar
# operatsion tizim muhitidan olinadi (production / CI uchun qulay).
load_dotenv(BASE_DIR / ".env")


def env(key, default=""):
    """Muhit o'zgaruvchisini matn sifatida qaytaradi."""
    return os.environ.get(key, default)


def env_bool(key, default=False):
    """'True', 'yes', '1', 'on' kabi qiymatlarni bool ga aylantiradi."""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(key, default=None):
    """Vergul bilan ajratilgan qatorni Python ro'yxatiga aylantiradi."""
    value = os.environ.get(key, "")
    if not value.strip():
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Asosiy xavfsizlik sozlamalari
# ---------------------------------------------------------------------------

SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY topilmadi. Loyiha ildizida .env fayli borligini tekshiring "
        "(.env.example dan nusxa oling)."
    )

DEBUG = env_bool("DEBUG", False)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Loyiha brendi — kontekst protsessori orqali barcha shablonlarga uzatiladi.
SITE_NAME = env("SITE_NAME", "MORE-MOVIE")
SITE_TAGLINE = env("SITE_TAGLINE", "Cheksiz kino zavqi...")


# ---------------------------------------------------------------------------
# Ilovalar
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
    # Loyiha ilovalari
    "core.apps.CoreConfig",
    "users.apps.UsersConfig",
    "movies.apps.MoviesConfig",
    "reviews.apps.ReviewsConfig",
    "dashboard.apps.DashboardConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise production'da statik fayllarni Django orqali xizmat qiladi.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Admin bloklagan foydalanuvchini darhol tizimdan chiqaradi.
    "users.middleware.BlockedUserMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Sayt nomi, slogan, navbar janrlari, foydalanuvchi to'plamlari.
                "core.context_processors.site_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ---------------------------------------------------------------------------
# Ma'lumotlar bazasi
# DATABASE_URL bo'sh bo'lsa SQLite. To'ldirilsa PostgreSQL — kod o'zgarmaydi.
# ---------------------------------------------------------------------------

DATABASE_URL = env("DATABASE_URL").strip()

if DATABASE_URL:
    _url = urlparse(DATABASE_URL)
    _engines = {
        "postgres": "django.db.backends.postgresql",
        "postgresql": "django.db.backends.postgresql",
        "mysql": "django.db.backends.mysql",
        "sqlite": "django.db.backends.sqlite3",
    }
    DATABASES = {
        "default": {
            "ENGINE": _engines.get(_url.scheme, "django.db.backends.postgresql"),
            "NAME": unquote(_url.path).lstrip("/"),
            "USER": unquote(_url.username or ""),
            "PASSWORD": unquote(_url.password or ""),
            "HOST": _url.hostname or "",
            "PORT": str(_url.port or ""),
            "CONN_MAX_AGE": 600,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ---------------------------------------------------------------------------
# Autentifikatsiya
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    # Foydalanuvchi username YOKI email bilan kira oladi.
    "users.backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

# "Remember me" belgilangan bo'lsa sessiya 2 hafta yashaydi, aks holda
# brauzer yopilganda tugaydi (LoginView da set_expiry bilan boshqariladi).
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# ---------------------------------------------------------------------------
# Xalqarolashtirish
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Statik va media fayllar
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # Development'da oddiy storage — manifest xatolari bezovta qilmaydi.
        # Production'da siqilgan + hashlangan fayllar (uzoq muddatli kesh).
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

# Yuklanadigan fayl hajmi chegarasi (poster / backdrop / avatar uchun yetarli).
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB


# ---------------------------------------------------------------------------
# Keshlash — bosh sahifa bo'limlari uchun
# ---------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "more-movie-cache",
        "TIMEOUT": 300,
    }
}


# ---------------------------------------------------------------------------
# Email (Django 6.x MAILERS sintaksisi)
# Development'da xatlar terminalga chiqadi — parol tiklash havolasi shu yerda.
# ---------------------------------------------------------------------------

MAILERS = {
    "default": {
        "BACKEND": (
            "django.core.mail.backends.console.EmailBackend"
            if DEBUG
            else "django.core.mail.backends.smtp.EmailBackend"
        ),
        "HOST": env("EMAIL_HOST", "localhost"),
        "PORT": int(env("EMAIL_PORT", "587") or 587),
        "USERNAME": env("EMAIL_HOST_USER"),
        "PASSWORD": env("EMAIL_HOST_PASSWORD"),
        "USE_TLS": env_bool("EMAIL_USE_TLS", True),
    },
}

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "MORE-MOVIE <no-reply@more-movie.uz>")


# ---------------------------------------------------------------------------
# Boshqa
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# Sahifalash: bir sahifadagi kartalar soni (grid 2/3/4/6 ustunga bo'linadi).
MOVIES_PER_PAGE = 24


# ---------------------------------------------------------------------------
# Production xavfsizligi — faqat DEBUG=False bo'lganda yoqiladi
# ---------------------------------------------------------------------------

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 yil
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    # Reverse proxy (nginx / Render / Railway) orqasida HTTPS ni aniqlash.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
