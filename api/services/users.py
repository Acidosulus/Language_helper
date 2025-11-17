from sqlalchemy.orm import Session

from services import models


def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.name == username).first()


def get_user_id(db: Session, username: str):
    user = db.query(models.User).filter(models.User.name == username).first()
    if user:
        return user.user_id
    else:
        return None
