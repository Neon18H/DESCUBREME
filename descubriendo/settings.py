import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'descubriendo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
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

WSGI_APPLICATION = 'descubriendo.wsgi.application'


def parse_database_url(url: str):
    parsed = urlparse(url)
    if parsed.scheme not in ['postgres', 'postgresql']:
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': parsed.path.lstrip('/'),
        'USER': parsed.username,
        'PASSWORD': parsed.password,
        'HOST': parsed.hostname,
        'PORT': parsed.port or 5432,
    }


DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
DATABASES = {'default': parse_database_url(DATABASE_URL)}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.1-8b-instruct:free')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1/chat/completions')
APP_REFERER = os.getenv('APP_REFERER', 'http://localhost:8000')
