import uuid
import logging
from typing import List, Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import (
    UnauthorizedException,
    ForbiddenException,
    ResourceNotFoundException
)
from app.models.entities import User, Branch, RoleEnum

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authentication token is missing")
    
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception:
        raise UnauthorizedException("Invalid or expired authentication token")
    
    user_id = payload.get("sub")
    restaurant_id = payload.get("restaurant_id")
    
    if not user_id or not restaurant_id:
        raise UnauthorizedException("Token missing subject or tenant scope")
    
    try:
        user_uuid = uuid.UUID(user_id)
        tenant_uuid = uuid.UUID(restaurant_id)
    except ValueError:
        raise UnauthorizedException("Invalid user or tenant identifier format")
    
    user = db.query(User).filter(
        User.id == user_uuid,
        User.restaurant_id == tenant_uuid,
        User.is_active == True
    ).first()
    
    if not user:
        raise UnauthorizedException("User not found or deactivated")
    
    return user


def require_role(allowed_roles: List[RoleEnum]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                "Role authorization failed: user_id=%s, role=%s, required=%s",
                current_user.id, current_user.role.value, [r.value for r in allowed_roles]
            )
            raise ForbiddenException(
                f"Role '{current_user.role.value}' is not permitted to perform this action. Required: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker


def require_manager(current_user: User = Depends(get_current_user)) -> User:
    return require_role([RoleEnum.MANAGER])(current_user)


def require_waiter_or_manager(current_user: User = Depends(get_current_user)) -> User:
    return require_role([RoleEnum.MANAGER, RoleEnum.WAITER])(current_user)


def require_kitchen_or_manager(current_user: User = Depends(get_current_user)) -> User:
    return require_role([RoleEnum.MANAGER, RoleEnum.KITCHEN])(current_user)


def verify_branch_scope(user: User, branch_id: uuid.UUID, db: Optional[Session] = None) -> None:
    """
    Ensure staff can only access resources in their assigned branch.
    Managers can access any branch belonging to their tenant, but cannot access other tenants' branches.
    Fails closed if a non-manager has no branch assigned.
    """
    if user.role != RoleEnum.MANAGER:
        if not user.branch_id:
            logger.warning("Branch check failed: user_id=%s has no branch assignment", user.id)
            raise ForbiddenException("User has no branch assignment.")
        if user.branch_id != branch_id:
            logger.warning(
                "Branch authorization failed: user_id=%s, assigned_branch=%s, requested_branch=%s",
                user.id, user.branch_id, branch_id
            )
            raise ForbiddenException("Access denied: You are not authorized for this branch.")
    elif db is not None:
        # Validate that the requested branch actually belongs to this manager's tenant
        branch = db.query(Branch).filter(
            Branch.id == branch_id,
            Branch.restaurant_id == user.restaurant_id,
            Branch.is_active == True
        ).first()
        if not branch:
            logger.warning(
                "Cross-tenant or nonexistent branch access blocked: user_id=%s, tenant_id=%s, requested_branch=%s",
                user.id, user.restaurant_id, branch_id
            )
            raise ResourceNotFoundException("Branch")


def verify_kitchen_station_scope(user: User, branch_id: uuid.UUID, station_id: uuid.UUID) -> None:
    """
    Ensure kitchen staff can only update items in their assigned branch AND assigned station.
    Managers can access any station within their authorized branches.
    Waiters are strictly forbidden.
    Missing station assignment fails closed.
    """
    if user.role == RoleEnum.WAITER:
        logger.warning("Waiter attempted kitchen mutation: user_id=%s, station_id=%s", user.id, station_id)
        raise ForbiddenException("Waiters are not permitted to update kitchen item statuses.")
    
    if user.role == RoleEnum.KITCHEN:
        if not user.branch_id or user.branch_id != branch_id:
            logger.warning(
                "Kitchen staff attempted cross-branch item update: user_id=%s, user_branch=%s, item_branch=%s",
                user.id, user.branch_id, branch_id
            )
            raise ResourceNotFoundException("OrderItem")
        if not user.station_id:
            logger.warning("Kitchen staff has no station assignment: user_id=%s", user.id)
            raise ForbiddenException("Kitchen staff has no station assignment.")
        if user.station_id != station_id:
            logger.warning(
                "Kitchen staff station mismatch: user_id=%s, user_station=%s, item_station=%s",
                user.id, user.station_id, station_id
            )
            raise ForbiddenException("You are not authorized to update items for this kitchen station.")

