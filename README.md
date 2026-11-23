# Bara

Bara adalah panel web untuk mengotomatiskan pengiriman pesan streak TikTok. Berjalan di satu container Docker (FastAPI + Chromium headless + scheduler bawaan).

## Fitur

- Banyak akun TikTok: tiap akun punya cookie, kontak, dan jadwal sendiri; proses berjalan bergantian
- UI web: dashboard, log live, riwayat, kelola kontak, cookie, dan pengaturan
- Kirim sekarang atau mode uji (cek kontak tanpa mengirim)
- Beberapa jadwal kirim per hari (mis. pagi dan malam), tiap jadwal bisa punya pesan dan penerima sendiri, dengan timezone
- Login TikTok langsung di panel (browser remote) atau tempel cookie manual
- Notifikasi Discord (webhook) dan Telegram, opsional
- Semua data (cookie, kontak, pengaturan, riwayat) tersimpan di volume Docker `/data`

## Menjalankan

```bash
cp .env.example .env
# edit .env, isi API_KEY
docker compose up -d --build
```

Buka `http://localhost:8000`. Saat pertama kali, panel meminta Anda membuat **admin pertama**: isi `API_KEY` (dari `.env`), username, dan password (minimal 8 karakter). Setelah itu login memakai username dan password.

### Pengguna dan peran

- **admin**: melihat dan mengelola semua akun TikTok, pengaturan global, dan pengguna (tambah, reset password, ubah peran, nonaktifkan, hapus).
- **user**: hanya melihat dan mengelola akun TikTok miliknya sendiri. Setiap pengguna punya notifikasi pribadi (Discord/Telegram) di tab Pengaturan; admin juga bisa menerima notifikasi semua akun lewat saluran global (`Terima Notifikasi Semua Akun`).
- Sesi memakai cookie `bara_session` (HttpOnly, SameSite=Strict, berlaku 7 hari). Login dibatasi: 5 kali gagal dalam 15 menit mengunci selama 15 menit.
- Setiap request tulis dari browser wajib menyertakan header `X-Requested-With: bara` (sudah otomatis oleh UI).
- Data lama (akun tanpa pemilik) otomatis menjadi milik admin pertama saat setup.

### Akses privat di VPS (tanpa ekspose ke internet)

Secara default port hanya di-bind ke `127.0.0.1` di VPS (`BIND_ADDRESS` di `.env`), jadi tidak bisa diakses dari luar. Untuk membuka panel dari laptop, pakai SSH tunnel:

```bash
ssh -L 8000:127.0.0.1:8000 user@ip-vps
```

Lalu buka `http://localhost:8000` di laptop selama tunnel aktif. Alternatif: VPN pribadi seperti Tailscale atau WireGuard.

## Online dengan Domain (Caddy)

Cara memasang panel di VPS dengan domain sendiri dan HTTPS otomatis lewat [Caddy](https://caddyserver.com).

1. **DNS**: buat A record untuk domain Anda (mis. `panel.example.com`) yang mengarah ke IP VPS.
2. **Port**: buka port 80 dan 443 di firewall VPS. Port panel (`PORT`) tidak perlu dibuka.
3. **`.env`**: pastikan panel hanya bisa diakses dari VPS sendiri dan percayai header dari Caddy:

   ```env
   API_KEY=isi-dengan-kunci-acak-yang-panjang
   BIND_ADDRESS=127.0.0.1
   PORT=8001
   TRUST_PROXY=1
   ```

   `TRUST_PROXY=1` membuat panel memakai IP asli pengunjung (untuk pembatasan login) dan menandai cookie sebagai `Secure`. Aktifkan hanya bila `BIND_ADDRESS=127.0.0.1` dan semua akses lewat Caddy; jika port terbuka langsung, pengunjung bisa memalsukan IP.
4. **Jalankan panel**: `docker compose up -d --build`.
5. **Caddyfile**: tambahkan isi [`deploy/Caddyfile.example`](deploy/Caddyfile.example) ke `/etc/caddy/Caddyfile` (ganti domain, dan port harus sama dengan `PORT`):

   ```caddyfile
   panel.example.com {
   	encode zstd gzip
   	header {
   		Strict-Transport-Security "max-age=31536000"
   		X-Content-Type-Options nosniff
   		Referrer-Policy no-referrer
   		-Server
   	}
   	reverse_proxy 127.0.0.1:8001
   }
   ```
6. **Muat ulang Caddy**: `sudo systemctl reload caddy`.

   **Caddy di Docker (jaringan bersama)**: bila Caddy juga berjalan sebagai container, gabungkan keduanya ke satu jaringan Docker (mis. `proxy`), tidak perlu publish port panel, lalu arahkan Caddy ke nama service:

   ```caddyfile
   panel.example.com {
   	reverse_proxy bara:8000
   }
   ```
7. Buka `https://panel.example.com`, lalu buat admin pertama (isi `API_KEY`, username, dan password).

Karena panel bisa diakses publik, pakai `API_KEY` yang panjang dan acak (`openssl rand -hex 24`) serta password admin yang kuat.

## Langkah pertama di UI

1. **Akun** (opsional): tab *Akun* untuk menambah akun lain. Akun pertama bernama "Utama". Pilih akun aktif di pojok kanan atas; tab Kontak, Cookie, dan Dashboard mengikuti akun yang dipilih.
2. **Cookie**: di tab *Cookie* klik *Mulai login*, login ke TikTok pada tampilan browser di panel (klik/ketik langsung, captcha juga bisa), lalu *Simpan sesi login*. Alternatif: tempel cookie manual (JSON dari Cookie-Editor atau string header `Cookie`).
3. **Kontak**: tambahkan nickname persis seperti di daftar pesan TikTok.
4. **Dashboard**: jalankan *Uji* dulu untuk memastikan login dan kontak terbaca, lalu *Kirim Sekarang*.
5. **Pengaturan**: atur pesan default, zona waktu, dan Discord/Telegram.

## API

Semua endpoint `/api/*` (kecuali `/api/health` dan `/api/auth/*`) memakai sesi cookie (UI) atau header `X-API-Key` (skrip/otomasi). `X-API-Key` dianggap admin dan tidak butuh header CSRF. `API_KEY` tetap wajib diisi saat startup karena dipakai untuk setup awal.

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/status
```

| Method | Path | Fungsi |
|---|---|---|
| GET | `/api/status` | Status ringkas |
| POST | `/api/run` | `{"mode":"send"\|"test","message":"..."}` |
| POST | `/api/run/stop` | Hentikan proses |
| GET | `/api/run/current` | Log proses aktif |
| GET / POST / PUT / DELETE | `/api/accounts` | Kelola akun dan jadwalnya |
| GET / POST / DELETE | `/api/contacts?account=ID` | Kelola kontak akun |
| PUT / DELETE | `/api/cookies?account=ID` | Atur cookie akun |
| POST | `/api/login/start`, `/api/login/save`, `/api/login/stop` | Login remote |
| GET / PUT | `/api/settings` | Pengaturan global (PUT khusus admin) |
| GET / PUT | `/api/me/notifications` | Notifikasi pribadi pengguna |
| GET / POST / PUT / DELETE | `/api/users` | Kelola pengguna (admin) |
| POST | `/api/auth/setup`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/password` | Autentikasi |
| GET | `/api/history?account=<id\|all>&page=1&page_size=20&mode=&status=` | Riwayat berhalaman milik Anda: `{items,total,page,page_size}`; `page_size` 10, 20, atau 50 |
| DELETE | `/api/history` | Hapus riwayat milik Anda sendiri |
| GET | `/api/dashboard?account=<id>` | Statistik dasbor (hari ini, 7 hari, hari beruntun) lewat query terarah |

## Kapasitas & Antrean

Semua pekerjaan browser (kirim, uji, cek cookie) masuk ke **antrean yang disimpan di database** dan dijalankan oleh sejumlah worker Chromium (`BROWSER_WORKERS`, default 1). Aturan antrean:

- Maksimal satu job aktif per akun dan jenis; dua job untuk akun yang sama tidak pernah berjalan bersamaan; akun yang sedang login remote dilewati.
- Prioritas: kirim/uji manual, lalu kirim terjadwal (urut jam jatuh tempo), lalu cek cookie otomatis. Cek cookie tidak dimulai bila ada jadwal kirim dalam 10 menit.
- Jadwal yang jatuh tempo dimasukkan ke antrean sekali. Bila jendela 3 jam habis sebelum sempat jalan, job dicatat sebagai **Terlewat** di riwayat dan pemiliknya diberi notifikasi. Setelah restart, job yang sedang berjalan kembali ke antrean bila masih dalam jendela.
- Panel menghitung perkiraan waktu mulai (posisi antrean dan ETA) dari rata-rata 5 run terakhir akun; bila belum ada data: 30 detik per kontak + 20 detik. Bila perkiraan jatuh setelah tengah malam, pemilik mendapat satu peringatan per hari.
- Jeda acak 5-20 detik antar job (`QUEUE_JITTER_MIN/MAX`).
- Satu proses Chromium dipakai ulang per worker; tiap job memakai konteks browser terisolasi (cookie tidak bocor antar akun) dan konteksnya dibuang setelah selesai. Proses dimulai ulang tiap `BROWSER_RECYCLE_JOBS` job, saat crash, atau bila memori (PSS) melewati `BROWSER_MAX_MB`. Request video/audio diblokir pada job kirim/cek.
- `BROWSER_KIND=auto` memakai `chrome-headless-shell` bila terpasang (jauh lebih hemat memori), selain itu Chromium penuh. Login remote selalu memakai Chromium penuh.

Panduan RAM (hanya Bara, tanpa aplikasi lain):

| RAM server | `BROWSER_WORKERS` |
|---|---|
| 2 GB | 1 |
| 4 GB | 2 |
| 8 GB | 3-4 |

Hitungan kasar: satu kirim ke 4 kontak sekitar 2 menit, jadi **satu worker menangani sekitar 27 akun per jam**. Sebarkan jam jadwal; UI memberi petunjuk bila slot 30 menit sudah ramai. Pengukuran memori satu browser dengan satu tab (PSS): Chromium penuh sekitar 360 MB, `chrome-headless-shell` sekitar 90 MB.

## Pakai Image Jadi (GHCR)

Setiap push ke `main` yang lulus tes membangun image Docker dan mengirimnya ke GitHub Container Registry sebagai `ghcr.io/<pemilik>/<repo>` (huruf kecil) dengan tag `latest` dan SHA singkat commit. Untuk memakainya tanpa build di server:

```bash
# .env
BARA_IMAGE=ghcr.io/<pemilik>/<repo>:latest

docker compose pull
docker compose up -d
```

Tanpa `BARA_IMAGE`, `docker compose up -d --build` tetap membangun image lokal bernama `tikstreak-bara`.

Paket GHCR bersifat **privat secara default**. Pilih salah satu:

- buka halaman paket di GitHub (Packages) lalu ubah visibilitas menjadi Public di *Package settings*; atau
- di server jalankan `docker login ghcr.io` memakai username GitHub dan Personal Access Token dengan izin `read:packages`.

## Pengujian

`make install-test` memasang dependensi tes dan Chromium, `make test-api` menjalankan pytest, `make test-ui` menjalankan tes UI Playwright (Node), dan `make test` menjalankan keduanya. CI GitHub Actions menjalankan hal yang sama pada setiap push dan pull request.

## Landing Page

Pengunjung yang belum login melihat halaman depan Bara (fitur, cara kerja, keamanan, FAQ) di `/`. Tombol **Masuk** membuka `/login`. Setelah login, `/` langsung menampilkan panel. Sebelum admin pertama dibuat, `/` mengarahkan ke `/login` agar pengaturan awal tetap berjalan. Halaman memakai pilihan bahasa dan tema yang sama dengan panel.

| Variabel | Default | Keterangan |
|---|---|---|
| `LANDING_ENABLED` | `1` | `0` menonaktifkan landing page: `/` langsung menampilkan panel atau halaman login seperti sebelumnya (`/login` tetap bisa dipakai) |
| `LANDING_DOCS_URL` | kosong | Tautan tombol "Panduan Pasang". Kosong berarti tombol disembunyikan |

HTML dikirim dengan `Cache-Control: private, no-cache` dan `Vary: Cookie`, jadi aman di belakang Cloudflare.

## Backup

Semua data ada di satu file SQLite (`/data/streak.db`) plus `secret.key` (atau env `SECRET_KEY`) dan folder `proofs/`. Cookie dan rahasia notifikasi dienkripsi; **tanpa kunci yang sama cookie tidak bisa dibaca**, jadi simpan `SECRET_KEY` (atau `secret.key`) bersama backup database.

Backup database yang konsisten (aman saat panel berjalan):

```bash
docker compose exec bara python -c "import sqlite3; s=sqlite3.connect('/data/streak.db'); d=sqlite3.connect('/data/backup.db'); s.backup(d); d.close()"
docker compose cp bara:/data/backup.db ./streak-backup.db
```

Atau dengan CLI: `sqlite3 /data/streak.db ".backup '/data/backup.db'"`.

## Upgrade dari Versi JSON

Saat pertama kali dijalankan, panel otomatis memigrasikan file JSON lama (pengguna, sesi, pengaturan, akun, cookie, kontak, jadwal, riwayat) ke SQLite dalam satu transaksi. File lama tidak dihapus: dipindahkan ke `/data/backup-json-<waktu>/`. Folder `proofs/` tetap di tempatnya. Migrasi aman dijalankan berulang.

## Catatan

- Taruh di belakang HTTPS (reverse proxy) bila diakses lewat internet. Gunakan password pengguna dan `API_KEY` yang kuat.
- Cookie TikTok setara akses ke akun Anda; jaga volume `/data` tetap privat.
- Selector halaman TikTok bisa berubah sewaktu-waktu; jika gagal, lihat log di dashboard.
- Otomasi dapat melanggar ketentuan layanan TikTok. Gunakan dengan risiko sendiri.
