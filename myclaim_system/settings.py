import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-f5i1a^8$)(wi(5pvvft_3fv(+d_*_xz5yedl-mts!n-9-+1)ru'

DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'import_export',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # --- WAJIB UNTUK GOOGLE AUTH ---
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    'claims', # App anda
]

# ID untuk tapak web (Wajib untuk allauth)
SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = 'myclaim_system.urls'

# --- KONFIGURASI TEMPLATE ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'claims', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'myclaim_system.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# --- PENGURUSAN AUTHENTICATION ---
AUTH_USER_MODEL = 'claims.CustomUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# --- PENGURUSAN AKAUN AUTOMATIK (VERSI DJANGO 6.0) ---
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "none"

# Format baharu untuk menggantikan ACCOUNT_EMAIL_REQUIRED & ACCOUNT_USERNAME_REQUIRED
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

# Konfigurasi Username (Ditetapkan None kerana kita guna email)
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Memastikan proses pendaftaran google berlaku secara automatik
SOCIALACCOUNT_AUTO_SIGNUP = True 
SOCIALACCOUNT_QUERY_EMAIL = True

# Untuk selesaikan masalah Unique Constraint & Auto-Link akaun
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# Melangkau skrin pengesahan "Are you sure you want to log in?"
SOCIALACCOUNT_LOGIN_ON_GET = True

# PENTING: Menggunakan adapter kustom anda
SOCIALACCOUNT_ADAPTER = 'claims.adapters.MySocialAccountAdapter'
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'

# --- HALUAN SELEPAS LOGIN/LOGOUT ---
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

# --- KONFIGURASI PROVIDER GOOGLE ---
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'hd': 'moe.gov.my',  # Memaksa akaun MOE sahaja
            'prompt': 'select_account',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media Settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')