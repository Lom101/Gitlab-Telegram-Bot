import os
from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

# Получаем части строки подключения из переменных окружения
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', '12345')
db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('DB_NAME', 'user')

# Формируем строку подключения
DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"

# Создание подключения
engine = create_engine(DATABASE_URL)

# Создание сеанса
Session = sessionmaker(bind=engine)
session = Session()

#создаем базовый класс для моделей
class Base(DeclarativeBase): pass
class Token(Base):
    __tablename__ = 'tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    access_token = Column(Text, nullable=False)
    token_type = Column(Text, nullable=False)
    expires_in = Column(Integer, nullable=False)
    refresh_token = Column(Text, nullable=False)
    created_at = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)

# Создание таблицы
Base.metadata.create_all(engine)
def get_session():
    return Session()

def add_token(access_token, token_type, expires_in, refresh_token, created_at, chat_id):
    session = get_session()
    new_token = Token(
        access_token=access_token,
        token_type=token_type,
        expires_in=expires_in,
        refresh_token=refresh_token,
        created_at=created_at,
        chat_id=chat_id
    )
    session.add(new_token)
    session.commit()
    session.close()

def get_all_tokens():
    session = get_session()
    tokens = session.query(Token).all()
    session.close()
    return tokens

def get_token_by_chat_id(chat_id: str):
    session = get_session()
    tokens = session.query(Token).filter_by(chat_id=chat_id).first()
    session.close()
    return tokens

def update_token(token_id, access_token=None, token_type=None, expires_in=None, refresh_token=None, created_at=None, chat_id=None):
    session = get_session()
    token = session.query(Token).filter_by(id=token_id).first()
    if token:
        if access_token:
            token.access_token = access_token
        if token_type:
            token.token_type = token_type
        if expires_in:
            token.expires_in = expires_in
        if refresh_token:
            token.refresh_token = refresh_token
        if created_at:
            token.created_at = created_at
        if chat_id:
            token.chat_id = chat_id
        session.commit()
    session.close()

def delete_token(token_id):
    session = get_session()
    token = session.query(Token).filter_by(id=token_id).first()
    if token:
        session.delete(token)
        session.commit()
    session.close()

def get_token_id_by_chat_id(chat_id: str):
    """Возвращает id токена по chat_id."""
    session = get_session()
    token = session.query(Token).filter_by(chat_id=chat_id).first()
    session.close()
    if token:
        return token.id
    else:
        return None  # или поднять исключение, если токен не найден