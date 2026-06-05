"""Shared rate limiter instance — import from here to avoid circular imports."""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_user_id_for_limit(request: Request) -> str:
    """Extract user ID from JWT cookie for rate limiting. Falls back to IP."""
    try:
        from routes.auth import COOKIE_NAME, _decode_token

        token = request.cookies.get(COOKIE_NAME)
        if token:
            payload = _decode_token(token)
            if payload and "sub" in payload:
                return str(payload["sub"])
    except Exception:
        pass
    return get_remote_address(request)


limiter = Limiter(key_func=_get_user_id_for_limit)
