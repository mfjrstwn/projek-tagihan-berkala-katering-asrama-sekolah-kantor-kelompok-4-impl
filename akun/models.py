from django.contrib.auth.models import AbstractUser
from django.db import models


class Pengguna(AbstractUser):
    """Akun untuk login.

    Username, password (otomatis di-hash) dan is_active sudah disediakan
    Django lewat AbstractUser. Kita hanya menambahkan kolom peran.
    """

    class Peran(models.TextChoices):
        ADMIN = "Admin", "Admin"
        CUSTOMER = "Customer", "Customer"

    role = models.CharField(
        max_length=10, choices=Peran.choices, default=Peran.CUSTOMER
    )

    class Meta:
        db_table = "pengguna"

    def save(self, *args, **kwargs):
        # Superuser yang dibuat lewat createsuperuser otomatis menjadi Admin
        if self.is_superuser:
            self.role = self.Peran.ADMIN
        super().save(*args, **kwargs)

    def adalah_admin(self):
        return self.role == self.Peran.ADMIN

    def __str__(self):
        return f"{self.username} ({self.role})"
