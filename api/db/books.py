from datetime import datetime

from sqlalchemy import desc, select, func, update
from sqlalchemy.orm import noload
from sqlalchemy.ext.asyncio import AsyncSession
from db import models, users, dto


async def Get_Max_Paragraph_Number_By_Book(
    db: AsyncSession, user_name: str, id_book: int
):
    user_id = await users.aget_user_id(db, user_name)
    res = await db.execute(
        select(models.Sentence.id_paragraph)
        .join(models.Book, models.Sentence.id_book == models.Book.id_book)
        .where(models.Book.user_id == user_id)
        .where(models.Book.id_book == id_book)
        .order_by(desc(models.Sentence.id_paragraph))
        .limit(1)
    )
    row = res.first()
    return row[0] if row else None


async def Get_Min_Paragraph_Number_By_Book(
    db: AsyncSession, user_name: str, id_book: int
):
    user_id = await users.aget_user_id(db, user_name)
    res = await db.execute(
        select(models.Sentence.id_paragraph)
        .join(models.Book, models.Sentence.id_book == models.Book.id_book)
        .where(models.Book.user_id == user_id)
        .where(models.Book.id_book == id_book)
        .order_by(models.Sentence.id_paragraph)
        .limit(1)
    )
    row = res.first()
    return row[0] if row else None


async def get_user_books_with_stats(
    db: AsyncSession, user_name: str
) -> list[dto.BookWithStatsDTO]:
    from datetime import datetime, timedelta

    # Subquery to count paragraphs read in the last 24 hours for each book
    last_24h = datetime.utcnow() - timedelta(hours=24)
    paragraphs_last_24h = (
        select(
            models.ReadingJournal.id_book,
            (
                func.max(models.ReadingJournal.id_paragraph)
                - func.min(models.ReadingJournal.id_paragraph)
            ).label("paragraphs_read_24h"),
        )
        .join(models.User, models.ReadingJournal.user_id == models.User.user_id)
        .where(
            models.User.name == user_name, models.ReadingJournal.dt >= last_24h
        )
        .group_by(models.ReadingJournal.id_book)
        .subquery()
    )

    stmt = (
        select(
            models.Book,
            func.min(models.Sentence.id_paragraph).label("min_p"),
            func.max(models.Sentence.id_paragraph).label("max_p"),
            func.coalesce(paragraphs_last_24h.c.paragraphs_read_24h, 0).label(
                "paragraphs_read_24h"
            ),
        )
        .join(models.User, models.Book.user_id == models.User.user_id)
        .outerjoin(
            models.Sentence, models.Book.id_book == models.Sentence.id_book
        )
        .outerjoin(
            paragraphs_last_24h,
            models.Book.id_book == paragraphs_last_24h.c.id_book,
        )
        .where(models.User.name == user_name)
        .group_by(
            models.Book.id_book, paragraphs_last_24h.c.paragraphs_read_24h
        )
    )

    results = (await db.execute(stmt)).all()

    books_processed = []
    for row in results:
        book = row[0]
        book.Min_Paragraph_Number = row.min_p
        book.Max_Paragraph_Number = row.max_p
        book.paragraphs_read_24h = row.paragraphs_read_24h or 0
        books_processed.append(book)

    return books_processed


async def get_paragraph(
    db: AsyncSession,
    id_book: int,
    id_paragraph: int,
    user_name: str,
):
    res = await db.execute(
        select(models.Sentence)
        .join(models.Book, models.Sentence.id_book == models.Book.id_book)
        .join(models.User, models.Book.user_id == models.User.user_id)
        .where(models.User.name == user_name)
        .where(models.Book.id_book == id_book)
        .where(models.Sentence.id_paragraph == id_paragraph)
        .order_by(models.Sentence.id_sentence)
    )
    return res.scalars().all()


async def save_book_position(
    db: AsyncSession,
    id_book: int,
    new_current_paragraph: int,
    user_name: str,
):
    min_p = await Get_Min_Paragraph_Number_By_Book(db, user_name, id_book)
    max_p = await Get_Max_Paragraph_Number_By_Book(db, user_name, id_book)
    if (
        min_p is not None
        and max_p is not None
        and (min_p <= new_current_paragraph <= max_p)
    ):
        await db.execute(
            update(models.Book)
            .where(models.Book.id_book == id_book)
            .values(
                current_paragraph=new_current_paragraph, dt=datetime.utcnow()
            )
        )
        user_id = await users.aget_user_id(db, user_name)
        await save_book_read_event(db, user_id, id_book, new_current_paragraph)


async def get_book(
    db: AsyncSession, id_book: int, user_name: str
) -> dto.BookWithStatsDTO:
    books_list = await get_user_books_with_stats(db, user_name)
    return next(filter(lambda x: x.id_book == id_book, books_list), None)


async def last_opened_book(db: AsyncSession, user_name: str):
    user_id = await users.aget_user_id(db, user_name)
    res = await db.execute(
        select(models.Book)
        .options(noload("*"))
        .where(models.Book.user_id == user_id)
        .order_by(desc(models.Book.dt))
        .limit(1)
    )
    return res.scalar_one_or_none()


async def save_book_read_event(
    db: AsyncSession, id_user, id_book, id_paragraph
):
    db.add(
        models.ReadingJournal(
            user_id=id_user,
            id_book=id_book,
            id_paragraph=id_paragraph,
            dt=datetime.utcnow(),
        )
    )
    await db.flush()
