from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .akses import AdminRequiredMixin, CustomerRequiredMixin
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
    return redirect("akun:tagihan_saya")


# Dua halaman di bawah ini hanya penanda sementara.
# Nanti dipindahkan ke app masing-masing saat fiturnya dibuat.
class DashboardSementara(AdminRequiredMixin, TemplateView):
    template_name = "halaman/dashboard_sementara.html"


class TagihanSayaSementara(CustomerRequiredMixin, TemplateView):
    template_name = "halaman/tagihan_saya_sementara.html"
