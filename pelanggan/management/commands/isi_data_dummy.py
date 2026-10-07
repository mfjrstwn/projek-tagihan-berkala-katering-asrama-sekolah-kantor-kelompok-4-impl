from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from aset.models import Aset
from paket.models import Paket
from pelanggan.models import Langganan, Pelanggan
from tagihan.models import Tagihan

PASSWORD_DEMO = "demo12345"

# (nama paket, tarif, satuan). "Sarapan" sengaja tidak dipakai siapa pun,
# untuk menguji bahwa paket yang tidak dipakai boleh dihapus (FR-24).
DATA_PAKET = [
    ("Makan siang", Decimal("450000"), Paket.Satuan.PER_BULAN),
    ("Siang + malam", Decimal("800000"), Paket.Satuan.PER_BULAN),
    ("Instansi", Decimal("18000"), Paket.Satuan.PER_PORSI),
    ("Sarapan", Decimal("250000"), Paket.Satuan.PER_BULAN),
]

NAMA_ASRAMA = [
    "Dewi Anggraini", "Rizky Pratama", "Siti Nurhaliza", "Budi Santoso",
    "Ayu Lestari", "Andi Wijaya", "Nadia Putri", "Fajar Ramadhan",
    "Intan Permata", "Rahmat Hidayat", "Maya Sari", "Dimas Prasetyo",
    "Putri Amelia", "Yoga Saputra", "Lina Marlina", "Hendra Gunawan",
    "Citra Dewanti", "Eko Susanto",
]
LOKASI_ASRAMA = ["Asrama Putri Melati", "Asrama Putra Mawar", "Asrama Mahasiswa Kenanga"]
SEKOLAH = [("SMA Harapan Bangsa", 350), ("SMP Tunas Mulia", 280),
           ("SD Cahaya Bangsa", 220), ("MA Al-Hikmah", 300)]
KANTOR = [("PT Maju Bersama", 240), ("CV Karya Mandiri", 150),
          ("Kantor Desa Sukamaju", 90)]

# (nama, kategori, tanggal perolehan, nilai, kondisi): 5 baik, 2 perlu perawatan, 1 rusak
DATA_ASET = [
    ("Kompor industri 2 tungku", "Produksi", date(2025, 1, 10), "4500000", Aset.Kondisi.BAIK),
    ("Rice cooker 35 L", "Produksi", date(2025, 3, 5), "3200000", Aset.Kondisi.PERLU_PERAWATAN),
    ("Food tray stainless (200)", "Kemasan", date(2025, 6, 20), "2800000", Aset.Kondisi.BAIK),
    ("Motor box antar", "Distribusi", date(2024, 8, 15), "14000000", Aset.Kondisi.RUSAK),
    ("Freezer 2 pintu", "Penyimpanan", date(2025, 2, 1), "7500000", Aset.Kondisi.BAIK),
    ("Blender industri", "Produksi", date(2025, 4, 12), "2100000", Aset.Kondisi.BAIK),
    ("Dispenser air", "Pendukung", date(2024, 11, 3), "1200000", Aset.Kondisi.PERLU_PERAWATAN),
    ("Panci besar 50 L", "Produksi", date(2025, 5, 8), "950000", Aset.Kondisi.BAIK),
]

# username -> (peran, nama pelanggan yang ditautkan atau None)
AKUN_DEMO = {
    "admin_demo": ("Admin", None),
    "dewi": ("Customer", "Dewi Anggraini"),
    "rizky": ("Customer", "Rizky Pratama"),          # pelanggan nonaktif
    "sma_harapan": ("Customer", "SMA Harapan Bangsa"),
}


def daftar_periode(hari_ini):
    """Tiga bulan terakhir (dua bulan lalu, bulan lalu, bulan ini)."""
    hasil = []
    for selisih in (2, 1, 0):
        tahun, bulan = hari_ini.year, hari_ini.month - selisih
        while bulan < 1:
            bulan += 12
            tahun -= 1
        hasil.append((tahun, bulan))
    return hasil


def tentukan_status(urut_periode, indeks, jatuh_tempo, tahun, bulan):
    """Mengembalikan (status, tgl_lunas) agar datanya bervariasi."""
    S = Tagihan.Status
    if urut_periode == 0:  # dua bulan lalu
        if indeks % 11 == 0:
            return S.MENUNGGAK, None
        return S.LUNAS, jatuh_tempo - timedelta(days=2)
    if urut_periode == 1:  # bulan lalu
        if indeks % 7 == 0:
            return S.MENUNGGAK, None
        if indeks % 7 == 1:
            return S.BELUM, None  # sudah lewat jatuh tempo: bahan uji cek_tunggakan
        return S.LUNAS, jatuh_tempo - timedelta(days=2)
    # bulan ini
    if indeks % 3 == 0:
        return S.LUNAS, date(tahun, bulan, 2)
    return S.BELUM, None


class Command(BaseCommand):
    help = "Mengisi basis data dengan data dummy untuk pengembangan dan pengujian"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Hapus dulu semua paket, pelanggan, tagihan, aset, dan akun demo",
        )

    @transaction.atomic
    def handle(self, *args, **opsi):
        if opsi["reset"]:
            self._reset()
        paket = self._buat_paket()
        self._buat_pelanggan_dan_tagihan(paket)
        self._buat_aset()
        self._buat_akun()
        self.stdout.write(self.style.SUCCESS("Data dummy selesai dibuat."))
        self.stdout.write(
            f"Paket: {Paket.objects.count()} | Pelanggan: {Pelanggan.objects.count()} | "
            f"Tagihan: {Tagihan.objects.count()} | Aset: {Aset.objects.count()}"
        )
        self.stdout.write(f"Akun demo: {', '.join(AKUN_DEMO)} (password: {PASSWORD_DEMO})")

    def _reset(self):
        Tagihan.objects.all().delete()
        Langganan.objects.all().delete()
        Pelanggan.objects.all().delete()
        Paket.objects.all().delete()
        Aset.objects.all().delete()
        get_user_model().objects.filter(username__in=AKUN_DEMO).delete()

    def _buat_paket(self):
        hasil = {}
        for nama, tarif, satuan in DATA_PAKET:
            obj, _ = Paket.objects.get_or_create(
                nama_paket=nama, defaults={"tarif": tarif, "satuan_tarif": satuan}
            )
            hasil[nama] = obj
        return hasil

    def _susun_pelanggan(self):
        spek = []
        for i, nama in enumerate(NAMA_ASRAMA):
            mode = "normal"
            if nama == "Rizky Pratama":
                mode = "nonaktif"        # bahan uji: pelanggan nonaktif
            if nama == "Eko Susanto":
                mode = "tanpa_tagihan"   # bahan uji: hapus permanen boleh
            spek.append(dict(
                nama=nama, segmen=Pelanggan.Segmen.ASRAMA,
                tipe=Pelanggan.Tipe.PERORANGAN, alamat=LOKASI_ASRAMA[i % 3],
                paket="Makan siang" if i % 3 else "Siang + malam",
                porsi=None, mode=mode,
            ))
        for i, (nama, porsi) in enumerate(SEKOLAH):
            spek.append(dict(
                nama=nama, segmen=Pelanggan.Segmen.SEKOLAH,
                tipe=Pelanggan.Tipe.INSTANSI, alamat=f"Jl. Pendidikan No. {10 + i}",
                paket="Instansi", porsi=porsi, mode="normal",
            ))
        for i, (nama, porsi) in enumerate(KANTOR):
            spek.append(dict(
                nama=nama, segmen=Pelanggan.Segmen.KANTOR,
                tipe=Pelanggan.Tipe.INSTANSI, alamat=f"Jl. Niaga No. {5 + i}",
                paket="Instansi", porsi=porsi, mode="normal",
            ))
        return spek

    def _buat_pelanggan_dan_tagihan(self, paket):
        hari_ini = date.today()
        periode = daftar_periode(hari_ini)
        tgl_mulai = date(periode[0][0], periode[0][1], 1)
        for indeks, s in enumerate(self._susun_pelanggan()):
            status = (
                Pelanggan.Status.NONAKTIF if s["mode"] == "nonaktif"
                else Pelanggan.Status.AKTIF
            )
            pel, _ = Pelanggan.objects.get_or_create(
                nama=s["nama"],
                defaults={
                    "segmen": s["segmen"], "tipe": s["tipe"],
                    "kontak": f"0812345{indeks + 1:04d}",
                    "alamat": s["alamat"], "status": status,
                },
            )
            lang, _ = Langganan.objects.get_or_create(
                pelanggan=pel, paket=paket[s["paket"]],
                defaults={"jumlah_porsi": s["porsi"], "tgl_mulai": tgl_mulai},
            )
            if s["mode"] == "tanpa_tagihan":
                continue
            for urut, (tahun, bulan) in enumerate(periode):
                if s["mode"] == "nonaktif" and urut == 2:
                    continue  # pelanggan nonaktif tidak ditagih bulan ini
                tagihan, dibuat = lang.buat_tagihan(f"{tahun}-{bulan:02d}")
                if dibuat:
                    st, tgl_lunas = tentukan_status(
                        urut, indeks, tagihan.jatuh_tempo, tahun, bulan
                    )
                    Tagihan.objects.filter(pk=tagihan.pk).update(
                        status=st, tgl_lunas=tgl_lunas,
                        tgl_terbit=date(tahun, bulan, 1),
                    )

    def _buat_aset(self):
        for nama, kategori, tgl, nilai, kondisi in DATA_ASET:
            Aset.objects.get_or_create(
                nama=nama,
                defaults={"kategori": kategori, "tgl_perolehan": tgl,
                          "nilai": Decimal(nilai), "kondisi": kondisi},
            )

    def _buat_akun(self):
        User = get_user_model()
        for username, (peran, nama_pelanggan) in AKUN_DEMO.items():
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User.objects.create_user(
                    username=username, password=PASSWORD_DEMO,
                    role=peran, is_staff=(peran == "Admin"),
                )
            if nama_pelanggan:
                Pelanggan.objects.filter(nama=nama_pelanggan, user__isnull=True).update(user=user)
