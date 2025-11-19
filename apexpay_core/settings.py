"""
Django settings for ApexPay-Core (production-ready for Render).
Compiled cleanly with dev-safe HTTPS settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# -----------------------------------------------------------------------------
# BASE + ENV LOADING
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_123")

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,0.0.0.0").split(",")
]

APPEND_SLASH = True

# -----------------------------------------------------------------------------
# INSTALLED APPS
# -----------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'accounts.apps.AccountsConfig',
    'transactions.apps.TransactionsConfig',
    'kyc.apps.KycConfig',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'corsheaders',
]

AUTH_USER_MODEL = 'accounts.User'

# -----------------------------------------------------------------------------
# MIDDLEWARE
# -----------------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # Whitenoise MUST be high in the list
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'apexpay_core.urls'

# -----------------------------------------------------------------------------
# TEMPLATES
# -----------------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'apexpay_core.wsgi.application'

# -----------------------------------------------------------------------------
# DATABASE (Render-compatible)
# -----------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# -----------------------------------------------------------------------------
# PASSWORD VALIDATION
# -----------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -----------------------------------------------------------------------------
# INTERNATIONALIZATION
# -----------------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# REST FRAMEWORK + JWT
# -----------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ]
}

LOGIN_REDIRECT_URL = '/docs'

# -----------------------------------------------------------------------------
# STATIC FILES (Whitenoise)
# -----------------------------------------------------------------------------

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -----------------------------------------------------------------------------
# SECURITY SETTINGS (SAFE FOR DEV + PRODUCTION CORRECT)
# -----------------------------------------------------------------------------

if DEBUG:
    # Local development (NO forced HTTPS)
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0   # prevent browser from forcing HTTPS
else:
    # Production (Render)
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", 31536000))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True").lower() in ("true", "1", "yes")
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "True").lower() in ("true", "1", "yes")

# -----------------------------------------------------------------------------
# EMAIL CONFIG (SMTP)
# -----------------------------------------------------------------------------

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or "no-reply@example.com"

# -----------------------------------------------------------------------------
# SITE DOMAIN FOR EMAIL LINKS
# -----------------------------------------------------------------------------

SITE_DOMAIN = os.getenv("SITE_DOMAIN", "http://127.0.0.1:8000")

# -----------------------------------------------------------------------------
# CORS / SWAGGER
# -----------------------------------------------------------------------------

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "https://apexpay-core.azurewebsites.net",
]

SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,
    "relative_paths": False,
    "DISPLAY_OPERATION_ID": False,
    "SECURITY_DEFINITIONS": {
        "Basic": {"type": "basic"},
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"},
        "Token": {"type": "apiKey", "name": "Authorization", "in": "header"},
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
