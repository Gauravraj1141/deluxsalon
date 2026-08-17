from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Visitor

ACTIVE_WINDOW = timedelta(seconds=60)


def record_heartbeat(db: Session, visitor_id: str) -> int:
    """Mark visitor_id as active now and return the current "listening now" count."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    visitor = db.get(Visitor, visitor_id)
    if visitor is None:
        db.add(Visitor(id=visitor_id, first_seen=now, last_seen=now))
    else:
        visitor.last_seen = now
    db.commit()

    cutoff = now - ACTIVE_WINDOW
    return db.execute(
        select(func.count()).select_from(Visitor).where(Visitor.last_seen >= cutoff)
    ).scalar_one()
