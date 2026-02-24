import os
from pathlib import Path
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def env_int(name: str, default: int = 0) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == '':
        return default
    return int(value)


def parse_csv_env(name: str, default: str = '') -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(',') if item.strip()]


def build_csrf_origins(hosts: list[str]) -> list[str]:
    origins: list[str] = []
    for host in hosts:
        if host == '*' or '*' in host:
            continue
        normalized_host = host.lstrip('.')
        if normalized_host in {'localhost', '127.0.0.1'}:
            origins.extend([
                f'http://{normalized_host}',
                f'https://{normalized_host}',
            ])
            continue
        origins.append(f'https://{normalized_host}')
    # preserve order while removing duplicates
    return list(dict.fromkeys(origins))


DEBUG = env_bool('DEBUG', False)

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-dev-key'
    else:
        raise ImproperlyConfigured('SECRET_KEY is required when DEBUG=False.')

allow_all_hosts = env_bool('ALLOW_ALL_HOSTS_IN_PROD', False)
allowed_hosts_from_env = parse_csv_env('ALLOWED_HOSTS')
public_url = os.getenv('PUBLIC_URL', '').strip().rstrip('/')
public_host = ''
if public_url:
    public_host = (urlparse(public_url).hostname or '').strip()
if allowed_hosts_from_env:
    ALLOWED_HOSTS = allowed_hosts_from_env
elif allow_all_hosts:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.up.railway.app', 'descubreme-production.up.railway.app']

if public_host and public_host not in ALLOWED_HOSTS and '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(public_host)

csrf_from_env = parse_csv_env('CSRF_TRUSTED_ORIGINS')
required_csrf_origins = ['https://descubreme-production.up.railway.app']
if public_url:
    required_csrf_origins.append(public_url)

if csrf_from_env:
    CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(csrf_from_env + required_csrf_origins))
else:
    csrf_defaults = []
    if public_url:
        csrf_defaults.append(public_url)
    csrf_defaults.extend(build_csrf_origins(ALLOWED_HOSTS))
    csrf_defaults.extend(required_csrf_origins)
    CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(csrf_defaults))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig',
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
                'core.context_processors.social_counts',
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

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', True)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = env_int('SECURE_HSTS_SECONDS', 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', False)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', '')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'google/gemma-2-9b-it:free')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1/chat/completions')
OPENROUTER_SITE_URL = os.getenv('OPENROUTER_SITE_URL', '')
OPENROUTER_APP_NAME = os.getenv('OPENROUTER_APP_NAME', 'Descubriendo')

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/saved/'
LOGOUT_REDIRECT_URL = '/'

SILENCED_SYSTEM_CHECKS = ['fields.E210']
