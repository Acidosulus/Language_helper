from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Phrase(BaseModel):
    id_phrase: int
    phrase: str
    translation: Optional[str]
    show_count: Optional[int]
    ready: int
    user_id: int
    last_view: Optional[datetime]
    dt: Optional[datetime]

    class Config:
        orm_mode = True
