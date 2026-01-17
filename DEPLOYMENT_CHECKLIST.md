# Deployment & Setup Checklist

**Status:** Ready for Testing & Deployment  
**Date:** January 16, 2026

---

## ✅ Pre-Deployment Checklist

### Backend Setup

- [ ] Install dependencies:

  ```bash
  cd backend
  pip install -r requirements.txt
  ```

- [ ] Create `.env` file dari template:

  ```bash
  cp .env.example .env
  # Edit .env dengan nilai yang sesuai
  ```

- [ ] Setup database:

  ```bash
  # Pastikan PostgreSQL running
  # Run migrations
  alembic upgrade head
  ```

- [ ] Download/setup sentiment model:

  ```bash
  # Model file harus ada di ./model directory
  # File yang diperlukan:
  # - model.safetensors
  # - tokenizer.json
  # - vocab.json
  # - config.json
  # - special_tokens_map.json
  ```

- [ ] Create logs directory:

  ```bash
  mkdir -p logs
  ```

- [ ] Test backend startup:
  ```bash
  uvicorn app.main:app --reload
  # Seharusnya bisa diakses di http://localhost:8000
  # Health check: http://localhost:8000/health
  ```

### Frontend Setup

- [ ] Install dependencies:

  ```bash
  cd frontend
  npm install
  ```

- [ ] Create `.env.local` dari template:

  ```bash
  cp .env.example .env.local
  # Edit dengan API URL yang sesuai
  ```

- [ ] Test frontend development:

  ```bash
  npm run dev
  # Seharusnya bisa diakses di http://localhost:5173
  ```

- [ ] Build untuk production:
  ```bash
  npm run build
  # Output di folder dist/
  ```

---

## 🧪 Testing Checklist

### Security Features

- [ ] **Rate Limiting:**

  - [ ] Try 6 registrations in 1 minute → 6th should fail
  - [ ] Try 4 analysis in 1 minute → 4th should fail
  - [ ] Error message shows 429 status code

- [ ] **Input Validation:**

  - [ ] Try register dengan invalid email → Should reject
  - [ ] Try register dengan password "short" → Should reject (min 8 chars)
  - [ ] Try register dengan password "password123" → Should reject (no uppercase)
  - [ ] Try register dengan password "PASSWORD123" → Should reject (no lowercase)

- [ ] **URL Validation:**

  - [ ] Try analyze dengan URL "http://malicious.com" → Should reject
  - [ ] Try analyze dengan invalid YouTube URL → Should reject
  - [ ] Valid YouTube URL works correctly

- [ ] **XSS Prevention:**

  - [ ] Comments dengan `<script>` tags tidak bisa di-inject
  - [ ] Comments properly escaped saat displayed
  - [ ] No HTML tags bisa disimpan di database

- [ ] **Token Expiration:**

  - [ ] Access history/detail dengan expired token → 401 response
  - [ ] Frontend auto-redirect ke login
  - [ ] localStorage cleared
  - [ ] User must login again

- [ ] **CORS:**
  - [ ] Request dari allowed origins work
  - [ ] Request dari non-allowed origins rejected

### Functionality

- [ ] **Authentication:**

  - [ ] Register dengan valid data works
  - [ ] Login dengan correct credentials works
  - [ ] Login dengan wrong password fails
  - [ ] Google OAuth login works
  - [ ] Token diterima dan disimpan

- [ ] **Analysis:**

  - [ ] Analyze YouTube video works
  - [ ] Comments fetched dan dianalisis
  - [ ] Sentiment distribution correct
  - [ ] Results disimpan di database

- [ ] **History:**

  - [ ] Get analysis history works
  - [ ] Only user's data ditampilkan
  - [ ] Pagination works correctly

- [ ] **Comments:**

  - [ ] Get comments per analysis works
  - [ ] Sentiment filter works
  - [ ] Pagination works correctly
  - [ ] Comments properly sanitized

- [ ] **Logging:**
  - [ ] `logs/application.log` contains JSON logs
  - [ ] `logs/error.log` contains error logs
  - [ ] Logs properly rotated when size exceeds 10MB

---

## 📊 Performance Testing

- [ ] Load testing dengan 10 concurrent requests
- [ ] Database query optimization check
- [ ] API response time < 30 seconds untuk analysis
- [ ] Memory usage monitoring
- [ ] Log file size monitoring

---

## 🔐 Security Testing

- [ ] SQL injection attempts fail
- [ ] XSS attacks fail
- [ ] CSRF protection (if needed)
- [ ] Rate limiting blocks abuse
- [ ] No sensitive data in logs
- [ ] No hardcoded credentials

---

## 📝 Documentation

- [ ] README.md updated dengan latest features
- [ ] API documentation complete
- [ ] Environment variables documented (.env.example)
- [ ] Setup instructions clear
- [ ] Deployment instructions documented

---

## 🚀 Production Deployment Checklist

### Before Deploying

- [ ] All tests passing
- [ ] Security audit completed
- [ ] Performance testing done
- [ ] Database backups configured
- [ ] Error monitoring setup (e.g., Sentry)
- [ ] Log aggregation setup (e.g., ELK Stack)

### Deployment Steps

- [ ] Update environment variables untuk production
- [ ] Set `SECRET_KEY` ke strong random value
- [ ] Disable debug mode
- [ ] Set appropriate log level (WARNING or ERROR)
- [ ] Configure CORS untuk production domains
- [ ] Setup HTTPS/SSL certificates
- [ ] Configure database backups
- [ ] Setup monitoring & alerting

### Post-Deployment

- [ ] Verify health check endpoint
- [ ] Test critical user flows
- [ ] Monitor logs untuk errors
- [ ] Check rate limiting adalah effective
- [ ] Verify database performance
- [ ] Setup automated backups

---

## 🆘 Troubleshooting

### Backend Issues

**Problem:** "Module not found" error

```bash
# Solution: Install missing dependencies
pip install -r requirements.txt
```

**Problem:** Database connection error

```bash
# Solution: Check DATABASE_URL in .env
# Format: postgresql+asyncpg://user:password@localhost:5432/db
```

**Problem:** YouTube API error

```bash
# Solution: Check YOUTUBE_API_KEY is valid
# Get key from: https://console.cloud.google.com/
```

**Problem:** Sentiment model not found

```bash
# Solution: Check MODEL_PATH points to correct directory
# Required files: model.safetensors, tokenizer.json, vocab.json
```

### Frontend Issues

**Problem:** API calls failing with CORS error

```bash
# Solution: Check VITE_API_URL in .env.local
# Should match backend URL
```

**Problem:** Token not being sent to API

```bash
# Solution: Check localStorage has 'accessToken' key
# Clear localStorage dan login again
```

**Problem:** Build failing

```bash
# Solution: Clear node_modules dan reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 📞 Support

Untuk issues atau pertanyaan:

1. Check logs: `logs/application.log`
2. Check environment variables: `.env` file
3. Review documentation di repo
4. Check API health: `http://localhost:8000/health`

---

## ✨ Features Implemented

### Critical Security Fixes (✅ Complete)

- [x] Input validation (Pydantic schemas)
- [x] CORS hardening
- [x] Request size limits
- [x] YouTube URL validation
- [x] Exception handling
- [x] Authorization checks

### High Priority Features (✅ Complete)

- [x] Rate limiting
- [x] Structured JSON logging
- [x] Input sanitization (XSS prevention)
- [x] Frontend token expiration handling
- [x] Proper error messages

### Medium Priority (⏳ Recommended)

- [ ] Database connection health check
- [ ] Refresh token mechanism
- [ ] API documentation (Swagger)
- [ ] Monitoring & alerting setup
- [ ] Load testing

---

**Ready for deployment!** 🚀
