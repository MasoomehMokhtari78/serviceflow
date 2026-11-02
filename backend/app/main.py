import time
import json
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.api.router import api_router

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("serviceflow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce production security check on startup
    settings.validate_production_security()
    logger.info("ServiceFlow initialized successfully in '%s' environment.", settings.ENVIRONMENT)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-Branch Café Operations & Service Intelligence Platform for the Iranian Market",
    lifespan=lifespan
)

# CORS Middleware (Explicit origins only; no wildcard in credentials mode)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    request.state.request_id = request_id

    # Safely extract tenant_id and branch_id from JWT without throwing or logging token
    tenant_id = None
    branch_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        try:
            payload = decode_access_token(token)
            tenant_id = payload.get("restaurant_id")
            branch_id = payload.get("branch_id")
        except Exception:
            pass

    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    log_record = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
        "tenant_id": tenant_id,
        "branch_id": branch_id
    }
    logger.info("request_completed: %s", json.dumps(log_record))

    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "detail": exc.detail,
            "extra": exc.extra
        }
    )


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# Mount API V1 routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

