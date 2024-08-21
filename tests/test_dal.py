import pytest
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from database.models import User, Tweet, Media, Like, Follower

from database.func import UserDAL, TweetDAL, MediaDAL, LikeDAL, FollowerDAL

from tests.funcs import (
    fill_test_data,
    get_user_from_db,
    create_tests_users,
    get_user_info_from_db,
    get_media_from_db,
)


DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(
    engine=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.mark.asyncio
async def test_get_user_info():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    # Создание асинхронного движка SQLAlchemy
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)

    # Создание асинхронной сессии SQLAlchemy
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )
    fill_test_data(DATABASE_URL)

    async with async_session() as session:
        try:
            user_dal = UserDAL(session)

            # Получение данных через DAL
            user_info = await user_dal.get_user_by_api_key(api_key="111")

            # Получение данных напрямую из базы
            expected_data = await get_user_from_db(session, api_key="111")

            # Проверка соответствия
            assert {
                "user": {"api_key": user_info.api_key, "name": user_info.name}
            } == expected_data
        finally:
            # Очистка данных в таблицах
            await session.execute(text("DELETE FROM tweets"))
            await session.execute(text("DELETE FROM users"))
            await session.execute(text("DELETE FROM likes"))
            await session.execute(text("DELETE FROM followers"))
            await session.execute(text("DELETE FROM media"))
            await session.commit()


@pytest.mark.asyncio
async def test_get_user_by_api_key():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    # Создание асинхронного движка SQLAlchemy
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)

    # Создание асинхронной сессии SQLAlchemy
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    create_tests_users(DATABASE_URL)

    async with async_session() as session:
        try:
            user_dal = UserDAL(session)
            user = await user_dal.get_user_by_api_key("111")
            user1 = await get_user_info_from_db(session, api_key="111")
            # Проверка соответствия
            assert {
                "user_id": user.user_id,
                "api_key": user.api_key,
                "name": user.name,
            } == user1

        finally:
            # Очистка данных в таблицах
            await session.execute(text("DELETE FROM tweets"))
            await session.execute(text("DELETE FROM users"))
            await session.execute(text("DELETE FROM likes"))
            await session.execute(text("DELETE FROM followers"))
            await session.execute(text("DELETE FROM media"))
            await session.commit()


@pytest.mark.asyncio
async def test_create_media_record():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    # Создание асинхронного движка SQLAlchemy
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)

    # Создание асинхронной сессии SQLAlchemy
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            media_dal = MediaDAL(session)
            yadisk_link = "http://example.com/media1.jpg"
            media_path = "path/to/media1.jpg"
            media = await media_dal.create_media_record(yadisk_link, media_path)
            media1 = await get_media_from_db(session)
            assert {
                "media_id": media.media_id,
                "media_url": media.media_url,
                "media_path": media.media_path,
                "tweet_id": media.tweet_id,
            } == media1

        finally:
            # Очистка данных в таблицах
            await session.execute(text("DELETE FROM tweets"))
            await session.execute(text("DELETE FROM users"))
            await session.execute(text("DELETE FROM likes"))
            await session.execute(text("DELETE FROM followers"))
            await session.execute(text("DELETE FROM media"))
            await session.commit()


@pytest.mark.asyncio
async def test_update_media_ids():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            media_dal = MediaDAL(session)

            # Создание тестовых записей в базе данных
            media1 = Media(
                media_url="http://example.com/media1.jpg",
                media_path="path/to/media1.jpg",
            )
            media2 = Media(
                media_url="http://example.com/media2.jpg",
                media_path="path/to/media2.jpg",
            )
            session.add(media1)
            session.add(media2)
            await session.commit()

            # Сохранение media_id для тестов
            media_ids = [media1.media_id, media2.media_id]
            tweet_id = 1

            # Вызов тестируемого метода
            await media_dal.update_media_ids(tweet_id, media_ids)

            # Проверка обновления
            updated_media = await session.execute(
                select(Media).where(Media.media_id.in_(media_ids))
            )
            updated_media = updated_media.scalars().all()

            assert all(media.tweet_id == tweet_id for media in updated_media)

        finally:
            await session.execute(text("DELETE FROM media"))
            await session.commit()


@pytest.mark.asyncio
async def test_get_media_urls_by_tweet_id():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            media_dal = MediaDAL(session)

            # Создание тестовых записей в базе данных
            tweet_id = 1
            media1 = Media(
                media_url="http://example.com/media1.jpg",
                media_path="path/to/media1.jpg",
                tweet_id=tweet_id,
            )
            media2 = Media(
                media_url="http://example.com/media2.jpg",
                media_path="path/to/media2.jpg",
                tweet_id=tweet_id,
            )
            session.add(media1)
            session.add(media2)
            await session.commit()

            # Вызов тестируемого метода
            media_urls = await media_dal.get_media_urls_by_tweet_id(tweet_id)

            # Проверка результатов
            expected_urls = ["path/to/media1.jpg", "path/to/media2.jpg"]
            assert media_urls == expected_urls

        finally:
            await session.execute(text("DELETE FROM media"))
            await session.commit()


@pytest.mark.asyncio
async def test_save_tweet_to_database():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            tweet_dal = TweetDAL(session)
            user_id = 1
            tweet_data = "This is a test tweet."

            # Сохранение твита
            tweet_id = await tweet_dal.save_tweet_to_database(user_id, tweet_data)

            # Проверка, что твит был сохранен
            result = await session.execute(
                select(Tweet).where(Tweet.tweet_id == tweet_id)
            )
            saved_tweet = result.scalar_one()
            assert saved_tweet.user_id == user_id
            assert saved_tweet.content == tweet_data

        finally:
            await session.execute(text("DELETE FROM tweets"))
            await session.commit()


@pytest.mark.asyncio
async def test_update_tweet():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            tweet_dal = TweetDAL(session)

            # Создание тестового твита
            tweet = Tweet(user_id=1, content="Original tweet content")
            session.add(tweet)
            await session.commit()

            # Сохранение tweet_id для теста
            tweet_id = tweet.tweet_id
            new_tweet_data = "Updated tweet content"

            # Обновление твита
            await tweet_dal.update_tweet(tweet_id, new_tweet_data)

            # Проверка обновления
            result = await session.execute(
                select(Tweet).where(Tweet.tweet_id == tweet_id)
            )
            updated_tweet = result.scalar_one()
            assert updated_tweet.content == new_tweet_data

        finally:
            await session.execute(text("DELETE FROM tweets"))
            await session.commit()


@pytest.mark.asyncio
async def test_delete_tweet():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            tweet_dal = TweetDAL(session)

            # Создание тестового твита
            tweet = Tweet(user_id=1, content="Tweet to be deleted")
            session.add(tweet)
            await session.commit()

            # Удаление твита
            await tweet_dal.delete_tweet(tweet)

            # Проверка, что твит был удален
            result = await session.execute(
                select(Tweet).where(Tweet.tweet_id == tweet.tweet_id)
            )
            deleted_tweet = result.scalar_one_or_none()
            assert deleted_tweet is None

        finally:
            await session.execute(text("DELETE FROM tweets"))
            await session.commit()


@pytest.mark.asyncio
async def test_get_tweet_by_id():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            tweet_dal = TweetDAL(session)

            # Создание тестового твита
            tweet = Tweet(user_id=1, content="Tweet to be retrieved")
            session.add(tweet)
            await session.commit()

            # Получение твита по идентификатору
            retrieved_tweet = await tweet_dal.get_tweet_by_id(tweet.tweet_id)

            # Проверка данных твита
            assert retrieved_tweet.tweet_id == tweet.tweet_id
            assert retrieved_tweet.content == tweet.content

        finally:
            await session.execute(text("DELETE FROM tweets"))
            await session.commit()


@pytest.mark.asyncio
async def test_get_feed_tweets():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            tweet_dal = TweetDAL(session)

            # Создание тестовых данных
            user1 = User(api_key="user1_api_key", name="User 1")
            user2 = User(api_key="user2_api_key", name="User 2")
            session.add_all([user1, user2])
            await session.commit()

            follower = Follower(follower_id=user1.user_id, followee_id=user2.user_id)
            session.add(follower)
            await session.commit()

            tweet1 = Tweet(user_id=user2.user_id, content="Tweet 1")
            tweet2 = Tweet(user_id=user2.user_id, content="Tweet 2")
            session.add_all([tweet1, tweet2])
            await session.commit()

            # Получение фида твитов
            feed_tweets = await tweet_dal.get_feed_tweets(user1.user_id)

            # Проверка, что фид содержит твиты user2
            assert len(feed_tweets["tweets"]) == 2
            assert feed_tweets["tweets"][0]["user_name"] == "User 2"
            assert feed_tweets["tweets"][1]["user_name"] == "User 2"

        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.execute(text("DELETE FROM followers"))
            await session.execute(text("DELETE FROM tweets"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()


@pytest.mark.asyncio
async def test_create_like():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            like_dal = LikeDAL(session)

            # Создание тестовых данных
            user = User(api_key="user_api_key", name="User")
            tweet = Tweet(user_id=1, content="Tweet")
            session.add_all([user, tweet])
            await session.commit()

            # Создание лайка
            await like_dal.create_like(user.user_id, tweet.tweet_id)

            # Проверка лайка
            like = await session.execute(
                text(
                    "SELECT * FROM likes WHERE user_id = :user_id AND tweet_id = :tweet_id"
                ),
                {"user_id": user.user_id, "tweet_id": tweet.tweet_id},
            )
            like_result = like.fetchone()
            assert like_result is not None

        finally:
            await session.rollback()
            await session.execute(text("DELETE FROM likes"))
            await session.execute(text("DELETE FROM tweets"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()


@pytest.mark.asyncio
async def test_delete_like():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            like_dal = LikeDAL(session)

            # Создание тестовых данных
            user = User(api_key="user_api_key", name="User")
            session.add(user)
            await session.flush()  # Сохраняем user и получаем user_id

            tweet = Tweet(user_id=user.user_id, content="Tweet")
            session.add(tweet)
            await session.flush()  # Сохраняем tweet и получаем tweet_id

            like = Like(user_id=user.user_id, tweet_id=tweet.tweet_id)
            session.add(like)
            await session.commit()

            # Удаление лайка
            await like_dal.delete_like(user.user_id, tweet.tweet_id)

            # Проверка лайка
            like = await session.execute(
                text(
                    "SELECT * FROM likes WHERE user_id = :user_id AND tweet_id = :tweet_id"
                ),
                {"user_id": user.user_id, "tweet_id": tweet.tweet_id},
            )
            like_result = like.fetchone()
            assert like_result is None

        finally:
            await session.rollback()
            await session.execute(text("DELETE FROM likes"))
            await session.execute(text("DELETE FROM tweets"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()


@pytest.mark.asyncio
async def test_create_follower():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            follower_dal = FollowerDAL(session)

            # Создание тестовых данных
            user1 = User(api_key="user1_api_key", name="User 1")
            user2 = User(api_key="user2_api_key", name="User 2")
            session.add_all([user1, user2])
            await session.commit()

            # Создание подписки
            await follower_dal.create_follower(user1.user_id, user2.user_id)

            # Проверка подписки
            follower = await session.execute(
                text(
                    "SELECT * FROM followers WHERE follower_id = :follower_id AND followee_id = :followee_id"
                ),
                {"follower_id": user1.user_id, "followee_id": user2.user_id},
            )
            follower_result = follower.fetchone()
            assert follower_result is not None

        finally:
            await session.rollback()
            await session.execute(text("DELETE FROM followers"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()


@pytest.mark.asyncio
async def test_delete_follower():
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=True,
    )

    async with async_session() as session:
        try:
            follower_dal = FollowerDAL(session)

            # Create test data
            user1 = User(api_key="user1_api_key", name="User 1")
            user2 = User(api_key="user2_api_key", name="User 2")
            session.add_all([user1, user2])
            await session.commit()

            # Retrieve user IDs after commit
            user1_id = (
                await session.execute(
                    select(User.user_id).filter_by(api_key="user1_api_key")
                )
            ).scalar_one()
            user2_id = (
                await session.execute(
                    select(User.user_id).filter_by(api_key="user2_api_key")
                )
            ).scalar_one()

            # Create follower relationship
            follower = Follower(follower_id=user1_id, followee_id=user2_id)
            session.add(follower)
            await session.commit()

            # Delete follower
            await follower_dal.delete_follower(user1_id, user2_id)

            # Verify follower deletion
            follower = await session.execute(
                text(
                    "SELECT * FROM followers WHERE follower_id = :follower_id AND followee_id = :followee_id"
                ),
                {"follower_id": user1_id, "followee_id": user2_id},
            )
            follower_result = follower.fetchone()
            assert follower_result is None

        finally:
            await session.rollback()
            await session.execute(text("DELETE FROM followers"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()
