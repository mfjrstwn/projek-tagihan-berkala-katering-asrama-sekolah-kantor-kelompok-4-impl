from django.urls import path

from . import views

app_name = "paket"

urlpatterns = [
    path("paket/", views.DaftarPaketView.as_view(), name="daftar"),
    path("paket-saya/", views.PaketSayaView.as_view(), name="saya"),
    path("paket/tambah/", views.TambahPaketView.as_view(), name="tambah"),
    path("paket/<int:pk>/ubah/", views.UbahPaketView.as_view(), name="ubah"),
    path("paket/<int:pk>/hapus/", views.HapusPaketView.as_view(), name="hapus"),
]
