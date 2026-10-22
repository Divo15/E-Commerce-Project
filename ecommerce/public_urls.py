"""Absolute storefront URLs for customer messages and sharing metadata."""
from urllib.parse import urljoin

from django.conf import settings


def public_url(request, path):
    origin = settings.ACCOUNT_PUBLIC_ORIGIN.rstrip('/')
    return urljoin(origin + '/' if origin else request.build_absolute_uri('/'), path)
