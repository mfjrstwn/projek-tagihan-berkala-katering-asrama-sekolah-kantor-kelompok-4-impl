from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "akun"

urlpatterns = [
    path("", views.beranda, name="beranda"),
    path("masuk/", views.MasukView.as_view(), name="masuk"),
    path("keluar/", auth_views.LogoutView.as_view(), name="keluar"),
    path("dashboard/", views.DashboardSementara.as_view(), name="dashboard"),
]
