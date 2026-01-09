from typing import Literal, Optional

from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response
from datetime import datetime, timezone
import hashlib
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from db import syllables, books, phrases, models, dto, pages
from pydantic import BaseModel
from io import BytesIO
import gtts
import httpx
import json

from db.dto import SyllablesInTextIn
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
    "postgresql+psycopg2://postgres:123@192.168.0.60/language"
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


class LLMAnalyzeIn(BaseModel):
    text: str


from mistralai import Mistral


@app.post("/api/llm/analyze")
async def analyze_text_with_llm(payload: LLMAnalyzeIn):
    """
    Принимает текст, отправляет запрос в локальный Ollama (как в exp.py),
    и возвращает JSON-результат анализа.
    """
    with Mistral(
        api_key="7KzulYHjsyUpnBJPn5sUQDZYEB7V4maR",
    ) as mistral:
        text = (payload.text or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text is empty")

        try:
            res = mistral.chat.complete(
                model="mistral-small-latest",
                messages=[
                    {
                        "content": f"""
                        Проанализируй английский текст: "{text}"
                        Верни строго JSON на русском языке со следующей структурой:
                        {{
                            "translation": "перевод на русский",
                            "grammar": "разбор грамматики исходной фразы на русском языке",
                            "idioms": ["список идиом с их переводом на русский язык"],
                            "cultural_references": "культурные отсылки на русском языке"
                        }}
                        """,
                        "role": "user",
                    },
                ],
                stream=False,
                response_format={"type": "json_object"},
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="LLM недоступен: ошибка сетевого подключения (DNS/интернет). Повторите позже.",
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, detail="LLM не ответил вовремя"
            )
        except Exception as e:
            raise HTTPException(
                status_code=502, detail=f"LLM upstream error: {e}"
            )

        # Попытка извлечь текст ответа и вернуть его как JSON
        try:
            # Новые версии SDK могут иметь удобное поле output_text
            output_text = getattr(res, "output_text", None)

            if not output_text:
                # Универсальное извлечение из первой choice
                msg = res.choices[0].message
                content = getattr(msg, "content", "")
                if isinstance(content, list):
                    # content может быть списком частей с полем text
                    parts = []
                    for part in content:
                        text_part = getattr(part, "text", None)
                        if text_part:
                            parts.append(text_part)
                    output_text = "".join(parts)
                else:
                    output_text = content

            # Преобразуем в dict и возвращаем
            import json as _json

            return _json.loads(output_text)
        except Exception as e:
            # Если не удалось распарсить, вернем как 500 с текстом ошибки
            raise HTTPException(status_code=500, detail=f"LLM parse error: {e}")


@app.post("/api/llm/analyze_local_ollama")
async def analyze_text_with_llm_local_ollama(payload: LLMAnalyzeIn):
    """
    Принимает текст, отправляет запрос в локальный Ollama (как в exp.py),
    и возвращает JSON-результат анализа.
    """
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is empty")

    # Если запускаешь Python ВНУТРИ докера, замени 127.0.0.1 на 'ollama'
    # Здесь используем тот же URL, что и в exp.py
    url = "http://192.168.0.19:11434/api/generate"

    prompt = f"""
    Проанализируй английский текст: "{text}"
    Верни строго JSON на русском языке со следующей структурой:
    {{
        "translation": "перевод на русский",
        "grammar": "разбор грамматики исходной фразы на русском языке",
        "idioms": [
                    {
        "idiom":"идеома из предложеного предложения",
                        "translation":"перевод и объяснение идиомы на русском языке"
                    },
        ],
        "cultural_references": "культурные отсылки на русском языке"
    }}
    """

    payload_req = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=400) as client:
            resp = await client.post(url, json=payload_req)
            resp.raise_for_status()
            data = resp.json()
            # Ollama возвращает JSON-строку в поле 'response'
            return json.loads(data.get("response", "{}"))
    except httpx.ConnectError:
        raise HTTPException(
            status_code=502,
            detail="Не удалось подключиться к Ollama. Проверь, запущен ли контейнер.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")


@app.post("/api/syllables/in_text", response_model=list[dto.Syllable])
def get_user_syllables_in_text_endpoint(
    request: Request,
    payload: SyllablesInTextIn,
    db: Session = Depends(get_db),
):
    """
    Возвращает слоги пользователя (ready == 0), встречающиеся в переданном тексте.
    Текст передаётся в теле запроса: {"text": "..."}
    Требуется авторизация по сессии.
    """
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    text = (payload.text or "").strip()
    if not text:
        return []

    return syllables.get_user_syllables_in_text(
        db=db, text=text, username=username
    )


@app.get("/api/word_from_wooordhunt", response_model=dto.Syllable)
def word_from_wooordhunt(request: Request, word: str) -> dto.Syllable:
    lc_link = rf"https://wooordhunt.ru/word/{word}"
    wh = parser.Wooordhunt(lc_link)

    # Собираем данные не из БД, но приводим их к DTO, совместимому с моделью Syllable
    examples_list = wh.get_examples() or []
    # Сконвертируем список примеров в строку для поля examples (Pydantic ожидает str)
    examples_text = (
        "\n".join(
            f"{item.get('example', '').strip()} — {item.get('translate', '') or ''}"
            for item in examples_list
        )
        or None
    )

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

    return syllable_dto


@app.get("/api/start_page")
async def start_page(request: Request, db: Session = Depends(get_db)):
    """
    Возвращает данные для построения структуры стартовой страницы пользователя
    """

    return await pages.get_start_page(db=db, user_name=request.session.get("user"))


@app.get("/api/tile_icon")
async def tile_icon(request: Request, file_name: str, db: Session = Depends(get_db)) -> Response:
    content, content_type, created_at = await pages.get_icon(
        db=db, file_name=file_name
    )
    """
    Возвращает иконку для плитки по имени её файла
    """

    if not content:
        raise HTTPException(status_code=404, detail="Icon not found")

    # Build strong ETag from content bytes
    etag = 'W/"' + hashlib.sha256(content).hexdigest() + '"'

    # Handle conditional request via If-None-Match
    inm = request.headers.get("if-none-match")
    if inm and inm == etag:
        # Not modified, no body
        return Response(status_code=304, headers={
            "ETag": etag,
            "Cache-Control": "public, max-age=86400",
        })

    headers = {
        "ETag": etag,
        "Cache-Control": "public, max-age=86400",
    }

    # Optionally include Last-Modified if available
    if created_at and isinstance(created_at, datetime):
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        headers["Last-Modified"] = created_at.strftime("%a, %d %b %Y %H:%M:%S GMT")

    # Fallback conditional with If-Modified-Since
    ims = request.headers.get("if-modified-since")
    if ims and "Last-Modified" in headers:
        try:
            # Compare parsed dates to decide 304
            from email.utils import parsedate_to_datetime
            ims_dt = parsedate_to_datetime(ims)
            lm_dt = parsedate_to_datetime(headers["Last-Modified"])
            if lm_dt <= ims_dt:
                return Response(status_code=304, headers={
                    "ETag": etag,
                    "Cache-Control": headers["Cache-Control"],
                    "Last-Modified": headers["Last-Modified"],
                })
        except Exception:
            pass

    return Response(content=content, media_type=content_type, headers=headers)


# ----- Tiles CRUD -----
@app.post("/api/tiles", response_model=dto.TileDTO)
def create_tile_endpoint(
    request: Request,
    payload: dto.TileCreateIn,
    db: Session = Depends(get_db_autocommit),
):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        tile = pages.create_tile(
            db,
            username,
            row_id=payload.row_id,
            tile_index=payload.tile_index,
            name=payload.name,
            hyperlink=payload.hyperlink,
            onclick=payload.onclick,
            icon=payload.icon,
            color=payload.color,
        )
        return dto.TileDTO.model_validate(tile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/tiles", response_model=dto.TileDTO)
def update_tile_endpoint(
    request: Request,
    payload: dto.TileUpdateIn,
    db: Session = Depends(get_db_autocommit),
):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        tile = pages.update_tile(
            db,
            username,
            tile_id=payload.tile_id,
            name=payload.name,
            hyperlink=payload.hyperlink,
            onclick=payload.onclick,
            icon=payload.icon,
            color=payload.color,
        )
        return dto.TileDTO.model_validate(tile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/tiles/{tile_id}")
def delete_tile_endpoint(
    request: Request,
    tile_id: int,
    db: Session = Depends(get_db_autocommit),
):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        pages.delete_tile(db, username, tile_id=tile_id)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ----- Rows management -----
class RowCreateIn(BaseModel):
    row_name: str
    row_type: Optional[int] = 0
    row_index: Optional[int] = 0
    page_id: Optional[int] = 1


@app.post("/api/rows")
def create_row_endpoint(
    request: Request,
    payload: RowCreateIn,
    db: Session = Depends(get_db_autocommit),
):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        row = pages.create_row(
            db,
            username,
            row_name=payload.row_name,
            row_type=payload.row_type or 0,
            row_index=payload.row_index or 0,
            page_id=payload.page_id or 1,
        )
        return {
            "row_id": row.row_id,
            "row_name": row.row_name,
            "row_type": row.row_type,
            "row_index": row.row_index,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/rows/{row_id}")
def delete_row_endpoint(
    request: Request,
    row_id: int,
    db: Session = Depends(get_db_autocommit),
):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        pages.delete_row(db, username, row_id=row_id)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ----- Icon upload -----
@app.post("/api/icons/upload")
async def upload_icon(
    request: Request,
    db: Session = Depends(get_db_autocommit),
):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    form = await request.form()
    file = form.get("file")
    if not file:
        raise HTTPException(status_code=400, detail="file is required")
    filename = form.get("filename") or getattr(file, "filename", None) or "icon.bin"
    content_type = getattr(file, "content_type", None) or "application/octet-stream"
    data = await file.read()
    pages.save_icon(db, filename=filename, content_type=content_type, data=data)
    return {"status": "ok", "filename": filename}


@app.post("/api/tiles/order")
def set_tile_order_endpoint(
    request: Request,
    payload: dto.RowTileOrderIn,
    db: Session = Depends(get_db_autocommit),
):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        pages.set_row_tile_index(
            db,
            username,
            row_id=payload.row_id,
            tile_id=payload.tile_id,
            tile_index=payload.tile_index,
        )
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        ssl_certfile="localhost+3.pem",
        ssl_keyfile="localhost+3-key.pem",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
