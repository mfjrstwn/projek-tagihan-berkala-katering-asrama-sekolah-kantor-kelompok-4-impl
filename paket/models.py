from django.core.validators import MinValueValidator
from django.db import models


class Paket(models.Model):
    class Satuan(models.TextChoices):
        PER_BULAN = "Per bulan", "Per bulan"
        PER_PORSI = "Per porsi", "Per porsi"

    nama_paket = models.CharField(max_length=60, unique=True)
    tarif = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    satuan_tarif = models.CharField(max_length=10, choices=Satuan.choices)
    periode = models.CharField(max_length=10, default="Bulanan")

    class Meta:
        db_table = "paket"
        ordering = ["nama_paket"]

    def masih_dipakai(self):
        """True bila ada langganan yang memakai paket ini (untuk FR-24)."""
        return self.langganan.exists()

    def __str__(self):
        return self.nama_paket
