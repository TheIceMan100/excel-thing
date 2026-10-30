import os
import dj_database_url

# SECURITY WARNING: Don't run with debug turned on in production!
# Render sets an environment variable, or you can check if not in local debug
DEBUG = os.environ.get("RENDER", "False") != "True"

# Secure Secret Key handling (falls back to an unsafe default only if local)
SECRET_KEY = os.environ.get(
    "SECRET_KEY", 
    "django-insecure-fallback-key-for-local-dev-only"
)

# Allowed Hosts for Render
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    # Default Django contributed apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'excel_thing',
]

# Render provides the external hostname automatically via RENDER_EXTERNAL_HOSTNAME
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Security headers for production (Render uses HTTPS by default)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

ROOT_URLCONF = 'mysite.urls'

DATABASES = {
    'default': dj_database_url.config(
        # Fallback to local SQLite if DATABASE_URL environment variable is missing
        default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}