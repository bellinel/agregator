import kb
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, select, Column

DATABASE_URL = "sqlite+aiosqlite:///channels.db"
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
        query = select(Channel).where(Channel.channel_id == channel_id)
        result = await session.execute(query)
        if result.scalars().first():
            return 'Такой канал уже есть'
        else:
            try:
                channel = Channel(channel_name=channel_name, channel_id=channel_id)
                session.add(channel)
                await session.commit()
                await session.refresh(channel)
                
            except:
                return "Канал не получилось добавить"
        

async def remove_channel(channel_id: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Channel).where(Channel.channel_id == channel_id)
        )
        channel = result.scalar_one_or_none()
        if channel:
            await session.delete(channel)
            await session.commit()
            print(f"Канал {channel_id} удалён из базы.")
        else:
            print(f"Канал {channel_id} не найден в базе.")


async def get_all_channels():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Channel))
        channels = result.scalars().all()
        return channels
    

async def add_filter(filter_text):
    async with AsyncSessionLocal() as session:
        query = select(Filter).where(Filter.filter_text == filter_text)
        result = await session.execute(query)
        if result.scalars().first():
            return True
        else:
            filter = Filter(filter_text=filter_text)
            session.add(filter)
            await session.commit()
            await session.refresh(filter)

async def get_all_filters():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Filter))
        filters = result.scalars().all()
        return filters
    
async def remove_filter(id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Filter).where(Filter.id == id)
        )
        filter = result.scalar_one_or_none()
        if filter:
            await session.delete(filter)
            await session.commit()
