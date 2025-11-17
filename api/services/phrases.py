from datetime import datetime

from sqlalchemy.orm import Session
from services import models

from services import users


def get_phrases_by_user(
    db: Session, username: str, ready: int
) -> list[models.Phrase]:
    return (
        db.query(models.Phrase)
        .join(models.User)
        .filter(models.Phrase.ready == ready)
        .filter(models.User.name == username)
        .all()
    )


def get_phrase_by_id(db: Session, id_phrase: int, username: str):
    return (
        db.query(models.Phrase)
        .join(models.User)
        .filter(models.Phrase.id_phrase == id_phrase)
        .filter(models.User.name == username)
        .first()
    )


def set_phrase_status(db: Session, id_phrase: int, status: int, username: str):
    phrase = (
        db.query(models.Phrase)
        .join(models.User)
        .filter(models.Phrase.id_phrase == id_phrase)
        .filter(models.User.name == username)
        .first()
    )
    phrase.ready = status


def set_phrase_as_viewed(db: Session, id_phrase: int, username: str):
    phrase = (
        db.query(models.Phrase)
        .join(models.User)
        .filter(models.Phrase.id_phrase == id_phrase)
        .filter(models.User.name == username)
        .first()
    )
    phrase.last_view = datetime.utcnow()
    phrase.show_count += 1
    db.flush()


def get_next_phrase(db: Session, current_phrase_id: int, username: str):
    if current_phrase_id:
        set_phrase_as_viewed(db, current_phrase_id, username)

    return (
        db.query(models.Phrase)
        .join(models.User)
        .filter(models.Phrase.ready == 0)
        .filter(models.User.name == username)
        .order_by(models.Phrase.last_view)
        .first()
    )


def save_phrase(db: Session, phrase: models.Phrase, username: str):
    if phrase.id_phrase:
        phrase = (
            db.query(models.Phrase)
            .join(models.User)
            .filter(models.Phrase.id_phrase == phrase.id_phrase)
            .filter(models.User.name == username)
            .first()
        )
        phrase.phrase = phrase.phrase
        phrase.translation = phrase.translation
    else:
        phrase = models.Phrase(
            phrase=phrase.phrase,
            translation=phrase.translation,
            show_count=0,
            ready=0,
            last_view=datetime.utcnow(),
            dt=datetime.utcnow(),
            user_id=users.get_user_id(db, username)
        )
        db.add(phrase)

    db.commit()
    return phrase
