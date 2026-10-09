from .base import *

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

if not DEBUG:
    raise ImproperlyConfigured(
        "Local settings require DJANGO_DEBUG=True."
    )
