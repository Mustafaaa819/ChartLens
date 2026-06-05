# Payment provider: Lemon Squeezy
"""Billing routes — Lemon Squeezy subscription management."""
import hashlib
import hmac
import json
import logging
import uuid as uuid_module

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import get_settings
from models.database import get_db
from models.user import User
from routes.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["billing"])
templates = Jinja2Templates(directory="templates")

TRIAL_UPLOAD_LIMIT = 3
_LS_BASE = "https://api.lemonsqueezy.com/v1"


def _ls_headers(api_key: str) -> dict:
    """Return JSON:API headers with Bearer auth for Lemon Squeezy."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }


# ---------------------------------------------------------------------------
# GET /billing
# ---------------------------------------------------------------------------


@router.get("/")
async def billing_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Render the billing management page."""
    return templates.TemplateResponse(
        "billing.html",
        {
            "request": request,
            "user": current_user,
            "subscription_status": current_user.subscription_status,
            "is_trial": current_user.subscription_status == "trial",
            "trial_uploads_used": current_user.trial_cases_used,
            "TRIAL_UPLOAD_LIMIT": TRIAL_UPLOAD_LIMIT,
        },
    )


# ---------------------------------------------------------------------------
# POST /billing/subscribe
# ---------------------------------------------------------------------------


@router.post("/subscribe")
async def create_checkout(
    current_user: User = Depends(get_current_user),
):
    """Create a Lemon Squeezy checkout session and return the checkout URL."""
    settings = get_settings()
    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": current_user.email,
                    "custom": {"user_id": str(current_user.id)},
                }
            },
            "relationships": {
                "store": {
                    "data": {"type": "stores", "id": settings.LEMONSQUEEZY_STORE_ID}
                },
                "variant": {
                    "data": {"type": "variants", "id": settings.LEMONSQUEEZY_VARIANT_ID}
                },
            },
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_LS_BASE}/checkouts",
                headers=_ls_headers(settings.LEMONSQUEEZY_API_KEY),
                json=payload,
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
        checkout_url: str = data["data"]["attributes"]["url"]
        return JSONResponse({"checkout_url": checkout_url})
    except Exception as exc:
        logger.error("Lemon Squeezy checkout creation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create checkout — please try again",
        ) from exc


# ---------------------------------------------------------------------------
# GET /billing/success
# ---------------------------------------------------------------------------


@router.get("/success")
async def billing_success(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Render the post-payment success page."""
    return templates.TemplateResponse(
        "billing_success.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# GET /billing/cancel-page
# ---------------------------------------------------------------------------


@router.get("/cancel-page")
async def billing_cancel_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Render the cancelled-payment page."""
    return templates.TemplateResponse(
        "billing_cancel.html",
        {"request": request, "user": current_user},
    )


# ---------------------------------------------------------------------------
# POST /billing/cancel
# ---------------------------------------------------------------------------


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel the user's active Lemon Squeezy subscription."""
    if not current_user.lemon_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found",
        )

    settings = get_settings()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{_LS_BASE}/subscriptions/{current_user.lemon_subscription_id}",
                headers=_ls_headers(settings.LEMONSQUEEZY_API_KEY),
                timeout=15.0,
            )
            resp.raise_for_status()
    except Exception as exc:
        logger.error(
            "Lemon Squeezy cancellation failed for user %s: %s",
            current_user.email,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to cancel subscription — please try again",
        ) from exc

    return JSONResponse({"message": "Subscription cancelled."})


# ---------------------------------------------------------------------------
# POST /billing/webhook
# ---------------------------------------------------------------------------


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    """Receive and process Lemon Squeezy webhook events."""
    # Raw body must be read before any parsing — required for signature check
    payload = await request.body()

    settings = get_settings()
    signature = request.headers.get("X-Signature", "")
    expected = hmac.new(
        settings.LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    try:
        event = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        ) from exc

    meta: dict = event.get("meta", {})
    event_name: str = meta.get("event_name", "")
    data: dict = event.get("data", {})

    if event_name in ("subscription_created", "order_created"):
        custom_data: dict = meta.get("custom_data", {})
        user_id_str: str = custom_data.get("user_id", "")
        if not user_id_str:
            logger.warning("Webhook '%s' missing user_id in custom_data", event_name)
            return JSONResponse({"received": True})

        try:
            uid = uuid_module.UUID(user_id_str)
            user = db.query(User).filter(User.id == uid).first()
        except (ValueError, Exception) as exc:
            logger.error("DB/UUID error in webhook for user_id '%s': %s", user_id_str, exc)
            return JSONResponse({"received": True})

        if user:
            user.lemon_subscription_id = str(data.get("id", ""))
            user.subscription_status = "active"
            db.commit()
            logger.info(
                "Subscription activated for user %s (event: %s)", user.email, event_name
            )

    elif event_name == "subscription_payment_failed":
        subscription_id = str(data.get("id", ""))
        try:
            user = (
                db.query(User)
                .filter(User.lemon_subscription_id == subscription_id)
                .first()
            )
        except Exception as exc:
            logger.error(
                "DB error in webhook (payment_failed) subscription %s: %s",
                subscription_id,
                exc,
            )
            return JSONResponse({"received": True})

        if user:
            user.subscription_status = "past_due"
            db.commit()
            logger.info("Subscription past_due for user %s", user.email)

    elif event_name in ("subscription_cancelled", "subscription_expired"):
        subscription_id = str(data.get("id", ""))
        try:
            user = (
                db.query(User)
                .filter(User.lemon_subscription_id == subscription_id)
                .first()
            )
        except Exception as exc:
            logger.error(
                "DB error in webhook (cancelled) subscription %s: %s",
                subscription_id,
                exc,
            )
            return JSONResponse({"received": True})

        if user:
            user.subscription_status = "canceled"
            user.lemon_subscription_id = None
            db.commit()
            logger.info("Subscription cancelled for user %s", user.email)

    else:
        logger.debug("Unhandled Lemon Squeezy event: %s", event_name)

    return JSONResponse({"received": True})
