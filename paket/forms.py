from django import forms

from .models import Paket


class PaketForm(forms.ModelForm):
    tarif = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        label="Tarif (Rp)",
        error_messages={
            "required": "Tarif wajib diisi",
            "invalid": "Tarif harus berupa angka",
            "min_value": "Tarif tidak boleh negatif",
            "max_digits": "Tarif terlalu besar",
            "max_decimal_places": "Tarif maksimal dua angka di belakang koma",
            "max_whole_digits": "Tarif terlalu besar",
        },
    )
    periode = forms.ChoiceField(
        choices=[("Bulanan", "Bulanan")], initial="Bulanan", label="Periode tagihan"
    )

    class Meta:
        model = Paket
        fields = ["nama_paket", "tarif", "satuan_tarif", "periode"]
        labels = {"nama_paket": "Nama paket", "satuan_tarif": "Satuan tarif"}
        error_messages = {
            "nama_paket": {
                "required": "Nama paket wajib diisi",
                "unique": "Paket dengan nama ini sudah ada",
            },
            "satuan_tarif": {"required": "Satuan tarif wajib dipilih"},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for kolom in self.fields.values():
            kelas = "form-select" if isinstance(kolom.widget, forms.Select) else "form-control"
            kolom.widget.attrs["class"] = kelas
