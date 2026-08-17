from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Visitor

ACTIVE_WINDOW = timedelta(seconds=60)


def _live_cutoff() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None) - ACTIVE_WINDOW


def get_live_count(db: Session) -> int:
    """Return how many distinct visitors have sent a heartbeat in the last 60 seconds."""
    return db.execute(
        select(func.count()).select_from(Visitor).where(Visitor.last_seen >= _live_cutoff())
    ).scalar_one()


def record_heartbeat(db: Session, visitor_id: str) -> int:
    """Mark visitor_id as active now and return the current "listening now" count."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    visitor = db.get(Visitor, visitor_id)
    if visitor is None:
        db.add(Visitor(id=visitor_id, first_seen=now, last_seen=now))
    else:
        visitor.last_seen = now
    db.commit()

    return get_live_count(db)
