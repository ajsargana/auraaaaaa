import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')
_source_env = BASE_DIR / 'source' / 'Sat-Track3zip' / 'Sat-Track_latest' / '.env'
if _source_env.exists():
    load_dotenv(_source_env)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'SESSION_SECRET',
    'django-insecure-+17odery(^ow-1!669gal9mwc0s4169yq5znfl!+*17j6ud^+&'
)

DEV_MODE = True

if DEV_MODE:
    DEBUG = True
    ALLOWED_HOSTS = ['*']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DEBUG = False
    ALLOWED_HOSTS = ['ip-address and domain names']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'sattrack_db'
        }
    }




INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'tracker',
    'nasa',
    'launches',
    'airplanes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'core.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # CSRF middleware kept but API views use @csrf_exempt
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sat_track.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sat_track.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Path setup for support modules ---
for _app_dir in ['tracker', 'nasa', 'launches', 'airplanes', 'core']:
    _p = str(BASE_DIR / _app_dir)
    if _p not in sys.path:
        sys.path.insert(0, _p)

DATA_DIR = str(BASE_DIR / 'core' / 'data')
