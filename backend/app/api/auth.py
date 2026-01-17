from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from google.oauth2 import id_token
from google.auth.transport import requests
from jose import jwt, JWTError, ExpiredSignatureError
import uuid
import logging

from app.db.session import get_async_db
from app.db.models.user import User
from app.db.repositories.user_repository import UserRepository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    ALGORITHM,
)
from app.core.config import settings
from app.core.rate_limiter import limiter
from app.core.sanitizer import sanitize_input
from app.schemas import RegisterRequest, LoginRequest, GoogleLoginRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])
auth_scheme = HTTPBearer(auto_error=True)


@router.post("/register")
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        existing = await UserRepository.get_by_email(db, payload.email)
        if existing:
            logger.warning(f"Registration attempt with existing email: {payload.email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Sanitize full name
        full_name = sanitize_input(payload.full_name) if payload.full_name else None

        user = User(
            email=payload.email,
            full_name=full_name,
            password_hash=hash_password(payload.password),
            provider="local",
        )

        await UserRepository.create(db, user)
        logger.info(f"User registered successfully: {payload.email}")
        return {"message": "User registered successfully"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        user = await UserRepository.get_by_email(db, payload.email)

        if not user or not user.password_hash:
            logger.warning(f"Failed login attempt for: {payload.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(payload.password, user.password_hash):
            logger.warning(f"Failed login attempt for: {payload.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "provider": user.provider,
        })

        logger.info(f"User logged in successfully: {payload.email}")
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/google")
@limiter.limit("10/minute")
async def login_google(
    request: Request,
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        # Verify Google token with timeout and proper error handling
        google_user = id_token.verify_oauth2_token(
            payload.token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        logger.warning(f"Invalid Google token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        logger.error(f"Google OAuth verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication service temporarily unavailable")

    try:
        email = google_user.get("email")
        if not email:
            logger.warning("Google token missing email field")
            raise HTTPException(status_code=400, detail="Email not found in Google token")

        provider_id = google_user.get("sub")
        if not provider_id:
            logger.warning("Google token missing sub field")
            raise HTTPException(status_code=400, detail="Provider ID not found in Google token")

        user = await UserRepository.get_by_email(db, email)

        if not user:
            # Sanitize Google user data
            full_name = sanitize_input(google_user.get("name", "")) if google_user.get("name") else None
            
            user = User(
                email=email,
                full_name=full_name,
                avatar_url=google_user.get("picture"),
                provider="google",
                provider_id=provider_id,
            )
            user = await UserRepository.create(db, user)
            logger.info(f"New Google user created: {email}")
        else:
            logger.info(f"Google user logged in: {email}")

        jwt_token = create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "provider": "google",
        })

        return {"access_token": jwt_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error during Google login: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Unexpected error during Google login: {str(e)}")
        raise HTTPException(status_code=500, detail="Google login failed")



@router.get("/me")
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: AsyncSession = Depends(get_async_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # convert sub to UUID
        try:
            user_id = uuid.UUID(sub)
        except ValueError:
            logger.warning(f"Invalid token subject format: {sub}")
            raise HTTPException(status_code=401, detail="Invalid token subject")

        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            logger.warning(f"User not found for token: {user_id}")
            raise HTTPException(status_code=401, detail="User not found")

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "provider": user.provider,
            "avatar_url": user.avatar_url,
        }
    except ExpiredSignatureError:
        logger.warning("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        raise HTTPException(status_code=401, detail="Token validation failed")


@router.post("/logout")
async def logout():
    # JWT is stateless; just remove token on client side
    return {"message": "Logged out successfully"}



