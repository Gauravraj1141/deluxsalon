import secrets

from fastapi import Request, Response

from app.core.config import settings

VISITOR_COOKIE_NAME = "vid"
VISITOR_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year


def get_or_create_visitor_id(request: Request, response: Response) -> str:
    """Return the anonymous visitor id from a first-party cookie, creating one if absent.

    This is not an auth/session token - it carries no identity, just a random value
    used to de-duplicate heartbeats so "listening now" counts distinct clients.
    """
    visitor_id = request.cookies.get(VISITOR_COOKIE_NAME)
    if not visitor_id:
        visitor_id = secrets.token_urlsafe(24)
        response.set_cookie(
            VISITOR_COOKIE_NAME,
            visitor_id,
            max_age=VISITOR_COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=settings.is_production,
        )
    return visitor_id
