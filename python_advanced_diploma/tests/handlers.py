import os
from typing import Annotated
from uuid import uuid4

from fastapi import Header, Depends, UploadFile, File, HTTPException, Path, APIRouter, Request
from loguru import logger
import sys
from app.models_pydentic import (
    TweetRequest,
    MediaResponse,
    TweetResponse,
    LikeResponse,
    FollowerResponse,
    UserResponse,
)
from tests.initdb import AsyncSession, get_db
from database.func import UserDAL, TweetDAL, MediaDAL, LikeDAL, FollowerDAL


user_router = APIRouter()
image_router = APIRouter()

logger.remove()  # Удалите все существующие обработчики
logger.add(sys.stdout, level="INFO", format="{time} {level} {message}", backtrace=True, diagnose=True)
logger.add("app.log", rotation="500 MB", level="INFO", format="{time} {level} {message}", backtrace=True, diagnose=True)


@image_router.post(
    "/api/medias",
    response_model=MediaResponse,
    response_model_exclude_unset=True,
)
async def upload_media(
        api_key: Annotated[str | None, Header()],
        file: UploadFile = File(...),
        session: AsyncSession = Depends(get_db),
) -> MediaResponse:
    """
    Эндпоинт для загрузки медиафайла.

    Аргументы:
        api_key (str): API-ключ пользователя.
        file (UploadFile): Загружаемый файл.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        MediaResponse: Ответ с идентификатором медиа и URL файла.
    """
    logger.info("Received upload_media request", extra={"api_key": api_key, "filename": file.filename})
    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    user_dal = UserDAL(session)
    media_dal = MediaDAL(session)

    user = await user_dal.get_user_by_api_key(api_key)
    if user is None:
        logger.error("Invalid API key")
        raise HTTPException(status_code=401, detail="Invalid API key")

    logger.info("User fetched", extra={"user_id": user.user_id})

    try:

        # Директория для сохранения файлов
        UPLOAD_DIRECTORY = "/home/nikolasy/PycharmProjects/python_advanced_diploma/pictures"

        # Убедимся, что директория существует
        if not os.path.exists(UPLOAD_DIRECTORY):
            os.makedirs(UPLOAD_DIRECTORY)

        # Создание уникального имени файла
        file_extension = file.filename.split('.')[-1]
        unique_filename = f"{uuid4()}.{file_extension}"

        # Путь для сохранения файла
        file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

        # Сохранение файла на сервере
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Генерация URL для доступа к файлу
        # Используем localhost и порт 8000
        server_ip = "0.0.0.0"
        server_port = "8000"
        file_url = f"http://{server_ip}:{server_port}/pictures/{unique_filename}"

        # Сохранение записи о медиа в базе данных
        new_media = await media_dal.create_media_record(file_url, file_path)
        logger.info("Media uploaded and record created", extra={"media_id": new_media.media_id})

        return MediaResponse(result=True, media_id=new_media.media_id, url=file_url)

    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        logger.exception("Internal server error")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@user_router.post(
    "/api/tweets",
    response_model=TweetResponse,
)
async def create_tweet(
    tweet_request: TweetRequest,
    api_key: Annotated[str | None, Header()],
    session: AsyncSession = Depends(get_db),
) -> TweetResponse:
    """
    Эндпоинт для создания нового твита.

    Аргументы:
        tweet_request (TweetRequest): Объект запроса на создание твита.
        request (Request): Объект запроса.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        TweetResponse: Результат операции создания твита и его идентификатор.
    """

    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    user_dal = UserDAL(session)
    tweet_dal = TweetDAL(session)
    media_dal = MediaDAL(session)

    try:
        user = await user_dal.get_user_by_api_key(api_key)
        tweet_id = await tweet_dal.save_tweet_to_database(
            user.user_id, tweet_request.tweet_data
        )

        if tweet_request.tweet_media_ids:
            await media_dal.update_media_ids(tweet_id, tweet_request.tweet_media_ids)

        return TweetResponse(result=True, tweet_id=tweet_id)

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@user_router.delete(
    "/api/tweets/{tweet_id}",
    response_model=dict,
)
async def delete_tweet(
    api_key: Annotated[str | None, Header()],
    tweet_id: int = Path(..., description="ID твита для удаления"),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Эндпоинт для удаления твита.

    Аргументы:
        request (Request): Объект запроса.
        tweet_id (int): ID твита для удаления.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        dict: Результат операции.
    """

    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    user_dal = UserDAL(session)
    tweet_dal = TweetDAL(session)
    media_dal = MediaDAL(session)

    try:
        user = await user_dal.get_user_by_api_key(api_key)
        tweet = await tweet_dal.get_tweet_by_id(tweet_id)

        if tweet.user_id != user.user_id:
            raise HTTPException(
                status_code=403, detail="Вы не можете удалить чужой твит"
            )

        media_urls = await media_dal.get_media_urls_by_tweet_id(tweet_id)

        if media_urls:
            await media_dal.delete_file(media_urls)

        await tweet_dal.delete_tweet(tweet)

        return {"result": True}

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@user_router.post(
    "/api/tweets/{tweet_id}/likes",
    response_model=LikeResponse,
)
async def like_tweet(
    tweet_id: int,
    api_key: Annotated[str | None, Header()],
    session: AsyncSession = Depends(get_db),
) -> LikeResponse:
    """
    Эндпоинт для лайка твита.

    Аргументы:
        tweet_id (int): ID твита для лайка.
        request (Request): Объект запроса.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        LikeResponse: Результат операции.
    """

    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    user_dal = UserDAL(session)
    tweet_dal = TweetDAL(session)
    like_dal = LikeDAL(session)

    try:
        user = await user_dal.get_user_by_api_key(api_key)
        tweet = await tweet_dal.get_tweet_by_id(tweet_id)

        if tweet is None:
            raise HTTPException(status_code=404, detail="Tweet not found")

        await like_dal.create_like(user.user_id, tweet_id)

        return LikeResponse(result=True)

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create like: {str(e)}")


@user_router.delete(
    "/api/tweets/{tweet_id}/likes",
    response_model=LikeResponse,
)
async def unlike_tweet(
    tweet_id: int,
    api_key: Annotated[str | None, Header()],
    session: AsyncSession = Depends(get_db),
) -> LikeResponse:
    """
    Эндпоинт для удаления лайка с твита.

    Аргументы:
        tweet_id (int): ID твита для удаления лайка.
        request (Request): Объект запроса.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        LikeResponse: Результат операции.
    """

    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    user_dal = UserDAL(session)
    tweet_dal = TweetDAL(session)
    like_dal = LikeDAL(session)

    try:
        user = await user_dal.get_user_by_api_key(api_key)
        tweet = await tweet_dal.get_tweet_by_id(tweet_id)

        if tweet is None:
            raise HTTPException(status_code=404, detail="Tweet not found")

        await like_dal.delete_like(user.user_id, tweet_id)

        return LikeResponse(result=True)

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete like: {str(e)}")


@user_router.post(
    "/api/users/{followee_id}/follow",
    response_model=FollowerResponse,
)
async def follow_user(
    followee_id: int,
    api_key: Annotated[str | None, Header()],
    session: AsyncSession = Depends(get_db),
) -> FollowerResponse:
    """
    Эндпоинт для подписки на пользователя.

    Аргументы:
        followee_id (int): ID пользователя, на которого подписываются.
        request (Request): Объект запроса.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        FollowerResponse: Результат операции.
    """

    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    user_dal = UserDAL(session)
    follower_dal = FollowerDAL(session)

    try:
        user = await user_dal.get_user_by_api_key(api_key)
        await follower_dal.create_follower(user.user_id, followee_id)

        return FollowerResponse(result=True)

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create follower: {str(e)}"
        )


@user_router.delete(
    "/api/users/{followee_id}/follow",
    response_model=FollowerResponse,
)
async def unfollow_user(
    followee_id: int,
    api_key: Annotated[str | None, Header()],
    session: AsyncSession = Depends(get_db),
) -> FollowerResponse:
    """
    Эндпоинт для отмены подписки на пользователя.

    Аргументы:
        followee_id (int): ID пользователя, с которого снимается подписка.
        request (Request): Объект запроса.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        FollowerResponse: Результат операции.
    """

    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    user_dal = UserDAL(session)
    follower_dal = FollowerDAL(session)

    try:
        user = await user_dal.get_user_by_api_key(api_key)
        await follower_dal.delete_follower(user.user_id, followee_id)

        return FollowerResponse(result=True)

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete follower: {str(e)}"
        )


@user_router.get(
    "/api/users/me",
    response_model=UserResponse,
)
async def get_info_user(
    request: Request,
    api_key: Annotated[str | None, Header()],
    session: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Эндпоинт для получения информации о текущем пользователе.

    Аргументы:
        request (Request): Объект запроса.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        UserResponse: Информация о пользователе.
    """
    logger.info("Received get_info_user request", extra={"api_key": api_key, "headers": dict(request.headers), "client_ip": request.client.host})

    print(api_key)
    if not api_key:
        logger.error("API key is missing")
        raise HTTPException(status_code=401, detail="API key is missing")

    user_dal = UserDAL(session)

    try:
        user = await user_dal.get_user_by_api_key(api_key)
        print(user.name)
        response_data = await user_dal.get_user_info(user.user_id)
        logger.info("User info fetched", extra={"user_id": user.user_id})

        return UserResponse(**response_data)

    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        logger.exception("Internal server error")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@user_router.get(
    "/api/users/{id}",
    response_model=UserResponse,
)
async def get_info_user(
    id: int,
    api_key: Annotated[str | None, Header()],
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Эндпоинт для получения информации о пользователе по его ID.

    Аргументы:
        id (int): ID пользователя.
        request (Request): Объект запроса.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        UserResponse: Информация о пользователе.
    """
    logger.info("Received get_info_user request", extra={"api_key": api_key})
    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    user_dal = UserDAL(session)

    try:
        response_data = await user_dal.get_user_info(id)

        return UserResponse(**response_data)

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@user_router.get(
    "/api/tweets",
    response_model=dict,
)
async def get_tweets(
    api_key: Annotated[str | None, Header()], session: AsyncSession = Depends(get_db)
) -> dict:
    """
    Эндпоинт для получения списка твитов.

    Аргументы:
        request (Request): Объект запроса.
        session (AsyncSession): Асинхронная сессия для работы с базой данных.

    Возвращает:
        dict: Список твитов.
    """

    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    tweet_dal = TweetDAL(session)
    user_dal = UserDAL(session)

    try:
        user = await user_dal.get_user_by_api_key(api_key)
        tweets_list = await tweet_dal.get_feed_tweets(user.user_id)

        return tweets_list

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
