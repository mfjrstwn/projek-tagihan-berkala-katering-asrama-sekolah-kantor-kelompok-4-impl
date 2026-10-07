from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from akun.models import Pengguna

from .models import Aset


def buat_aset(nama="Kompor industri", kondisi=Aset.Kondisi.BAIK):
    return Aset.objects.create(
        nama=nama, kategori="Produksi", tgl_perolehan=date(2025, 1, 10),
        nilai=Decimal("4500000"), kondisi=kondisi,
    )


class HalamanAsetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Pengguna.objects.create_user(
            "admin1", password="rahasia123", role=Pengguna.Peran.ADMIN
        )
        cls.customer = Pengguna.objects.create_user("cust1", password="rahasia123")

    def setUp(self):
        self.client.force_login(self.admin)

    def data_valid(self, **tambahan):
        data = {
            "nama": "Kompor industri", "kategori": "Produksi",
            "tgl_perolehan": "2025-01-10", "nilai": "4500000",
            "kondisi": "Baik", "catatan": "",
        }
        data.update(tambahan)
        return data

    def test_daftar_hanya_untuk_admin(self):
        url = reverse("aset:daftar")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_daftar_kosong_menampilkan_pesan(self):
        self.assertContains(self.client.get(reverse("aset:daftar")), "Belum ada aset")

    def test_daftar_menampilkan_aset(self):
        buat_aset()
        self.assertContains(self.client.get(reverse("aset:daftar")), "Kompor industri")

    def test_tambah_aset_berhasil(self):
        r = self.client.post(reverse("aset:tambah"), self.data_valid(), follow=True)
        self.assertContains(r, "Aset berhasil disimpan")
        self.assertTrue(Aset.objects.filter(nama="Kompor industri").exists())

    def test_nilai_bukan_angka_ditolak(self):
        r = self.client.post(reverse("aset:tambah"), self.data_valid(nilai="abc"))
        self.assertContains(r, "Nilai harus berupa angka")
        self.assertEqual(Aset.objects.count(), 0)

    def test_nilai_negatif_ditolak(self):
        r = self.client.post(reverse("aset:tambah"), self.data_valid(nilai="-1"))
        self.assertContains(r, "Nilai tidak boleh negatif")

    def test_tanggal_tidak_valid_ditolak(self):
        r = self.client.post(reverse("aset:tambah"), self.data_valid(tgl_perolehan="bukan-tanggal"))
        self.assertContains(r, "Format tanggal tidak valid")

    def test_tanggal_masa_depan_ditolak(self):
        besok = (date.today() + timedelta(days=30)).isoformat()
        r = self.client.post(reverse("aset:tambah"), self.data_valid(tgl_perolehan=besok))
        self.assertContains(r, "Tanggal perolehan tidak boleh di masa depan")

    def test_nama_kosong_ditolak(self):
        r = self.client.post(reverse("aset:tambah"), self.data_valid(nama=""))
        self.assertContains(r, "Nama aset wajib diisi")

    def test_perbarui_kondisi_aset(self):
        aset = buat_aset()
        r = self.client.post(
            reverse("aset:ubah", args=[aset.pk]),
            self.data_valid(kondisi="Rusak"), follow=True,
        )
        self.assertContains(r, "Aset berhasil disimpan")
        aset.refresh_from_db()
        self.assertEqual(aset.kondisi, Aset.Kondisi.RUSAK)

    def test_konfirmasi_hapus_aset(self):
        aset = buat_aset()
        r = self.client.get(reverse("aset:hapus", args=[aset.pk]))
        self.assertContains(r, "Hapus aset?")

    def test_hapus_aset_berhasil(self):
        aset = buat_aset()
        r = self.client.post(reverse("aset:hapus", args=[aset.pk]), follow=True)
        self.assertContains(r, "Data berhasil dihapus")
        self.assertFalse(Aset.objects.filter(pk=aset.pk).exists())
