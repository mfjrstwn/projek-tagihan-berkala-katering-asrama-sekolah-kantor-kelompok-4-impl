from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from akun.akses import AdminRequiredMixin

from .forms import AsetForm
from .models import Aset


class DaftarAsetView(AdminRequiredMixin, ListView):
    """Daftar aset dengan pencarian nama dan filter kondisi."""

    model = Aset
    template_name = "aset/daftar.html"
    context_object_name = "daftar_aset"
    paginate_by = 15

    def _filter(self):
        kata = self.request.GET.get("q", "").strip()
        kondisi = self.request.GET.get("kondisi", "")
        if kondisi not in Aset.Kondisi.values:
            kondisi = ""
        return kata, kondisi

    def get_queryset(self):
        kata, kondisi = self._filter()
        qs = super().get_queryset()
        if kata:
            qs = qs.filter(nama__icontains=kata)
        if kondisi:
            qs = qs.filter(kondisi=kondisi)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kata, kondisi = self._filter()
        parameter = self.request.GET.copy()
        parameter.pop("page", None)
        ctx.update(
            kata=kata,
            kondisi_dipilih=kondisi,
            kondisi_pilihan=Aset.Kondisi.choices,
            query_filter=parameter.urlencode(),
            ada_filter=bool(kata or kondisi),
        )
        return ctx


class TambahAsetView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Aset
    form_class = AsetForm
    template_name = "form_umum.html"
    success_url = reverse_lazy("aset:daftar")
    success_message = "Aset berhasil disimpan"
    extra_context = {"judul": "Tambah aset", "url_batal": reverse_lazy("aset:daftar")}


class UbahAsetView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    """Dipakai juga untuk memperbarui kondisi aset (FR-07)."""

    model = Aset
    form_class = AsetForm
    template_name = "form_umum.html"
    success_url = reverse_lazy("aset:daftar")
    success_message = "Aset berhasil disimpan"
    extra_context = {"judul": "Ubah aset", "url_batal": reverse_lazy("aset:daftar")}


class HapusAsetView(AdminRequiredMixin, View):
    def get(self, request, pk):
        aset = get_object_or_404(Aset, pk=pk)
        return render(
            request,
            "konfirmasi_umum.html",
            {
                "judul": "Hapus aset?",
                "pesan": f"Data {aset.nama} akan dihapus. Tindakan ini tidak bisa dibatalkan.",
                "url_batal": reverse("aset:daftar"),
            },
        )

    def post(self, request, pk):
        aset = get_object_or_404(Aset, pk=pk)
        aset.delete()
        messages.success(request, "Data berhasil dihapus")
        return redirect("aset:daftar")
