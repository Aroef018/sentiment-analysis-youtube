# 🚀 PANDUAN DEPLOYMENT - RAILWAY & VERCEL

> Menggunakan GitHub Student Pack benefits

---

## 📋 Pre-requisites

- [ ] GitHub Account
- [ ] Railway Account (https://railway.app - use GitHub Student Pack)
- [ ] Vercel Account (https://vercel.com - use GitHub Student Pack)
- [ ] Project di GitHub
- [ ] Environment variables siap

---

## TAHAP 1: Setup GitHub Repository

### 1.1 Push ke GitHub

```bash
cd /home/amar/skripsi/analisis-sentimen

# Jika belum git init
git init
git add .
git commit -m "Initial commit: YouTube sentiment analysis"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/analisis-sentimen.git
git push -u origin main
```

### 1.2 Buat Personal Access Token

- Pergi ke https://github.com/settings/tokens
- Click "Generate new token (classic)"
- Permissions: `repo`, `read:user`
- Copy token (simpan baik-baik!)

---

## TAHAP 2: Setup Backend di Railway

### 2.1 Buat PostgreSQL Database

1. Login ke https://railway.app
2. Click "Create Project"
3. Pilih "Provision PostgreSQL"
4. Tunggu database ready
5. Copy connection string dari Variables tab

### 2.2 Setup Backend Service

1. Di project yang sama, click "Create" > "GitHub Repo"
2. Connect ke repository `analisis-sentimen`
3. Setup Environment Variables:

```
DATABASE_URL=<dari PostgreSQL>
SECRET_KEY=generate-random-string (gunakan: openssl rand -hex 32)
GOOGLE_CLIENT_ID=your-google-client-id
YOUTUBE_API_KEY=your-youtube-api-key
FRONTEND_URL=https://your-frontend-domain.vercel.app
DEBUG=false
ENVIRONMENT=production
```

### 2.3 Deploy Backend

1. Push ke GitHub (jika ada perubahan)
2. Railway akan auto-deploy
3. Tunggu status "Success"
4. Copy domain backend dari Railway (misal: `https://analisis-sentimen-prod.up.railway.app`)

---

## TAHAP 3: Setup Frontend di Vercel

### 3.1 Konfigurasi Build Settings

Di dalam folder `/frontend`, pastikan ada:

```json
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### 3.2 Deploy ke Vercel

1. Login ke https://vercel.com
2. Click "Add New..." > "Project"
3. Import dari GitHub repository
4. Select root directory: `frontend`
5. Setup Environment Variables:

```
VITE_API_URL=https://your-backend-domain.railway.app
VITE_GOOGLE_CLIENT_ID=your-google-client-id
```

6. Build Command: `npm run build`
7. Output Directory: `dist`
8. Click "Deploy"

### 3.3 Update CORS di Backend

Setelah mendapat Vercel domain:

1. Di Railway, update environment variable:

```
FRONTEND_URL=https://your-app.vercel.app
```

2. Atau update `backend/app/main.py`:

```python
allow_origins=[
    "https://your-app.vercel.app",
    "https://www.your-app.vercel.app",
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
]
```

---

## TAHAP 4: Setup Database Migration

### 4.1 Run Alembic Migration

Setelah Railway database siap:

```bash
# Connect ke Railway database (dari Railway console)
# Copy DATABASE_URL dari Railway

# Run migration
SQLALCHEMY_DATABASE_URL="<database_url>" alembic upgrade head
```

Atau setup di Railway:

1. Create a "Worker" service
2. Command: `alembic upgrade head`
3. Jalankan sekali, lalu disable

---

## TAHAP 5: Testing

### 5.1 Test Backend

```bash
curl https://your-backend-domain.railway.app/health
# Expected: {"status": "ok"}
```

### 5.2 Test Frontend

- Buka https://your-app.vercel.app
- Pastikan bisa:
  - [ ] Register
  - [ ] Login
  - [ ] Submit YouTube URL
  - [ ] Lihat hasil analisis

---

## 🔒 Security Checklist

- [ ] SECRET_KEY di-generate random
- [ ] DEBUG=false di production
- [ ] Database password di-hide di environment variable
- [ ] CORS hanya allow domain sendiri
- [ ] API keys di environment variable
- [ ] `.env` tidak di-commit ke GitHub

---

## 📊 Monitoring

### Railway Monitoring

- Pergi ke Railway dashboard
- Tab "Logs" untuk melihat error
- Tab "Metrics" untuk CPU/Memory

### Vercel Monitoring

- Pergi ke Vercel project
- Tab "Analytics" untuk performance
- Tab "Functions" untuk API usage

---

## 🆘 Troubleshooting

### Error: Database connection refused

**Solution:**

- Pastikan DATABASE_URL benar
- Copy dari Railway > PostgreSQL > Variables
- Format harus: `postgresql://user:password@host:port/dbname`

### Error: CORS error di frontend

**Solution:**

- Update FRONTEND_URL di Railway environment
- Tambah domain di `allow_origins` di backend

### Error: Static assets 404 di frontend

**Solution:**

- Pastikan `vite.config.ts` sudah benar
- Build command: `npm run build`
- Output directory: `dist`

---

## 📱 Custom Domain (Optional)

### Setup Custom Domain

1. **Railway**: Dashboard > Service > Settings > Custom Domain
2. **Vercel**: Project Settings > Domains > Add Domain
3. Update DNS records sesuai instruksi

---

## ✅ Checklist Deployment

- [ ] Repository di GitHub
- [ ] PostgreSQL database di Railway
- [ ] Backend deployed di Railway
- [ ] Frontend deployed di Vercel
- [ ] Environment variables ter-setup
- [ ] Database migration sudah jalan
- [ ] Testing manual selesai
- [ ] Custom domain setup (optional)
- [ ] Monitoring setup

---

## 📚 Resources

- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- GitHub Student Pack: https://education.github.com/pack
