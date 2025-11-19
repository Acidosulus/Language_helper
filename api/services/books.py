from datetime import datetime
from typing import Optional

from sqlalchemy import desc, select, func
from sqlalchemy.orm import Session, selectinload
from services import models, dto, users


def Get_Max_Paragraph_Number_By_Book(db: Session, user_name: str, id_book: int):
    return (
        db.query(models.Sentence)
        .filter(models.Book.user_id == users.get_user_id(db, user_name))
        .filter(models.Book.id_book == id_book)
        .filter(models.Sentence.id_book == models.Book.id_book)
        .order_by(desc(models.Sentence.id_paragraph))
        .first()
    ).id_paragraph


def Get_Min_Paragraph_Number_By_Book(db: Session, user_name: str, id_book: int):
    return (
        db.query(models.Sentence)
        .filter(models.Book.user_id == users.get_user_id(db, user_name))
        .filter(models.Book.id_book == id_book)
        .filter(models.Sentence.id_book == models.Book.id_book)
        .order_by(models.Sentence.id_paragraph)
        .first()
    ).id_paragraph


def get_user_books_with_stats(db: Session, user_name: str) -> list[models.Book]:
    """
    ORM-стиль: выбираем объекты Book и агрегатные значения.
    Затем проставляем значения атрибутов вручную, чтобы Pydantic мог их считать.
    """

    stmt = (
            select(
            models.Book,  # <-- Выбираем весь ORM-объект
            func.min(models.Sentence.id_paragraph).label("min_p"),
            func.max(models.Sentence.id_paragraph).label("max_p")
        )
        .join(models.User, models.Book.user_id == models.User.user_id)
        .outerjoin(models.Sentence, models.Book.id_book == models.Sentence.id_book)
        .where(models.User.name == user_name)
        .group_by(models.Book.id_book)
    )

    # Получаем список кортежей: [(BookInstance, 1, 10), (BookInstance, 2, 5), ...]
    results = db.execute(stmt).all()

    books_processed = []
    for row in results:
        book = row[0]  # Это настоящий объект SQLAlchemy модели Book

        # Динамически добавляем атрибуты к объекту.
        # Pydantic (orm_mode=True / from_attributes=True) считает их автоматически.
        book.Min_Paragraph_Number = row.min_p
        book.Max_Paragraph_Number = row.max_p

        books_processed.append(book)

    return books_processed

