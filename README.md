XipserCloud - Panel Kontrol Hosting Termux
Selamat datang di XipserCloud! Panel kontrol hosting berbasis web yang dirancang untuk menjalankan dan mengelola perintah sistem di lingkungan Termux.
Persyaratan Awal
 * Aplikasi Termux terinstal.
 * Pastikan Termux memiliki Git dan Python. Jalankan:
   pkg update && pkg upgrade -y
pkg install git python -y

 * Anda mungkin perlu menginstal procps dan util-linux untuk fitur status real-time:
   pkg install procps-ng util-linux -y

Langkah-Langkah Instalasi (GitHub Workflow)
1. Clone Repositori
Asumsikan Anda telah menyimpan file-file ini di repositori GitHub (misalnya, https://github.com/user/xipsercloud.git).
git clone [https://github.com/user/xipsercloud.git](https://github.com/user/xipsercloud.git)
cd xipsercloud

2. Konfigurasi
Edit file config.json untuk mengatur username dan password default Anda.
nano config.json
# Ganti nilai "username" dan "password"

3. Setup Persistence (Wajib)
Untuk memastikan server tetap berjalan meskipun layar ponsel mati atau Termux di-background, jalankan:
termux-wake-lock

Anda akan melihat notifikasi persisten Termux. Untuk menghentikan wake lock, jalankan termux-wake-unlock.
4. Menjalankan Server
Jalankan skrip Python API di Termux. Server akan mulai berjalan di port 8080.
python server.py

Server akan menampilkan alamat IP lokal Anda (contoh: 192.168.1.5).
5. Akses Dashboard
Buka browser (di ponsel atau PC yang terhubung ke jaringan WiFi yang sama) dan akses alamat:
http://<IP_ADDRESS_ANDA>:8080
Gunakan kredensial dari config.json untuk login.
Catatan Penting
 * Keamanan: Panel ini tidak menggunakan HTTPS dan otentikasi hanya sederhana. JANGAN gunakan ini untuk hosting publik yang sensitif.
 * Perintah Sistem: Server ini menjalankan perintah shell secara langsung. Berhati-hatilah saat memodifikasi endpoint di server.py.
