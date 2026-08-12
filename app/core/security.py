import secrets

from fastapi import HTTPException, Request, status

from app.core.config import settings

SESSION_ADMIN_KEY = "is_admin"


def verify_admin_credentials(username: str, password: str) -> bool:
    """Constant-time comparison of submitted credentials against configured admin credentials."""
    username_ok = secrets.compare_digest(username, settings.ADMIN_USERNAME)
    password_ok = secrets.compare_digest(password, settings.ADMIN_PASSWORD)
    return username_ok and password_ok


def login_admin(request: Request) -> None:
    request.session[SESSION_ADMIN_KEY] = True


def logout_admin(request: Request) -> None:
    request.session.clear()


def is_admin_logged_in(request: Request) -> bool:
    return bool(request.session.get(SESSION_ADMIN_KEY))


def require_admin(request: Request) -> None:
    """Dependency that protects admin routes, redirecting anonymous users to the login page."""
    if not is_admin_logged_in(request):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"},
        )
