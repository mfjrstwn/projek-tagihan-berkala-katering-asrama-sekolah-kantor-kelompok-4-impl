from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from .models import Pengguna


class PeranMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Membatasi halaman untuk satu peran saja.

    - Belum login      -> dialihkan ke halaman masuk
    - Sudah login tapi peran salah -> ditolak (403)
    """

    peran = None

    def test_func(self):
        return self.request.user.role == self.peran

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class AdminRequiredMixin(PeranMixin):
    peran = Pengguna.Peran.ADMIN


class CustomerRequiredMixin(PeranMixin):
    peran = Pengguna.Peran.CUSTOMER
