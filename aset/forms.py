from datetime import date

from django import forms

from .models import Aset


class AsetForm(forms.ModelForm):
    tgl_perolehan = forms.DateField(
        label="Tanggal perolehan",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={
            "required": "Tanggal perolehan wajib diisi",
            "invalid": "Format tanggal tidak valid",
        },
    )
    nilai = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0,
        label="Nilai (Rp)",
        error_messages={
            "required": "Nilai wajib diisi",
            "invalid": "Nilai harus berupa angka",
            "min_value": "Nilai tidak boleh negatif",
            "max_digits": "Nilai terlalu besar",
            "max_decimal_places": "Nilai maksimal dua angka di belakang koma",
            "max_whole_digits": "Nilai terlalu besar",
        },
    )

    class Meta:
        model = Aset
        fields = ["nama", "kategori", "tgl_perolehan", "nilai", "kondisi", "catatan"]
        labels = {"nama": "Nama aset", "kategori": "Kategori", "kondisi": "Kondisi"}
        widgets = {"catatan": forms.Textarea(attrs={"rows": 2})}
        error_messages = {
            "nama": {"required": "Nama aset wajib diisi"},
            "kategori": {"required": "Kategori wajib diisi"},
            "kondisi": {"required": "Kondisi wajib dipilih"},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for kolom in self.fields.values():
            kelas = "form-select" if isinstance(kolom.widget, forms.Select) else "form-control"
            kolom.widget.attrs["class"] = kelas

    def clean_tgl_perolehan(self):
        tanggal = self.cleaned_data["tgl_perolehan"]
        if tanggal > date.today():
            raise forms.ValidationError("Tanggal perolehan tidak boleh di masa depan")
        return tanggal
