from django import forms


class FormLunas(forms.Form):
    tanggal = forms.DateField(
        label="Tanggal pelunasan",
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"
        ),
        error_messages={
            "required": "Tanggal pelunasan wajib diisi",
            "invalid": "Format tanggal tidak valid",
        },
    )
