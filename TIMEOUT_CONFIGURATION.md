# ⏱️ Timeout Configuration

Configuration untuk handle analisis video dengan banyak komentar (1500+).

## 📊 Timeout Architecture

### 1. **Frontend (axios)**

```typescript
timeout: 900000; // 15 minutes
```

- **Purpose**: Client-side request timeout
- **Location**: `frontend/src/api/axios.ts`
- **Handles**: Long-running analysis requests

### 2. **Backend Semaphore (Queue Wait)**

```python
asyncio.timeout(300)  // 5 minutes
```

- **Purpose**: Maximum time to wait in queue
- **Location**: `backend/app/services/analysis_service.py`
- **Handles**: When server is processing other analyses
- **Config**: `MAX_CONCURRENT_ANALYSIS=2` (default)

### 3. **Uvicorn Server**

```bash
--timeout-keep-alive 120        # 2 minutes
--timeout-graceful-shutdown 300  # 5 minutes
```

- **Purpose**: Connection and shutdown timeouts
- **Location**: `Dockerfile`, `railway.json`
- **Note**: Uvicorn has NO request timeout (allows long-running requests)

### 4. **Cloud Provider Limits**

#### Railway

- **Platform timeout**: ~5-10 minutes (free tier)
- **Workaround**: Upgrade to paid plan for longer timeouts
- **Alternative**: Use background jobs for very long analyses

#### Vercel (if used for backend)

- **Serverless timeout**: 10 seconds (Hobby), 60 seconds (Pro)
- **❌ Not suitable** for this backend - use Railway/Docker deployment

## 🎯 Recommended Settings

### For Analysis with 1000-2000 comments:

- **Expected duration**: 2-5 minutes
- **Frontend timeout**: 15 minutes ✅
- **Queue timeout**: 5 minutes ✅
- **Concurrent limit**: 2 analyses ✅

### For Analysis with 2000+ comments:

- **Expected duration**: 5-10 minutes
- **Consider**: Increase `MAX_CONCURRENT_ANALYSIS=1` to prevent OOM
- **Consider**: Add progress streaming or background job pattern

## 🔧 Tuning Guide

### If analysis times out:

1. Check concurrent analyses via `/health` endpoint
2. Increase `MAX_CONCURRENT_ANALYSIS` if memory allows
3. Decrease `SENTIMENT_BATCH_SIZE` to reduce memory usage
4. Consider ONNX optimization for 5-10x speedup

### If server runs out of memory:

1. Decrease `MAX_CONCURRENT_ANALYSIS=1`
2. Decrease `SENTIMENT_BATCH_SIZE=8`
3. Monitor via Railway metrics dashboard

## 📝 Environment Variables

```bash
# Backend
MAX_CONCURRENT_ANALYSIS=2      # Max parallel analyses
SENTIMENT_BATCH_SIZE=16        # Batch size for inference
ONNX_MODEL_PATH=/app/models    # Use ONNX for speed

# Frontend (optional override)
VITE_API_TIMEOUT=900000        # 15 minutes in ms
```

## 🚀 Performance Optimizations

1. **Batch Processing**: ✅ Implemented (100 comments per chunk)
2. **ONNX Runtime**: ⚡ 5-10x faster inference
3. **Concurrent Control**: ✅ Semaphore protection
4. **Thread-safe Singleton**: ✅ Shared model across requests

## 📈 Monitoring

Health check endpoint shows concurrent status:

```bash
curl http://localhost:8000/health
{
  "status": "ok",
  "concurrent_analysis": {
    "active": 1,
    "max": 2,
    "available": 1
  }
}
```

## ⚠️ Important Notes

- Railway free tier may have platform-level timeout (5-10 min)
- Vercel is NOT suitable for backend (too short timeout)
- Frontend timeout should be > (max analysis time + queue time)
- Consider WebSocket streaming for very long analyses
