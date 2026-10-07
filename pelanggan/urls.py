from django.urls import path

from . import views

app_name = "pelanggan"

urlpatterns = [
    path("pelanggan/", views.DaftarPelangganView.as_view(), name="daftar"),
    path("pelanggan/tambah/", views.TambahPelangganView.as_view(), name="tambah"),
    path("pelanggan/<int:pk>/ubah/", views.UbahPelangganView.as_view(), name="ubah"),
    path("pelanggan/<int:pk>/hapus/", views.HapusPelangganView.as_view(), name="hapus"),
    path(
        "pelanggan/<int:pk>/aktifkan/",
        views.AktifkanPelangganView.as_view(),
        name="aktifkan",
    ),
]
