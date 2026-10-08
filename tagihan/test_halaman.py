from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from akun.models import Pengguna
from pelanggan.models import Pelanggan

from . import layanan
from .models import Tagihan
from .pembantu_tes import buat_langganan


class DasarHalamanTagihan(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Pengguna.objects.create_user(
            "admin1", password="rahasia123", role=Pengguna.Peran.ADMIN
        )
        cls.customer = Pengguna.objects.create_user("cust1", password="rahasia123")

    def setUp(self):
        self.client.force_login(self.admin)
        self.periode = layanan.periode_sekarang()
        self.label = layanan.label_periode(self.periode)


class DaftarTagihanTest(DasarHalamanTagihan):
    def test_hanya_untuk_admin(self):
        url = reverse("tagihan:daftar")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_daftar_kosong_menampilkan_pesan(self):
        self.assertContains(self.client.get(reverse("tagihan:daftar")), "Belum ada tagihan")

    def test_membuka_daftar_menandai_menunggak(self):
        lang = buat_langganan("Pelanggan lama")
        tagihan = Tagihan.objects.create(
            langganan=lang, periode="2020-01", jumlah=Decimal("450000"),
            jatuh_tempo=date(2020, 1, 10),
        )
        self.client.get(reverse("tagihan:daftar"))
        tagihan.refresh_from_db()
        self.assertEqual(tagihan.status, Tagihan.Status.MENUNGGAK)

    def test_filter_status(self):
        lunas = buat_langganan("Pelanggan Lunas")
        belum = buat_langganan("Pelanggan Belum")
        t1, _ = lunas.buat_tagihan(self.periode)
        t1.tandai_lunas(date.today())
        belum.buat_tagihan(self.periode)
        r = self.client.get(reverse("tagihan:daftar"), {"status": "Lunas"})
        self.assertContains(r, "Pelanggan Lunas")
        self.assertNotContains(r, "Pelanggan Belum")

    def test_filter_periode(self):
        lang = buat_langganan("Pelanggan Satu")
        lang.buat_tagihan("2026-08")
        lang.buat_tagihan("2026-09")
        r = self.client.get(reverse("tagihan:daftar"), {"periode": "2026-08"})
        self.assertContains(r, "Agu 2026")
        self.assertNotContains(r, "<td>Sep 2026</td>")


class BuatTagihanTest(DasarHalamanTagihan):
    def test_konfirmasi_menampilkan_jumlah_pelanggan(self):
        lang = buat_langganan("Satu")
        buat_langganan("Dua")
        lang.buat_tagihan(self.periode)
        r = self.client.get(reverse("tagihan:buat"))
        self.assertContains(r, f"Buat tagihan {self.label}?")
        self.assertContains(r, "untuk 1 pelanggan aktif")

    def test_hanya_untuk_admin(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("tagihan:buat")).status_code, 403)
        self.assertEqual(self.client.post(reverse("tagihan:buat")).status_code, 403)

    def test_buat_tagihan_berhasil(self):
        buat_langganan("Satu")
        r = self.client.post(reverse("tagihan:buat"), follow=True)
        self.assertContains(r, f"1 tagihan berhasil dibuat untuk {self.label}")
        self.assertEqual(Tagihan.objects.count(), 1)

    def test_semua_sudah_ada_ditolak(self):
        lang = buat_langganan("Satu")
        lang.buat_tagihan(self.periode)
        r = self.client.post(reverse("tagihan:buat"), follow=True)
        self.assertContains(r, "sudah ada untuk semua pelanggan aktif")
        self.assertEqual(Tagihan.objects.count(), 1)

    def test_sebagian_sudah_ada(self):
        lang = buat_langganan("Satu")
        buat_langganan("Dua")
        lang.buat_tagihan(self.periode)
        r = self.client.post(reverse("tagihan:buat"), follow=True)
        self.assertContains(r, "1 tagihan baru dibuat. 1 pelanggan dilewati")
        self.assertEqual(Tagihan.objects.count(), 2)

    def test_pelanggan_nonaktif_tidak_ditagih(self):
        buat_langganan("Nonaktif", status_pelanggan=Pelanggan.Status.NONAKTIF)
        r = self.client.post(reverse("tagihan:buat"), follow=True)
        self.assertContains(r, "Tidak ada pelanggan aktif yang bisa ditagih")
        self.assertEqual(Tagihan.objects.count(), 0)


class TandaiLunasTest(DasarHalamanTagihan):
    def setUp(self):
        super().setUp()
        self.tagihan, _ = buat_langganan("Dewi").buat_tagihan(self.periode)
        self.url = reverse("tagihan:lunas", args=[self.tagihan.pk])

    def test_halaman_menampilkan_data_tagihan(self):
        r = self.client.get(self.url)
        self.assertContains(r, "Tandai tagihan lunas")
        self.assertContains(r, "Dewi")

    def test_tandai_lunas_berhasil(self):
        r = self.client.post(self.url, {"tanggal": date.today().isoformat()}, follow=True)
        self.assertContains(r, "Tagihan ditandai lunas")
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status, Tagihan.Status.LUNAS)
        self.assertEqual(self.tagihan.tgl_lunas, date.today())

    def test_tanggal_tidak_valid_ditolak(self):
        r = self.client.post(self.url, {"tanggal": "bukan-tanggal"})
        self.assertContains(r, "Format tanggal tidak valid")
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status, Tagihan.Status.BELUM)

    def test_tanggal_kosong_ditolak(self):
        r = self.client.post(self.url, {"tanggal": ""})
        self.assertContains(r, "Tanggal pelunasan wajib diisi")

    def test_tanggal_sebelum_terbit_ditolak(self):
        r = self.client.post(self.url, {"tanggal": "2000-01-01"})
        self.assertContains(r, "Tanggal pelunasan tidak boleh sebelum tanggal terbit")
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status, Tagihan.Status.BELUM)

    def test_tagihan_yang_sudah_lunas_dialihkan(self):
        self.tagihan.tandai_lunas(date.today())
        r = self.client.get(self.url, follow=True)
        self.assertContains(r, "Tagihan ini sudah lunas")

    def test_hanya_untuk_admin(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.url).status_code, 403)
