from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_user
from app.models.entities import User, Restaurant
from app.schemas.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Tenant-aware login requiring restaurant_slug, email, and password.
    Normalizes credentials, resolves tenant context, and fails closed.
    """
    slug = credentials.restaurant_slug.lower().strip()
    email = credentials.email.lower().strip()

    restaurant = db.query(Restaurant).filter(Restaurant.slug == slug).first()
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid restaurant identifier, email, or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(
        User.restaurant_id == restaurant.id,
        User.email == email
    ).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid restaurant identifier, email, or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive. Please contact your manager.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = {
        "restaurant_id": str(user.restaurant_id),
        "branch_id": str(user.branch_id) if user.branch_id else None,
        "station_id": str(user.station_id) if user.station_id else None,
        "role": user.role.value,
        "full_name": user.full_name
    }

    token = create_access_token(subject=str(user.id), claims=claims)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        restaurant_id=user.restaurant_id,
        branch_id=user.branch_id,
        role=user.role,
        full_name=user.full_name,
        restaurant_name=restaurant.name
    )


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
