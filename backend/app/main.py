import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import __version__
from app.core.config import settings
from app.core.logging import setup_logging
from app.db import SessionLocal, init_db
from app.core.limits import limiter
from app.models import MarkingJob
from app.api.v1.router import api_router

log = logging.getLogger("redpen")

setup_logging()


def _recover_stuck_jobs() -> None:
    """A restart cannot resume an in-process marking run: mark it failed, honestly."""
    with SessionLocal() as db:
        db.query(MarkingJob).filter(MarkingJob.status.in_(["extracting", "marking"])).update(
            {
                MarkingJob.status: "failed",
                MarkingJob.error_message: "Marking was interrupted by a server restart. Run it again.",
            },
            synchronize_session=False,
        )
        db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    _recover_stuck_jobs()
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    lifespan=lifespan,
    docs_url=None if settings.is_prod else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_prod else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Only the origins this deployment serves may call the API; no cookies are used,
# so credentials stay off and every request carries a bearer token.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    if settings.is_prod:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    """Local studio: say what broke instead of a bare 500 the teacher can't act on."""
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {str(exc)[:300]}"},
    )


app.include_router(api_router)