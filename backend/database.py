from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base   # ПРо створення data transit object для транзиту даних
from sqlalchemy.orm import sessionmaker, relationship   #  Ядро. Дані переносити з таблиці в модель або навпаки. 
# sessionmaker - сеанси підключення до БД

SQLALCHEMY_DATABASE_URL = "sqlite:///./blockchain.db"  #Connection string для підключення до бази даних. Не потребує установки сервера.

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}     # Перевірка схожості потоків
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind = engine)  #flush - автоочищення, engine -
Base = declarative_base()  # Базовий клас моделей

# Треба описати самі моделі

class DBUser(Base):
    ''' Модель користувача (власника криптогаманця)'''
    __tablename__ = "users"  # Назва таблиці в базі даних

    id = Column(Integer, primary_key=True, index=True)  
    username = Column(String, unique=True, index=True)  
    address = Column(String, unique=True, index=True)  # Унікальна адреса гаманця
    private_key = Column(String, unique=True)          # Унікальний приватний ключ для підпису транзакцій
    balance = Column(Float, default=100.0)

    my_contacts = relationship("DBUserContacts", back_populates="owner")  # Для контактів зв'язок


class DBBlock(Base):
    ''' Модель блоку транзакцій'''
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)  
    index = Column(Integer, unique=True)
    timestamp=Column(Float)
    proof=Column(Integer)
    previous_hash = Column(String)  
    hash = Column(String, unique=True)
    
    transactions = relationship("DBTransaction", back_populates="block")

class DBTransaction(Base):
    ''' Модель окремої транзакції'''
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String) # Тут буде адреса гаманця відправника
    recipient = Column(String) # Тут буде адреса гаманця отримувача
    amount = Column(Float) # Сума транзакції
    signature = Column(String)
    block_id = Column(Integer, ForeignKey("blocks.id")) # Зовнішній ключ для зв'язку з блоком
    block = relationship("DBBlock", back_populates="transactions") # Встановлення зв'язку з блоком


class DBUserContacts(Base):
    ''' Модель контактів юзера '''
    __tablename__ = "userContacts"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id")) # Юзер, який додав контакт до себе
    nickname = Column(String)                          # Як він підписав контакт (мама, брат)
    address = Column(String)                           

    owner = relationship("DBUser", back_populates="my_contacts")


# Base.metadata.create_all(bind=engine)  # Створення таблиць в базі даних на основі описаних моделей

# Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("бд успішно створена")