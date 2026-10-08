from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("akun.urls")),
    path("", include("pelanggan.urls")),
    path("", include("paket.urls")),
    path("", include("aset.urls")),
    path("", include("tagihan.urls")),
]
