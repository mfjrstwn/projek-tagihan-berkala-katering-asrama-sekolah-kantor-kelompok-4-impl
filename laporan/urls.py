from django.urls import path

from . import views

app_name = "laporan"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("laporan/", views.LaporanView.as_view(), name="laporan"),
]
