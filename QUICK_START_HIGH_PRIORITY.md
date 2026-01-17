# Quick Start Guide - High Priority Improvements

**Get up and running in 5 minutes!**

---

## 🚀 Quick Setup

### Step 1: Install New Dependencies (1 minute)

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Setup Environment Files (1 minute)

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your values (YouTube API key, DB URL, Secret key)

# Frontend
cd ../frontend
cp .env.example .env.local
# Edit .env.local with API URL
```

### Step 3: Verify Backend (1 minute)

```bash
cd backend
uvicorn app.main:app --reload

# In another terminal, test health check:
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### Step 4: Verify Frontend (1 minute)

```bash
cd frontend
npm install  # jika belum
npm run dev

# Akses: http://localhost:5173
```

### Step 5: Test Features (1 minute)

```bash
# Test rate limiting (try 6 registrations in 1 min)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"SecurePass123"}'

# 6th attempt akan return 429 (Too Many Requests)

# Check logs
tail -f logs/application.log | jq '.'
```

---

## 📊 What's New

### Rate Limiting

```
Per IP address limits:
- /auth/register:   5/minute
- /auth/login:      10/minute
- /analysis:        3/minute (heavy)
- /analysis/*:      30/minute (light)
```

### JSON Logging

```
Logs stored in:
- logs/application.log  (all logs)
- logs/error.log        (errors only)

Format:
{"timestamp":"2026-01-16T10:30:45.123456","level":"INFO",...}
```

### XSS Prevention

```
All comments sanitized:
- HTML tags removed
- Special characters escaped
- Max 5000 chars per comment
```

### Token Expiration

```
Frontend now:
- Auto-detects 401 responses
- Clears token automatically
- Redirects to /login
```

---

## 🧪 Quick Tests

### Test 1: Rate Limiting

```bash
# Run 6 times in quick succession
for i in {1..6}; do
  curl -X POST http://localhost:8000/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"user$i@test.com\",\"password\":\"SecurePass123\"}" \
    -w "\nStatus: %{http_code}\n"
  sleep 1
done

# Expected: First 5 succeed, 6th returns 429
```

### Test 2: Input Validation

```bash
# Try weak password
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"weak"}'

# Expected: 422 Unprocessable Entity
```

### Test 3: Check Logs

```bash
# Pretty-print JSON logs
tail -f logs/application.log | jq '.'

# Watch errors only
tail -f logs/error.log | jq '.'
```

### Test 4: Token Expiration (Frontend)

```typescript
// In browser console
localStorage.setItem("accessToken", "invalid.token.here");

// Try to fetch any protected endpoint
// Frontend should auto-redirect to /login
```

---

## ⚙️ Configuration Quick Reference

### Backend (.env)

```env
# Critical
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
YOUTUBE_API_KEY=your_api_key
SECRET_KEY=min-32-char-random-string

# Optional
MODEL_PATH=./model
LOG_LEVEL=INFO
```

### Frontend (.env.local)

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_client_id
```

---

## 📱 Common Issues & Fixes

### Issue: "Rate limit exceeded" on first try

**Fix:** Rate limit is per IP. For localhost, wait before retrying or test with different endpoints.

### Issue: "No module named 'slowapi'"

**Fix:** Run `pip install -r requirements.txt` again

### Issue: Logs not showing up

**Fix:** Check if `logs/` directory exists:

```bash
mkdir -p logs
```

### Issue: Frontend can't connect to backend

**Fix:** Verify VITE_API_URL in frontend/.env.local matches backend URL

### Issue: Comments showing as escaped HTML

**Fix:** This is correct! Frontend should use `textContent` or `innerText`, not `innerHTML`

---

## ✨ Feature Highlights

| Feature         | Command                                  | Result            |
| --------------- | ---------------------------------------- | ----------------- |
| Health Check    | `curl http://localhost:8000/health`      | `{"status":"ok"}` |
| Check Logs      | `tail -f logs/application.log \| jq '.'` | JSON logs         |
| View Errors     | `tail -f logs/error.log`                 | Error logs only   |
| Register        | POST /auth/register                      | Create account    |
| Rate Limit Test | Run 6 registrations/min                  | 6th gets 429      |

---

## 🔐 Security Checklist

- [x] Rate limiting enabled on all endpoints
- [x] JSON logging for audit trail
- [x] XSS prevention (sanitized comments)
- [x] CORS restrictions applied
- [x] Request size limits (1 MB max)
- [x] Token expiration handling
- [x] Input validation on all schemas
- [x] Proper error messages (no info leak)

---

## 📈 Next Steps

### Immediate (Before Using in Production):

1. [ ] Update SECRET_KEY in .env (generate with Python)
2. [ ] Configure proper DATABASE_URL
3. [ ] Get YOUTUBE_API_KEY from Google Console
4. [ ] Setup Google OAuth credentials
5. [ ] Download/setup sentiment model

### Before Deployment:

1. [ ] Run full test suite
2. [ ] Check all logs are working
3. [ ] Verify rate limiting works
4. [ ] Test XSS prevention
5. [ ] Verify token expiration

### Optional Enhancements:

1. [ ] Setup database monitoring
2. [ ] Setup error tracking (Sentry)
3. [ ] Setup log aggregation (ELK)
4. [ ] Add API documentation (Swagger)
5. [ ] Setup CI/CD pipeline

---

## 💡 Pro Tips

### Development

```bash
# Watch logs in real-time
tail -f logs/application.log | jq '.level, .message'

# Filter by level
tail -f logs/application.log | jq 'select(.level=="ERROR")'

# Generate test data
for i in {1..10}; do
  curl -X POST http://localhost:8000/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"user$i@test.com\",\"password\":\"SecurePass123\"}"
done
```

### Testing

```bash
# Test with Bearer token
TOKEN="eyJ..."
curl http://localhost:8000/analysis/history \
  -H "Authorization: Bearer $TOKEN"

# Save response to file
curl ... -o response.json | jq '.'

# Load test (install: pip install locust)
# locust -f locustfile.py --host=http://localhost:8000
```

---

## ✅ You're All Set!

**All high priority features are now implemented and ready to use!**

- ✅ Rate limiting prevents abuse
- ✅ JSON logging for monitoring
- ✅ XSS prevention for security
- ✅ Better error handling for UX
- ✅ Token expiration handling

**Start the application and enjoy the improvements!** 🚀
