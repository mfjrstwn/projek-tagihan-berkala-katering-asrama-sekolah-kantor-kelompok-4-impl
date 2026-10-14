from django import template

register = template.Library()


@register.filter
def foto_paket(nama):
    """Memetakan nama paket ke berkas foto di static/img/paket/ (hanya untuk tampilan).

    {% static item.paket.nama_paket|foto_paket %} -> img/paket/sarapan.jpg
    Nama yang tidak dikenali memakai umum.jpg. Bila berkasnya belum ada, kartu
    menampilkan huruf awal paket sebagai cadangan.
    """
    n = (nama or "").lower()
    if "siang" in n and "malam" in n:
        berkas = "siang-malam"
    elif "sarapan" in n or "pagi" in n:
        berkas = "sarapan"
    elif "siang" in n:
        berkas = "makan-siang"
    elif "malam" in n:
        berkas = "makan-malam"
    elif any(k in n for k in ("instansi", "kantor", "acara", "prasmanan", "porsi")):
        berkas = "instansi"
    else:
        berkas = "umum"
    return f"img/paket/{berkas}.jpg"


@register.filter
def atribut_galat(kolom):
    """Merender widget kolom form dengan aria-invalid dan aria-describedby.

    Menghubungkan isian ke pesan galat (id galat-<nama>) dan teks bantuan
    (id bantuan-<nama>) agar terbaca pembaca layar, tanpa mengubah forms.py.
    """
    atribut, id_terkait = {}, []
    if kolom.errors:
        atribut["aria-invalid"] = "true"
        id_terkait.append(f"galat-{kolom.html_name}")
    if kolom.help_text:
        id_terkait.append(f"bantuan-{kolom.html_name}")
    if id_terkait:
        atribut["aria-describedby"] = " ".join(id_terkait)
    return kolom.as_widget(attrs=atribut)
