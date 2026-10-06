from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class Pelanggan(models.Model):
    class Segmen(models.TextChoices):
        ASRAMA = "Asrama", "Asrama"
        SEKOLAH = "Sekolah", "Sekolah"
        KANTOR = "Kantor", "Kantor"

    class Tipe(models.TextChoices):
        PERORANGAN = "Perorangan", "Perorangan"
        INSTANSI = "Instansi", "Instansi"

    class Status(models.TextChoices):
        AKTIF = "Aktif", "Aktif"
        NONAKTIF = "Nonaktif", "Nonaktif"

    # Satu akun login maksimal satu pelanggan. Admin tidak punya data pelanggan.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pelanggan",
    )
    nama = models.CharField(
        max_length=100,
        unique=True,
        error_messages={"unique": "Pelanggan dengan nama ini sudah ada"},
    )
    segmen = models.CharField(max_length=10, choices=Segmen.choices)
    tipe = models.CharField(max_length=12, choices=Tipe.choices)
    kontak = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                r"^\d{8,15}$",
                "Format nomor tidak valid. Gunakan angka, misalnya 0812xxxxxxx",
            )
        ],
    )
    alamat = models.TextField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.AKTIF
    )
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pelanggan"
        ordering = ["nama"]

    def punya_tagihan(self):
        """True bila salah satu langganan pelanggan ini sudah punya tagihan."""
        return self.langganan.filter(tagihan__isnull=False).exists()

    def nonaktifkan(self):
        self.status = self.Status.NONAKTIF
        self.save(update_fields=["status"])

    def aktifkan(self):
        self.status = self.Status.AKTIF
        self.save(update_fields=["status"])

    def hapus(self):
        """Hapus permanen, hanya boleh bila belum punya tagihan."""
        if self.punya_tagihan():
            raise ValidationError(
                "Pelanggan sudah punya tagihan sehingga tidak bisa dihapus. "
                "Nonaktifkan saja."
            )
        self.delete()

    def __str__(self):
        return self.nama


class Langganan(models.Model):
    class Status(models.TextChoices):
        AKTIF = "Aktif", "Aktif"
        SELESAI = "Selesai", "Selesai"

    # CASCADE: bila pelanggan dihapus, langganannya ikut terhapus
    pelanggan = models.ForeignKey(
        Pelanggan, on_delete=models.CASCADE, related_name="langganan"
    )
    # PROTECT: paket yang dipakai langganan tidak bisa dihapus (FR-24)
    paket = models.ForeignKey(
        "paket.Paket", on_delete=models.PROTECT, related_name="langganan"
    )
    tgl_mulai = models.DateField(default=date.today)
    jumlah_porsi = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.AKTIF
    )

    class Meta:
        db_table = "langganan"

    def clean(self):
        if (
            self.pelanggan_id
            and self.pelanggan.tipe == Pelanggan.Tipe.INSTANSI
            and not self.jumlah_porsi
        ):
            raise ValidationError(
                {"jumlah_porsi": "Jumlah porsi wajib diisi untuk pelanggan instansi"}
            )

    def buat_tagihan(self, periode):
        """Membuat tagihan untuk satu periode berformat 'YYYY-MM'.

        Mengembalikan (tagihan, dibuat). Bila tagihan periode itu sudah ada,
        tidak dibuat lagi dan dibuat bernilai False (untuk FR-14).
        """
        # Diimpor di sini agar pelanggan dan tagihan tidak saling mengimpor
        from tagihan.models import Tagihan

        tahun, bulan = (int(x) for x in periode.split("-"))
        return Tagihan.objects.get_or_create(
            langganan=self,
            periode=periode,
            defaults={
                "jumlah": Tagihan.hitung_total(self),
                "jatuh_tempo": date(tahun, bulan, 10),
            },
        )

    def __str__(self):
        return f"{self.pelanggan} - {self.paket}"
