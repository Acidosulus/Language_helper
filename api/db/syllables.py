from datetime import datetime, timedelta
from typing import Optional
import re

from sqlalchemy.orm import selectinload
from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from db import models, dto
from db import users


async def get_syllable(db: AsyncSession, syllable_id: int, username: str):
    user_id = await users.aget_user_id(db, username)
    result = await db.execute(
        select(models.Syllable)
        .join(models.User)
        .where(models.Syllable.syllable_id == syllable_id)
        .where(models.User.user_id == user_id)
        .options(selectinload(models.Syllable.paragraphs))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def save_syllable(
    db: AsyncSession, syllable: models.Syllable, username: str
) -> models.Syllable:
    # existing syllable
    if syllable.syllable_id:
        user_id = await users.aget_user_id(db, username)
        result = await db.execute(
            select(models.Syllable)
            .where(models.Syllable.syllable_id == syllable.syllable_id)
            .where(models.Syllable.user_id == user_id)
        )
        syllable_db = result.scalar_one_or_none()
        syllable_db.word = syllable.word
        syllable_db.transcription = syllable.transcription
        syllable_db.translations = syllable.translations
        syllable_db.examples = syllable.examples

        # update existing paragraphs
        for paragraph in list(syllable_db.paragraphs):
            result = await db.execute(
                select(models.SyllableParagraph)
                .where(
                    models.SyllableParagraph.paragraph_id
                    == paragraph.paragraph_id
                )
                .where(
                    models.SyllableParagraph.syllable_id == syllable.syllable_id
                )
            )
            paragraph_db = result.scalar_one_or_none()
            if not paragraph_db:
                continue
            paragraph_db.example = paragraph.example
            paragraph_db.translate = paragraph.translate
            paragraph_db.sequence = paragraph.sequence

        # delete absent paragraphs
        for paragraph in list(syllable_db.paragraphs):
            if paragraph.paragraph_id not in [
                p.paragraph_id for p in syllable.paragraphs
            ]:
                await db.execute(
                    delete(models.SyllableParagraph).where(
                        models.SyllableParagraph.paragraph_id
                        == paragraph.paragraph_id,
                        models.SyllableParagraph.syllable_id
                        == syllable.syllable_id,
                    )
                )

        # add new paragraphs
        for paragraph in syllable.paragraphs:
            if paragraph.paragraph_id not in [
                p.paragraph_id for p in syllable_db.paragraphs
            ]:
                paragraph_db = models.SyllableParagraph(
                    example=paragraph.example,
                    translate=paragraph.translate,
                    sequence=paragraph.sequence,
                    syllable_id=syllable.syllable_id,
                )
                db.add(paragraph_db)
    # new syllable
    else:
        user_id = await users.aget_user_id(db, username)
        syllable_db = models.Syllable(
            word=syllable.word,
            transcription=syllable.transcription,
            translations=syllable.translations,
            examples=syllable.examples,
            show_count=0,
            ready=0,
            last_view=datetime.utcnow(),
            user_id=user_id,
        )
        db.add(syllable_db)
        await db.flush()

        for paragraph in syllable.paragraphs:
            paragraph_db = models.SyllableParagraph(
                example=paragraph.example,
                translate=paragraph.translate,
                sequence=paragraph.sequence,
                syllable_id=syllable_db.syllable_id,
            )
            db.add(paragraph_db)

    await db.flush()
    return syllable_db


async def set_syllable_as_viewed(
    db: AsyncSession, sillable_id: int, username: str
):
    result = await db.execute(
        select(models.Syllable)
        .join(models.User)
        .where(models.Syllable.syllable_id == sillable_id)
        .where(models.User.name == username)
    )
    syllable = result.scalar_one_or_none()
    syllable.last_view = datetime.utcnow()
    syllable.show_count += 1
    await db.flush()


async def get_next_syllable(
    db: AsyncSession, current_syllable_id: int, username: str
) -> Optional[dto.Syllable]:
    if current_syllable_id:
        await set_syllable_as_viewed(db, current_syllable_id, username)

    result = await db.execute(
        select(models.Syllable)
        .join(models.User)
        .where(models.Syllable.ready == 0)
        .where(models.User.name == username)
        .options(selectinload(models.Syllable.paragraphs))
        .order_by(models.Syllable.last_view)
        .limit(1)
    )
    syllable = result.scalar_one_or_none()

    if not syllable:
        return None

    # Конвертируем SQLAlchemy модель в Pydantic модель
    return dto.Syllable.model_validate(syllable, from_attributes=True)


async def get_syllables_by_word_part(
    db: AsyncSession,
    user_name: str,
    ready: int,
    word_part: str = "",
    offset: int = 0,
    limit: int = 100,
):
    """Возвращает список слогов по подстроке слова, только для слов на изучении

    используется для поиска слов среди добавленных на изучение
    """

    base = (
        select(models.Syllable)
        .join(models.User)
        .where(models.Syllable.ready == ready)
        .where(models.User.name == user_name)
    )

    if word_part:
        base = base.where(models.Syllable.word.contains(word_part))

    result = await db.execute(
        base.order_by(models.Syllable.word).offset(offset).limit(limit)
    )
    return result.scalars().all()


async def get_syllables_count_repeated_today(
    db: AsyncSession, username: str
) -> int:
    user_id = await users.aget_user_id(db, username)
    result = await db.execute(
        select(func.count(models.Syllable.syllable_id))
        .where(
            models.Syllable.last_view
            >= datetime.utcnow().date() - timedelta(days=1)
        )
        .where(models.Syllable.user_id == user_id)
    )
    return result.scalar_one()


async def get_user_syllables_in_text(
    db: AsyncSession, text: str, username: str
):
    """
    Возвращает список слов (Syllable) пользователя на изучении (ready == 0),
    которые встречаются в переданном тексте. Реляции paragraphs подгружаются
    так же, как это делается в get_syllable (см. options(selectinload(...))).

    Сопоставление слов выполняется по регистронезависимому сравнению
    с учётом границ слов: из текста извлекаются токены вида [\w'-]+.
    """

    # Извлекаем слова из текста и нормализуем к нижнему регистру
    tokens = set(
        w.lower() for w in re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE)
    )
    if not tokens:
        return []

    user_id = await users.aget_user_id(db, username)

    result = await db.execute(
        select(models.Syllable)
        .where(models.Syllable.user_id == user_id)
        .where(models.Syllable.ready == 0)
        .where(func.lower(models.Syllable.word).in_(tokens))
        .options(selectinload(models.Syllable.paragraphs))
        .order_by(models.Syllable.word)
    )
    return result.scalars().all()


async def set_syllable_as_learned(
    db: AsyncSession, syllable_id: int, username: str
):
    """Помечает слово как изученное"""

    result = await db.execute(
        select(models.Syllable)
        .join(models.User)
        .where(models.Syllable.syllable_id == syllable_id)
        .where(models.User.name == username)
    )
    syllable = result.scalar_one_or_none()
    if syllable:
        syllable.ready = 1
        await db.flush()


async def set_syllable_as_unlearned(
    db: AsyncSession, syllable_id: int, username: str
):
    """Помечает слово как не изученное"""

    result = await db.execute(
        select(models.Syllable)
        .join(models.User)
        .where(models.Syllable.syllable_id == syllable_id)
        .where(models.User.name == username)
    )
    syllable = result.scalar_one_or_none()
    if syllable:
        syllable.ready = 0
        await db.flush()
