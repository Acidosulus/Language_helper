from typing import Literal, Optional

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from db import syllables, books, phrases, models, dto
from pydantic import BaseModel
from io import BytesIO
import gtts

from wooordhunt import parser

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
    "postgresql+psycopg2://postgres:321@192.168.0.112/language"
    # "postgresql+psycopg2://postgres:321@192.168.0.112/language_helper"
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


@app.get("/api/phrase/repeated_today", response_model=dto.RepeatedToday)
def get_phrases_repeated_today(request: Request, db: Session = Depends(get_db)):
    if request.session.get("user"):
        return dto.RepeatedToday(
            count=phrases.get_phrases_count_repeated_today(
                db,
                request.session.get("user"),
            )
        )
    else:
        raise HTTPException(status_code=401, detail="Требуется авторизация")


@app.get("/api/syllable", response_model=dto.Syllable)
def get_syllable(
    request: Request, syllable_id: int = None, db: Session = Depends(get_db)
):
    return syllables.get_syllable(db, syllable_id, request.session.get("user"))


@app.post("/api/syllable", response_model=dto.Syllable)
def save_syllable(
    request: Request,
    syllable_dto: dto.Syllable,
    db: Session = Depends(get_db_autocommit),
):
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


@app.get("/api/syllable/repeated_today", response_model=dto.RepeatedToday)
def get_syllables_repeated_today(
    request: Request, db: Session = Depends(get_db)
):
    if request.session.get("user"):
        return dto.RepeatedToday(
            count=syllables.get_syllables_count_repeated_today(
                db,
                request.session.get("user"),
            )
        )
    else:
        raise HTTPException(status_code=401, detail="Требуется авторизация")


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


@app.get("/api/book/last", response_model=dto.BookDTO)
def get_last_opened_book(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="User not authenticated")

    return books.last_opened_book(db, request.session.get("user"))


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


class TTSIn(BaseModel):
    text: str
    lang: Optional[str] = "en"


@app.post("/api/text_to_speech")
def text_to_speech(request: Request, payload: TTSIn):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="User not authenticated")

    text = (payload.text or "").strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text is empty")

    try:
        tts = gtts.gTTS(text=text, lang=payload.lang or "en")
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

@app.get("/api/word_from_wooordhunt", response_model=dto.Syllable)
def word_from_wooordhunt(request: Request, word: str) -> dto.Syllable:
    lc_link = fr"https://wooordhunt.ru/word/{word}"
    wh = parser.Wooordhunt(lc_link)

    # Собираем данные не из БД, но приводим их к DTO, совместимому с моделью Syllable
    examples_list = wh.get_examples() or []
    # Сконвертируем список примеров в строку для поля examples (Pydantic ожидает str)
    examples_text = "\n".join(
        f"{item.get('example','').strip()} — {item.get('translate','') or ''}" for item in examples_list
    ) or None

    # И одновременно подготовим paragraphs как структурированный список
    paragraphs = [
        dto.SyllableParagraph(
            example=item.get("example"),
            translate=item.get("translate"),
            sequence=idx + 1,
        )
        for idx, item in enumerate(examples_list)
    ]

    syllable_dto = dto.Syllable(
        syllable_id=None,
        word=word,
        transcription=wh.get_transcription(),
        translations=wh.get_translation(),
        examples=examples_text,
        show_count=0,
        ready=0,
        last_view=None,
        user_id=None,
        paragraphs=paragraphs,
    )

    from rich import print
    print(syllable_dto)

    return syllable_dto


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        ssl_certfile="localhost+3.pem",
        ssl_keyfile="localhost+3-key.pem",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
