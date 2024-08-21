import pytest

from fastapi import status

from tests.conftest import check_response


@pytest.mark.asyncio
async def test_upload_media(client, setup_database):
    media_file = ("test_image.jpg", b"dummy data", "image/jpeg")

    response = await client.post(
        "/api/medias", headers={"api-key": "111"}, files={"file": media_file}
    )

    # Вывод ответа для отладки
    print(response.text)

    # Проверка ответа
    check_response(
        response, status.HTTP_200_OK, {"result": True, "media_id": 4}
    )  # Замените ID медиа на фактический


@pytest.mark.asyncio
async def test_create_tweet(client, setup_database):
    tweet_request = {"tweet_data": "New tweet by User1"}

    response = await client.post(
        "/api/tweets", headers={"api-key": "111"}, json=tweet_request
    )

    # Вывод ответа для отладки
    print(response.text)

    # Проверка ответа
    check_response(
        response, status.HTTP_200_OK, {"result": True, "tweet_id": 7}
    )  # Замените ID твита на фактический


@pytest.mark.asyncio
async def test_delete_tweet(client, setup_database):
    response = await client.delete("/api/tweets/4", headers={"api-key": "222"})

    # Вывод ответа для отладки
    print(response.text)

    # Проверка ответа
    check_response(response, status.HTTP_200_OK, {"result": True})


@pytest.mark.asyncio
async def test_like_tweet(client, setup_database):
    response = await client.post("/api/tweets/2/likes", headers={"api-key": "222"})

    # Вывод ответа для отладки
    print(response.text)

    # Проверка ответа
    check_response(response, status.HTTP_200_OK, {"result": True})


@pytest.mark.asyncio
async def test_dislike_tweet(client, setup_database):
    response = await client.delete("/api/tweets/1/likes", headers={"api-key": "222"})

    # Вывод ответа для отладки
    print(response.text)

    # Проверка ответа
    check_response(response, status.HTTP_200_OK, {"result": True})


@pytest.mark.asyncio
async def test_follow_user(client, setup_database):
    response = await client.post("/api/users/3/follow", headers={"api-key": "111"})

    # Вывод ответа для отладки
    print(response.text)

    # Проверка ответа
    check_response(response, status.HTTP_200_OK, {"result": True})


@pytest.mark.asyncio
async def test_unfollow_user(client, setup_database):
    response = await client.delete("/api/users/2/follow", headers={"api-key": "111"})

    # Вывод ответа для отладки
    print(response.text)

    # Проверка ответа
    check_response(response, status.HTTP_200_OK, {"result": True})


@pytest.mark.asyncio
async def test_get_user_info(client, setup_database):
    response = await client.get("/api/users/me", headers={"api-key": "111"})

    # Вывод ответа для отладки
    print(response.text)

    # Проверка ответа
    check_response(
        response,
        status.HTTP_200_OK,
        {
            "result": True,
            "user": {
                "followers": [{"id": 3, "name": "User3"}],
                "following": [{"id": 2, "name": "User2"}],
                "id": 1,
                "name": "User1",
            },
        },
    )


@pytest.mark.asyncio
async def test_get_tweets(client, setup_database):
    response = await client.get("/api/tweets", headers={"api-key": "111"})

    # Вывод ответа для отладки
    print(response.text)

    # Исправленный формат ожидаемого ответа
    expected_tweets = {
        "result": True,
        "tweets": [
            {
                "id": 1,
                "content": "First tweet by User1",
                "author": {"id": 1, "name": "User1"},
                "attachments": ["http://example.com/media1.jpg"],
                "likes": [
                    {"user_id": 1, "name": "User1"},
                    {"user_id": 2, "name": "User2"}
                ]
            },
            {
                "id": 2,
                "content": "Second tweet by User1",
                "author": {"id": 1, "name": "User1"},
                "attachments": ["http://example.com/media2.jpg"],
                "likes": [
                    {"user_id": 1, "name": "User1"},
                    {"user_id": 3, "name": "User3"}
                ]
            },
            {
                "id": 3,
                "content": "First tweet by User2",
                "author": {"id": 2, "name": "User2"},
                "attachments": ["http://example.com/media3.jpg"],
                "likes": [{"user_id": 2, "name": "User2"}]
            },
            {
                "id": 4,
                "content": "Second tweet by User2",
                "author": {"id": 2, "name": "User2"},
                "attachments": [],
                "likes": [{"user_id": 2, "name": "User2"}]
            },
            {
                "id": 5,
                "content": "First tweet by User3",
                "author": {"id": 3, "name": "User3"},
                "attachments": [],
                "likes": [{"user_id": 3, "name": "User3"}]
            },
            {
                "id": 6,
                "content": "Second tweet by User3",
                "author": {"id": 3, "name": "User3"},
                "attachments": [],
                "likes": [{"user_id": 3, "name": "User3"}]
            }
        ]
    }

    check_response(response, status.HTTP_200_OK, expected_tweets)
