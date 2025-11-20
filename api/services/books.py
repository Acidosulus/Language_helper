from datetime import datetime

from sqlalchemy import desc, select, func, update
from sqlalchemy.orm import Session
from services import models, users


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
    stmt = (
        select(
            models.Book,
            func.min(models.Sentence.id_paragraph).label("min_p"),
            func.max(models.Sentence.id_paragraph).label("max_p"),
        )
        .join(models.User, models.Book.user_id == models.User.user_id)
        .outerjoin(
            models.Sentence, models.Book.id_book == models.Sentence.id_book
        )
        .where(models.User.name == user_name)
        .group_by(models.Book.id_book)
    )

    results = db.execute(stmt).all()

    books_processed = []
    for row in results:
        book = row[0]

        book.Min_Paragraph_Number = row.min_p
        book.Max_Paragraph_Number = row.max_p

        books_processed.append(book)

    return books_processed


def get_paragraph(
    db: Session,
    id_book: int,
    id_paragraph: int,
    user_name: str,
):
    return (
        db.query(models.Sentence)
        .filter(models.User.name == user_name)
        .filter(models.Book.id_book == id_book)
        .filter(models.Sentence.id_paragraph == id_paragraph)
        .order_by(models.Sentence.id_sentence)
        .all()
    )


def save_book_position(
    db: Session,
    id_book: int,
    new_current_paragraph: int,
    user_name: str,
):
    if (
        Get_Min_Paragraph_Number_By_Book(db, user_name, id_book)
        <= new_current_paragraph
        <= Get_Max_Paragraph_Number_By_Book(db, user_name, id_book)
    ):
        db.execute(
            update(models.Book)
            .where(models.User.name == user_name)
            .where(models.Book.id_book == id_book)
            .where(models.Book.user_id == models.User.user_id)
            .values(
                current_paragraph=new_current_paragraph, dt=datetime.utcnow()
            )
        )


def get_book(db: Session, id_book: int, user_name: str):
    books = get_user_books_with_stats(db, user_name)
    return next(filter(lambda x: x.id_book == id_book, books), None)
