from django import template

from .. import layanan

register = template.Library()


@register.filter
def label_periode(nilai):
    """{{ t.periode|label_periode }} menampilkan 2026-10 sebagai Okt 2026."""
    return layanan.label_periode(nilai)
