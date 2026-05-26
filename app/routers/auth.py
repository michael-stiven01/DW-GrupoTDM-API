from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.schemas.auth import LoginRequest, Token, UserResponse
from app.auth.dependencies import USERS_DB, require_active_user
from app.auth.jwt_handler import verify_password, create_access_token
from app.config import settings
from app.middleware.rate_limit import limiter

router = APIRouter(tags=["Auth"])

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    user = USERS_DB.get(login_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario está inactivo",
        )
        
    # Crear token JWT
    token_payload = {"sub": user["username"], "role": user["role"]}
    access_token = create_access_token(token_payload)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60
    )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(require_active_user)):
    return UserResponse(
        username=current_user["username"],
        role=current_user["role"],
        is_active=current_user["is_active"]
    )

@router.get("/verify")
async def verify_token_endpoint(current_user: dict = Depends(require_active_user)):
    return {
        "valid": True,
        "username": current_user["username"]
    }
