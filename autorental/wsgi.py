"""
WSGI config for autorental project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autorental.settings')

application = get_wsgi_application()
application = get_wsgi_application()
# http://127.0.0.1:8000
