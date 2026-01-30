from sqlalchemy.orm import Session

from db import models


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.name == username).first()


def get_user_id(db: Session, username: str):
    user = db.query(models.User).filter(models.User.name == username).first()
    if user:
        return user.user_id
    else:
        return None


async def aget_user(db: AsyncSession, username: str):
    result = await db.execute(
        select(models.User).where(models.User.name == username)
    )
    return result.scalar_one_or_none()


async def aget_user_id(db: AsyncSession, username: str):
    result = await db.execute(
        select(models.User.user_id).where(models.User.name == username)
    )
    user_id = result.scalar_one_or_none()
    if user_id is not None:
        return user_id
    else:
        return None
