from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
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

    hp_pages = relationship("HpPage", back_populates="user", lazy="select")
    hp_rows = relationship("HpRow", back_populates="user", lazy="select")
    hp_tiles = relationship("HpTile", back_populates="user", lazy="select")


# ---------------- BOOKS ---------------- #


class Book(Base):
    __tablename__ = "books"

    id_book = Column(Integer, primary_key=True)
    book_name = Column(Text, nullable=False)
    current_paragraph = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    dt = Column(TIMESTAMP)

    user = relationship("User", back_populates="books", lazy="selectin")
    sentences = relationship("Sentence", back_populates="book", lazy="selectin")


class Sentence(Base):
    __tablename__ = "sentences"

    sentence = Column(Text, nullable=False)
    id_book = Column(Integer, ForeignKey("books.id_book"))
    id_paragraph = Column(Integer, nullable=False)
    id_sentence = Column(Integer, primary_key=True)

    book = relationship("Book", back_populates="sentences", lazy="selectin")


# ---------------- PHRASES ---------------- #


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


# ---------------- SYLLABLES ---------------- #


class Syllable(Base):
    __tablename__ = "syllables"

    word = Column(Text, nullable=False)
    transcription = Column(Text)
    translations = Column(Text)
    examples = Column(Text)
    show_count = Column(Integer)
    ready = Column(Integer)
    last_view = Column(TIMESTAMP)
    syllable_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))

    user = relationship("User", back_populates="syllables", lazy="selectin")


# ---------------- HOMEPAGE STRUCTURE ---------------- #


class HpPage(Base):
    __tablename__ = "hp_pages"

    page_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    page_name = Column(Text, nullable=False)
    index = Column(BigInteger, default=0)
    default = Column(Integer)

    user = relationship("User", back_populates="hp_pages", lazy="selectin")
    rows = relationship("HpPageRow", back_populates="page", lazy="selectin")


class HpRow(Base):
    __tablename__ = "hp_rows"

    row_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    row_name = Column(Text, nullable=False)
    row_type = Column(BigInteger, default=0)
    row_index = Column(BigInteger, default=0)

    user = relationship("User", back_populates="hp_rows", lazy="selectin")
    tiles = relationship("HpRowTile", back_populates="row", lazy="selectin")


class HpTile(Base):
    __tablename__ = "hp_tiles"

    tile_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    name = Column(Text, nullable=False)
    hyperlink = Column(Text)
    onclick = Column(Text)
    icon = Column(Text, nullable=False)
    color = Column(Text, nullable=False)

    user = relationship("User", back_populates="hp_tiles", lazy="selectin")


class HpPageRow(Base):
    __tablename__ = "hp_page_rows"

    id = Column(BigInteger, primary_key=True)
    page_id = Column(BigInteger, ForeignKey("hp_pages.page_id"))
    row_id = Column(BigInteger, ForeignKey("hp_rows.row_id"))
    row_index = Column(BigInteger, default=0)
    user_id = Column(Integer, nullable=False)

    page = relationship("HpPage", back_populates="rows", lazy="selectin")
    row = relationship("HpRow", lazy="selectin")


class HpRowTile(Base):
    __tablename__ = "hp_row_tiles"

    id = Column(BigInteger, primary_key=True)
    row_id = Column(BigInteger, ForeignKey("hp_rows.row_id"))
    tile_id = Column(BigInteger)
    tile_index = Column(BigInteger, default=0)
    user_id = Column(Integer)

    row = relationship("HpRow", back_populates="tiles", lazy="selectin")


# ---------------- MESSAGES ---------------- #


class Message(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True)
    dt = Column(TIMESTAMP)
    message = Column(String)
    icon = Column(String)
    user_id = Column(BigInteger)
    hyperlink = Column(String)
    action = Column(String)


# ---------------- READING JOURNAL ---------------- #


class ReadingJournal(Base):
    __tablename__ = "reading_journal"

    row_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    id_paragraph = Column(Integer)
    dt = Column(TIMESTAMP)
    id_book = Column(Integer)


# ---------------- TRANSITIONS ---------------- #


class HpTransition(Base):
    __tablename__ = "hp_transitions"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    tile_id = Column(BigInteger)
    hyperlink = Column(String)
    dt = Column(TIMESTAMP)
