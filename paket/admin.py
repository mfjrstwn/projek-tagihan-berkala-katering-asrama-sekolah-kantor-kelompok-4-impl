from django.contrib import admin

from .models import Paket


@admin.register(Paket)
class PaketAdmin(admin.ModelAdmin):
    list_display = ("nama_paket", "tarif", "satuan_tarif", "periode")
