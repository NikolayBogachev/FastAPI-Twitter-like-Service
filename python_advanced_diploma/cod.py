import asyncio
import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from database.models import User
from main import app  # Импортируем наше FastAPI приложение

from app import TweetRequest
from tests.funcs import fill_test_data

DATABASE_URL = "sqlite+aiosqlite:///./test.db"
# Создание двигателя и сессии
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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
        print(user)

fill_test_data(DATABASE_URL)
asyncio.run(db_content())


@pytest.mark.asyncio
async def test_create_tweet():
    # Заполнение тестовой базы данных
    fill_test_data(DATABASE_URL)
    await db_content()

    # Создание тестового твита
    tweet_request = TweetRequest(
        tweet_data="This is a test tweet"
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Выполняем POST запрос к эндпоинту
        response = await client.post(
            "/api/tweets",
            params={"api-key": "111"},  # Используем правильный API ключ
            json=tweet_request.dict()
        )

        # Вывод ответа для отладки
        print(response.text)
        # Проверка ответа
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"result": True, "tweet_id": 1}



# class UserDAL:
#     def __init__(self, session: AsyncSession):
#         self.session = session
#     async def create_user(self, api_key: str, name: str) -> User:
#         new_user = User(api_key=api_key, name=name)
#         try:
#             self.session.add(new_user)
#             await self.session.commit()
#         except SQLAlchemyError:
#             await self.session.rollback()
#             raise HTTPException(status_code=500, detail="Ошибка создания пользователя")
#         return new_user
#
#
#     async def update_user(self, user_id: int, name: Optional[str] = None, api_key: Optional[str] = None) -> Type[User]:
#         try:
#             user = await self.session.get(User, user_id)
#             if not user:
#                 raise HTTPException(status_code=404, detail="Пользователь не найден")
#
#             if name:
#                 user.name = name
#             if api_key:
#                 user.api_key = api_key
#
#             await self.session.commit()
#         except SQLAlchemyError:
#             await self.session.rollback()
#             raise HTTPException(status_code=500, detail="Ошибка обновления пользователя")
#         return user
#
#
#     async def delete_user(self, user_id: int):
#         try:
#             user = await self.session.get(User, user_id)
#             if not user:
#                 raise HTTPException(status_code=404, detail="Пользователь не найден")
#
#             await self.session.delete(user)
#             await self.session.commit()
#         except SQLAlchemyError:
#             await self.session.rollback()
#             raise HTTPException(status_code=500, detail="Ошибка удаления пользователя")
