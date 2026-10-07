from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from paket.models import Paket
from pelanggan.models import Langganan, Pelanggan

from .models import Tagihan


def buat_langganan(nama, tipe, tarif, satuan, porsi=None):
    paket = Paket.objects.create(
        nama_paket=f"Paket {nama}", tarif=Decimal(tarif), satuan_tarif=satuan
    )
    pel = Pelanggan.objects.create(
        nama=nama, segmen=Pelanggan.Segmen.ASRAMA, tipe=tipe,
        kontak="081234567890", alamat="Alamat contoh",
    )
    return Langganan.objects.create(pelanggan=pel, paket=paket, jumlah_porsi=porsi)


class HitungTotalTest(TestCase):
    def test_perorangan_memakai_tarif_paket(self):
        lang = buat_langganan(
            "Dewi", Pelanggan.Tipe.PERORANGAN, "450000", Paket.Satuan.PER_BULAN
        )
        self.assertEqual(Tagihan.hitung_total(lang), Decimal("450000"))

    def test_instansi_porsi_kali_tarif(self):
        lang = buat_langganan(
            "SMA", Pelanggan.Tipe.INSTANSI, "18000", Paket.Satuan.PER_PORSI, porsi=100
        )
        self.assertEqual(Tagihan.hitung_total(lang), Decimal("1800000"))


class BuatTagihanTest(TestCase):
    def setUp(self):
        self.lang = buat_langganan(
            "Dewi", Pelanggan.Tipe.PERORANGAN, "450000", Paket.Satuan.PER_BULAN
        )

    def test_tagihan_pertama_dibuat(self):
        tagihan, dibuat = self.lang.buat_tagihan("2026-10")
        self.assertTrue(dibuat)
        self.assertEqual(tagihan.jumlah, Decimal("450000"))
        self.assertEqual(tagihan.status, Tagihan.Status.BELUM)

    def test_jatuh_tempo_tanggal_10(self):
        tagihan, _ = self.lang.buat_tagihan("2026-10")
        self.assertEqual(tagihan.jatuh_tempo, date(2026, 10, 10))

    def test_tidak_ada_tagihan_ganda(self):
        self.lang.buat_tagihan("2026-10")
        _, dibuat = self.lang.buat_tagihan("2026-10")
        self.assertFalse(dibuat)
        self.assertEqual(Tagihan.objects.count(), 1)

    def test_periode_berbeda_boleh(self):
        self.lang.buat_tagihan("2026-10")
        _, dibuat = self.lang.buat_tagihan("2026-11")
        self.assertTrue(dibuat)
        self.assertEqual(Tagihan.objects.count(), 2)


class TandaiLunasTest(TestCase):
    def setUp(self):
        lang = buat_langganan(
            "Dewi", Pelanggan.Tipe.PERORANGAN, "450000", Paket.Satuan.PER_BULAN
        )
        self.tagihan, _ = lang.buat_tagihan("2026-10")

    def test_tanggal_valid_menjadi_lunas(self):
        hari_ini = date.today()
        self.tagihan.tandai_lunas(hari_ini)
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status, Tagihan.Status.LUNAS)
        self.assertEqual(self.tagihan.tgl_lunas, hari_ini)

    def test_tanggal_sebelum_terbit_ditolak(self):
        with self.assertRaises(ValidationError):
            self.tagihan.tandai_lunas(date(2000, 1, 1))
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status, Tagihan.Status.BELUM)

    def test_tanggal_bukan_tanggal_ditolak(self):
        with self.assertRaises(ValidationError):
            self.tagihan.tandai_lunas("bukan tanggal")

    def test_tagihan_sudah_lunas_ditolak(self):
        self.tagihan.tandai_lunas(date.today())
        with self.assertRaises(ValidationError):
            self.tagihan.tandai_lunas(date.today())


class CekTunggakanTest(TestCase):
    def test_lewat_jatuh_tempo_menjadi_menunggak(self):
        lang = buat_langganan(
            "Dewi", Pelanggan.Tipe.PERORANGAN, "450000", Paket.Satuan.PER_BULAN
        )
        lama, _ = lang.buat_tagihan("2026-09")   # jatuh tempo 10 Sep 2026
        baru, _ = lang.buat_tagihan("2026-10")   # jatuh tempo 10 Okt 2026
        jumlah = Tagihan.cek_tunggakan(hari_ini=date(2026, 10, 6))
        lama.refresh_from_db()
        baru.refresh_from_db()
        self.assertEqual(jumlah, 1)
        self.assertEqual(lama.status, Tagihan.Status.MENUNGGAK)
        self.assertEqual(baru.status, Tagihan.Status.BELUM)

    def test_tagihan_lunas_tidak_berubah(self):
        lang = buat_langganan(
            "Dewi", Pelanggan.Tipe.PERORANGAN, "450000", Paket.Satuan.PER_BULAN
        )
        tagihan, _ = lang.buat_tagihan("2026-09")
        tagihan.tandai_lunas(date.today())
        Tagihan.cek_tunggakan(hari_ini=date(2026, 10, 6))
        tagihan.refresh_from_db()
        self.assertEqual(tagihan.status, Tagihan.Status.LUNAS)
