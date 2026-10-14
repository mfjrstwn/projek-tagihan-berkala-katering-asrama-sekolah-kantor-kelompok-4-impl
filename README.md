Prasyarat (sekali saja):

Python versi terbaru dari python.org. Django 6.x butuh Python 3.12 ke atas, jadi cek versi yang dibutuhkan di requirements.txt. Di Windows, centang “Add Python to PATH” saat instalasi.
Git dari git-scm.com.
Koneksi internet, karena Bootstrap dan font dimuat lewat CDN.

Langkah menjalankan:

bash
# 1. Ambil proyek
git clone https://github.com/mfjrstwn/projek-tagihan-berkala-katering-asrama-sekolah-kantor-kelompok-4-impl.git
cd "alamat folder clone dari github tadi(cek di file explorer untuk alamat nya)"

# 2. Buat virtual environment
python -m venv venv

# 3. Aktifkan
venv\Scripts\activate            # Windows (CMD/PowerShell)
source venv/bin/activate         # macOS / Linux

# 4. Pasang dependensi
pip install -r requirements.txt

# 5. Buat database
python manage.py migrate

# 6. Isi data awal (pilih salah satu)
python manage.py loaddata data_awal.json
# atau buat akun admin sendiri:
python manage.py createsuperuser

# 7. Jalankan
python manage.py runserver

Buka http://127.0.0.1:8000 di browser. Hentikan server dengan Ctrl + C.
