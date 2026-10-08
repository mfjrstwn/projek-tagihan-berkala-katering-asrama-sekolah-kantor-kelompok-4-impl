from datetime import date

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView

from akun.akses import AdminRequiredMixin

from . import layanan
from .forms import FormLunas
from .models import Tagihan


class DaftarTagihanView(AdminRequiredMixin, ListView):
    template_name = "tagihan/daftar.html"
    context_object_name = "daftar_tagihan"
    paginate_by = 15

    def get_queryset(self):
        # Setiap daftar dibuka, tagihan yang lewat jatuh tempo ditandai Menunggak (FR-18)
        Tagihan.cek_tunggakan()
        qs = Tagihan.objects.select_related(
            "langganan__pelanggan", "langganan__paket"
        ).order_by("-periode", "langganan__pelanggan__nama")
        periode = self.request.GET.get("periode")
        status = self.request.GET.get("status")
        if periode:
            qs = qs.filter(periode=periode)
        if status in dict(Tagihan.Status.choices):
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        parameter = self.request.GET.copy()
        parameter.pop("page", None)
        ctx.update(
            periode_pilihan=Tagihan.objects.order_by("-periode")
            .values_list("periode", flat=True)
            .distinct(),
            status_pilihan=Tagihan.Status.choices,
            periode_dipilih=self.request.GET.get("periode", ""),
            status_dipilih=self.request.GET.get("status", ""),
            query_filter=parameter.urlencode(),
        )
        return ctx


class BuatTagihanView(AdminRequiredMixin, View):
    """Tombol 'Buat tagihan bulan ini': konfirmasi dulu, lalu proses (FR-13, FR-14)."""

    def get(self, request):
        periode = layanan.periode_sekarang()
        jumlah = layanan.hitung_belum_ditagih(periode)
        return render(
            request,
            "konfirmasi_umum.html",
            {
                "judul": f"Buat tagihan {layanan.label_periode(periode)}?",
                "pesan": (
                    f"Sistem akan membuat tagihan untuk {jumlah} pelanggan aktif "
                    "yang belum punya tagihan bulan ini. "
                    "Tagihan yang sudah ada tidak dibuat ulang."
                ),
                "url_batal": "/tagihan/",
                "teks_tombol": "Buat tagihan",
                "kelas_tombol": "btn-teal",
            },
        )

    def post(self, request):
        periode = layanan.periode_sekarang()
        label = layanan.label_periode(periode)
        dibuat, dilewati = layanan.buat_tagihan_periode(periode)
        if dibuat == 0 and dilewati == 0:
            messages.warning(request, "Tidak ada pelanggan aktif yang bisa ditagih")
        elif dibuat == 0:
            messages.error(
                request,
                f"Tagihan {label} sudah ada untuk semua pelanggan aktif. "
                "Tidak ada tagihan baru yang dibuat.",
            )
        elif dilewati == 0:
            messages.success(request, f"{dibuat} tagihan berhasil dibuat untuk {label}")
        else:
            messages.success(
                request,
                f"{dibuat} tagihan baru dibuat. "
                f"{dilewati} pelanggan dilewati karena tagihannya sudah ada.",
            )
        return redirect("tagihan:daftar")


class TandaiLunasView(AdminRequiredMixin, View):
    template_name = "tagihan/tandai_lunas.html"

    def _tagihan(self, pk):
        return get_object_or_404(
            Tagihan.objects.select_related("langganan__pelanggan"), pk=pk
        )

    def get(self, request, pk):
        tagihan = self._tagihan(pk)
        if tagihan.status == Tagihan.Status.LUNAS:
            messages.error(request, "Tagihan ini sudah lunas")
            return redirect("tagihan:daftar")
        form = FormLunas(initial={"tanggal": date.today()})
        return render(request, self.template_name, {"tagihan": tagihan, "form": form})

    def post(self, request, pk):
        tagihan = self._tagihan(pk)
        form = FormLunas(request.POST)
        if form.is_valid():
            try:
                tagihan.tandai_lunas(form.cleaned_data["tanggal"])
            except ValidationError as galat:
                form.add_error("tanggal", galat.messages[0])
            else:
                messages.success(request, "Tagihan ditandai lunas")
                return redirect("tagihan:daftar")
        return render(request, self.template_name, {"tagihan": tagihan, "form": form})
