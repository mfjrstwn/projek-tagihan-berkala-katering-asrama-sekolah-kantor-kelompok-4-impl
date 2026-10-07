from decimal import Decimal

from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from akun.models import Pengguna
from pelanggan.models import Langganan, Pelanggan

from .models import Paket


def buat_paket(nama="Makan siang", tarif="450000"):
    return Paket.objects.create(
        nama_paket=nama, tarif=Decimal(tarif), satuan_tarif=Paket.Satuan.PER_BULAN
    )


def pakai_paket(paket, nama_pelanggan="Dewi"):
    pel = Pelanggan.objects.create(
        nama=nama_pelanggan, segmen=Pelanggan.Segmen.ASRAMA,
        tipe=Pelanggan.Tipe.PERORANGAN, kontak="081234567890", alamat="Alamat",
    )
    return Langganan.objects.create(pelanggan=pel, paket=paket)


class PaketModelTest(TestCase):
    def test_paket_baru_belum_dipakai(self):
        self.assertFalse(buat_paket().masih_dipakai())

    def test_paket_dipakai_langganan(self):
        paket = buat_paket()
        pakai_paket(paket)
        self.assertTrue(paket.masih_dipakai())

    def test_basis_data_menolak_hapus_paket_dipakai(self):
        paket = buat_paket()
        pakai_paket(paket)
        with self.assertRaises(ProtectedError):
            paket.delete()


class HalamanPaketTest(TestCase):
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
            "nama_paket": "Makan siang", "tarif": "450000",
            "satuan_tarif": "Per bulan", "periode": "Bulanan",
        }
        data.update(tambahan)
        return data

    def test_daftar_hanya_untuk_admin(self):
        url = reverse("paket:daftar")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_daftar_kosong_menampilkan_pesan(self):
        self.assertContains(self.client.get(reverse("paket:daftar")), "Belum ada paket")

    def test_tambah_paket_berhasil(self):
        r = self.client.post(reverse("paket:tambah"), self.data_valid(), follow=True)
        self.assertContains(r, "Paket berhasil disimpan")
        self.assertTrue(Paket.objects.filter(nama_paket="Makan siang").exists())

    def test_tambah_nama_duplikat_ditolak(self):
        buat_paket()
        r = self.client.post(reverse("paket:tambah"), self.data_valid())
        self.assertContains(r, "Paket dengan nama ini sudah ada")
        self.assertEqual(Paket.objects.count(), 1)

    def test_tarif_bukan_angka_ditolak(self):
        r = self.client.post(reverse("paket:tambah"), self.data_valid(tarif="abc"))
        self.assertContains(r, "Tarif harus berupa angka")
        self.assertEqual(Paket.objects.count(), 0)

    def test_tarif_negatif_ditolak(self):
        r = self.client.post(reverse("paket:tambah"), self.data_valid(tarif="-100"))
        self.assertContains(r, "Tarif tidak boleh negatif")

    def test_nama_kosong_ditolak(self):
        r = self.client.post(reverse("paket:tambah"), self.data_valid(nama_paket=""))
        self.assertContains(r, "Nama paket wajib diisi")

    def test_ubah_paket_berhasil(self):
        paket = buat_paket()
        r = self.client.post(
            reverse("paket:ubah", args=[paket.pk]),
            self.data_valid(tarif="500000"), follow=True,
        )
        self.assertContains(r, "Paket berhasil disimpan")
        paket.refresh_from_db()
        self.assertEqual(paket.tarif, Decimal("500000"))

    def test_hapus_paket_tidak_dipakai_berhasil(self):
        paket = buat_paket()
        r = self.client.post(reverse("paket:hapus", args=[paket.pk]), follow=True)
        self.assertContains(r, "Data berhasil dihapus")
        self.assertFalse(Paket.objects.filter(pk=paket.pk).exists())

    def test_hapus_paket_dipakai_ditolak(self):
        paket = buat_paket()
        pakai_paket(paket)
        r = self.client.post(reverse("paket:hapus", args=[paket.pk]), follow=True)
        self.assertContains(r, "masih dipakai pelanggan dan tidak bisa dihapus")
        self.assertTrue(Paket.objects.filter(pk=paket.pk).exists())
