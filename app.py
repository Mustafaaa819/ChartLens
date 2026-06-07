"""ChartLens — FastAPI application entry point."""
import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from config import get_settings
from core.limiter import limiter
from models.database import init_db

# ---------------------------------------------------------------------------
# Logging — configured before anything else runs
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("chartlens")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    from db_sync import pull_db
    logger.info("ChartLens starting up — restoring database from remote …")
    pull_db()
    logger.info("Database restore complete. Initialising tables …")
    await init_db()
    logger.info("Database ready. ChartLens is live.")
    yield
    logger.info("ChartLens shutting down. Goodbye.")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ChartLens",
    description=(
        "Upload your client's medical records. "
        "Get a court-ready damages chronology in minutes, not days."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

settings = get_settings()

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tightened to real origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files & templates
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ---------------------------------------------------------------------------
# Routers — imported lazily so missing stubs don't block startup
# ---------------------------------------------------------------------------


def _include_router(module_path: str, prefix: str, tag: str) -> None:
    """Import a router module and attach it to the app, warning if not ready."""
    try:
        import importlib

        module = importlib.import_module(module_path)
        app.include_router(module.router, prefix=prefix)
        logger.info("Router '%s' mounted at '%s'", module_path, prefix or "/")
    except ImportError as exc:
        logger.warning(
            "Router '%s' not available yet — skipping. (%s)", module_path, exc
        )


_include_router("routes.auth", "", "auth")
_include_router("routes.cases", "", "cases")
_include_router("routes.reports", "/reports", "reports")
_include_router("routes.billing", "/billing", "billing")

# ---------------------------------------------------------------------------
# Core routes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
async def health_check() -> JSONResponse:
    """Liveness probe — returns app status, env, and config flags."""
    cfg = get_settings()
    return JSONResponse(
        {
            "status": "ok",
            "env": cfg.APP_ENV,
            "database": "connected",
            "anthropic_key_set": bool(cfg.ANTHROPIC_API_KEY),
        }
    )


@app.get("/", include_in_schema=False)
async def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/register-page", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse("register_page.html", {"request": request})
