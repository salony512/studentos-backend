from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.user import User
from app.services.auth_service import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ── Schemas ────────────────────────────────────────────────────────────────
from typing import Optional

class RegisterRequest(BaseModel):
    name:        str
    email:       EmailStr
    password:    str
    college:     Optional[str] = None
    branch:      Optional[str] = None
    year:        Optional[int] = None
    target_role: Optional[str] = "Developer"

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"

class UserOut(BaseModel):
    id:           int
    name:         str
    email:        str
    college:      Optional[str]
    branch:       Optional[str]
    year:         Optional[int]
    target_role:  Optional[str]
    current_cgpa: Optional[float]
    target_cgpa:  Optional[float]

    class Config:
        from_attributes = True

# ── Routes ─────────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check duplicate
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name        = body.name,
        email       = body.email,
        hashed_pw   = hash_password(body.password),
        college     = body.college,
        branch      = body.branch,
        year        = body.year,
        target_role = body.target_role,
    )
    db.add(user)
    await db.flush()  # get user.id

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me")
async def update_profile(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    allowed = {"name", "college", "branch", "year", "target_role", "current_cgpa", "target_cgpa"}
    for k, v in body.items():
        if k in allowed:
            setattr(current_user, k, v)
    db.add(current_user)
    return {"message": "Profile updated"}
