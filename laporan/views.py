from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.views.generic import TemplateView

from akun.akses import AdminRequiredMixin
from aset.models import Aset
from pelanggan.models import Pelanggan
from tagihan import layanan
from tagihan.models import Tagihan


def _nol(nilai):
    return nilai or Decimal("0")


class DashboardView(AdminRequiredMixin, TemplateView):
    """Ringkasan tagihan bulan ini, tunggakan, pelanggan aktif, dan rekap aset (FR-19, FR-20)."""

    template_name = "laporan/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        Tagihan.cek_tunggakan()  # agar jumlah tunggakan selalu terbaru
        periode = layanan.periode_sekarang()
        bulan_ini = Tagihan.objects.filter(periode=periode)
        ctx.update(
            periode=periode,
            total_tagihan=_nol(bulan_ini.aggregate(t=Sum("jumlah"))["t"]),
            total_lunas=_nol(
                bulan_ini.filter(status=Tagihan.Status.LUNAS).aggregate(t=Sum("jumlah"))["t"]
            ),
            jumlah_menunggak=Tagihan.objects.filter(
                status=Tagihan.Status.MENUNGGAK
            ).count(),
            pelanggan_aktif=Pelanggan.objects.filter(
                status=Pelanggan.Status.AKTIF
            ).count(),
            rekap_aset=[
                (nilai, Aset.objects.filter(kondisi=nilai).count())
                for nilai, _ in Aset.Kondisi.choices
            ],
            tagihan_terbaru=Tagihan.objects.select_related(
                "langganan__pelanggan"
            ).order_by("-id")[:5],
        )
        return ctx


class LaporanView(AdminRequiredMixin, TemplateView):
    """Rekap tagihan per periode dan per segmen (FR-21)."""

    template_name = "laporan/laporan.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        Tagihan.cek_tunggakan()

        periode = self.request.GET.get("periode") or layanan.periode_sekarang()
        try:
            layanan.periksa_periode(periode)
        except ValueError:
            periode = layanan.periode_sekarang()
        segmen = self.request.GET.get("segmen", "")
        if segmen not in Pelanggan.Segmen.values:
            segmen = ""

        qs = Tagihan.objects.filter(periode=periode)
        if segmen:
            qs = qs.filter(langganan__pelanggan__segmen=segmen)
        S = Tagihan.Status
        data = (
            qs.order_by()
            .values("langganan__pelanggan__segmen")
            .annotate(
                n_tagihan=Count("id"),
                nominal_total=Sum("jumlah"),
                nominal_lunas=Sum("jumlah", filter=Q(status=S.LUNAS)),
                nominal_belum=Sum("jumlah", filter=Q(status=S.BELUM)),
                nominal_menunggak=Sum("jumlah", filter=Q(status=S.MENUNGGAK)),
            )
            .order_by("langganan__pelanggan__segmen")
        )
        baris = [
            {
                "segmen": d["langganan__pelanggan__segmen"],
                "jumlah": d["n_tagihan"],
                "total": _nol(d["nominal_total"]),
                "lunas": _nol(d["nominal_lunas"]),
                "belum": _nol(d["nominal_belum"]),
                "menunggak": _nol(d["nominal_menunggak"]),
            }
            for d in data
        ]
        total = {
            kunci: sum((b[kunci] for b in baris), 0 if kunci == "jumlah" else Decimal("0"))
            for kunci in ("jumlah", "total", "lunas", "belum", "menunggak")
        }
        semua_periode = set(
            Tagihan.objects.order_by().values_list("periode", flat=True).distinct()
        )
        semua_periode.add(layanan.periode_sekarang())
        ctx.update(
            baris=baris,
            total=total,
            periode=periode,
            segmen_dipilih=segmen,
            periode_pilihan=sorted(semua_periode, reverse=True),
            segmen_pilihan=Pelanggan.Segmen.choices,
        )
        return ctx
