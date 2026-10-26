from typing import Dict, Any, List, Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.entities import User
from app.core.security import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role_name: str
    department: Optional[str] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_name = user.role.role_name if user.role else "Procurement Manager"
    token_payload = {
        "sub": user.user_id,
        "email": user.email,
        "name": user.full_name,
        "role": role_name,
    }
    access_token = create_access_token(token_payload)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserProfileResponse(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            role_name=role_name,
            department=user.department,
        )
    )


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    role_name = current_user.role.role_name if current_user.role else "Procurement Manager"
    return UserProfileResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        role_name=role_name,
        department=current_user.department,
    )


@router.get("/users", response_model=List[UserProfileResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    res = []
    for u in users:
        role_name = u.role.role_name if u.role else "Procurement Manager"
        res.append(
            UserProfileResponse(
                user_id=u.user_id,
                email=u.email,
                full_name=u.full_name,
                role_name=role_name,
                department=u.department,
            )
        )
    return res
