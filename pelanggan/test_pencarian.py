from django.test import TestCase
from django.urls import reverse

from akun.models import Pengguna

from .models import Pelanggan


def buat(nama, segmen=Pelanggan.Segmen.ASRAMA, status=Pelanggan.Status.AKTIF):
    return Pelanggan.objects.create(
        nama=nama, segmen=segmen, tipe=Pelanggan.Tipe.PERORANGAN,
        kontak="081234567890", alamat="Alamat contoh", status=status,
    )


class PencarianPelangganTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Pengguna.objects.create_user(
            "admin1", password="rahasia123", role=Pengguna.Peran.ADMIN
        )

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse("pelanggan:daftar")

    def test_cari_nama_sebagian_tanpa_peka_huruf_besar(self):
        buat("Dewi Anggraini")
        buat("Budi Santoso")
        r = self.client.get(self.url, {"q": "dewi"})
        self.assertContains(r, "Dewi Anggraini")
        self.assertNotContains(r, "Budi Santoso")

    def test_filter_segmen(self):
        buat("Pelanggan Asrama", segmen=Pelanggan.Segmen.ASRAMA)
        buat("Pelanggan Kantor", segmen=Pelanggan.Segmen.KANTOR)
        r = self.client.get(self.url, {"segmen": "Kantor"})
        self.assertContains(r, "Pelanggan Kantor")
        self.assertNotContains(r, "Pelanggan Asrama")

    def test_filter_status(self):
        buat("Pelanggan Aktif")
        buat("Pelanggan Nonaktif", status=Pelanggan.Status.NONAKTIF)
        r = self.client.get(self.url, {"status": "Nonaktif"})
        self.assertContains(r, "Pelanggan Nonaktif")
        self.assertNotContains(r, "Pelanggan Aktif")

    def test_gabungan_pencarian_dan_filter(self):
        buat("Budi Asrama", segmen=Pelanggan.Segmen.ASRAMA)
        buat("Budi Kantor", segmen=Pelanggan.Segmen.KANTOR)
        buat("Dewi Kantor", segmen=Pelanggan.Segmen.KANTOR)
        r = self.client.get(self.url, {"q": "budi", "segmen": "Kantor"})
        self.assertContains(r, "Budi Kantor")
        self.assertNotContains(r, "Budi Asrama")
        self.assertNotContains(r, "Dewi Kantor")

    def test_tidak_ada_hasil(self):
        buat("Dewi Anggraini")
        r = self.client.get(self.url, {"q": "zzz"})
        self.assertContains(r, "Tidak ada hasil")
        self.assertNotContains(r, "Belum ada pelanggan")

    def test_tanpa_data_dan_tanpa_filter(self):
        r = self.client.get(self.url)
        self.assertContains(r, "Belum ada pelanggan")

    def test_nilai_filter_tidak_valid_diabaikan(self):
        buat("Dewi Anggraini")
        buat("Budi Santoso")
        r = self.client.get(self.url, {"segmen": "Bukan segmen", "status": "Entah"})
        self.assertContains(r, "Dewi Anggraini")
        self.assertContains(r, "Budi Santoso")

    def test_halaman_berikutnya_mempertahankan_filter(self):
        for i in range(16):
            buat(f"Budi {i:02d}")
        r = self.client.get(self.url, {"q": "Budi"})
        self.assertContains(r, "q=Budi&page=2")
