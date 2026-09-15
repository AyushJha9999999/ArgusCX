"""ArgusCX — Auth route stub"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/auth")

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(req: LoginRequest):
    """Demo login — returns static token."""
    return {"access_token": "demo_token_arguscx", "token_type": "bearer", "user": {"name": "Agent Smith", "role": "support_agent"}}

@router.post("/logout")
async def logout():
    return {"message": "Logged out"}
