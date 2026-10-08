from django.core.management.base import BaseCommand, CommandError

from tagihan import layanan


class Command(BaseCommand):
    help = (
        "Membuat tagihan bulanan untuk semua pelanggan aktif. "
        "Dijadwalkan berjalan otomatis setiap tanggal 1."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--periode", help="Format YYYY-MM, misalnya 2026-10. Bawaan: bulan ini"
        )

    def handle(self, *args, **opsi):
        periode = opsi["periode"] or layanan.periode_sekarang()
        try:
            layanan.periksa_periode(periode)
        except ValueError as galat:
            raise CommandError(str(galat))
        dibuat, dilewati = layanan.buat_tagihan_periode(periode)
        self.stdout.write(
            self.style.SUCCESS(
                f"Periode {periode}: {dibuat} tagihan dibuat, {dilewati} dilewati."
            )
        )
