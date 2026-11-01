# Deploy ke Vercel - Panduan Lengkap

## STEP 1: Setup Database Cloud (10 menit)

Pilih salah satu:

### Opsi A: TiDB Cloud (Recommended)
1. Buka https://tidbcloud.com/free-trial
2. Daftar (gratis)
3. Buat Serverless Cluster
4. Tunggu ~5 menit
5. Klik **Connect** → Copy connection string
6. Ganti format ke:
   ```
   mysql+pymysql://user:password@host.tidbcloud.com:4000/database?ssl_verify_cert=false&ssl_verify_identity=false
   ```

### Opsi B: PlanetScale (Alternatif)
1. Buka https://planetscale.com
2. Daftar gratis
3. Buat database
4. Klik **Connect** → Python
5. Copy connection string

---

## STEP 2: Update `.env` Local

Ganti di file `.env`:
```env
DATABASE_URL=<paste-connection-string-dari-step-1>
SECRET_KEY=pinjamkampus_secret_2024_production_key_change_me
VERCEL=1
```

---

## STEP 3: Test Local dengan DB Cloud

```powershell
# Terminal di folder project
python -m pip install -r requirements.txt
alembic upgrade head
python seed.py
```

**Jika error**, berarti koneksi DB salah. Cek:
- Username/password benar?
- Host bisa diakses dari internet?
- Firewall DB cloud sudah allow semua IP?

---

## STEP 4: Push ke GitHub

```powershell
git add .
git commit -m "Prepare for Vercel deployment: serverless config"
git push origin main
```

---

## STEP 5: Deploy di Vercel

### Cara 1: CLI (Cepat)
```powershell
npm i -g vercel
vercel
```
Ikuti prompt, pilih import repo.

### Cara 2: Web Dashboard
1. Buka https://vercel.com
2. Login dengan GitHub
3. Klik **Add New** → **Project**
4. Pilih repo `campus-lending-system`
5. Di **Environment Variables**, isi:

| Var | Value |
|-----|-------|
| DATABASE_URL | `mysql+pymysql://...` |
| SECRET_KEY | `pinjamkampus_secret...` |
| ALGORITHM | `HS256` |
| ACCESS_TOKEN_EXPIRE_MINUTES | `60` |
| UPLOAD_DIR | `./app/static/uploads` |
| MAX_UPLOAD_SIZE | `5242880` |
| FINE_RATE_PER_DAY | `5000` |
| MAX_ACTIVE_LOANS_PER_USER | `3` |
| VERCEL | `1` |

6. Klik **Deploy**

---

## STEP 6: Verifikasi

Setelah deploy selesai:

```powershell
# Test homepage
curl https://<project-name>.vercel.app/

# Test API health
curl https://<project-name>.vercel.app/docs

# Test login
curl -X POST https://<project-name>.vercel.app/auth/login
```

---

## Troubleshooting

| Problem | Solusi |
|---------|--------|
| 500 Error | Cek Environment Variables di Vercel console |
| Database timeout | TiDB Cloud? Disable SSL verify atau upgrade plan |
| Static files 404 | Tunggu rebuild selesai, refresh browser |
| "Permission denied" | Check DB user permissions punya CREATE/ALTER |

---

## File yang Sudah Diupdate

✅ `vercel.json` - Config build
✅ `app/database.py` - Serverless pool config
✅ `.env.example` - Template env

## Next Run

Cukup push ke GitHub, Vercel auto-deploy otomatis setiap push.

---

**Butuh bantuan?** Reply dengan error message atau screenshot.
