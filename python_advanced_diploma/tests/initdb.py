import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from database.models import Base, User
from tests.funcs import fill_test_data

DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine=engine, class_=AsyncSession, expire_on_commit=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session: AsyncSession = async_session()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise
    finally:
        await session.close()


async def create_db_and_tables():
    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def check_db_content():
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User))
            users = result.scalars().all()
            return users


# Функция для тестирования наполненности базы данных
async def db_content():
    users = await check_db_content()
    print(f"Number of tweets in the database: {len(users)}")
    for user in users:
        print(user.api_key)


if __name__ == "__main__":
    asyncio.run(create_db_and_tables())
    # fill_test_data(DATABASE_URL)
    # asyncio.run(db_content())
