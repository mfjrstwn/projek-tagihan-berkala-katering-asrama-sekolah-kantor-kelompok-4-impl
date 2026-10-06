from django.core.validators import MinValueValidator
from django.db import models


class Aset(models.Model):
    class Kondisi(models.TextChoices):
        BAIK = "Baik", "Baik"
        PERLU_PERAWATAN = "Perlu perawatan", "Perlu perawatan"
        RUSAK = "Rusak", "Rusak"

    nama = models.CharField(max_length=100)
    kategori = models.CharField(max_length=30)
    tgl_perolehan = models.DateField()
    nilai = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(0)]
    )
    kondisi = models.CharField(
        max_length=20, choices=Kondisi.choices, default=Kondisi.BAIK
    )
    catatan = models.TextField(blank=True)

    class Meta:
        db_table = "aset"
        ordering = ["nama"]

    def __str__(self):
        return self.nama
