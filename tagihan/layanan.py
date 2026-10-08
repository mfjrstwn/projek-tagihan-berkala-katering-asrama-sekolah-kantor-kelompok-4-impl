"""Logika pembuatan tagihan yang dipakai bersama oleh tombol di halaman
dan perintah otomatis (manage.py buat_tagihan)."""

import re
from datetime import date

from django.db import transaction

from pelanggan.models import Langganan, Pelanggan

NAMA_BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
              "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
POLA_PERIODE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def periode_sekarang(hari_ini=None):
    hari_ini = hari_ini or date.today()
    return f"{hari_ini.year}-{hari_ini.month:02d}"


def periksa_periode(periode):
    if not POLA_PERIODE.match(periode or ""):
        raise ValueError("Format periode harus YYYY-MM, misalnya 2026-10")
    return periode


def label_periode(periode):
    """'2026-10' menjadi 'Okt 2026'. Nilai yang tidak dikenali dikembalikan apa adanya."""
    try:
        periksa_periode(periode)
        tahun, bulan = periode.split("-")
        return f"{NAMA_BULAN[int(bulan) - 1]} {tahun}"
    except (ValueError, AttributeError):
        return periode


def langganan_yang_ditagih():
    """Hanya langganan aktif milik pelanggan aktif yang ditagih."""
    return Langganan.objects.filter(
        status=Langganan.Status.AKTIF, pelanggan__status=Pelanggan.Status.AKTIF
    )


def hitung_belum_ditagih(periode):
    return langganan_yang_ditagih().exclude(tagihan__periode=periode).count()


@transaction.atomic
def buat_tagihan_periode(periode):
    """Membuat tagihan satu periode untuk semua langganan yang berhak.

    Mengembalikan (jumlah_dibuat, jumlah_dilewati). Langganan yang sudah punya
    tagihan di periode itu dilewati (FR-14).
    """
    periksa_periode(periode)
    dibuat = dilewati = 0
    for langganan in langganan_yang_ditagih().select_related("pelanggan", "paket"):
        _, baru = langganan.buat_tagihan(periode)
        if baru:
            dibuat += 1
        else:
            dilewati += 1
    return dibuat, dilewati
