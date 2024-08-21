from pydantic import BaseModel
from typing import List, Optional


class TunedModel(BaseModel):
    """
    Базовый класс для всех моделей.
    Конфигурация:
    - from_attributes: позволяет создавать модели из словарей атрибутов.
    """

    class Config:
        from_attributes = True


class MediaRequest(TunedModel):
    """
    Запрос на загрузку медиафайла.

    Атрибуты:
    - file (bytes): Двоичное содержимое медиафайла.
    """

    file: bytes


class MediaResponse(TunedModel):
    """
    Ответ после загрузки медиафайла.

    Атрибуты:
    - result (bool): Указывает, была ли загрузка медиафайла успешной.
    - media_id (int): Уникальный идентификатор загруженного медиафайла.
    """

    result: bool
    media_id: int


class TweetRequest(TunedModel):
    """
    Запрос на создание твита.

    Атрибуты:
    - tweet_data (str): Содержимое твита.
    - tweet_media_ids (Optional[List[int]]): Список идентификаторов медиафайлов, прикрепленных к твиту. Может быть пустым.
    """

    tweet_data: str
    tweet_media_ids: Optional[List[int]] = None


class TweetResponse(TunedModel):
    """
    Ответ после создания твита.

    Атрибуты:
    - result (bool): Указывает, был ли твит успешно создан.
    - tweet_id (int): Уникальный идентификатор созданного твита.
    """

    result: bool
    tweet_id: int


class LikeResponse(TunedModel):
    """
    Ответ на действие "лайк".

    Атрибуты:
    - result (bool): Указывает, было ли действие "лайк" успешным.
    """

    result: bool


class FollowerResponse(TunedModel):
    """
    Ответ на запрос о подписчиках.

    Атрибуты:
    - result (bool): Указывает, был ли запрос о подписчиках успешным.
    """

    result: bool


class Follower(TunedModel):
    """
    Информация о подписчике.

    Атрибуты:
    - id (int): Уникальный идентификатор подписчика.
    - name (str): Имя подписчика.
    """

    id: int
    name: str


class User(TunedModel):
    """
    Информация о пользователе.

    Атрибуты:
    - id (int): Уникальный идентификатор пользователя.
    - name (str): Имя пользователя.
    - followers (List[Follower]): Список подписчиков пользователя.
    - following (List[Follower]): Список пользователей, на которых подписан пользователь.
    """

    id: int
    name: str
    followers: List[Follower]
    following: List[Follower]


class UserResponse(TunedModel):
    """
    Ответ на запрос о пользователе.

    Атрибуты:
    - result (bool): Указывает, был ли запрос о пользователе успешным.
    - user (User): Объект пользователя, содержащий информацию о нём.
    """

    result: bool
    user: User
