import sqlite3
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def fill_test_data(database_url):
    # Подключаемся к базе данных
    conn = sqlite3.connect(database_url.replace("sqlite+aiosqlite:///", ""))
    cursor = conn.cursor()

    # Удаляем все записи (если требуется)
    cursor.execute("DELETE FROM tweets")
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM likes")
    cursor.execute("DELETE FROM followers")
    cursor.execute("DELETE FROM media")

    # Вставляем пользователей
    users = [("111", "User1"), ("222", "User2"), ("333", "User3")]
    cursor.executemany("INSERT INTO users (api_key, name) VALUES (?, ?)", users)

    # Получаем идентификаторы пользователей
    cursor.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]

    # Вставляем твиты
    tweets = [
        (user_ids[0], "First tweet by User1", datetime.now()),
        (user_ids[0], "Second tweet by User1", datetime.now()),
        (user_ids[1], "First tweet by User2", datetime.now()),
        (user_ids[1], "Second tweet by User2", datetime.now()),
        (user_ids[2], "First tweet by User3", datetime.now()),
        (user_ids[2], "Second tweet by User3", datetime.now()),
    ]
    cursor.executemany(
        "INSERT INTO tweets (user_id, content, timestamp) VALUES (?, ?, ?)", tweets
    )

    # Получаем идентификаторы твитов
    cursor.execute("SELECT tweet_id FROM tweets")
    tweet_ids = [row[0] for row in cursor.fetchall()]

    # Вставляем лайки
    likes = [
        (user_ids[0], tweet_ids[0]),
        (user_ids[0], tweet_ids[1]),
        (user_ids[1], tweet_ids[2]),
        (user_ids[1], tweet_ids[3]),
        (user_ids[2], tweet_ids[4]),
        (user_ids[2], tweet_ids[5]),
        (user_ids[1], tweet_ids[0]),  # Лайк на твит другого пользователя
        (user_ids[2], tweet_ids[1]),  # Лайк на твит другого пользователя
    ]
    cursor.executemany("INSERT INTO likes (user_id, tweet_id) VALUES (?, ?)", likes)

    # Вставляем подписки
    followers = [
        (user_ids[0], user_ids[1]),  # User1 follows User2
        (user_ids[1], user_ids[2]),  # User2 follows User3
        (user_ids[2], user_ids[0]),  # User3 follows User1
    ]
    cursor.executemany(
        "INSERT INTO followers (follower_id, followee_id) VALUES (?, ?)", followers
    )

    # Вставляем медиа
    media = [
        ("http://example.com/media1.jpg", "path/to/media1.jpg", tweet_ids[0]),
        ("http://example.com/media2.jpg", "path/to/media2.jpg", tweet_ids[1]),
        ("http://example.com/media3.jpg", "path/to/media3.jpg", tweet_ids[2]),
    ]
    cursor.executemany(
        "INSERT INTO media (media_url, media_path, tweet_id) VALUES (?, ?, ?)", media
    )

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()


def create_tests_users(database_url):
    # Подключаемся к базе данных
    conn = sqlite3.connect(database_url.replace("sqlite+aiosqlite:///", ""))
    cursor = conn.cursor()

    # Удаляем все записи (если требуется)
    cursor.execute("DELETE FROM tweets")
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM likes")
    cursor.execute("DELETE FROM followers")
    cursor.execute("DELETE FROM media")

    # Вставляем пользователей
    users = [("111", "User1"), ("222", "User2"), ("333", "User3")]
    cursor.executemany("INSERT INTO users (api_key, name) VALUES (?, ?)", users)

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()


# Функция для получения данных из базы
async def get_user_from_db(session: AsyncSession, api_key: str):
    result = await session.execute(
        text("SELECT api_key, name FROM users WHERE api_key = :api_key"),
        {"api_key": api_key},
    )
    row = result.fetchone()
    if row:
        return {"user": {"api_key": row[0], "name": row[1]}}
    return None


async def get_user_info_from_db(session: AsyncSession, api_key: str):
    # Выполняем запрос к базе данных
    result = await session.execute(
        text("SELECT user_id, api_key, name FROM users WHERE api_key = :api_key"),
        {"api_key": api_key},
    )
    row = result.fetchone()
    # Проверяем, найден ли пользователь, и возвращаем объект пользователя
    if row:
        return {"user_id": row[0], "api_key": row[1], "name": row[2]}
    return None


async def get_media_from_db(session: AsyncSession):
    # Выполняем запрос к базе данных
    result = await session.execute(
        text("SELECT * FROM media ORDER BY media_id DESC LIMIT 1")
    )
    row = result.fetchone()
    # Проверяем, найден ли пользователь, и возвращаем объект пользователя
    if row:
        return {
            "media_id": row[0],
            "media_url": row[1],
            "media_path": row[2],
            "tweet_id": row[3],
        }
    return None
