from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    ForeignKey,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ---------------- USERS ---------------- #


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    name = Column(Text)
    uuid = Column(String, nullable=False)
    hashed_password = Column(Text)

    # relations
    books = relationship("Book", back_populates="user", lazy="select")
    phrases = relationship("Phrase", back_populates="user", lazy="select")
    syllables = relationship("Syllable", back_populates="user", lazy="select")

    def __repr__(self):
        return f"<User(id={self.user_id}, name='{self.name}')>"


class Book(Base):
    __tablename__ = "books"

    id_book = Column(Integer, primary_key=True)
    book_name = Column(Text, nullable=False)
    current_paragraph = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    dt = Column(TIMESTAMP)

    user = relationship("User", back_populates="books", lazy="selectin")
    sentences = relationship("Sentence", back_populates="book", lazy="selectin")

    def __repr__(self):
        return f"<Book(id={self.id_book}, book_name='{self.book_name}', current_paragraph={self.current_paragraph}, user_id={self.user_id})>"


class Sentence(Base):
    __tablename__ = "sentences"

    sentence = Column(Text, nullable=False)
    id_book = Column(Integer, ForeignKey("books.id_book"))
    id_paragraph = Column(Integer, nullable=False)
    id_sentence = Column(Integer, primary_key=True)

    book = relationship("Book", back_populates="sentences", lazy="selectin")


class Phrase(Base):
    __tablename__ = "phrases"

    id_phrase = Column(Integer, primary_key=True)
    phrase = Column(Text)
    translation = Column(Text)
    show_count = Column(Integer)
    ready = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    last_view = Column(TIMESTAMP)
    dt = Column(TIMESTAMP)

    user = relationship("User", back_populates="phrases", lazy="selectin")

    def __repr__(self):
        return f"<Phrase(id={self.id_phrase}, phrase='{self.phrase}' translation='{self.translation}')>"


class Syllable(Base):
    __tablename__ = "syllables"

    word = Column(Text, nullable=False, unique=True)
    transcription = Column(Text)
    translations = Column(Text)
    examples = Column(Text)
    show_count = Column(Integer)
    ready = Column(Integer)
    last_view = Column(TIMESTAMP)
    syllable_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"))

    user = relationship("User", back_populates="syllables")

    paragraphs = relationship(
        "SyllableParagraph",
        back_populates="syllable",
        order_by="SyllableParagraph.sequence",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Syllable(id={self.syllable_id}, word='{self.word}')>"


class SyllableParagraph(Base):
    __tablename__ = "syllables_paragraphs"

    syllable_id = Column(
        Integer,
        ForeignKey("syllables.syllable_id", ondelete="CASCADE"),
        nullable=False,
    )
    example = Column(Text)
    translate = Column(Text, name="translate")
    sequence = Column(Integer, name="sequence")
    paragraph_id = Column(Integer, primary_key=True, autoincrement=True)

    syllable = relationship("Syllable", back_populates="paragraphs")

    def __repr__(self):
        return f"<SyllableParagraph(id={self.paragraph_id}, syllable_id={self.syllable_id}, sequence={self.sequence})>"
