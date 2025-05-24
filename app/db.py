from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, select

# PostgreSQL подключение (обнови логин/пароль при необходимости)
DATABASE_URL = "postgresql+asyncpg://username:password@localhost:5432/your_database"
async_engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

class Channel(Base):
    __tablename__ = 'channels'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(Integer, nullable=False)
    channel_name: Mapped[str] = mapped_column(String, nullable=True)

class Filter(Base):
    __tablename__ = 'filters'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filter_text: Mapped[str] = mapped_column(String, nullable=False)

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def add_channel(channel_name: str, channel_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Channel).where(Channel.channel_id == channel_id))
        if result.scalars().first():
            return 'Такой канал уже есть'
        try:
            channel = Channel(channel_name=channel_name, channel_id=channel_id)
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
        except:
            return "Канал не получилось добавить"

async def remove_channel(channel_id:
