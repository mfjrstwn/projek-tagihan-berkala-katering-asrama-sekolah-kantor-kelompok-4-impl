from django.contrib import admin

from .models import Langganan, Pelanggan


class LanggananInline(admin.TabularInline):
    model = Langganan
    extra = 0


@admin.register(Pelanggan)
class PelangganAdmin(admin.ModelAdmin):
    list_display = ("nama", "segmen", "tipe", "status")
    list_filter = ("segmen", "tipe", "status")
    search_fields = ("nama",)
    inlines = [LanggananInline]
