from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator


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


class SentenceDTO(BaseModel):
    id_sentence: Optional[int] = Field(default=None, alias="id_sentence")
    sentence: str
    id_book: int
    id_paragraph: int

    class Config:
        from_attributes = True
        populate_by_name = True


class BookDTO(BaseModel):
    id_book: Optional[int] = Field(default=None, alias="id_book")
    book_name: str
    current_paragraph: Optional[int] = None
    user_id: int
    dt: Optional[datetime] = None

    # Вложенный список DTO для связи relationship
    sentences: list[SentenceDTO] = Field(default_factory=list)

    class Config:
        from_attributes = True
        populate_by_name = True


class BookWithStatsDTO(BaseModel):
    id_book: int
    book_name: str
    dt: Optional[datetime] = None
    current_paragraph: Optional[int] = None
    user_id: int

    # Поля из label(...)
    Min_Paragraph_Number: Optional[int] = None
    Max_Paragraph_Number: Optional[int] = None

    # Вычисляемое поле, включаемое в сериализацию как обычное поле
    read_percentage: float = 0

    @model_validator(mode="after")
    def _validate(self) -> "BookWithStatsDTO":
        if (
            self.Min_Paragraph_Number is not None
            and self.Max_Paragraph_Number is not None
            and self.current_paragraph is not None
        ):
            self.read_percentage = (
                (self.current_paragraph - self.Min_Paragraph_Number)
                * 100
                / (self.Max_Paragraph_Number - self.Min_Paragraph_Number)
            )
        else:
            self.read_percentage = 0
        return self

    model_config = ConfigDict(from_attributes=True)


class BookPositionIn(BaseModel):
    id_book: int
    id_new_paragraph: int


class RepeatedToday(BaseModel):
    count: int | None
