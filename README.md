# TikTok Streak Panel

Panel web untuk mengotomatiskan pengiriman pesan streak TikTok. Berjalan di satu container Docker (FastAPI + Chromium headless + scheduler bawaan).

## Fitur

- Banyak akun TikTok: tiap akun punya cookie, kontak, dan jadwal sendiri; proses berjalan bergantian
- UI web: dashboard, log live, riwayat, kelola kontak, cookie, dan pengaturan
- Kirim sekarang atau mode uji (cek kontak tanpa mengirim)
- Beberapa jadwal kirim per hari (mis. pagi dan malam), tiap jadwal bisa punya pesan sendiri, dengan timezone
- Login TikTok langsung di panel (browser remote) atau tempel cookie manual
- Notifikasi Discord (webhook) dan Telegram, opsional
- Semua data (cookie, kontak, pengaturan, riwayat) tersimpan di volume Docker `/data`

## Menjalankan

```bash
cp .env.example .env
# edit .env, isi API_KEY
docker compose up -d --build
```

Buka `http://localhost:8000`, masuk dengan `API_KEY`.

### Akses privat di VPS (tanpa ekspose ke internet)

Secara default port hanya di-bind ke `127.0.0.1` di VPS (`BIND_ADDRESS` di `.env`), jadi tidak bisa diakses dari luar. Untuk membuka panel dari laptop, pakai SSH tunnel:

```bash
ssh -L 8000:127.0.0.1:8000 user@ip-vps
```

Lalu buka `http://localhost:8000` di laptop selama tunnel aktif. Alternatif: VPN pribadi seperti Tailscale atau WireGuard.

## Langkah pertama di UI

1. **Akun** (opsional): tab *Akun* untuk menambah akun lain. Akun pertama bernama "Utama". Pilih akun aktif di pojok kanan atas; tab Kontak, Cookie, dan Dashboard mengikuti akun yang dipilih.
2. **Cookie**: di tab *Cookie* klik *Mulai login*, login ke TikTok pada tampilan browser di panel (klik/ketik langsung, captcha juga bisa), lalu *Simpan sesi login*. Alternatif: tempel cookie manual (JSON dari Cookie-Editor atau string header `Cookie`).
3. **Kontak**: tambahkan nickname persis seperti di daftar pesan TikTok.
4. **Dashboard**: jalankan *Uji* dulu untuk memastikan login dan kontak terbaca, lalu *Kirim streak sekarang*.
5. **Pengaturan**: atur pesan default, zona waktu, dan Discord/Telegram.

## API

Semua endpoint `/api/*` (kecuali `/api/health`) memakai header `X-API-Key`.

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
| GET / PUT | `/api/settings` | Pengaturan |
| GET / DELETE | `/api/history` | Riwayat |

## Catatan

- Taruh di belakang HTTPS (reverse proxy) bila diakses lewat internet. Jangan expose tanpa `API_KEY` yang kuat.
- Cookie TikTok setara akses ke akun Anda; jaga volume `/data` tetap privat.
- Selector halaman TikTok bisa berubah sewaktu-waktu; jika gagal, lihat log di dashboard.
- Otomasi dapat melanggar ketentuan layanan TikTok. Gunakan dengan risiko sendiri.
