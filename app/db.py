import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, select
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создание движка и сессий
async_engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовая модель
class Base(DeclarativeBase):
    pass

# Модель Channel
class Channel(Base):
    __tablename__ = 'channels'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(String, nullable=False)
    channel_name: Mapped[str] = mapped_column(String, nullable=True)

# Модель Filter
class Filter(Base):
    __tablename__ = 'filters'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filter_text: Mapped[str] = mapped_column(String, nullable=False)

# Инициализация БД
async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Добавить канал
async def add_channel(channel_name: str, channel_id: int):
    async with AsyncSessionLocal() as session:
        query = select(Channel).where(Channel.channel_id == channel_id)
        result = await session.execute(query)
        if result.scalars().first():
            return 'Такой канал уже есть'
        try:
            channel = Channel(channel_name=channel_name, channel_id=channel_id)
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
        except Exception as e:
            return f"Ошибка добавления канала: {e}"

# Удалить канал
async def remove_channel(channel_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Channel).where(Channel.channel_id == channel_id))
        channel = result.scalar_one_or_none()
        if channel:
            await session.delete(channel)
            await session.commit()
            print(f"Канал {channel_id} удалён из базы.")
        else:
            print(f"Канал {channel_id} не найден в базе.")

# Получить все каналы
async def get_all_channels():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Channel))
        return result.scalars().all()

# Добавить фильтр
async def add_filter(filter_text: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Filter).where(Filter.filter_text == filter_text))
        if result.scalars().first():
            return True
        filt = Filter(filter_text=filter_text)
        session.add(filt)
        await session.commit()
        await session.refresh(filt)

# Получить все фильтры
async def get_all_filters():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Filter))
        return result.scalars().all()

# Удалить фильтр
async def remove_filter(id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Filter).where(Filter.id == id))
        filt = result.scalar_one_or_none()
        if filt:
            await session.delete(filt)
            await session.commit()
