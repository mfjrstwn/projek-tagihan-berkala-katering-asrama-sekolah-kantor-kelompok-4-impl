from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from akun.models import Pengguna
from paket.models import Paket

from .models import Langganan, Pelanggan


def buat_pelanggan(nama, tipe=Pelanggan.Tipe.PERORANGAN, paket=None, porsi=None):
    pel = Pelanggan.objects.create(
        nama=nama, segmen=Pelanggan.Segmen.ASRAMA, tipe=tipe,
        kontak="081234567890", alamat="Alamat contoh",
    )
    if paket:
        Langganan.objects.create(pelanggan=pel, paket=paket, jumlah_porsi=porsi)
    return pel


class AturanHapusPelangganTest(TestCase):
    def setUp(self):
        self.paket = Paket.objects.create(
            nama_paket="Makan siang", tarif=Decimal("450000"),
            satuan_tarif=Paket.Satuan.PER_BULAN,
        )
        self.bersih = buat_pelanggan("Pelanggan Bersih", paket=self.paket)
        self.bertagihan = buat_pelanggan("Pelanggan Bertagihan", paket=self.paket)
        self.bertagihan.langganan.first().buat_tagihan("2026-10")

    def test_punya_tagihan(self):
        self.assertFalse(self.bersih.punya_tagihan())
        self.assertTrue(self.bertagihan.punya_tagihan())

    def test_pelanggan_tanpa_tagihan_bisa_dihapus(self):
        self.bersih.hapus()
        self.assertFalse(Pelanggan.objects.filter(pk=self.bersih.pk).exists())
        self.assertEqual(Langganan.objects.filter(pelanggan_id=self.bersih.pk).count(), 0)

    def test_pelanggan_bertagihan_tidak_bisa_dihapus(self):
        with self.assertRaises(ValidationError):
            self.bertagihan.hapus()
        self.assertTrue(Pelanggan.objects.filter(pk=self.bertagihan.pk).exists())

    def test_basis_data_menolak_hapus_langsung(self):
        # Lapisan pengaman kedua: PROTECT di basis data
        with self.assertRaises(ProtectedError):
            self.bertagihan.delete()

    def test_nonaktifkan_dan_aktifkan(self):
        self.bertagihan.nonaktifkan()
        self.bertagihan.refresh_from_db()
        self.assertEqual(self.bertagihan.status, Pelanggan.Status.NONAKTIF)
        self.bertagihan.aktifkan()
        self.bertagihan.refresh_from_db()
        self.assertEqual(self.bertagihan.status, Pelanggan.Status.AKTIF)


class HalamanPelangganTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Pengguna.objects.create_user(
            "admin1", password="rahasia123", role=Pengguna.Peran.ADMIN
        )
        cls.customer = Pengguna.objects.create_user("cust1", password="rahasia123")
        cls.paket = Paket.objects.create(
            nama_paket="Makan siang", tarif=Decimal("450000"),
            satuan_tarif=Paket.Satuan.PER_BULAN,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def data_valid(self, **tambahan):
        data = {
            "nama": "Dewi Anggraini", "segmen": "Asrama", "tipe": "Perorangan",
            "kontak": "081234567890", "alamat": "Asrama Putri Melati",
            "paket": self.paket.pk, "jumlah_porsi": "",
        }
        data.update(tambahan)
        return data

    # --- Hak akses ---
    def test_daftar_hanya_untuk_admin(self):
        url = reverse("pelanggan:daftar")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_daftar_kosong_menampilkan_pesan(self):
        r = self.client.get(reverse("pelanggan:daftar"))
        self.assertContains(r, "Belum ada pelanggan")

    # --- Tambah ---
    def test_tambah_pelanggan_perorangan_berhasil(self):
        r = self.client.post(reverse("pelanggan:tambah"), self.data_valid(), follow=True)
        self.assertContains(r, "Pelanggan berhasil disimpan")
        pel = Pelanggan.objects.get(nama="Dewi Anggraini")
        self.assertEqual(pel.status, Pelanggan.Status.AKTIF)
        self.assertEqual(pel.langganan.count(), 1)

    def test_tambah_instansi_tanpa_porsi_ditolak(self):
        r = self.client.post(
            reverse("pelanggan:tambah"),
            self.data_valid(nama="SMA Contoh", tipe="Instansi"),
        )
        self.assertContains(r, "Jumlah porsi wajib diisi untuk pelanggan instansi")
        self.assertFalse(Pelanggan.objects.filter(nama="SMA Contoh").exists())

    def test_tambah_instansi_dengan_porsi_berhasil(self):
        self.client.post(
            reverse("pelanggan:tambah"),
            self.data_valid(nama="SMA Contoh", tipe="Instansi", jumlah_porsi="300"),
        )
        self.assertEqual(Langganan.objects.get(pelanggan__nama="SMA Contoh").jumlah_porsi, 300)

    def test_tambah_nama_duplikat_ditolak(self):
        self.client.post(reverse("pelanggan:tambah"), self.data_valid())
        r = self.client.post(reverse("pelanggan:tambah"), self.data_valid())
        self.assertContains(r, "Pelanggan dengan nama ini sudah ada")
        self.assertEqual(Pelanggan.objects.filter(nama="Dewi Anggraini").count(), 1)

    def test_tambah_kontak_tidak_valid_ditolak(self):
        r = self.client.post(reverse("pelanggan:tambah"), self.data_valid(kontak="abc"))
        self.assertContains(r, "Format nomor tidak valid")

    def test_tambah_nama_kosong_ditolak(self):
        r = self.client.post(reverse("pelanggan:tambah"), self.data_valid(nama=""))
        self.assertContains(r, "Nama wajib diisi")

    # --- Ubah ---
    def test_ubah_pelanggan_berhasil(self):
        pel = buat_pelanggan("Budi", paket=self.paket)
        r = self.client.post(
            reverse("pelanggan:ubah", args=[pel.pk]),
            self.data_valid(nama="Budi Santoso"), follow=True,
        )
        self.assertContains(r, "Pelanggan berhasil disimpan")
        pel.refresh_from_db()
        self.assertEqual(pel.nama, "Budi Santoso")
        self.assertEqual(pel.langganan.count(), 1)  # tidak menambah langganan baru

    # --- Hapus atau nonaktifkan ---
    def test_konfirmasi_hapus_untuk_pelanggan_tanpa_tagihan(self):
        pel = buat_pelanggan("Tanpa Tagihan", paket=self.paket)
        r = self.client.get(reverse("pelanggan:hapus", args=[pel.pk]))
        self.assertContains(r, "Hapus pelanggan?")

    def test_konfirmasi_nonaktifkan_untuk_pelanggan_bertagihan(self):
        pel = buat_pelanggan("Bertagihan", paket=self.paket)
        pel.langganan.first().buat_tagihan("2026-10")
        r = self.client.get(reverse("pelanggan:hapus", args=[pel.pk]))
        self.assertContains(r, "Nonaktifkan pelanggan?")

    def test_post_hapus_pelanggan_tanpa_tagihan(self):
        pel = buat_pelanggan("Tanpa Tagihan", paket=self.paket)
        r = self.client.post(reverse("pelanggan:hapus", args=[pel.pk]), follow=True)
        self.assertContains(r, "Data berhasil dihapus")
        self.assertFalse(Pelanggan.objects.filter(pk=pel.pk).exists())

    def test_post_hapus_pelanggan_bertagihan_menjadi_nonaktif(self):
        pel = buat_pelanggan("Bertagihan", paket=self.paket)
        pel.langganan.first().buat_tagihan("2026-10")
        r = self.client.post(reverse("pelanggan:hapus", args=[pel.pk]), follow=True)
        self.assertContains(r, "Pelanggan dinonaktifkan")
        pel.refresh_from_db()
        self.assertEqual(pel.status, Pelanggan.Status.NONAKTIF)
        self.assertTrue(pel.langganan.first().tagihan.exists())  # riwayat utuh

    def test_aktifkan_kembali(self):
        pel = buat_pelanggan("Nonaktif", paket=self.paket)
        pel.nonaktifkan()
        r = self.client.post(reverse("pelanggan:aktifkan", args=[pel.pk]), follow=True)
        self.assertContains(r, "Pelanggan diaktifkan kembali")
        pel.refresh_from_db()
        self.assertEqual(pel.status, Pelanggan.Status.AKTIF)


class AtributGalatFormTest(TestCase):
    """Isian yang bermasalah terhubung ke pesan galatnya untuk pembaca layar."""

    def test_isian_bermasalah_menunjuk_ke_pesan_galat(self):
        admin = Pengguna.objects.create_user(
            "admin_aria", password="rahasia123", role=Pengguna.Peran.ADMIN
        )
        self.client.force_login(admin)
        r = self.client.post(reverse("pelanggan:tambah"), {"nama": ""})
        self.assertContains(r, 'aria-invalid="true"')
        self.assertContains(r, 'aria-describedby="galat-nama"')
        self.assertContains(r, 'id="galat-nama"')
