from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db import models

from db import users


async def get_phrases_by_user(
    db: AsyncSession, username: str, ready: int
) -> list[models.Phrase]:
    result = await db.execute(
        select(models.Phrase)
        .join(models.User)
        .where(models.Phrase.ready == ready)
        .where(models.User.name == username)
    )
    return result.scalars().all()


async def get_phrase_by_id(db: AsyncSession, id_phrase: int, username: str):
    result = await db.execute(
        select(models.Phrase)
        .join(models.User)
        .where(models.Phrase.id_phrase == id_phrase)
        .where(models.User.name == username)
    )
    return result.scalar_one_or_none()


async def set_phrase_status(
    db: AsyncSession, id_phrase: int, status: int, username: str
):
    result = await db.execute(
        select(models.Phrase)
        .join(models.User)
        .where(models.Phrase.id_phrase == id_phrase)
        .where(models.User.name == username)
    )
    phrase = result.scalar_one_or_none()
    if phrase:
        phrase.ready = status
        db.add(phrase)


async def set_phrase_as_viewed(db: AsyncSession, id_phrase: int, username: str):
    result = await db.execute(
        select(models.Phrase)
        .join(models.User)
        .where(models.Phrase.id_phrase == id_phrase)
        .where(models.User.name == username)
    )
    phrase = result.scalar_one_or_none()
    if phrase:
        phrase.last_view = datetime.utcnow()
        phrase.show_count += 1
        db.add(phrase)
        await db.flush()


async def get_next_phrase(
    db: AsyncSession, current_phrase_id: int, username: str
):
    if current_phrase_id:
        await set_phrase_as_viewed(db, current_phrase_id, username)

    result = await db.execute(
        select(models.Phrase)
        .join(models.User)
        .where(models.Phrase.ready == 0)
        .where(models.User.name == username)
        .order_by(models.Phrase.last_view)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def save_phrase(db: AsyncSession, phrase: models.Phrase, username: str):
    if phrase.id_phrase:
        result = await db.execute(
            select(models.Phrase)
            .join(models.User)
            .where(models.Phrase.id_phrase == phrase.id_phrase)
            .where(models.User.name == username)
        )
        phrase_db = result.scalar_one_or_none()
        if not phrase_db:
            return None
        phrase_db.phrase = phrase.phrase
        phrase_db.translation = phrase.translation
        db.add(phrase_db)
    else:
        user_id = await users.aget_user_id(db, username)
        phrase_db = models.Phrase(
            phrase=phrase.phrase,
            translation=phrase.translation,
            show_count=0,
            ready=0,
            last_view=datetime.utcnow(),
            dt=datetime.utcnow(),
            user_id=user_id,
        )
        db.add(phrase_db)

    await db.commit()
    return phrase_db


async def get_phrases_count_repeated_today(
    db: AsyncSession, username: str
) -> int:
    user_id = await users.aget_user_id(db, username)
    result = await db.execute(
        select(func.count(models.Phrase.id_phrase))
        .where(models.Phrase.user_id == user_id)
        .where(
            models.Phrase.last_view
            >= datetime.utcnow().date() - timedelta(days=1)
        )
    )
    return result.scalar_one()
