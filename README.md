## A. Persiapan (sekali saja)

### 1. Install Python

Unduh dari python.org/downloads.
Saat instalasi, centang “Add Python to PATH”. Ini yang paling sering terlewat.
Cek versinya di terminal dengan python --version. README menyebut Django 6.x butuh Python 3.12 ke atas. Kalau versinya lebih rendah, install ulang yang terbaru.

### 2. Install Git

Unduh dari git-scm.com, lalu install dengan pengaturan default.
Cek dengan git --version.

### 3. Install VS Code dan ekstensi Python

Buka VS Code, klik ikon Extensions (Ctrl+Shift+X), cari Python (dari Microsoft), lalu install.

### 4. Pastikan ada internet saat menjalankan aplikasi, karena Bootstrap dan font dimuat lewat CDN.

## B. Ambil proyek dari GitHub
Buat atau pilih folder tempat menyimpan proyek, misalnya D:\Projek.
Di VS Code: File → Open Folder, pilih folder itu.
Buka terminal di VS Code: Terminal → New Terminal (atau Ctrl+`).
Jalankan:

git clone https://github.com/mfjrstwn/projek-tagihan-berkala-katering-asrama-sekolah-kantor-kelompok-4-impl.git

Masuk ke folder hasil clone:

cd projek-tagihan-berkala-katering-asrama-sekolah-kantor-kelompok-4-impl
Buka folder proyek itu di VS Code: File → Open Folder lalu pilih folder projek-tagihan-berkala-katering-asrama-sekolah-kantor-kelompok-4-impl.

Pastikan terminal berikutnya terbuka di folder ini, yaitu folder yang berisi file manage.py.


## C. Menyiapkan dan menjalankan proyek

Semua perintah di bawah dijalankan di terminal VS Code, di dalam folder yang ada manage.py-nya.

### 1. Buat virtual environment

python -m venv venv

### 2. Aktifkan virtual environment

Pilih sesuai terminal yang dipakai:

venv\Scripts\activate            # CMD atau PowerShell

source venv/Scripts/activate     # Git Bash

source venv/bin/activate         # macOS / Linux

Kalau berhasil, muncul tulisan (venv) di awal baris terminal.

### 3. Pasang dependensi

pip install -r requirements.txt

### 4. Buat database

python manage.py migrate

### 5. Isi data awal (pilih salah satu)

python manage.py loaddata data_awal.json

atau buat akun admin sendiri:

python manage.py createsuperuser

Kalau memakai data_awal.json, tanyakan ke pemilik proyek username dan password akun bawaannya.

### 6. Jalankan server

python manage.py runserver

Buka http://127.0.0.1:8000 di browser. Untuk menghentikan server, tekan Ctrl + C di terminal.

## D. Kendala yang sering muncul

“running scripts is disabled on this system” (PowerShell saat mengaktifkan venv). Jalankan ini sekali di terminal yang sama, lalu aktifkan venv lagi:

Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

Alternatif lain: ganti terminal VS Code ke Command Prompt atau Git Bash lewat tanda panah di sebelah tombol + pada panel terminal.

“python is not recognized”. Python belum masuk PATH. Install ulang dan centang “Add Python to PATH”, atau coba py sebagai pengganti python.

“No module named django”. Venv belum aktif atau pip install belum dijalankan. Pastikan ada tulisan (venv) di terminal, lalu ulangi pip install -r requirements.txt.

VS Code tidak mengenali venv. Tekan Ctrl+Shift+P, ketik Python: Select Interpreter, lalu pilih yang ada tulisan venv.

Error saat pip install (misalnya versi Django tidak ditemukan). Biasanya Python terlalu lama. Cek versinya dengan python --version.

E. Untuk kerja bareng setelah ini

Mengambil pembaruan terbaru dari repo (jalankan di folder proyek):

git pull

Kalau teman-temanmu juga mau push perubahan ke repo ini, kamu perlu menambahkan mereka dulu di GitHub: Settings → Collaborators → Add people. Tanpa itu mereka akan kena error 403 seperti yang kamu alami tadi. Alternatifnya, mereka bisa membuat fork lalu mengirim Pull Request.

Hanya git pull yang perlu dilakukan setiap ada pembaruan. Langkah di bagian A sampai C cukup sekali saja. Pada hari-hari berikutnya mereka tinggal membuka folder di VS Code, mengaktifkan venv, lalu menjalankan python manage.py runserver. Kalau ada perubahan database dari git pull, jalankan juga python manage.py migrate sebelum runserver.