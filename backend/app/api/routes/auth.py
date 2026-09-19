"""Dashboard authentication and Firebase identity exchange."""
from datetime import datetime, timedelta
from typing import Optional
import secrets

from fastapi import APIRouter, Request
from fastapi import HTTPException
from jose import jwt
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/auth")

class LoginRequest(BaseModel):
    email: str
    password: str

class FirebaseLoginRequest(BaseModel):
    id_token: str


def create_access_token(subject: str, email: str, provider: str = "password") -> str:
    expires = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": subject, "email": email, "provider": provider, "role": "admin", "exp": expires},
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY.get_secret_value(), algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        return None


@router.post("/login")
async def login(req: LoginRequest):
    configured_password = settings.ADMIN_PASSWORD.get_secret_value()
    if (
        not settings.ADMIN_EMAIL
        or not configured_password
        or not secrets.compare_digest(req.email, settings.ADMIN_EMAIL)
        or not secrets.compare_digest(req.password, configured_password)
    ):
        raise HTTPException(status_code=401, detail="Invalid dashboard credentials")
    return {
        "access_token": create_access_token("dashboard_admin", req.email),
        "token_type": "bearer",
        "user": {"name": req.email, "email": req.email, "role": "admin"},
    }


@router.post("/firebase")
async def firebase_login(req: FirebaseLoginRequest):
    """Verify a Firebase Google ID token and issue an ArgusCX dashboard JWT."""
    if not settings.FIREBASE_PROJECT_ID:
        raise HTTPException(status_code=503, detail="Firebase authentication is not configured")
    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth, credentials
        if not firebase_admin._apps:
            credential = credentials.Certificate({
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
                "private_key": (settings.FIREBASE_PRIVATE_KEY or "").replace("\\n", "\n"),
                "token_uri": "https://oauth2.googleapis.com/token",
            })
            firebase_admin.initialize_app(credential)
        decoded = firebase_auth.verify_id_token(req.id_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid Firebase identity") from exc
    email = decoded.get("email")
    if not email or not decoded.get("email_verified", False):
        raise HTTPException(status_code=403, detail="A verified Google email is required")
    return {
        "access_token": create_access_token(decoded["uid"], email, "firebase"),
        "token_type": "bearer",
        "user": {"name": decoded.get("name") or email, "email": email, "role": "admin"},
    }

@router.post("/logout")
async def logout():
    return {"message": "Logged out"}


class ProfileSetupRequest(BaseModel):
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    use_case: Optional[str] = None


@router.get("/me")
async def get_me(request: Request):
    """Return the current user's profile including onboarding status."""
    identity = getattr(request.state, "authenticated_user", None)
    if not identity:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sub = identity.get("sub")
    email = identity.get("email")

    from app.db.mongodb import get_users_col
    users_col = get_users_col()
    profile = await users_col.find_one({"sub": sub}) if users_col is not None else None

    return {
        "sub": sub,
        "email": email,
        "onboarding_complete": bool(profile and profile.get("company_name")),
        "company_name": profile.get("company_name") if profile else None,
        "industry": profile.get("industry") if profile else None,
        "company_size": profile.get("company_size") if profile else None,
        "use_case": profile.get("use_case") if profile else None,
    }


@router.post("/profile")
async def save_profile(req: ProfileSetupRequest, request: Request):
    """Save/update company profile after onboarding."""
    identity = getattr(request.state, "authenticated_user", None)
    if not identity:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sub = identity.get("sub")
    email = identity.get("email")

    from app.db.mongodb import get_users_col
    from datetime import datetime as dt
    users_col = get_users_col()
    if users_col is None:
        raise HTTPException(status_code=503, detail="Database not available")

    await users_col.update_one(
        {"sub": sub},
        {"$set": {
            "sub": sub,
            "email": email,
            "company_name": req.company_name,
            "industry": req.industry,
            "company_size": req.company_size,
            "use_case": req.use_case,
            "updated_at": dt.utcnow().isoformat(),
        }, "$setOnInsert": {"created_at": dt.utcnow().isoformat()}},
        upsert=True,
    )
    return {"message": "Profile saved", "company_name": req.company_name}
