from pydantic import BaseModel, Field


class PresenceCount(BaseModel):
    count: int = Field(..., ge=0, description="Distinct visitors with a heartbeat in the last 60 seconds.")
