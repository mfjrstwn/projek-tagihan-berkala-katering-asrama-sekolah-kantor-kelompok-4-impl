from django.contrib import admin

from .models import Tagihan


@admin.register(Tagihan)
class TagihanAdmin(admin.ModelAdmin):
    list_display = ("langganan", "periode", "jumlah", "jatuh_tempo", "status")
    list_filter = ("status", "periode")
