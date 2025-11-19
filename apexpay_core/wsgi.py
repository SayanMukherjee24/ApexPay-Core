"""
WSGI config for apexpay_core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
# HOSTNAME = "apexpay_core.azurewebsites.net"

# settings_module = 'apexpay_core.deployment' if HOSTNAME in os.environ else 'apexpay_core.settings'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apexpay_core.settings')

application = get_wsgi_application()