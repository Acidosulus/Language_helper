from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# --- FastAPI ---
app = FastAPI()
# Секретный ключ в проде должен быть из env. Здесь для локалки.
app.add_middleware(SessionMiddleware, secret_key="super-secret-key", https_only=False)

# CORS — только для dev, в проде указать реальный фронтенд домен
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Passlib ---
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# --- SQLAlchemy ---
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# --- Dependencies ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user

# --- API ---
@app.post("/api/register")
def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    hashed_password = pwd_context.hash(password)
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "Регистрация успешна"}

@app.post("/api/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверные данные")
    request.session["user"] = user.username
    return {"message": "Вход выполнен", "user": user.username}

@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Выход выполнен"}

@app.get("/api/secret")
def secret(user: User = Depends(get_current_user)):
    return {"message": f"Секретная страница, {user.username}!"}

# --- Доп. эндпоинт для проверки сессии ---
@app.get("/api/me")
def me(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("user")
    if not username:
        return {"authenticated": False}
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user.username}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)