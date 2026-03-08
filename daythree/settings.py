import os
from pathlib import Path
from datetime import timedelta
from django.conf import settings
from corsheaders.defaults import default_headers
from decouple import config
import dj_database_url
from typing import cast, Optional



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='build-time-only-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'library',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'daythree.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'daythree.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

if DEBUG:
    DATABASES = {
            "default":{
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DATABASE_NAME', default='librarylens'),
            'USER': config('DATABASE_USER', default='anochiwaalfred'),
            'PASSWORD': config('DATABASE_PASSWORD', default='Alfieolli'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default=5432),
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL', default='sqlite:///db.sqlite3'),
            conn_max_age=600,
            ssl_require=True
        )
    }



# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

SPOTIFY_CLIENT_ID = config('SPOTIFY_CLIENT_ID', default="a285018c117242559582817451953444")
SPOTIFY_CLIENT_SECRET = config('SPOTIFY_CLIENT_SECRET', default="a285018c117242559582817451953444")
SPOTIFY_REDIRECT_URI = config('SPOTIFY_REDIRECT_URI', default="a285018c117242559582817451953444")
SPOTIFY_SCOPE = "user-library-read"


# Use the 'name' from your accounts/urls.py
# If using a namespace in the root urls.py, use 'accounts:login_page'
LOGIN_URL = 'login_page'

# Where to send the user after they successfully log in
LOGIN_REDIRECT_URL = 'home'

# Where to send the user after they log out
LOGOUT_REDIRECT_URL = 'login_page'


INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://192.168.43.73:8000",
    config('HOST_URI', default="http://localhost:8000"),
]


CORS_ALLOW_ALL_ORIGINS = True  #*****************************************************************************************CHANGE LATER

CORS_ALLOW_HEADERS=(
    *default_headers,
)

CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
