from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from akun.akses import AdminRequiredMixin, CustomerRequiredMixin
from pelanggan.models import Langganan, Pelanggan

from .forms import PaketForm
from .models import Paket


class DaftarPaketView(AdminRequiredMixin, ListView):
    template_name = "paket/daftar.html"
    context_object_name = "daftar_paket"

    def get_queryset(self):
        # jumlah_pengguna = berapa langganan yang memakai paket ini
        return Paket.objects.annotate(jumlah_pengguna=Count("langganan"))


class TambahPaketView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Paket
    form_class = PaketForm
    template_name = "form_umum.html"
    success_url = reverse_lazy("paket:daftar")
    success_message = "Paket berhasil disimpan"
    extra_context = {"judul": "Tambah paket", "url_batal": reverse_lazy("paket:daftar")}


class UbahPaketView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Paket
    form_class = PaketForm
    template_name = "form_umum.html"
    success_url = reverse_lazy("paket:daftar")
    success_message = "Paket berhasil disimpan"
    extra_context = {"judul": "Ubah paket", "url_batal": reverse_lazy("paket:daftar")}


class HapusPaketView(AdminRequiredMixin, View):
    def get(self, request, pk):
        paket = get_object_or_404(Paket, pk=pk)
        return render(
            request,
            "konfirmasi_umum.html",
            {
                "judul": "Hapus paket?",
                "pesan": (
                    f"Paket {paket.nama_paket} akan dihapus. "
                    "Paket yang masih dipakai pelanggan tidak bisa dihapus."
                ),
                "url_batal": reverse("paket:daftar"),
            },
        )

    def post(self, request, pk):
        paket = get_object_or_404(Paket, pk=pk)
        pesan_ditolak = (
            f"Paket {paket.nama_paket} masih dipakai pelanggan dan tidak bisa dihapus"
        )
        if paket.masih_dipakai():
            messages.error(request, pesan_ditolak)
        else:
            try:
                paket.delete()
            except ProtectedError:
                messages.error(request, pesan_ditolak)
            else:
                messages.success(request, "Data berhasil dihapus")
        return redirect("paket:daftar")


class PaketSayaView(CustomerRequiredMixin, TemplateView):
    """Customer melihat semua paket dan tarif. Paket yang sedang dipakainya ditandai (FR-10)."""

    template_name = "paket/paket_saya.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pelanggan = Pelanggan.objects.filter(user=self.request.user).first()
        paket_aktif = set()
        if pelanggan:
            paket_aktif = set(
                pelanggan.langganan.filter(status=Langganan.Status.AKTIF).values_list(
                    "paket_id", flat=True
                )
            )
        ctx["daftar_paket"] = [
            {"paket": p, "aktif": p.pk in paket_aktif} for p in Paket.objects.all()
        ]
        return ctx
