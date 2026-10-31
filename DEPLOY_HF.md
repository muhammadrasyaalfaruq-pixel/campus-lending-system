# Deploy ke Hugging Face Spaces

Siap deploy. Langkah:

## 1. Setup Database (Supabase Free)
- Daftar di [supabase.com](https://supabase.com)
- Buat project baru, ambil connection string PostgreSQL
- Format: `postgresql://user:password@host:port/dbname`

## 2. Setup Hugging Face Space
- Buka [huggingface.co/spaces](https://huggingface.co/spaces)
- Klik **Create new Space**
- Pilih **Docker** sebagai runtime
- Pilih **Private** atau **Public**
- Connect repository ini (atau upload files)

## 3. Environment Variables di HF Space Settings
Tambah di **Settings > Secrets**:
```
DATABASE_URL=postgresql://user:password@host:port/dbname
SECRET_KEY=pinjamkampus-secret-key-2026-uts-semester-3-ganti-di-production
FINE_RATE_PER_DAY=5000
MAX_ACTIVE_LOANS_PER_USER=3
```

## 4. Startup
Space otomatis run dengan `Dockerfile`. Tunggu build selesai (5-10 menit).

## 5. URL Aktif
Setelah running:
```
https://huggingface.co/spaces/[username]/[space-name]
```

Linkat ke dosen buat dicek.

## Notes
- Aplikasi sleep jika idle 48 jam (bisa reactivate manual)
- Database di Supabase tetap aktif gratis
- Upload file besar? Tanya dosen untuk extended storage
