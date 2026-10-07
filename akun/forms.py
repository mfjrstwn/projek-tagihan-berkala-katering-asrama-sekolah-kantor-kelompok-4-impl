from django.contrib.auth.forms import AuthenticationForm


class FormMasuk(AuthenticationForm):
    """Form login dengan pesan error dan tampilan Bootstrap."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Username atau password salah. Coba lagi",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username"
        self.fields["password"].label = "Password"
        for kolom in self.fields.values():
            kolom.widget.attrs["class"] = "form-control"
