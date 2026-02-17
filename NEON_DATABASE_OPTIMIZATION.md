# 🐘 Neon Database Optimization Guide

Panduan optimasi untuk menggunakan Neon Serverless PostgreSQL dengan aplikasi sentiment analysis.

## 📊 Current Setup

- **Database:** Neon Serverless PostgreSQL (Free Tier)
- **Backend:** VPS Hostinger (8GB RAM, 100GB Storage)
- **Frontend:** Vercel

## ⚠️ Neon Free Tier Limitations

### 1. **Connection Limits**

- **Max connections:** ~100-200 (shared across all clients)
- **Impact:** Multiple workers/apps bisa exhaust connections
- **Solution:** Conservative connection pooling

### 2. **Cold Start (Auto-Suspend)**

- **Idle timeout:** 5 minutes
- **Wake-up time:** 1-3 seconds
- **Impact:** First query setelah idle lambat
- **Solution:** Connection warmup saat startup

### 3. **Compute Hours**

- **Free tier:** ~100 active hours/month
- **Impact:** Enough untuk dev/testing, mungkin kurang untuk production
- **Monitoring:** Check usage di Neon dashboard

### 4. **Storage**

- **Free tier:** 512MB
- **Monitoring:**
  ```sql
  SELECT pg_size_pretty(pg_database_size('neondb'));
  ```

### 5. **Region Latency**

- **Neon US/EU regions**
- **VPS Hostinger location:** Check region
- **Impact:** Network latency 50-200ms jika cross-region
- **Solution:** Pilih Neon region terdekat dengan VPS

## ✅ Optimizations Implemented

### 1. **Conservative Connection Pool**

```python
pool_size=3        # Max 3 persistent connections per worker
max_overflow=5     # Max 5 additional connections when busy
# Total: 8 connections per worker
```

**Why:**

- Neon free tier: ~100 max connections
- Reserve buffer untuk admin tools, other apps
- Prevent pool exhaustion

### 2. **Connection Health Checks**

```python
pool_pre_ping=True      # Check before use
pool_recycle=300        # Recycle after 5 minutes
```

**Why:**

- Neon auto-suspends after 5 min idle
- Recycle prevents stale connections
- Pre-ping detects cold starts early

### 3. **Optimized Timeouts**

```python
statement_timeout=300000   # 5 minutes (reduced from 10)
command_timeout=300        # 5 minutes
```

**Why:**

- Faster failure detection
- Prevent connection hogging
- Better for serverless architecture

### 4. **JIT Disabled**

```python
"jit": "off"  # Disable PostgreSQL JIT compilation
```

**Why:**

- Neon cold start already slow
- JIT adds ~100-500ms warmup
- Benefit negligible for small queries

### 5. **Startup Database Warmup**

```python
@app.on_event("startup")
async def startup_event():
    # Execute SELECT 1 to wake up Neon
```

**Why:**

- Prevent first user experiencing cold start
- Keep connection alive during startup

### 6. **Chunked Bulk Operations**

```python
CHUNK_SIZE = 100  # Insert 100 comments per transaction
```

**Why:**

- Prevent long-running transactions
- Avoid connection timeout
- Better memory usage

## 📈 Performance Benchmarks

### Cold Start (First Query After Idle)

- **Before optimization:** 2-4 seconds
- **With warmup:** 0.5-1 second (if within 5 min)

### Bulk Insert (500 comments)

- **Single transaction:** ❌ Timeout
- **Chunked (100 per batch):** ✅ 5-10 seconds

### Connection Pool Exhaustion

- **Before (pool_size=5, overflow=10):** 15 connections × workers = potential exhaust
- **After (pool_size=3, overflow=5):** 8 connections × workers = safer

## 🔍 Monitoring & Debugging

### 1. Health Check Endpoint

```bash
curl https://your-api.com/health
```

**Response:**

```json
{
  "status": "ok",
  "database": {
    "healthy": true,
    "pool": {
      "size": 3,
      "checked_in": 2,
      "checked_out": 1,
      "overflow": 0
    }
  },
  "concurrent_analysis": {
    "active": 1,
    "max": 2,
    "available": 1
  }
}
```

### 2. Check Neon Dashboard

- **Active hours:** Console → Project → Usage
- **Connections:** Console → Project → Operations
- **Storage:** SQL Editor → Run query above

### 3. Backend Logs

Look for:

```
INFO: Database connection warmed up successfully
INFO: Starting bulk insert of 419 comments in chunks of 100
WARNING: DB error on chunk 0, retry 1/3
```

## 🚨 Common Issues & Solutions

### Issue: "Connection pool exhausted"

**Cause:** Too many concurrent requests
**Solution:**

1. Check health endpoint → pool status
2. Reduce `MAX_CONCURRENT_ANALYSIS=1`
3. Consider rate limiting stricter

### Issue: "Connection does not exist error"

**Cause:** Long-running transaction + connection timeout
**Solution:**

1. ✅ Already fixed: Chunked bulk operations
2. Check if transaction > 5 minutes

### Issue: Slow first query

**Cause:** Neon cold start after idle
**Solution:**

1. ✅ Already implemented: Startup warmup
2. Consider periodic keep-alive (cron job)

### Issue: "Too many connections" error

**Cause:** Exceeded Neon connection limit
**Solution:**

1. Reduce pool_size further (2 instead of 3)
2. Check for connection leaks
3. Ensure proper connection closing

## 💰 Upgrade Considerations

### When to Upgrade to Neon Pro:

- ✅ If compute hours > 100/month
- ✅ If need >512MB storage
- ✅ If need higher connection limit
- ✅ If cold start becomes UX issue
- ✅ If need better SLA/support

### Neon Pro Benefits:

- **No auto-suspend:** Zero cold starts
- **More compute hours:** Unlimited
- **Higher connection limit:** ~1000+
- **Better performance:** Dedicated resources
- **Autoscaling:** Scale compute dynamically

## 🎯 Best Practices for Neon

### DO ✅

- Use connection pooling (already configured)
- Close connections properly (async context managers)
- Monitor usage via health endpoint
- Use chunked operations for bulk data
- Keep transactions short (<30 seconds ideal)
- Use indexes on frequently queried columns

### DON'T ❌

- Don't open connections without pooling
- Don't run transactions >5 minutes
- Don't ignore pool_pre_ping warnings
- Don't exceed connection limits
- Don't store large binary data (use S3/R2)
- Don't use multiple large connections simultaneously

## 📊 Recommended Settings by Use Case

### Development/Testing (Current - Free Tier)

```python
pool_size=3
max_overflow=5
MAX_CONCURRENT_ANALYSIS=2
```

### Low Traffic Production (<100 users/day)

```python
pool_size=3
max_overflow=5
MAX_CONCURRENT_ANALYSIS=2
```

**Consider:** Upgrade to Pro for reliability

### Medium Traffic (100-1000 users/day)

```python
pool_size=5
max_overflow=10
MAX_CONCURRENT_ANALYSIS=3
```

**Requires:** Neon Pro plan

### High Traffic (>1000 users/day)

```python
pool_size=10
max_overflow=20
MAX_CONCURRENT_ANALYSIS=5
```

**Requires:** Neon Scale/Business plan

## 🔧 Alternative Solutions

### If Neon Free Tier Too Limited:

1. **Supabase Free Tier**
   - 500MB storage
   - No auto-suspend
   - More generous limits

2. **Railway PostgreSQL**
   - $5/month
   - 1GB storage
   - Good for startups

3. **Self-hosted PostgreSQL on VPS**
   - Full control
   - No external network latency
   - Requires maintenance

4. **CockroachDB Serverless**
   - 5GB storage free
   - Good global distribution

## 📝 Connection String Format

Neon provides pooler connection string:

```bash
# Direct connection (not recommended for serverless)
postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb

# Pooled connection (recommended)
postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require&pooler=true
```

**Always use `?pooler=true`** for serverless environments!

## 🎓 Summary

**Neon Free Tier is SUFFICIENT for:**

- ✅ Development & testing
- ✅ Skripsi/thesis projects
- ✅ MVP/proof-of-concept
- ✅ Low-traffic applications (<50 daily users)

**Consider upgrading if:**

- ❌ >100 compute hours/month
- ❌ Frequent cold starts affecting UX
- ❌ >512MB storage needed
- ❌ Need SLA/support
- ❌ Production app with paying customers

**Your setup (8GB VPS + Neon Free) is OPTIMAL for skripsi!** 🎉
