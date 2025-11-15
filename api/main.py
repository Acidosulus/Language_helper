from typing import Literal

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from services import models, dto
from services import phrases


# --- FastAPI ---
app = FastAPI()
# Секретный ключ в проде должен быть из env. Здесь для локалки.
app.add_middleware(SessionMiddleware, secret_key="super-secret-key", https_only=False)

# CORS — только для dev, в проде указать реальный фронтенд домен
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Passlib ---
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# --- SQLAlchemy ---
DATABASE_URL = "postgresql+psycopg2://postgres:321@192.168.0.112/language_helper"
engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=True, expire_on_commit=False)
Base = declarative_base()
# Base.metadata.create_all(bind=engine)

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
    db: Session = Depends(get_db_autocommit)
):
    # ищем пользователя, чьё имя указано
    user = db.query(models.User).filter(models.User.name == target_username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # разрешаем менять пароль только себе
    if current_user.name != target_username:
        raise HTTPException(status_code=403, detail="Можно менять только свой пароль")

    # хешируем и обновляем
    user.hashed_password = pwd_context.hash(new_password)
    db.add(user)
    db.commit()

    return {"message": "Пароль успешно обновлён"}

@app.post("/api/register")
def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db_autocommit)):
    if db.query(models.User).filter(models.User.name == username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    hashed_password = pwd_context.hash(password)
    new_user = models.User(name=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "Регистрация успешна"}

@app.post("/api/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
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

# --- Доп. эндпоинт для проверки сессии ---
@app.get("/api/me")
def me(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("user")
    if not username:
        return {"authenticated": False}
    user = db.query(models.User).filter(models.User.name == username).first()
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user.name, "email": "emty@email.dummy"}

@app.get("/api/phrases", response_model=list[dto.PhraseOut])
def phrases_list(request: Request, ready: Literal[0, 1] = 0, db: Session = Depends(get_db)):
    return phrases.get_phrases_by_user(db, request.session.get("user"), ready)

@app.get("/api/phrase/{id_phrase}", response_model=dto.PhraseOut)
def get_phrase_by_id(id_phrase: int, db: Session = Depends(get_db)):
    return phrases.get_phrase_by_id(db, id_phrase)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)