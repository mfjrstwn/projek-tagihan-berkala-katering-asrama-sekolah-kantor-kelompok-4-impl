from django.test import TestCase
from django.urls import reverse

from paket.models import Paket
from tagihan import layanan
from tagihan.pembantu_tes import buat_langganan

from .models import Pengguna

HALAMAN_CUSTOMER = ["tagihan:saya", "paket:saya", "pelanggan:data_diri"]


def hubungkan(langganan, username):
    """Membuat akun Customer dan menautkannya ke pelanggan dari langganan."""
    user = Pengguna.objects.create_user(username, password="rahasia123")
    langganan.pelanggan.user = user
    langganan.pelanggan.save(update_fields=["user"])
    return user


class PortalCustomerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Pengguna.objects.create_user(
            "admin1", password="rahasia123", role=Pengguna.Peran.ADMIN
        )
        cls.lang_dewi = buat_langganan("Dewi Anggraini")
        cls.lang_budi = buat_langganan("Budi Santoso")
        cls.dewi = hubungkan(cls.lang_dewi, "dewi")
        cls.budi = hubungkan(cls.lang_budi, "budi")
        cls.tanpa_data = Pengguna.objects.create_user("tanpa", password="rahasia123")
        cls.lang_dewi.buat_tagihan("2020-03")      # tagihan lama milik Dewi
        cls.lang_budi.buat_tagihan("2020-04")      # tagihan lama milik Budi

    # --- Hak akses ---
    def test_pengguna_belum_login_dialihkan(self):
        for nama in HALAMAN_CUSTOMER:
            with self.subTest(halaman=nama):
                self.assertEqual(self.client.get(reverse(nama)).status_code, 302)

    def test_admin_ditolak_di_halaman_customer(self):
        self.client.force_login(self.admin)
        for nama in HALAMAN_CUSTOMER:
            with self.subTest(halaman=nama):
                self.assertEqual(self.client.get(reverse(nama)).status_code, 403)

    def test_customer_tidak_boleh_membuka_halaman_admin(self):
        self.client.force_login(self.dewi)
        for nama in ["pelanggan:daftar", "paket:daftar", "aset:daftar", "tagihan:daftar"]:
            with self.subTest(halaman=nama):
                self.assertEqual(self.client.get(reverse(nama)).status_code, 403)

    # --- Tagihan saya ---
    def test_hanya_tagihan_sendiri_yang_tampil(self):
        self.client.force_login(self.dewi)
        r = self.client.get(reverse("tagihan:saya"))
        self.assertContains(r, "Mar 2020")
        self.assertNotContains(r, "Apr 2020")

    def test_ringkasan_tagihan_bulan_ini(self):
        self.lang_dewi.buat_tagihan(layanan.periode_sekarang())
        self.client.force_login(self.dewi)
        r = self.client.get(reverse("tagihan:saya"))
        self.assertContains(r, "Tagihan bulan ini")
        self.assertContains(r, "Total belum lunas")

    def test_tanpa_tagihan_menampilkan_keadaan_kosong(self):
        lang = buat_langganan("Pelanggan Baru")
        user = hubungkan(lang, "baru")
        self.client.force_login(user)
        r = self.client.get(reverse("tagihan:saya"))
        self.assertContains(r, "Belum ada tagihan")

    def test_tagihan_lama_otomatis_menunggak(self):
        self.client.force_login(self.dewi)
        r = self.client.get(reverse("tagihan:saya"))
        self.assertContains(r, "Menunggak")

    def test_pelanggan_nonaktif_melihat_banner_dan_riwayat(self):
        self.lang_dewi.pelanggan.nonaktifkan()
        self.client.force_login(self.dewi)
        r = self.client.get(reverse("tagihan:saya"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Akun pelanggan Anda nonaktif")
        self.assertContains(r, "Mar 2020")

    # --- Akun belum terhubung ---
    def test_akun_tanpa_data_pelanggan_diberi_penjelasan(self):
        self.client.force_login(self.tanpa_data)
        for nama in ["tagihan:saya", "pelanggan:data_diri"]:
            with self.subTest(halaman=nama):
                r = self.client.get(reverse(nama))
                self.assertContains(r, "belum terhubung dengan data pelanggan")

    # --- Paket dan tarif ---
    def test_paket_dipakai_ditandai(self):
        Paket.objects.create(
            nama_paket="Sarapan", tarif=250000, satuan_tarif=Paket.Satuan.PER_BULAN
        )
        self.client.force_login(self.dewi)
        r = self.client.get(reverse("paket:saya"))
        self.assertContains(r, "Sarapan")
        self.assertContains(r, "Makan siang")
        self.assertContains(r, "Paket Anda", count=1)

    # --- Data diri ---
    def test_data_diri_hanya_milik_sendiri(self):
        self.client.force_login(self.dewi)
        r = self.client.get(reverse("pelanggan:data_diri"))
        self.assertContains(r, "Dewi Anggraini")
        self.assertNotContains(r, "Budi Santoso")

    # --- Navigasi ---
    def test_menu_customer_tampil(self):
        self.client.force_login(self.dewi)
        r = self.client.get(reverse("tagihan:saya"))
        for teks in ["Tagihan saya", "Paket dan tarif", "Data diri"]:
            self.assertContains(r, teks)

    def test_beranda_mengarahkan_customer_ke_tagihan_saya(self):
        self.client.force_login(self.dewi)
        r = self.client.get(reverse("akun:beranda"))
        self.assertRedirects(r, reverse("tagihan:saya"), fetch_redirect_response=False)
