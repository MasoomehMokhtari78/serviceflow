from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.entities import User, MenuCategory, MenuItem
from app.schemas.schemas import MenuCategoryOut, MenuItemOut

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.get("/categories", response_model=List[MenuCategoryOut])
def list_menu_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve menu categories and their items for the tenant."""
    categories = db.query(MenuCategory).options(
        joinedload(MenuCategory.items)
    ).filter(
        MenuCategory.restaurant_id == current_user.restaurant_id,
        MenuCategory.is_active == True
    ).order_by(MenuCategory.display_order.asc()).all()

    return categories


@router.get("/items", response_model=List[MenuItemOut])
def list_menu_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available menu items for the tenant."""
    items = db.query(MenuItem).filter(
        MenuItem.restaurant_id == current_user.restaurant_id,
        MenuItem.is_available == True
    ).order_by(MenuItem.name_fa.asc()).all()

    return items
