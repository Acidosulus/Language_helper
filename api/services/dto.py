from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
        populate_by_name = True


class SyllableParagraph(BaseModel):
    paragraph_id: Optional[int] = Field(default=None, alias="paragraph_id")
    example: Optional[str] = None
    translate: Optional[str] = None
    sequence: Optional[int] = None
    syllable_id: Optional[int] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class Syllable(BaseModel):
    syllable_id: Optional[int] = Field(default=None, alias="syllable_id")
    word: str
    transcription: Optional[str] = None
    translations: Optional[str] = None
    examples: Optional[str] = None
    show_count: Optional[int] = 0
    ready: Optional[int] = 0
    last_view: Optional[datetime] = None
    user_id: Optional[int] = None
    paragraphs: list[SyllableParagraph]

    class Config:
        from_attributes = True
        populate_by_name = True
