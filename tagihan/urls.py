from django.urls import path

from . import views

app_name = "tagihan"

urlpatterns = [
    path("tagihan/", views.DaftarTagihanView.as_view(), name="daftar"),
    path("tagihan/buat/", views.BuatTagihanView.as_view(), name="buat"),
    path("tagihan-saya/", views.TagihanSayaView.as_view(), name="saya"),
    path("tagihan/<int:pk>/lunas/", views.TandaiLunasView.as_view(), name="lunas"),
]
