# Valorant Update Bot (Webhook + GitHub Actions)

Template ini memantau halaman berita Valorant (patch notes) dan mengirim notifikasi ke Discord melalui Webhook.

## Setup
1. Buat repository baru di GitHub dan push file-file template ini.
2. Di repo GitHub: Settings -> Secrets -> Actions -> New repository secret
   - Name: `WEBHOOK`
   - Value: Discord webhook URL
3. Aktifkan GitHub Actions (default aktif). Workflow akan berjalan otomatis sesuai cron (15 menit).

## Menyesuaikan
- Jika struktur laman berubah, perbarui selector di `valorant_updates.py` pada fungsi `fetch_latest()`.
- Untuk memantau sumber lain (dev blog, reddit), ubah `URL` dan parsing logic.

