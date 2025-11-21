from typing import Literal, Optional

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from services import syllables, books, phrases, models, dto

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key-change-in-production",
    session_cookie="session_cookie",
    https_only=True,
    same_site="none",
    max_age=86400 * 365,
)

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

DATABASE_URL = (
    "postgresql+psycopg2://postgres:321@192.168.0.112/language_helper"
)
engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=True,
    expire_on_commit=False,
)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_autocommit():
    """Сессия с автокоммитом для операций добавления/обновления"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    user = db.query(models.User).filter(models.User.name == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user


# --- API ---
@app.post("/api/set_password")
def set_password(
    target_username: str = Form(...),
    new_password: str = Form(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_autocommit),
):
    # ищем пользователя, чьё имя указано
    user = (
        db.query(models.User)
        .filter(models.User.name == target_username)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # разрешаем менять пароль только себе
    if current_user.name != target_username:
        raise HTTPException(
            status_code=403, detail="Можно менять только свой пароль"
        )

    # хешируем и обновляем
    user.hashed_password = pwd_context.hash(new_password)
    db.add(user)
    db.commit()

    return {"message": "Пароль успешно обновлён"}


@app.post("/api/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db_autocommit),
):
    if db.query(models.User).filter(models.User.name == username).first():
        raise HTTPException(
            status_code=400, detail="Пользователь уже существует"
        )
    hashed_password = pwd_context.hash(password)
    new_user = models.User(name=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "Регистрация успешна"}


@app.post("/api/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.name == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверные данные")
    request.session["user"] = user.name
    return {"message": "Вход выполнен", "user": user.name}


@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Выход выполнен"}


@app.get("/api/secret")
def secret(user: models.User = Depends(get_current_user)):
    return {"message": f"Секретная страница, {user.name}!"}


# --- Доп.эндпоинт для проверки сессии ---
@app.get("/api/me")
def me(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("user")
    if not username:
        return {"authenticated": False}
    user = db.query(models.User).filter(models.User.name == username).first()
    if not user:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user": user.name,
        "email": "emty@email.dummy",
    }


@app.get("/api/phrases", response_model=list[dto.Phrase])
def phrases_list(
    request: Request,
    ready: Literal["0", "1"] = "0",
    db: Session = Depends(get_db),
):
    return phrases.get_phrases_by_user(
        db, request.session.get("user"), int(ready)
    )


@app.get("/api/phrase", response_model=dto.Phrase)
def get_phrase_by_id(
    request: Request, id_phrase: int, db: Session = Depends(get_db)
):
    if request.session.get("user"):
        return phrases.get_phrase_by_id(
            db, id_phrase, request.session.get("user")
        )
    else:
        raise HTTPException(status_code=401, detail="Требуется авторизация")


@app.post("/api/phrase/status")
def set_phrase_status(
    request: Request,
    id_phrase: int,
    status: Literal["0", "1"],
    db: Session = Depends(get_db),
):
    if request.session.get("user"):
        phrases.set_phrase_status(
            db, id_phrase, int(status), request.session.get("user")
        )
    else:
        raise HTTPException(status_code=401, detail="Требуется авторизация")


@app.get("/api/phrase/next", response_model=dto.Phrase)
def get_next_phrase(
    request: Request,
    current_phrase_id: int,
    db: Session = Depends(get_db_autocommit),
):
    if request.session.get("user"):
        return phrases.get_next_phrase(
            db, current_phrase_id, request.session.get("user")
        )
    else:
        raise HTTPException(status_code=401, detail="Требуется авторизация")


@app.post("/api/phrase", response_model=dto.Phrase)
def phrase(
    request: Request,
    phrase: dto.Phrase,
    db: Session = Depends(get_db_autocommit),
):
    if request.session.get("user"):
        return phrases.save_phrase(db, phrase, request.session.get("user"))
    else:
        raise HTTPException(status_code=401, detail="Требуется авторизация")


@app.get("/api/syllable", response_model=dto.Syllable)
def get_syllable(
    request: Request, syllable_id: int = None, db: Session = Depends(get_db)
):
    return syllables.get_syllable(db, syllable_id, request.session.get("user"))


@app.get("/api/syllables", response_model=list[dto.Syllable])
def all_syllables(
    request: Request, limit=100, offset=0, db: Session = Depends(get_db)
):
    result = syllables.get_syllables(
        db, limit=limit, offset=offset, username=request.session.get("user")
    )
    return result


@app.post("/api/syllable", response_model=dto.Syllable)
def save_syllable(
    request: Request,
    syllable_dto: dto.Syllable,
    db: Session = Depends(get_db_autocommit),
):
    from rich import print

    print(syllable_dto)

    return syllables.save_syllable(
        db, syllable_dto, request.session.get("user")
    )


@app.get("/api/syllable/next", response_model=Optional[dto.Syllable])
def get_next_syllable(
    request: Request,
    current_syllable_id: int,
    db: Session = Depends(get_db_autocommit),
):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return syllables.get_next_syllable(db, current_syllable_id, username)


@app.get("/api/syllables/search", response_model=list[dto.Syllable])
def get_syllables_by_word_part_endpoint(
    request: Request,
    ready: Literal["0", "1"] = "0",
    word_part: str = "",
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Возвращает список слогов по подстроке слова и признаку готовности.

    Параметры:
    - ready: "0" или "1" — фильтр выученности
    - word_part: подстрока для поиска в поле word
    - offset, limit: пагинация
    """
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    return syllables.get_syllables_by_word_part(
        db=db,
        user_name=username,
        ready=int(ready),
        word_part=word_part,
        offset=offset,
        limit=limit,
    )


@app.get("/api/books", response_model=list[dto.BookWithStatsDTO])
def get_books(request: Request, db: Session = Depends(get_db)):
    return books.get_user_books_with_stats(db, request.session.get("user"))


@app.get("/api/book", response_model=dto.BookWithStatsDTO)
def get_book_information(
    request: Request, book_id: int, db: Session = Depends(get_db)
):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="User not authenticated")

    book = books.get_book(db, book_id, request.session.get("user"))

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found.")

    return book


@app.get("/api/book/paragraph", response_model=list[dto.SentenceDTO])
def get_book_paragraph(
    request: Request,
    id_book: int,
    id_paragraph: int,
    db: Session = Depends(get_db),
):
    return books.get_paragraph(
        db,
        id_book=id_book,
        id_paragraph=id_paragraph,
        user_name=request.session.get("user"),
    )


@app.post("/api/book/paragraph")
def save_book_position(
    request: Request,
    data: dto.BookPositionIn,
    db: Session = Depends(get_db_autocommit),
):
    books.save_book_position(
        db,
        id_book=data.id_book,
        new_current_paragraph=data.id_new_paragraph,
        user_name=request.session.get("user"),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        ssl_certfile="localhost+3.pem",
        ssl_keyfile="localhost+3-key.pem",
    )
