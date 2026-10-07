from django import forms
from django.db import transaction

from paket.models import Paket

from .models import Langganan, Pelanggan


class PelangganForm(forms.ModelForm):
    """Form tambah/ubah pelanggan beserta paket langganannya.

    Satu form mengisi dua tabel: Pelanggan dan Langganan.
    """

    paket = forms.ModelChoiceField(
        queryset=Paket.objects.all(),
        label="Paket langganan",
        empty_label="Pilih paket",
        error_messages={"required": "Paket wajib dipilih"},
    )
    jumlah_porsi = forms.IntegerField(
        required=False,
        min_value=1,
        label="Jumlah porsi",
        help_text="Wajib diisi untuk tipe Instansi",
        error_messages={
            "min_value": "Jumlah porsi minimal 1",
            "invalid": "Jumlah porsi harus berupa angka",
        },
    )

    class Meta:
        model = Pelanggan
        fields = ["nama", "segmen", "tipe", "kontak", "alamat"]
        labels = {
            "nama": "Nama",
            "segmen": "Segmen",
            "tipe": "Tipe",
            "kontak": "Kontak",
            "alamat": "Alamat",
        }
        widgets = {"alamat": forms.Textarea(attrs={"rows": 3})}
        error_messages = {
            "nama": {"required": "Nama wajib diisi"},
            "segmen": {"required": "Segmen wajib dipilih"},
            "tipe": {"required": "Tipe wajib dipilih"},
            "kontak": {"required": "Kontak wajib diisi"},
            "alamat": {"required": "Alamat wajib diisi"},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for kolom in self.fields.values():
            kelas = "form-select" if isinstance(kolom.widget, forms.Select) else "form-control"
            kolom.widget.attrs["class"] = kelas
        # Saat mengubah, isi paket dan porsi dari langganan aktif yang ada
        if self.instance.pk:
            lang = self.instance.langganan.filter(status=Langganan.Status.AKTIF).first()
            if lang:
                self.fields["paket"].initial = lang.paket_id
                self.fields["jumlah_porsi"].initial = lang.jumlah_porsi

    def clean(self):
        data = super().clean()
        tipe = data.get("tipe")
        if tipe == Pelanggan.Tipe.INSTANSI and not data.get("jumlah_porsi"):
            self.add_error(
                "jumlah_porsi", "Jumlah porsi wajib diisi untuk pelanggan instansi"
            )
        if tipe == Pelanggan.Tipe.PERORANGAN:
            data["jumlah_porsi"] = None
        return data

    def save(self, commit=True):
        # Selalu menyimpan ke basis data (commit diabaikan) karena dua tabel terlibat
        with transaction.atomic():
            pelanggan = super().save(commit=True)
            paket = self.cleaned_data["paket"]
            porsi = self.cleaned_data["jumlah_porsi"]
            lang = pelanggan.langganan.filter(status=Langganan.Status.AKTIF).first()
            if lang:
                lang.paket = paket
                lang.jumlah_porsi = porsi
                lang.save()
            else:
                Langganan.objects.create(
                    pelanggan=pelanggan, paket=paket, jumlah_porsi=porsi
                )
        return pelanggan
