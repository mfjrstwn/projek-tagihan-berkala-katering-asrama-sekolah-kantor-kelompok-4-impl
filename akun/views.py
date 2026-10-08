from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .akses import AdminRequiredMixin
from .forms import FormMasuk


class MasukView(LoginView):
    template_name = "akun/masuk.html"
    authentication_form = FormMasuk
    redirect_authenticated_user = True


@login_required
def beranda(request):
    """Mengarahkan pengguna ke halaman awal sesuai perannya."""
    if request.user.adalah_admin():
        return redirect("akun:dashboard")
    return redirect("tagihan:saya")


# Halaman sementara untuk Admin. Diganti saat fitur dashboard dikerjakan.
class DashboardSementara(AdminRequiredMixin, TemplateView):
    template_name = "halaman/dashboard_sementara.html"
