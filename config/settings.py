from datetime import timedelta
from pathlib import Path

from environ import Env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# typing and default env values
env = Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    SQL_ENGINE=(str, "django.db.backends.sqlite3"),
    SQL_DATABASE=(str, str(BASE_DIR / "db.sqlite3")),
    SQL_USER=(str, "user"),
    SQL_PASSWORD=(str, "password"),
    SQL_HOST=(str, "localhost"),
    SQL_PORT=(str, "5432"),
)
env.read_env()  # for docker env
env.read_env(f"{BASE_DIR}/.env")  # for local runserver

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition

UNFOLD_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    "unfold.contrib.location_field",
    "unfold.contrib.constance",
]

STD_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

REMOTE_APPS = [
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "rest_framework_simplejwt.token_blacklist",
    "imagekit",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.authentication",
    "apps.common",
    "apps.menus",
    "apps.orders",
    "apps.wallets",
    "apps.users",
]

INSTALLED_APPS = [*UNFOLD_APPS, *STD_APPS, *REMOTE_APPS, *LOCAL_APPS]

AUTH_USER_MODEL = "users.User"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "TOKEN_OBTAIN_SERIALIZER": "authentication.serializers.TokenWithRoleObtainPairSerializer",
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:8080",
    "https://localhost",
]
CORS_ALLOW_CREDENTIALS = True

CSRF_ALLOWED_ORIGINS = [
    "https://localhost",
    "https://127.0.0.1",
    "http://localhost",
    "http://127.0.0.1",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# if needed in dev
# CSRF_COOKIE_SECURE = False
# SESSION_COOKIE_SECURE = False
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

REST_FRAMEWORK = {
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%SZ",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "apps.common.throttling.UnverifiedUserThrottle",
        "apps.common.throttling.VerifiedUserThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "5/hour",
        "unverified": "20/hour",
        "verified": "100/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "UTM Canteen API",
    "DESCRIPTION": "Buy grechka, borsch and kompot easily.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://localhost", "description": "Secure development server"},
    ],
}

UNFOLD = {
    "SITE_TITLE": "TrayGo administration",
    "SITE_HEADER": "TrayGo administration",
    "SITE_BRAND": "TrayGo",
    "COLORS": {
        "primary": {
            "50": "#edf2fe",
            "100": "#d9e3fd",
            "200": "#b3c7fb",
            "300": "#8daaf9",
            "400": "#678ef7",
            "500": "#4874e4",
            "600": "#3a5ec4",
            "700": "#2c49a3",
            "800": "#1f3482",
            "900": "#132062",
            "950": "#0a143d",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Authentication and Authorization",
                "separator": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": "/admin/users/user/",
                    },
                    {
                        "title": "Groups",
                        "icon": "group",
                        "link": "/admin/auth/group/",
                    },
                ],
            },
            {
                "title": "Menus",
                "separator": True,
                "items": [
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": "/admin/menus/category/",
                    },
                    {
                        "title": "Items",
                        "icon": "restaurant",
                        "link": "/admin/menus/item/",
                    },
                    {
                        "title": "Menu Items",
                        "icon": "list_alt",
                        "link": "/admin/menus/menuitem/",
                    },
                    {
                        "title": "Menus",
                        "icon": "menu_book",
                        "link": "/admin/menus/menu/",
                    },
                ],
            },
            {
                "title": "Orders",
                "separator": True,
                "items": [
                    {
                        "title": "Order Confirmation",
                        "icon": "check_circle",
                        "link": "/admin/orders/confirmation/",
                    },
                    {
                        "title": "All Orders",
                        "icon": "shopping_cart",
                        "link": "/admin/orders/order/",
                    },
                    {
                        "title": "Order Items",
                        "icon": "inventory",
                        "link": "/admin/orders/orderitem/",
                    },
                ],
            },
            {
                "title": "Wallets",
                "separator": True,
                "items": [
                    {
                        "title": "Balances",
                        "icon": "account_balance_wallet",
                        "link": "/admin/wallets/balance/",
                    },
                    {
                        "title": "Transactions",
                        "icon": "receipt",
                        "link": "/admin/wallets/transaction/",
                    },
                ],
            },
            {
                "title": "Token Blacklist",
                "separator": True,
                "items": [
                    {
                        "title": "Outstanding Tokens",
                        "icon": "token",
                        "link": "/admin/token_blacklist/outstandingtoken/",
                    },
                    {
                        "title": "Blacklisted Tokens",
                        "icon": "block",
                        "link": "/admin/token_blacklist/blacklistedtoken/",
                    },
                ],
            },
        ],
    },
}

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": env("SQL_ENGINE"),
        "NAME": env("SQL_DATABASE"),
        "USER": env("SQL_USER"),
        "PASSWORD": env("SQL_PASSWORD"),
        "HOST": env("SQL_HOST"),
        "PORT": env("SQL_PORT"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

RBAC_FORCE_UPDATE_PERMISSIONS = False
