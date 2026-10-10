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
