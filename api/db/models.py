from sqlalchemy import (
    Integer,
    Text,
    String,
    ForeignKey,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    # Mapped[int] подразумевает NOT NULL, primary_key настраиваем в mapped_column
    user_id: Mapped[int] = mapped_column(primary_key=True)

    # Mapped[Optional[str]] = mapped_column(Text) -> это эквивалент Column(Text, nullable=True)
    name: Mapped[Optional[str]] = mapped_column(Text)

    # Mapped[str] без Optional -> это эквивалент Column(..., nullable=False)
    uuid: Mapped[str] = mapped_column(String)

    hashed_password: Mapped[Optional[str]] = mapped_column(Text)

    # Relations
    # lazy="select" является значением по умолчанию, его можно не писать явно,
    # но я оставил комментарии для ясности.

    # Примечание: Класс "Book" должен быть определен (или импортирован),
    # чтобы связь работала, либо используйте строковое имя "Book" во всех местах.
    books: Mapped[List["Book"]] = relationship(back_populates="user")

    phrases: Mapped[List["Phrase"]] = relationship(back_populates="user")

    syllables: Mapped[List["Syllable"]] = relationship(back_populates="user")

    def __repr__(self):
        return f"<User(id={self.user_id}, name='{self.name}')>"


class Phrase(Base):
    __tablename__ = "phrases"

    id_phrase: Mapped[int] = mapped_column(primary_key=True)
    phrase: Mapped[Optional[str]] = mapped_column(Text)
    translation: Mapped[Optional[str]] = mapped_column(Text)
    show_count: Mapped[Optional[int]] = mapped_column(Integer)
    ready: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id"))
    last_view: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    dt: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    user: Mapped["User"] = relationship(
        back_populates="phrases", lazy="selectin"
    )

    def __repr__(self):
        return f"<Phrase(id={self.id_phrase}, phrase='{self.phrase}' translation='{self.translation}')>"


class Syllable(Base):
    __tablename__ = "syllables"

    # В оригинале: nullable=False, unique=True
    word: Mapped[str] = mapped_column(Text, unique=True)
    transcription: Mapped[Optional[str]] = mapped_column(Text)
    translations: Mapped[Optional[str]] = mapped_column(Text)
    examples: Mapped[Optional[str]] = mapped_column(Text)
    show_count: Mapped[Optional[int]] = mapped_column(Integer)
    ready: Mapped[Optional[int]] = mapped_column(Integer)
    last_view: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    syllable_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL")
    )

    user: Mapped["User"] = relationship(back_populates="syllables")
    paragraphs: Mapped[List["SyllableParagraph"]] = relationship(
        back_populates="syllable",
        order_by="SyllableParagraph.sequence",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Syllable(id={self.syllable_id}, word='{self.word}')>"


class SyllableParagraph(Base):
    __tablename__ = "syllables_paragraphs"

    rowid: Mapped[int] = mapped_column(primary_key=True)

    syllable_id: Mapped[int] = mapped_column(
        ForeignKey("syllables.syllable_id", ondelete="CASCADE")
    )

    example: Mapped[Optional[str]] = mapped_column(Text)
    translate: Mapped[Optional[str]] = mapped_column(Text)
    sequence: Mapped[Optional[int]] = mapped_column(Integer)

    syllable: Mapped["Syllable"] = relationship(back_populates="paragraphs")

    def __repr__(self):
        return f"<SyllableParagraph(id={self.paragraph_id}, syllable_id={self.syllable_id}, sequence={self.sequence})>"


class Book(Base):
    __tablename__ = "books"

    id_book: Mapped[int] = mapped_column(primary_key=True)
    book_name: Mapped[str] = mapped_column(Text, nullable=False)
    current_paragraph: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False
    )
    dt: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    user: Mapped["User"] = relationship(back_populates="books")
    sentences: Mapped[List["Sentence"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )


class Sentence(Base):
    __tablename__ = "sentences"

    id_sentence: Mapped[int] = mapped_column(primary_key=True)
    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    id_book: Mapped[int] = mapped_column(
        ForeignKey("books.id_book"), nullable=False
    )
    id_paragraph: Mapped[int] = mapped_column(Integer, nullable=False)

    book: Mapped["Book"] = relationship(back_populates="sentences")


class ReadingJournal(Base):
    __tablename__ = "reading_journal"

    row_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False
    )
    id_book: Mapped[int] = mapped_column(
        ForeignKey("books.id_book"), nullable=False
    )
    id_paragraph: Mapped[int] = mapped_column(Integer, nullable=False)
    dt: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
