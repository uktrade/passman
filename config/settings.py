import os
import sys

from django.contrib.messages import constants as messages
from django.urls import reverse_lazy

import dj_database_url
from django_log_formatter_ecs import ECSFormatter
import environ

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up .env
ENV_FILE = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_FILE):
    environ.Env.read_env(ENV_FILE)
env = environ.Env(DEBUG=(bool, False),)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "authbroker_client",
    "crispy_forms",
    "django_filters",
    "guardian",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "axes",
    "twofactor",
    "audit",
    "user",
    "secret",
    "core",
    "localauth",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.ProtectAllViewsMiddleware",
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {"default": dj_database_url.config()}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = False

USE_TZ = True

DATETIME_FORMAT = "jS M y G:i:s"
TIME_FORMAT = "%H:%M:%S"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "static")

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "staticfiles"),
]

AUTH_USER_MODEL = "user.User"

# Authbroker config

AUTHBROKER_URL = env("AUTHBROKER_URL")
AUTHBROKER_CLIENT_ID = env("AUTHBROKER_CLIENT_ID")
AUTHBROKER_CLIENT_SECRET = env("AUTHBROKER_CLIENT_SECRET")
AUTHBROKER_STAFF_SSO_SCOPE = "read write"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "core.backends.CustomAuthbrokerBackend",
    "guardian.backends.ObjectPermissionBackend",
]

LOGIN_URL = reverse_lazy("authbroker_client:login")
LOGIN_REDIRECT_URL = reverse_lazy("secret:list")
LOGOUT_REDIRECT_URL = reverse_lazy("user:logged-out")
USE_X_FORWARDED_HOST = True

AUTHBROKER_PROFILE_ID_FIELD_NAME = "email_user_id"

PUBLIC_VIEWS = [
    reverse_lazy("user:logged-out"),
]

# sentry config

if not DEBUG:
    sentry_sdk.init(
        env("SENTRY_DSN"),
        environment=env("SENTRY_ENVIRONMENT"),
        integrations=[DjangoIntegration()],
    )

# crispy forms config

CRISPY_TEMPLATE_PACK = "bootstrap4"

# messages config

MESSAGE_TAGS = {
    messages.INFO: "success",
    messages.ERROR: "danger",
}

# django cryptography

CRYPTOGRAPHY_KEY = env("CRYPTOGRAPHY_KEY", default=SECRET_KEY)
CRYPTOGRAPHY_SALT = env("CRYPTOGRAPHY_SALT")

# guardian config

GUARDIAN_MONKEY_PATCH = False
GUARDIAN_RENDER_403 = True

# OTP / 2FA config

# REQUIRE_2FA = True
REQUIRE_2FA = env("TWO_FACTOR_AUTH", default=True)
OTP_LOGIN_URL = reverse_lazy("twofactor:verify")
OTP_HOTP_ISSUER = env("OTP_HOTP_ISSUER", default="Passman")
OTP_TOTP_ISSUER = OTP_HOTP_ISSUER

# audit event config

AUDIT_EVENT_REPEAT_AFTER_MINUTES = env.int("AUDIT_EVENT_REPEAT_AFTER_MINUTES", default=12 * 60)

# app settings

SECRET_PAGINATION_ITEMS_PER_PAGE = 20
SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=86400)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
        "ecs_formatter": {
            "()": ECSFormatter,
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "ecs_formatter",
        },
    },
    "root": {
        "handlers": ["stdout"],
        "level": env("LOG_LEVEL_ROOT", default="INFO"),
    },
    "loggers": {
        "django": {
            "handlers": [
                "stdout",
            ],
            "level": env("LOG_LEVEL_ROOT", default="INFO"),
            "propagate": True,
        },
        "django.server": {
            "handlers": [
                "stdout",
            ],
            "level": env("LOG_LEVEL_ROOT", default="INFO"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": [
                "stdout",
            ],
            "level": env("LOG_LEVEL_ROOT", default="INFO"),
            "propagate": True,
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "axes_cache": {
        # See - https://github.com/jazzband/django-axes/blob/master/docs/configuration.rst#cache-problems
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}

AXES_CACHE = "axes_cache"
AXES_ONLY_USER_FAILURES = True
AXES_VERBOSE = True
AXES_RESET_ON_SUCCESS = True
AXES_FAILURE_LIMIT = 3

# Include the local auth page?
LOCAL_AUTH_PAGE = env.bool("LOCAL_AUTH_PAGE", default=True)

SSO_RECOVERY_USERS = env.list("SSO_RECOVERY_USERS", default=[])

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")
