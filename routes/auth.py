"""Auth routes — page rendering, register, login, logout, and current-user info."""
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import get_settings
from models.database import get_db
from models.user import User, UserOut

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
COOKIE_NAME = "access_token"


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _create_access_token(email: str) -> str:
    """Return a signed JWT containing the user's email and a 24-hour expiry."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload: dict = {"sub": email, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> str | None:
    """Decode a JWT and return the subject (email), or None if invalid/expired."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        logger.debug("Token decoded successfully, sub=%s", sub)
        return sub
    except JWTError as e:
        logger.warning("JWT decode failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def _hash_password(plain: str) -> str:
    """Return a bcrypt hash of the plain-text password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _is_valid_email(email: str) -> bool:
    """Basic email check — must have a local part, @, and a dotted domain."""
    at = email.find("@")
    if at < 1:
        return False
    domain = email[at + 1:]
    return "." in domain and len(domain) > 2


def _attach_auth_cookie(response: RedirectResponse, token: str) -> None:
    """Attach the HttpOnly access_token cookie to a redirect response."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        path="/",
    )


# ---------------------------------------------------------------------------
# Auth dependency — used by all protected routes
# ---------------------------------------------------------------------------


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Read the JWT from the HttpOnly cookie and return the authenticated User.

    Raises HTTP 401 if the cookie is absent, the token is invalid/expired,
    or the user row no longer exists.
    """
    token: str | None = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    email = _decode_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    try:
        user = db.query(User).filter(User.email == email).first()
    except Exception as exc:
        logger.error("DB error fetching user '%s': %s", email, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
        )

    return user


# ---------------------------------------------------------------------------
# GET /login  — login page
# ---------------------------------------------------------------------------


@router.get("/login")
async def login_page(request: Request):
    """Render the sign-in page."""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "current_user": None},
    )


# ---------------------------------------------------------------------------
# GET /register  — registration page
# ---------------------------------------------------------------------------


@router.get("/register")
async def register_page(request: Request):
    """Render the account registration page."""
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "current_user": None},
    )


# ---------------------------------------------------------------------------
# POST /auth/register  — create account
# ---------------------------------------------------------------------------


@router.post("/auth/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    firm_name: str = Form(...),
    db: Session = Depends(get_db),
):
    """Create a new lawyer account and set the auth cookie.

    Validation errors re-render the registration page with an inline error
    message instead of raising HTTPException, so the user stays on the form.
    """
    email = email.strip().lower()
    firm_name = firm_name.strip()

    def _reg_err(msg: str):
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "current_user": None, "error": msg},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not _is_valid_email(email):
        return _reg_err("Invalid email address")
    if len(password) < 8:
        return _reg_err("Password must be at least 8 characters")
    if password != confirm_password:
        return _reg_err("Passwords do not match")
    if not firm_name:
        return _reg_err("Firm name is required")

    new_user = User(
        email=email,
        password_hash=_hash_password(password),
        firm_name=firm_name,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        return _reg_err("An account with that email already exists")
    except Exception as exc:
        db.rollback()
        logger.error("DB error registering user '%s': %s", email, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create account — please try again",
        ) from exc

    logger.info("New user registered: %s | firm: %s", email, firm_name)
    token = _create_access_token(email)
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    _attach_auth_cookie(response, token)
    return response


# ---------------------------------------------------------------------------
# POST /auth/login  — authenticate
# ---------------------------------------------------------------------------


@router.post("/auth/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Authenticate an existing user and set the auth cookie.

    Returns the same error message for wrong email or wrong password to
    prevent user-enumeration attacks. Bad credentials re-render the login
    page with an inline error instead of raising HTTPException.
    """
    email = email.strip().lower()

    try:
        user = db.query(User).filter(User.email == email).first()
    except Exception as exc:
        logger.error("DB error during login for '%s': %s", email, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from exc

    if user is None or not _verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "current_user": None, "error": "Invalid email or password"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    logger.info("User logged in: %s", email)
    token = _create_access_token(email)
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    _attach_auth_cookie(response, token)
    return response


# ---------------------------------------------------------------------------
# POST /auth/logout  — clear session
# ---------------------------------------------------------------------------


@router.post("/auth/logout")
async def logout() -> RedirectResponse:
    """Clear the auth cookie and redirect to the login page."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key=COOKIE_NAME, httponly=True, samesite="lax")
    return response


# ---------------------------------------------------------------------------
# GET /auth/me  — current user JSON
# ---------------------------------------------------------------------------


@router.get("/auth/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    """Return the authenticated user's profile as JSON."""
    return UserOut.model_validate(current_user)
