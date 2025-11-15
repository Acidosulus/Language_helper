from sqlalchemy.orm import Session
from services import models


def get_phrases_by_user(db: Session, username: str, ready: int) -> list[models.Phrase]:
    return (
        db.query(models.Phrase)
        .join(models.User)
        .filter(models.Phrase.ready == ready)
        .filter(models.User.name == username)
        .all()
    )

def get_phrase_by_id(db: Session, id_phrase: int):
    return db.query(models.Phrase).join(models.User).filter(models.Phrase.id_phrase == id_phrase).first()
