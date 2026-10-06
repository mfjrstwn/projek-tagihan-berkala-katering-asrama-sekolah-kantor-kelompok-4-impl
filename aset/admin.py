from django.contrib import admin

from .models import Aset


@admin.register(Aset)
class AsetAdmin(admin.ModelAdmin):
    list_display = ("nama", "kategori", "tgl_perolehan", "nilai", "kondisi")
    list_filter = ("kondisi", "kategori")
