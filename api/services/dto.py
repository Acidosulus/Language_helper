from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Phrase(BaseModel):
    id_phrase: Optional[int] = None
    phrase: str
    translation: str = ""
    show_count: int = 0
    ready: int = 0
    user_id: Optional[int] = None
    last_view: Optional[datetime] = None
    dt: Optional[datetime] = None

    class Config:
        from_attributes = True
