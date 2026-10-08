from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from pelanggan.models import Langganan, Pelanggan

from . import layanan
from .models import Tagihan
from .pembantu_tes import buat_langganan


class LayananTagihanTest(TestCase):
    def test_hanya_langganan_aktif_milik_pelanggan_aktif_ditagih(self):
        buat_langganan("Aktif satu")
        buat_langganan("Aktif dua")
        buat_langganan("Pelanggan nonaktif", status_pelanggan=Pelanggan.Status.NONAKTIF)
        buat_langganan("Langganan selesai", status_langganan=Langganan.Status.SELESAI)
        dibuat, dilewati = layanan.buat_tagihan_periode("2026-10")
        self.assertEqual((dibuat, dilewati), (2, 0))
        self.assertEqual(Tagihan.objects.count(), 2)

    def test_dijalankan_dua_kali_tidak_menggandakan(self):
        buat_langganan("Aktif satu")
        buat_langganan("Aktif dua")
        layanan.buat_tagihan_periode("2026-10")
        dibuat, dilewati = layanan.buat_tagihan_periode("2026-10")
        self.assertEqual((dibuat, dilewati), (0, 2))
        self.assertEqual(Tagihan.objects.count(), 2)

    def test_hitung_belum_ditagih(self):
        lang = buat_langganan("Aktif satu")
        buat_langganan("Aktif dua")
        self.assertEqual(layanan.hitung_belum_ditagih("2026-10"), 2)
        lang.buat_tagihan("2026-10")
        self.assertEqual(layanan.hitung_belum_ditagih("2026-10"), 1)

    def test_periode_tidak_valid_ditolak(self):
        for periode in ("2026-13", "2026-1", "Okt 2026", "", None):
            with self.assertRaises(ValueError):
                layanan.periksa_periode(periode)

    def test_label_periode(self):
        self.assertEqual(layanan.label_periode("2026-10"), "Okt 2026")
        self.assertEqual(layanan.label_periode("2026-01"), "Jan 2026")
        self.assertEqual(layanan.label_periode("bukan periode"), "bukan periode")


class PerintahBuatTagihanTest(TestCase):
    def test_perintah_membuat_tagihan(self):
        buat_langganan("Aktif satu")
        keluaran = StringIO()
        call_command("buat_tagihan", periode="2026-10", stdout=keluaran)
        self.assertIn("1 tagihan dibuat", keluaran.getvalue())
        self.assertEqual(Tagihan.objects.filter(periode="2026-10").count(), 1)

    def test_perintah_tanpa_periode_memakai_bulan_ini(self):
        buat_langganan("Aktif satu")
        call_command("buat_tagihan", stdout=StringIO())
        self.assertTrue(
            Tagihan.objects.filter(periode=layanan.periode_sekarang()).exists()
        )

    def test_perintah_dengan_periode_salah_ditolak(self):
        with self.assertRaises(CommandError):
            call_command("buat_tagihan", periode="2026-13", stdout=StringIO())
