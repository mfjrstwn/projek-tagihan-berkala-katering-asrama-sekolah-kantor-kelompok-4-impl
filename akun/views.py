from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

from .forms import FormMasuk


class MasukView(LoginView):
    template_name = "akun/masuk.html"
    authentication_form = FormMasuk
    redirect_authenticated_user = True


@login_required
def beranda(request):
    """Mengarahkan pengguna ke halaman awal sesuai perannya."""
    if request.user.adalah_admin():
        return redirect("laporan:dashboard")
    return redirect("tagihan:saya")
