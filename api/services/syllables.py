from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, selectinload
from services import models, dto
from services import users


def get_syllable(db: Session, syllable_id: int, username: str):
    return (
        db.query(models.Syllable)
        .join(models.User)
        .filter(models.Syllable.syllable_id == syllable_id)
        .filter(models.User.user_id == users.get_user_id(db, username))
        .options(selectinload(models.Syllable.paragraphs))
        .first()
    )


def get_syllables(
    db: Session,
    username: str,
    offset: int = 0,
    limit: int = 100,
) -> list[models.Syllable]:
    query = (
        db.query(models.Syllable)
        .join(models.User)
        .filter(models.User.user_id == users.get_user_id(db, username))
        .options(selectinload(models.Syllable.paragraphs))
    )
    return query.offset(offset).limit(limit).all()


def save_syllable(
    db: Session, syllable: models.Syllable, username: str
) -> models.Syllable:
    # existing syllable
    if syllable.syllable_id:
        user_id = users.get_user_id(db, username)
        syllable_db = (
            db.query(models.Syllable)
            .filter(models.Syllable.syllable_id == syllable.syllable_id)
            .filter(models.Syllable.user_id == user_id)
            .first()
        )
        syllable_db.word = syllable.word
        syllable_db.transcription = syllable.transcription
        syllable_db.translations = syllable.translations
        syllable_db.examples = syllable.examples

        # update existing paragraphs
        for paragraph in syllable_db.paragraphs:
            paragraph_db = (
                db.query(models.SyllableParagraph)
                .filter(
                    models.SyllableParagraph.paragraph_id
                    == paragraph.paragraph_id
                )
                .filter(
                    models.SyllableParagraph.syllable_id == syllable.syllable_id
                )
                .first()
            )
            if not paragraph_db:
                continue
            paragraph_db.example = paragraph.example
            paragraph_db.translate = paragraph.translate
            paragraph_db.sequence = paragraph.sequence

        # delete absent paragraphs
        for paragraph in syllable_db.paragraphs:
            if paragraph.paragraph_id not in [
                p.paragraph_id for p in syllable.paragraphs
            ]:
                paragraph_db = (
                    db.query(models.SyllableParagraph)
                    .filter(
                        models.SyllableParagraph.paragraph_id
                        == paragraph.paragraph_id
                    )
                    .filter(
                        models.SyllableParagraph.syllable_id
                        == syllable.syllable_id
                    )
                    .first()
                )
                db.delete(paragraph_db)

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
        user_id = users.get_user_id(db, username)
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
        db.flush()

        for paragraph in syllable.paragraphs:
            paragraph_db = models.SyllableParagraph(
                example=paragraph.example,
                translate=paragraph.translate,
                sequence=paragraph.sequence,
                syllable_id=syllable_db.syllable_id,
            )
            db.add(paragraph_db)

    db.flush()
    return syllable_db


def set_syllable_as_viewed(db: Session, sillable_id: int, username: str):
    syllable = (
        db.query(models.Syllable)
        .join(models.User)
        .filter(models.Syllable.syllable_id == sillable_id)
        .filter(models.User.name == username)
        .first()
    )
    syllable.last_view = datetime.utcnow()
    syllable.show_count += 1
    db.flush()


def get_next_syllable(
    db: Session, current_syllable_id: int, username: str
) -> Optional[dto.Syllable]:
    if current_syllable_id:
        set_syllable_as_viewed(db, current_syllable_id, username)

    syllable = (
        db.query(models.Syllable)
        .join(models.User)
        .filter(models.Syllable.ready == 0)
        .filter(models.User.name == username)
        .options(selectinload(models.Syllable.paragraphs))
        .order_by(models.Syllable.last_view)
        .first()
    )

    if not syllable:
        return None

    # Конвертируем SQLAlchemy модель в Pydantic модель
    return dto.Syllable.model_validate(syllable, from_attributes=True)
