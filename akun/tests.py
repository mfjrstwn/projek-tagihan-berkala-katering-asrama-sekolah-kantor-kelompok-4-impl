from django.test import TestCase
from django.urls import reverse

from .models import Pengguna


class AksesPerPeranTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Pengguna.objects.create_user(
            "admin1", password="rahasia123", role=Pengguna.Peran.ADMIN
        )
        cls.customer = Pengguna.objects.create_user("cust1", password="rahasia123")

    def test_pengguna_belum_login_dialihkan_ke_masuk(self):
        r = self.client.get(reverse("akun:dashboard"))
        self.assertRedirects(
            r, f"{reverse('akun:masuk')}?next={reverse('akun:dashboard')}"
        )

    def test_admin_boleh_membuka_dashboard(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("akun:dashboard"))
        self.assertEqual(r.status_code, 200)

    def test_customer_ditolak_di_dashboard(self):
        self.client.force_login(self.customer)
        r = self.client.get(reverse("akun:dashboard"))
        self.assertEqual(r.status_code, 403)

    def test_admin_ditolak_di_halaman_customer(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("akun:tagihan_saya"))
        self.assertEqual(r.status_code, 403)

    def test_beranda_mengarahkan_sesuai_peran(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("akun:beranda"))
        self.assertRedirects(r, reverse("akun:dashboard"), fetch_redirect_response=False)
        self.client.force_login(self.customer)
        r = self.client.get(reverse("akun:beranda"))
        self.assertRedirects(r, reverse("akun:tagihan_saya"), fetch_redirect_response=False)

    def test_login_benar_berhasil(self):
        r = self.client.post(
            reverse("akun:masuk"), {"username": "admin1", "password": "rahasia123"}
        )
        self.assertRedirects(r, reverse("akun:beranda"), fetch_redirect_response=False)

    def test_login_salah_menampilkan_pesan(self):
        r = self.client.post(
            reverse("akun:masuk"), {"username": "admin1", "password": "salah"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Username atau password salah")

    def test_logout_mengakhiri_sesi(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("akun:keluar"))
        r = self.client.get(reverse("akun:dashboard"))
        self.assertEqual(r.status_code, 302)
