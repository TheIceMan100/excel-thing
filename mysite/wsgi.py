import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# <-- Make sure this line exists and is named exactly 'application'
application = get_wsgi_application()