from django.urls import path

from . import views

app_name = "aset"

urlpatterns = [
    path("aset/", views.DaftarAsetView.as_view(), name="daftar"),
    path("aset/tambah/", views.TambahAsetView.as_view(), name="tambah"),
    path("aset/<int:pk>/ubah/", views.UbahAsetView.as_view(), name="ubah"),
    path("aset/<int:pk>/hapus/", views.HapusAsetView.as_view(), name="hapus"),
]
