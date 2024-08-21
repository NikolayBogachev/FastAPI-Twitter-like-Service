import asyncio
from datetime import datetime
import os
import aiofiles
from fastapi import HTTPException
from sqlalchemy import select, update, delete, desc, func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
import sqlalchemy

from database.db import engine, async_session
from database.models import Base, User, Tweet, Media, Like, Follower


async def wait_for_db():

    while True:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

                break
        except Exception as e:

            await asyncio.sleep(5)  # Подождите 5 секунд перед повторной попыткой


async def check_tables_exist() -> bool:
    async with engine.connect() as conn:
        def sync_inspect(connection):
            inspector = sqlalchemy.inspect(connection)
            tables = inspector.get_table_names()
            return "diploma_db" in tables

        return await conn.run_sync(sync_inspect)


# Функция для заполнения тестовыми данными
async def fill_data():

    async with AsyncSession(engine) as session:
        # Удаляем все записи
        await session.execute(delete(Like))
        await session.execute(delete(Tweet))
        await session.execute(delete(User))
        await session.execute(delete(Follower))
        await session.execute(delete(Media))
        await session.commit()

        # Вставляем пользователей
        users = [User(api_key="111", name="User11"),
                 User(api_key="222", name="User22"),
                 User(api_key="333", name="User32"),
                 User(api_key="test", name="TestUser")]
        session.add_all(users)
        await session.commit()

        # Получаем идентификаторы пользователей
        result = await session.execute(select(User.user_id))
        user_ids = result.scalars().all()

        # Вставляем твиты
        tweets = [
            Tweet(user_id=user_ids[0], content="First tweet by User1", timestamp=datetime.now()),
            Tweet(user_id=user_ids[0], content="Second tweet by User1", timestamp=datetime.now()),
            Tweet(user_id=user_ids[1], content="First tweet by User2", timestamp=datetime.now()),
            Tweet(user_id=user_ids[1], content="Second tweet by User2", timestamp=datetime.now()),
            Tweet(user_id=user_ids[2], content="First tweet by User3", timestamp=datetime.now()),
            Tweet(user_id=user_ids[2], content="Second tweet by User3", timestamp=datetime.now()),
        ]
        session.add_all(tweets)
        await session.commit()

        # Получаем идентификаторы твитов
        result = await session.execute(select(Tweet.tweet_id))
        tweet_ids = result.scalars().all()

        # Вставляем лайки
        likes = [
            Like(user_id=user_ids[0], tweet_id=tweet_ids[0]),
            Like(user_id=user_ids[0], tweet_id=tweet_ids[1]),
            Like(user_id=user_ids[1], tweet_id=tweet_ids[2]),
            Like(user_id=user_ids[1], tweet_id=tweet_ids[3]),
            Like(user_id=user_ids[2], tweet_id=tweet_ids[4]),
            Like(user_id=user_ids[2], tweet_id=tweet_ids[5]),
            Like(user_id=user_ids[1], tweet_id=tweet_ids[0]),  # Лайк на твит другого пользователя
            Like(user_id=user_ids[2], tweet_id=tweet_ids[1]),  # Лайк на твит другого пользователя
        ]
        session.add_all(likes)
        await session.commit()

        # Вставляем подписки
        followers = [
            Follower(follower_id=user_ids[0], followee_id=user_ids[1]),  # User1 follows User2
            Follower(follower_id=user_ids[1], followee_id=user_ids[2]),  # User2 follows User3
            Follower(follower_id=user_ids[2], followee_id=user_ids[0]),  # User3 follows User1
        ]
        session.add_all(followers)
        await session.commit()

        # Вставляем медиа
        media = [
            Media(media_url="http://example.com/media1.jpg", media_path="path/to/media1.jpg", tweet_id=tweet_ids[0]),
            Media(media_url="http://example.com/media2.jpg", media_path="path/to/media2.jpg", tweet_id=tweet_ids[1]),
            Media(media_url="http://example.com/media3.jpg", media_path="path/to/media3.jpg", tweet_id=tweet_ids[2]),
        ]
        session.add_all(media)
        await session.commit()

    await engine.dispose()


async def create_tables():
    async with async_session() as session:
        async with session.begin():  # Начало транзакции
            # Выполняем запрос для получения списка таблиц
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            result = await session.execute(text(query))
            existing_tables = result.fetchall()

            # Извлекаем имена таблиц
            table_names = [row[0] for row in existing_tables]

            if 'users' not in table_names:

                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                await fill_data()


async def create_and_fill_tables():
    async with async_session() as session:
        async with session.begin():

            query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            result = await session.execute(text(query))
            existing_tables = result.fetchall()
            table_names = [row[0] for row in existing_tables]

            if 'users' not in table_names:

                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                await fill_data()


class UserDAL:
    """
    Класс для работы с пользователями в базе данных.

    Аргументы:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для взаимодействия с базой данных.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_info(self, user_id: int) -> dict:
        """
        Получает детализированную информацию о пользователе, включая его подписчиков и подписки.

        Аргументы:
            user_id (int): Идентификатор пользователя.

        Возвращает:
            dict: Словарь с информацией о пользователе, его подписчиках и подписках.

        Исключения:
            HTTPException: Если пользователь не найден или возникает ошибка базы данных.
        """
        try:
            query = (
                select(User)
                .options(
                    joinedload(User.followers).joinedload(Follower.follower),
                    joinedload(User.followees).joinedload(Follower.followee),
                )
                .where(User.user_id == user_id)
            )
            result = await self.session.execute(query)
            user = result.unique().scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="Пользователь не найден")

            user_info = {
                "result": True,
                "user": {
                    "id": user.user_id,
                    "name": user.name,
                    "followers": [
                        {
                            "id": follower.follower.user_id,
                            "name": follower.follower.name,
                        }
                        for follower in user.followers
                    ],
                    "following": [
                        {
                            "id": followee.followee.user_id,
                            "name": followee.followee.name,
                        }
                        for followee in user.followees
                    ],
                },
            }

            return user_info

        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка получения информации о пользователе: {str(e)}",
            )

    async def get_user_by_api_key(self, api_key: str) -> User:
        """
        Получает пользователя из базы данных по его api_key.

        Аргументы:
            api_key (str): API ключ пользователя.

        Возвращает:
            User: Объект пользователя.

        Исключения:
            HTTPException: Если пользователь не найден или возникает ошибка базы данных.
        """
        try:
            result = await self.session.execute(
                select(User).where(User.api_key == api_key)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=401, detail="Invalid API key")
            return user
        except SQLAlchemyError:
            raise HTTPException(
                status_code=500, detail="Ошибка получения пользователя по API ключу"
            )


class TweetDAL:
    """
    Класс для работы с твитами в базе данных.

    Аргументы:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для взаимодействия с базой данных.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_tweet_to_database(self, user_id: int, tweet_data: str) -> int:
        """
        Сохраняет твит в базу данных.

        Аргументы:
            user_id (int): Идентификатор пользователя, создающего твит.
            tweet_data (str): Текст твита.

        Возвращает:
            int: Идентификатор сохраненного твита.

        Исключения:
            HTTPException: Если возникает ошибка базы данных при сохранении твита.
        """
        tweet = Tweet(user_id=user_id, content=tweet_data)

        try:
            self.session.add(tweet)
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise HTTPException(
                status_code=500, detail="Ошибка сохранения твита в базе данных"
            )

        return tweet.tweet_id

    async def update_tweet(self, tweet_id: int, tweet_data: str):
        """
        Обновляет существующий твит в базе данных.

        Аргументы:
            tweet_id (int): Идентификатор твита для обновления.
            tweet_data (str): Новый текст твита.

        Исключения:
            HTTPException: Если твит не найден или возникает ошибка базы данных.
        """
        try:
            await self.session.execute(
                update(Tweet)
                .where(Tweet.tweet_id == tweet_id)
                .values(content=tweet_data)
            )
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise HTTPException(
                status_code=500, detail="Ошибка обновления твита в базе данных"
            )

    async def delete_tweet(self, tweet):
        """
        Удаляет твит из базы данных.

        Аргументы:
            tweet (Tweet): Объект твита для удаления.

        Исключения:
            HTTPException: Если возникает ошибка базы данных при удалении твита.
        """
        try:
            await self.session.delete(tweet)
            await self.session.commit()
            print(f"Tweet с ID {tweet.tweet_id} был успешно удален.")
        except SQLAlchemyError:
            await self.session.rollback()
            raise HTTPException(
                status_code=500, detail="Ошибка удаления твита из базы данных"
            )

    async def get_tweet_by_id(self, tweet_id: int) -> Tweet:
        """
        Получает твит по его идентификатору.

        Аргументы:
            tweet_id (int): Идентификатор твита.

        Возвращает:
            Tweet: Объект твита.

        Исключения:
            HTTPException: Если твит не найден или возникает ошибка базы данных.
        """
        try:
            result = await self.session.execute(
                select(Tweet).where(Tweet.tweet_id == tweet_id)
            )
            tweet = result.scalar_one()
            return tweet
        except SQLAlchemyError:
            await self.session.rollback()
            raise HTTPException(
                status_code=500, detail="Ошибка получения твита из базы данных"
            )

    async def get_feed_tweets(self, user_id: int) -> dict:
        """
        Получает ленту твитов для указанного пользователя, включая информацию о лайках и медиафайлах.

        Аргументы:
            user_id (int): Идентификатор пользователя.

        Возвращает:
            dict: Словарь с лентой твитов.

        Исключения:
            HTTPException: Если возникает ошибка базы данных при получении ленты твитов.
        """
        try:

            # Основной запрос для получения твитов
            query = (
                select(
                    Tweet.tweet_id,
                    Tweet.content,
                    Tweet.user_id,
                    User.name.label("user_name"),
                    func.coalesce(Media.media_url, "").label("media_url"),
                    func.count(Like.like_id).label("likes_count"),
                )
                .join(User, Tweet.user_id == User.user_id)
                .outerjoin(Media, Tweet.tweet_id == Media.tweet_id)
                .outerjoin(Like, Tweet.tweet_id == Like.tweet_id)
                .group_by(Tweet.tweet_id, Tweet.content, Tweet.user_id, User.name, Media.media_url)
                .order_by(desc(func.count(Like.like_id)))
            )

            result = await self.session.execute(query)
            tweets = result.all()

            tweets_list = []
            for tweet in tweets:
                # Подготовка данных твита
                tweet_info = {
                    "id": tweet.tweet_id,
                    "content": tweet.content,
                    "author": {
                        "id": tweet.user_id,
                        "name": tweet.user_name,
                    },
                    "attachments": [tweet.media_url] if tweet.media_url else [],
                    "likes": [],
                }

                # Запрос для получения лайков твита
                likes_query = (
                    select(Like.user_id, User.name)
                    .join(User, Like.user_id == User.user_id)
                    .where(Like.tweet_id == tweet.tweet_id)
                )
                likes_result = await self.session.execute(likes_query)
                likes = likes_result.all()

                # Подготовка данных о лайках
                tweet_info["likes"] = [
                    {"user_id": like.user_id, "name": like.name} for like in likes
                ]

                tweets_list.append(tweet_info)
                print(tweet.media_url)
            return {"result": True, "tweets": tweets_list}

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


class MediaDAL:
    """
    Класс для работы с медиафайлами в базе данных.

    Аргументы:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для взаимодействия с базой данных.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    async def delete_file(file_path: str):
        """
        Удаляет файл по указанному пути асинхронно.

        :param file_path: Путь к файлу, который нужно удалить.
        :return: Строка с результатом удаления.
        """
        try:
            # Проверяем, существует ли файл
            if os.path.exists(file_path):
                # Удаляем файл
                os.remove(file_path)
                return f"File '{file_path}' deleted successfully."
            else:
                return f"File '{file_path}' does not exist."
        except Exception as e:
            # Ловим любые ошибки и возвращаем их
            return f"An error occurred: {str(e)}"

    async def create_media_record(self, yadisk_link: str, media_path: str) -> Media:
        """
        Создает запись медиафайла в базе данных.

        Аргументы:
            yadisk_link (str): Ссылка на медиафайл в Яндекс.Диске.
            media_path (str): Путь к медиафайлу.

        Возвращает:
            Media: Объект созданного медиафайла.

        Исключения:
            HTTPException: Если возникает ошибка базы данных при создании записи медиафайла.
        """
        new_media = Media(media_url=yadisk_link, media_path=media_path)
        self.session.add(new_media)
        try:
            await self.session.commit()
            await self.session.refresh(new_media)
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        return new_media

    async def update_media_ids(self, tweet_id: int, tweet_media_ids: list[int]):
        """
        Обновляет идентификаторы медиафайлов для указанного твита.

        Аргументы:
            tweet_id (int): Идентификатор твита.
            tweet_media_ids (list[int]): Список идентификаторов медиафайлов.

        Исключения:
            HTTPException: Если возникает ошибка базы данных при обновлении идентификаторов медиафайлов.
        """
        try:
            stmt = (
                update(Media)
                .where(Media.media_id.in_(tweet_media_ids))
                .values(tweet_id=tweet_id)
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            )

    async def get_media_urls_by_tweet_id(self, tweet_id: int) -> str:
        """
        Получает список URL медиафайлов по идентификатору твита.

        Аргументы:
            tweet_id (int): Идентификатор твита.

        Возвращает:
            str | None: Путь к медиафайлу, или None, если медиафайл не найден.

        Исключения:
            HTTPException: Если возникает ошибка базы данных при получении URL медиафайлов.
        """
        try:
            query = select(Media.media_path).where(Media.tweet_id == tweet_id)
            result = await self.session.execute(query)
            media_path = result.scalar()  # Получаем единственное значение
            return media_path  # Возвращаем путь или None
        except SQLAlchemyError:
            await self.session.rollback()
            raise HTTPException(
                status_code=500,
                detail="Ошибка получения URL медиафайлов для твита из базы данных",
            )


class LikeDAL:
    """
    Класс для работы с лайками в базе данных.

    Аргументы:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для взаимодействия с базой данных.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_like(self, user_id: int, tweet_id: int) -> None:
        """
        Создает лайк в базе данных.

        Аргументы:
            user_id (int): Идентификатор пользователя, который ставит лайк.
            tweet_id (int): Идентификатор твита, которому ставится лайк.

        Исключения:
            HTTPException: Если возникает ошибка базы данных при создании лайка.
        """
        new_like = Like(user_id=user_id, tweet_id=tweet_id)
        self.session.add(new_like)
        await self.session.commit()

    async def delete_like(self, user_id: int, tweet_id: int) -> None:
        """
        Удаляет лайк из базы данных.

        Аргументы:
            user_id (int): Идентификатор пользователя, который удаляет лайк.
            tweet_id (int): Идентификатор твита, у которого удаляется лайк.

        Исключения:
            HTTPException: Если возникает ошибка базы данных при удалении лайка.
        """
        await self.session.execute(
            delete(Like).where(Like.user_id == user_id, Like.tweet_id == tweet_id)
        )
        await self.session.commit()


class FollowerDAL:
    """
    Класс для работы с подписками в базе данных.

    Аргументы:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для взаимодействия с базой данных.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_follower(self, follower_id: int, followee_id: int):
        """
        Создает подписку в базе данных.

        Аргументы:
            follower_id (int): Идентификатор пользователя, который подписывается.
            followee_id (int): Идентификатор пользователя, на которого подписываются.

        Возвращает:
            Follower: Объект созданной подписки.

        Исключения:
            HTTPException: Если возникает ошибка базы данных при создании подписки.
        """
        new_follower = Follower(follower_id=follower_id, followee_id=followee_id)
        self.session.add(new_follower)
        await self.session.commit()
        return new_follower

    async def delete_follower(self, follower_id: int, followee_id: int):
        """
        Удаляет подписку из базы данных.

        Аргументы:
            follower_id (int): Идентификатор пользователя, который подписывается.
            followee_id (int): Идентификатор пользователя, на которого подписываются.

        Возвращает:
            bool: True, если подписка успешно удалена, иначе False.

        Исключения:
            HTTPException: Если возникает ошибка базы данных при удалении подписки.
        """
        result = await self.session.execute(
            Follower.__table__.delete().where(
                (Follower.follower_id == follower_id)
                & (Follower.followee_id == followee_id)
            )
        )
        await self.session.commit()
        return result.rowcount > 0
