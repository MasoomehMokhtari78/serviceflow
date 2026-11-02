from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "ERROR",
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra or {}


class ConflictException(AppException):
    def __init__(
        self,
        detail: str = "Resource was modified by another operation. Please refresh.",
        current_version: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        extra_data = extra or {}
        if current_version is not None:
            extra_data["current_version"] = current_version
        self.current_version = current_version
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="VERSION_CONFLICT",
            extra=extra_data
        )



class ResourceNotFoundException(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found",
            error_code="NOT_FOUND"
        )


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Operation not permitted"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )


# Support modern Starlette status code without deprecation warning
HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class InvalidStateTransitionException(AppException):
    def __init__(self, detail: str, current_status: str, target_status: str):
        super().__init__(
            status_code=HTTP_422,
            detail=detail,
            error_code="INVALID_STATE_TRANSITION",
            extra={"current_status": current_status, "target_status": target_status}
        )


class UnreadyItemsException(AppException):
    def __init__(self, detail: str, unready_items: list):
        super().__init__(
            status_code=HTTP_422,
            detail=detail,
            error_code="UNREADY_ITEMS_REMAINING",
            extra={"unready_items": unready_items}
        )
