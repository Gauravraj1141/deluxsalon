from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.core.visitor import get_or_create_visitor_id
from app.db.database import get_db
from app.schemas.presence import PresenceCount
from app.services.presence import record_heartbeat

router = APIRouter(prefix="/api/v1/presence", tags=["presence"])


@router.post(
    "/heartbeat",
    response_model=PresenceCount,
    summary="Record a listener heartbeat",
    description=(
        "Called periodically by the player while a listener has the site open. Assigns an "
        "anonymous, non-identifying visitor cookie on first call, then returns how many "
        "distinct visitors have sent a heartbeat in the last 60 seconds."
    ),
)
@limiter.limit("10/minute")
def heartbeat(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> PresenceCount:
    visitor_id = get_or_create_visitor_id(request, response)
    count = record_heartbeat(db, visitor_id)
    return PresenceCount(count=count)
