"""Platforma nomi (18-bosqich): `{% site_name %}` — kontekst protsessori ishlamaydigan sahifalar uchun (500)."""

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def site_name() -> str:
    return settings.SITE_NAME
