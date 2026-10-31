# PinjamKampus

Sistem manajemen peminjaman alat/barang di kampus dengan FastAPI, SQLAlchemy, dan MySQL.

## Fitur

- **Autentikasi** – Registrasi, login, logout dengan bcrypt hashing
- **Katalog Alat** – Lihat daftar alat dengan kategori dan foto
- **Peminjaman** – User ajukan pinjam, admin setujui/tolak, keluar notifikasi
- **Denda Otomatis** – Hitung denda jika pengembalian terlambat
- **Dashboard Admin** – Ringkasan statistik, persetujuan pinjaman, kelola alat
- **Laporan PDF** – Export riwayat peminjaman
- **Notifikasi** – User & admin menerima notifikasi status pinjam
- **Tiket QR Peminjaman** – QR untuk verifikasi pengambilan atau pengembalian alat
- **Bukti Pengembalian PDF** – Peminjam mengunduh bukti setelah pinjaman selesai, termasuk kondisi alat dan tanggal pengembalian
- **Pemeriksaan Kondisi Alat** – Admin mencatat kondisi dan catatan tiap alat saat menerima pengembalian

## Persyaratan

- Python 3.11+
- MySQL 5.7+
- pip

## Instalasi

### 1. Clone dan masuk folder
```bash
cd pinjamkampus
```

### 2. Buat virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup database
Buat database MySQL:
```sql
CREATE DATABASE pinjamkampus_dev DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Konfigurasi .env
Copy `.env.example` ke `.env` dan sesuaikan:
```bash
cp .env.example .env
```

Isi nilai:
```
SQLALCHEMY_DATABASE_URL=mysql+pymysql://root:@localhost/pinjamkampus_dev
SECRET_KEY=your-secret-key-here
FINE_RATE_PER_DAY=50000
MAX_ACTIVE_LOANS_PER_USER=3
```

### 6. Jalankan migrasi
```bash
alembic upgrade head
```

### 7. Seed data awal
```bash
python seed.py
```

Akun admin default:
- Email: `admin@kampus.ac.id`
- Password: `admin123`

### 8. Jalankan server
```bash
uvicorn app.main:app --reload
```

Buka: http://127.0.0.1:8000

## Struktur Folder

```
pinjamkampus/
├── app/
│   ├── main.py                 # FastAPI app & router inclusion
│   ├── database.py             # SQLAlchemy config
│   ├── models/
│   │   └── entities.py         # SQLAlchemy models (User, Item, Loan, dll)
│   ├── routers/
│   │   ├── auth.py             # Register, login, logout
│   │   ├── admin.py            # Dashboard, laporan PDF
│   │   ├── items.py            # Katalog, CRUD alat
│   │   ├── loans.py            # Pinjam, approve, return
│   │   └── notifications.py    # Notifikasi user
│   ├── services/
│   │   └── auth_service.py     # Bcrypt hashing
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/main.js
│   │   └── uploads/            # Folder foto alat
│   └── templates/
│       ├── base.html
│       ├── home.html
│       ├── auth/
│       ├── admin/
│       ├── items/
│       ├── loans/
│       └── notifications/
├── migrations/                  # Alembic migrations
├── erd/                         # Diagram relasi entitas basis data (Mermaid & DBML)
│   ├── README.md                # Dokumentasi relasi & Mermaid diagram
│   └── schema.dbml              # Schema file untuk dbdiagram.io
├── alembic.ini                 # Alembic config
├── seed.py                     # Seeder admin & user role
├── requirements.txt            # Dependencies
├── .env.example                # Template .env
└── README.md                   # File ini
```

## Routes Utama

### Auth
- `GET /auth/register` – Halaman registrasi
- `POST /auth/register` – Submit registrasi
- `GET /auth/login` – Halaman login
- `POST /auth/login` – Submit login
- `GET /auth/logout` – Logout

### Katalog & Alat
- `GET /items` – Lihat katalog alat
- `GET /admin/items` – Admin: kelola alat (list)
- `POST /admin/items/add` – Admin: tambah alat
- `POST /admin/items/{id}/edit` – Admin: edit alat
- `POST /admin/items/{id}/delete` – Admin: hapus alat
- `GET /admin/items/categories` – Admin: kelola kategori

### Pinjaman
- `GET /loans/request` – Form ajukan pinjam
- `POST /loans/request` – Submit ajukan pinjam
- `GET /loans/my` – User: lihat pinjaman saya
- `GET /admin/loans` – Admin: persetujuan pinjaman
- `POST /admin/loans/{id}/approve` – Admin: setujui
- `POST /admin/loans/{id}/reject` – Admin: tolak
- `POST /admin/loans/{id}/mark-returned` – Admin: tandai dikembalikan

### Notifikasi
- `GET /notifications` – Lihat notifikasi
- `POST /notifications/{id}/read` – Tandai dibaca

### Admin
- `GET /admin` – Dashboard admin dengan ringkasan status pinjaman dan aksi cepat
- `GET /admin/users` – Kelola pengguna dan role
- `POST /admin/users` – Tambah pengguna
- `GET /admin/users/{id}/edit` – Form edit pengguna
- `POST /admin/users/{id}/update` – Simpan perubahan pengguna atau reset password
- `POST /admin/users/{id}/delete` – Hapus pengguna tanpa riwayat pinjaman
- `POST /admin/roles` – Tambah role
- `POST /admin/roles/{id}/delete` – Hapus role yang belum dipakai
- `GET /admin/reports/loans/pdf` – Download laporan PDF

## Teknologi

- **Framework:** FastAPI
- **Database:** MySQL + SQLAlchemy + Alembic
- **Auth:** Bcrypt
- **Template:** Jinja2
- **CSS:** Bootstrap 5
- **PDF:** ReportLab

## Testing

Jalankan pytest:
```bash
pytest
```

## Catatan

- Foto alat disimpan di `app/static/uploads/`, max 5MB.
- Denda dihitung otomatis jika pengembalian melampaui tanggal rencana.
- User maksimal 3 pinjaman aktif (dapat diubah di .env).
- Email admin saat ada pinjaman baru (optional, belum diimplementasi).

## Lisensi

MIT License - Tugas UTS Semester 3
