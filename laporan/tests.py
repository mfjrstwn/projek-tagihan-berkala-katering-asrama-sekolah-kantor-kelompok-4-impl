from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from akun.models import Pengguna
from aset.models import Aset
from pelanggan.models import Pelanggan
from tagihan import layanan
from tagihan.models import Tagihan
from tagihan.pembantu_tes import buat_langganan


def buat_aset(nama, kondisi):
    return Aset.objects.create(
        nama=nama, kategori="Produksi", tgl_perolehan=date(2025, 1, 1),
        nilai=Decimal("1000"), kondisi=kondisi,
    )


class DasarLaporan(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Pengguna.objects.create_user(
            "admin1", password="rahasia123", role=Pengguna.Peran.ADMIN
        )
        cls.customer = Pengguna.objects.create_user("cust1", password="rahasia123")

    def setUp(self):
        self.client.force_login(self.admin)
        self.periode = layanan.periode_sekarang()


class DashboardTest(DasarLaporan):
    def test_hanya_untuk_admin(self):
        url = reverse("laporan:dashboard")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_dashboard_kosong_tetap_tampil(self):
        r = self.client.get(reverse("laporan:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["total_tagihan"], 0)
        self.assertEqual(r.context["pelanggan_aktif"], 0)
        self.assertContains(r, "Belum ada tagihan")

    def test_total_tagihan_dan_lunas_bulan_ini(self):
        t1, _ = buat_langganan("Satu").buat_tagihan(self.periode)
        buat_langganan("Dua").buat_tagihan(self.periode)
        t1.tandai_lunas(date.today())
        r = self.client.get(reverse("laporan:dashboard"))
        self.assertEqual(r.context["total_tagihan"], Decimal("900000"))
        self.assertEqual(r.context["total_lunas"], Decimal("450000"))

    def test_tagihan_bulan_lain_tidak_dihitung(self):
        buat_langganan("Satu").buat_tagihan("2020-03")
        r = self.client.get(reverse("laporan:dashboard"))
        self.assertEqual(r.context["total_tagihan"], 0)

    def test_jumlah_menunggak_diperbarui_saat_dibuka(self):
        buat_langganan("Lama").buat_tagihan("2020-01")  # jatuh tempo sudah lewat
        r = self.client.get(reverse("laporan:dashboard"))
        self.assertEqual(r.context["jumlah_menunggak"], 1)

    def test_pelanggan_aktif_tidak_menghitung_nonaktif(self):
        buat_langganan("Aktif")
        buat_langganan("Nonaktif", status_pelanggan=Pelanggan.Status.NONAKTIF)
        r = self.client.get(reverse("laporan:dashboard"))
        self.assertEqual(r.context["pelanggan_aktif"], 1)

    def test_rekap_aset_per_kondisi(self):
        buat_aset("Kompor", Aset.Kondisi.BAIK)
        buat_aset("Blender", Aset.Kondisi.BAIK)
        buat_aset("Rice cooker", Aset.Kondisi.PERLU_PERAWATAN)
        r = self.client.get(reverse("laporan:dashboard"))
        self.assertEqual(
            dict(r.context["rekap_aset"]),
            {"Baik": 2, "Perlu perawatan": 1, "Rusak": 0},
        )


class LaporanTest(DasarLaporan):
    def setUp(self):
        super().setUp()
        self.asrama = buat_langganan("Pelanggan Asrama")
        self.kantor = buat_langganan("Pelanggan Kantor")
        self.kantor.pelanggan.segmen = Pelanggan.Segmen.KANTOR
        self.kantor.pelanggan.save()
        lunas, _ = self.asrama.buat_tagihan(self.periode)
        lunas.tandai_lunas(date.today())
        self.kantor.buat_tagihan(self.periode)

    def _baris(self, respons, segmen):
        return next(b for b in respons.context["baris"] if b["segmen"] == segmen)

    def test_hanya_untuk_admin(self):
        url = reverse("laporan:laporan")
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_bawaan_bulan_ini_per_segmen(self):
        r = self.client.get(reverse("laporan:laporan"))
        self.assertEqual(r.context["periode"], self.periode)
        self.assertEqual(len(r.context["baris"]), 2)
        asrama = self._baris(r, "Asrama")
        self.assertEqual(asrama["jumlah"], 1)
        self.assertEqual(asrama["total"], Decimal("450000"))
        self.assertEqual(asrama["lunas"], Decimal("450000"))

    def test_rincian_status_menjumlah_ke_total(self):
        r = self.client.get(reverse("laporan:laporan"))
        kantor = self._baris(r, "Kantor")
        self.assertEqual(kantor["lunas"], 0)
        self.assertEqual(kantor["belum"] + kantor["menunggak"], kantor["total"])

    def test_baris_jumlah(self):
        r = self.client.get(reverse("laporan:laporan"))
        self.assertEqual(r.context["total"]["jumlah"], 2)
        self.assertEqual(r.context["total"]["total"], Decimal("900000"))
        self.assertEqual(r.context["total"]["lunas"], Decimal("450000"))

    def test_filter_segmen(self):
        r = self.client.get(reverse("laporan:laporan"), {"segmen": "Kantor"})
        self.assertEqual([b["segmen"] for b in r.context["baris"]], ["Kantor"])

    def test_periode_tanpa_data(self):
        r = self.client.get(reverse("laporan:laporan"), {"periode": "2019-01"})
        self.assertEqual(r.context["baris"], [])
        self.assertContains(r, "Tidak ada hasil")

    def test_periode_tidak_valid_kembali_ke_bulan_ini(self):
        r = self.client.get(reverse("laporan:laporan"), {"periode": "abc"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["periode"], self.periode)

    def test_segmen_tidak_valid_diabaikan(self):
        r = self.client.get(reverse("laporan:laporan"), {"segmen": "Entah"})
        self.assertEqual(len(r.context["baris"]), 2)
