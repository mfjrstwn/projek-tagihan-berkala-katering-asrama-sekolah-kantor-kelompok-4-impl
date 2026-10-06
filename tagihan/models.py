from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from pelanggan.models import Pelanggan


class Tagihan(models.Model):
    class Status(models.TextChoices):
        BELUM = "Belum dibayar", "Belum dibayar"
        LUNAS = "Lunas", "Lunas"
        MENUNGGAK = "Menunggak", "Menunggak"

    # PROTECT: langganan yang sudah punya tagihan tidak bisa dihapus
    langganan = models.ForeignKey(
        "pelanggan.Langganan", on_delete=models.PROTECT, related_name="tagihan"
    )
    periode = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                r"^\d{4}-(0[1-9]|1[0-2])$", "Format periode harus YYYY-MM"
            )
        ],
    )
    jumlah = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    tgl_terbit = models.DateField(default=date.today)
    jatuh_tempo = models.DateField()
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.BELUM
    )
    tgl_lunas = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "tagihan"
        ordering = ["-periode", "langganan"]
        constraints = [
            # Satu langganan hanya boleh punya satu tagihan per periode (FR-14)
            models.UniqueConstraint(
                fields=["langganan", "periode"], name="tagihan_unik_per_periode"
            )
        ]

    @staticmethod
    def hitung_total(langganan):
        """Perorangan: tarif paket. Instansi: jumlah porsi x tarif (FR-12)."""
        tarif = langganan.paket.tarif
        if langganan.pelanggan.tipe == Pelanggan.Tipe.INSTANSI:
            return Decimal(langganan.jumlah_porsi or 0) * tarif
        return tarif

    def tandai_lunas(self, tanggal):
        if self.status == self.Status.LUNAS:
            raise ValidationError("Tagihan ini sudah lunas")
        if not isinstance(tanggal, date):
            raise ValidationError("Format tanggal tidak valid")
        if tanggal < self.tgl_terbit:
            raise ValidationError(
                "Tanggal pelunasan tidak boleh sebelum tanggal terbit"
            )
        self.status = self.Status.LUNAS
        self.tgl_lunas = tanggal
        self.save(update_fields=["status", "tgl_lunas"])

    @classmethod
    def cek_tunggakan(cls, hari_ini=None):
        """Ubah 'Belum dibayar' yang lewat jatuh tempo menjadi 'Menunggak'.

        Mengembalikan jumlah tagihan yang diubah (FR-18).
        """
        hari_ini = hari_ini or date.today()
        return cls.objects.filter(
            status=cls.Status.BELUM, jatuh_tempo__lt=hari_ini
        ).update(status=cls.Status.MENUNGGAK)

    def __str__(self):
        return f"{self.langganan} - {self.periode}"
