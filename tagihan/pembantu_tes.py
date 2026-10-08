"""Fungsi bantu untuk unit test tagihan (bukan test)."""

from decimal import Decimal

from paket.models import Paket
from pelanggan.models import Langganan, Pelanggan


def buat_langganan(nama, status_pelanggan=Pelanggan.Status.AKTIF,
                   status_langganan=Langganan.Status.AKTIF):
    paket, _ = Paket.objects.get_or_create(
        nama_paket="Makan siang",
        defaults={"tarif": Decimal("450000"), "satuan_tarif": Paket.Satuan.PER_BULAN},
    )
    pelanggan = Pelanggan.objects.create(
        nama=nama, segmen=Pelanggan.Segmen.ASRAMA,
        tipe=Pelanggan.Tipe.PERORANGAN, kontak="081234567890",
        alamat="Alamat contoh", status=status_pelanggan,
    )
    return Langganan.objects.create(
        pelanggan=pelanggan, paket=paket, status=status_langganan
    )
