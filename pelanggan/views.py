from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from akun.akses import AdminRequiredMixin, CustomerRequiredMixin

from .forms import PelangganForm
from .models import Pelanggan


class DaftarPelangganView(AdminRequiredMixin, ListView):
    template_name = "pelanggan/daftar.html"
    context_object_name = "daftar_pelanggan"
    paginate_by = 15

    def get_queryset(self):
        return Pelanggan.objects.prefetch_related("langganan__paket")


class TambahPelangganView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Pelanggan
    form_class = PelangganForm
    template_name = "pelanggan/form.html"
    success_url = reverse_lazy("pelanggan:daftar")
    success_message = "Pelanggan berhasil disimpan"


class UbahPelangganView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Pelanggan
    form_class = PelangganForm
    template_name = "pelanggan/form.html"
    success_url = reverse_lazy("pelanggan:daftar")
    success_message = "Pelanggan berhasil disimpan"


class HapusPelangganView(AdminRequiredMixin, View):
    """Halaman konfirmasi. Sistem memilih sendiri: hapus atau nonaktifkan."""

    def get(self, request, pk):
        pelanggan = get_object_or_404(Pelanggan, pk=pk)
        return render(
            request,
            "pelanggan/konfirmasi_hapus.html",
            {"pelanggan": pelanggan, "punya_tagihan": pelanggan.punya_tagihan()},
        )

    def post(self, request, pk):
        pelanggan = get_object_or_404(Pelanggan, pk=pk)
        if pelanggan.punya_tagihan():
            pelanggan.nonaktifkan()
            messages.success(request, "Pelanggan dinonaktifkan")
        else:
            try:
                pelanggan.hapus()
            except (ValidationError, ProtectedError):
                messages.error(
                    request, "Pelanggan tidak bisa dihapus karena sudah punya tagihan"
                )
            else:
                messages.success(request, "Data berhasil dihapus")
        return redirect("pelanggan:daftar")


class AktifkanPelangganView(AdminRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        pelanggan = get_object_or_404(Pelanggan, pk=pk)
        pelanggan.aktifkan()
        messages.success(request, "Pelanggan diaktifkan kembali")
        return redirect("pelanggan:daftar")


class DataDiriView(CustomerRequiredMixin, TemplateView):
    """Customer melihat data dirinya sendiri, hanya baca (FR-04)."""

    template_name = "pelanggan/data_diri.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["pelanggan"] = (
            Pelanggan.objects.filter(user=self.request.user)
            .prefetch_related("langganan__paket")
            .first()
        )
        return ctx
