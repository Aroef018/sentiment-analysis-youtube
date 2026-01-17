# Security & Validation Review - Aplikasi Analisis Sentimen

## 🔴 CRITICAL ISSUES (Prioritas Tinggi)

### 1. **Input Validation di Schemas (Pydantic)**

**Lokasi:** `backend/app/schemas.py`

**Masalah:**

- Email tidak memiliki validasi format atau panjang maksimal
- Password tidak memiliki minimum strength requirements
- Tidak ada validasi panjang atau format untuk `full_name`
- `GoogleLoginRequest.token` bisa berisi string kosong

**Solusi:**

```python
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Dict

class RegisterRequest(BaseModel):
    email: EmailStr  # Validasi format email
    password: str = Field(min_length=8, max_length=128)  # Min 8 karakter
    full_name: str | None = Field(None, max_length=200)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

class GoogleLoginRequest(BaseModel):
    token: str = Field(min_length=1)
```

---

### 2. **Missing Exception Handling di Auth Endpoints**

**Lokasi:** `backend/app/api/auth.py`

**Masalah:**

- `@router.post("/google")` tidak menangani exception dari `id_token.verify_oauth2_token()`
  - Bisa expose error details ke client
  - Tidak ada timeout handling untuk Google API call
- Duplikasi class `RegisterRequest` dan `LoginRequest` di schemas.py (baris 25-35)
- Exception handling terlalu generic

**Solusi:**

```python
@router.post("/google")
async def login_google(
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        google_user = id_token.verify_oauth2_token(
            payload.token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Authentication service error")

    email = google_user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not found in Google token")
```

---

### 3. **SQL Injection & Database Security**

**Lokasi:** `backend/app/api/analysis.py` & repository files

**Masalah:**

- URL YouTube dari user langsung diproses tanpa sanitasi
- Tidak ada rate limiting pada API endpoints
- Database queries bisa vulnerable jika ada dynamic query building

**Solusi:**

- Gunakan parameterized queries (sudah dilakukan via SQLAlchemy)
- Tambah rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/", response_model=AnalysisResponse)
@limiter.limit("5/minute")
async def analyze_youtube_video(...):
    pass
```

---

## 🟠 HIGH PRIORITY ISSUES

### 4. **YouTube URL Validation Terlalu Sederhana**

**Lokasi:** `backend/app/services/youtube_video_service.py`

**Masalah:**

- Regex pattern hanya check format, tidak validasi apakah URL dari YouTube
- Bisa menerima format: `v=xyzabcd1234` tanpa domain
- Tidak ada handling untuk URL yang di-encode atau special characters

**Solusi:**

```python
from urllib.parse import urlparse, parse_qs

def extract_video_id(self, url: str) -> str:
    """Extract video ID dengan validasi URL yang lebih ketat"""

    # Validasi protocol
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL harus menggunakan http atau https")

    try:
        parsed = urlparse(url)

        # Validasi domain
        if parsed.netloc not in ("youtube.com", "www.youtube.com", "youtu.be"):
            raise ValueError("URL harus dari YouTube")

        # Extract video ID
        if parsed.netloc == "youtu.be":
            video_id = parsed.path.lstrip("/")
        else:
            query_params = parse_qs(parsed.query)
            video_id = query_params.get("v", [""])[0]

        if not video_id or len(video_id) != 11:
            raise ValueError("Video ID tidak valid")

        # Validate character set
        if not re.match(r"^[a-zA-Z0-9_-]{11}$", video_id):
            raise ValueError("Video ID format tidak valid")

        return video_id
    except ValueError:
        raise
    except Exception:
        raise ValueError("URL YouTube tidak valid")
```

---

### 5. **No Request Size Limits**

**Lokasi:** `backend/app/main.py`

**Masalah:**

- Tidak ada limit untuk request body size
- User bisa kirim request sangat besar yang crash server
- YouTube API call tanpa timeout

**Solusi:**

```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class SizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int):
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            if "content-length" in request.headers:
                content_length = int(request.headers["content-length"])
                if content_length > self.max_upload_size:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request too large"}
                    )
        return await call_next(request)

app.add_middleware(SizeLimitMiddleware, max_upload_size=1_000_000)  # 1MB

# Timeout untuk YouTube API
from googleapiclient.discovery import build
timeout = 30  # detik
self.youtube = build(
    "youtube",
    "v3",
    developerKey=settings.YOUTUBE_API_KEY,
    cache_discovery=False,
    requestsPerSecond=1
)
```

---

### 6. **Token Expiration Tidak Divalidasi dengan Baik**

**Lokasi:** `backend/app/api/analysis.py` & `backend/app/api/auth.py`

**Masalah:**

- Catch-all exception handler di `/analysis` endpoint menyembunyikan actual error
- Jika token expired, user tidak tahu perbedaan antara "token invalid" vs "token expired"
- Tidak ada refresh token mechanism

**Solusi:**

```python
from jose import jwt, JWTError, ExpiredSignatureError

def decode_token_safely(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
```

---

### 7. **Incomplete Error Handling di YouTube Comment Service**

**Lokasi:** `backend/app/services/youtube_comment_service.py`

**Masalah:**

- API call ke YouTube tanpa error handling
- Jika quota habis atau video tidak punya comments, crash
- Tidak ada pagination limit (infinite loop risk)

**Solusi:**

```python
def _get_top_level_comments(self, video_id: str) -> list[dict]:
    comments = []
    next_page_token = None
    MAX_PAGES = 50  # Safety limit
    page_count = 0

    while True:
        try:
            if page_count >= MAX_PAGES:
                break

            response = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                textFormat="plainText",
                pageToken=next_page_token,
            ).execute()

            if "items" not in response or not response["items"]:
                break

            for item in response["items"]:
                try:
                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                    # ... process comment
                except (KeyError, TypeError):
                    continue  # Skip malformed comments

            next_page_token = response.get("nextPageToken")
            page_count += 1

            if not next_page_token:
                break

        except Exception as e:
            if "quotaExceeded" in str(e):
                raise Exception("YouTube API quota exceeded")
            elif "commentDisabled" in str(e):
                raise Exception("Comments disabled for this video")
            else:
                raise Exception(f"Failed to fetch comments: {str(e)}")

    return comments
```

---

## 🟡 MEDIUM PRIORITY ISSUES

### 8. **Missing User Authorization Checks**

**Lokasi:** `backend/app/api/analysis.py`

**Masalah:**

- Di endpoint `/detail/{video_id}`, hanya check user dari token tapi tidak selalu verified
- Tidak ada explicit check apakah analysis milik user yang request

**Solusi (sudah ada tapi bisa diperkuat):**

```python
# Di AnalysisRepository atau Analysis Service
async def get_latest_for_video_and_user(db, video_id, user_id):
    analysis = await db.execute(
        select(Analysis, Video)
        .join(Video)
        .where(
            Analysis.video_id == video_id,
            Analysis.user_id == user_id  # ← Ensure authorization
        )
        .order_by(Analysis.created_at.desc())
        .limit(1)
    )
    return analysis.first()
```

---

### 9. **No Input Sanitization untuk Comment Text**

**Lokasi:** `backend/app/services/preprocessing_service.py`

**Masalah:**

- Comment text dari YouTube langsung disimpan ke database
- Bisa mengandung XSS payload
- Frontend bisa render HTML tanpa escape

**Solusi:**

```python
from html import escape

# Di Comment model save atau service:
def clean_text(self, text: str) -> str:
    # Remove HTML tags
    text = escape(text)
    # Remove extra whitespace
    text = " ".join(text.split())
    return text
```

---

### 10. **Database Connection Not Validated**

**Lokasi:** `backend/app/core/config.py`

**Masalah:**

- `DATABASE_URL` tidak divalidasi waktu app startup
- Jika database down, error tidak clear
- No connection pooling configuration

**Solusi:**

```python
from pydantic import BaseModel, Field, validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

class Settings(BaseSettings):
    DATABASE_URL: str

    @validator('DATABASE_URL')
    def validate_db_url(cls, v):
        if not v.startswith(('postgresql://', 'mysql://', 'sqlite://')):
            raise ValueError('Invalid database URL')
        return v

# Di main.py startup
@app.on_event("startup")
async def startup_event():
    try:
        engine = create_async_engine(settings.DATABASE_URL, pool_size=10, max_overflow=20)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"Database connection failed: {str(e)}")
```

---

### 11. **CORS Configuration Terlalu Permissif**

**Lokasi:** `backend/app/main.py`

**Masalah:**

```python
allow_methods=["*"],  # ← Bahaya! Allow semua HTTP methods
allow_headers=["*"],  # ← Bahaya! Allow semua headers
```

**Solusi:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # ← Specific methods only
    allow_headers=["Content-Type", "Authorization"],  # ← Specific headers only
    max_age=600,  # Cache preflight requests
)
```

---

### 12. **No Logging & Monitoring**

**Masalah:**

- Tidak ada audit log untuk user actions
- Error tidak di-track untuk debugging
- No rate limiting implementation

**Solusi:**

```python
import logging
from pythonjsonlogger import jsonlogger

# Setup JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(logHandler)

# Di setiap endpoint:
logger.info("Analysis request", extra={
    "user_id": user_id,
    "video_id": video_id,
    "timestamp": datetime.utcnow().isoformat()
})
```

---

## 🟢 MINOR ISSUES

### 13. **Frontend Issues**

**Lokasi:** `frontend/src/api/axios.ts`

- Tidak ada request/response interceptor untuk token
- No timeout configuration
- Error handling tidak konsisten

**Solusi:**

```typescript
import axios from "axios";

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem("accessToken");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
```

---

### 14. **Password Requirements**

**Masalah:**

- No password strength validation
- Tidak ada password history
- User bisa set password yang sangat weak

---

### 15. **Missing Environment Variables Documentation**

**Lokasi:** `.env` file tidak ada dokumentasi

**Solusi:**
Buat `.env.example`:

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/sentiment_db
YOUTUBE_API_KEY=your_youtube_api_key_here
MODEL_PATH=./model
SECRET_KEY=your-secret-key-min-32-characters
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
SENTIMENT_SWAP_POS_NEG=false
```

---

## 📋 CHECKLIST PERBAIKAN

### Priority 1 (Critical) - Lakukan ASAP:

- [ ] Tambah validation di Pydantic schemas (issue #1)
- [ ] Fix YouTube URL validation (issue #4)
- [ ] Add request size limits (issue #5)
- [ ] Fix CORS configuration (issue #11)
- [ ] Remove duplicate classes di schemas (issue #2)

### Priority 2 (High) - Lakukan minggu ini:

- [ ] Add exception handling di Google auth (issue #2)
- [ ] Add rate limiting (issue #3)
- [ ] Add timeout handling YouTube API (issue #5)
- [ ] Improve error handling di comment service (issue #7)
- [ ] Add user authorization checks (issue #8)

### Priority 3 (Medium) - Lakukan bulan ini:

- [ ] Add input sanitization (issue #9)
- [ ] Add database connection validation (issue #10)
- [ ] Fix frontend axios interceptors (issue #13)
- [ ] Add logging & monitoring (issue #12)

---

## 🧪 TESTING RECOMMENDATIONS

```python
# Test cases yang harus ditambahkan:

# 1. Invalid email format
def test_register_invalid_email():
    assert raises RegisterRequest(email="invalid", password="test1234")

# 2. Weak password
def test_register_weak_password():
    assert raises RegisterRequest(email="user@example.com", password="123")

# 3. Malicious YouTube URL
def test_analysis_malicious_url():
    assert raises AnalysisRequest(youtube_url="http://malicious.com/v=abc")

# 4. Large request body
def test_large_request_body():
    # Send 10MB request, should get 413

# 5. Token expiration
def test_expired_token():
    # Decode token that expired
    assert raises 401 error
```

---

**Last Updated:** Januari 16, 2026  
**Status:** Needs Review & Implementation
