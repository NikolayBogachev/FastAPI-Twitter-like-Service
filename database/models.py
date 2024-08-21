from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Text,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """
    Модель пользователя

    :param user_id: Идентификатор пользователя (первичный ключ)
    :param api_key: API ключ пользователя (уникальный)
    :param tweets: Связь с твитами пользователя
    :param followers: Связь с подписчиками пользователя
    :param followees: Связь с пользователями, на которых подписан пользователь
    :param likes: Связь с лайками пользователя
    """

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    api_key = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    # Другие поля пользователя

    tweets = relationship("Tweet", back_populates="user", cascade="all, delete-orphan")
    followers = relationship(
        "Follower", foreign_keys="Follower.followee_id", back_populates="followee"
    )
    followees = relationship(
        "Follower", foreign_keys="Follower.follower_id", back_populates="follower"
    )
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")


class Tweet(Base):
    """
    Модель твита

    :param tweet_id: Идентификатор твита (первичный ключ)
    :param user_id: Идентификатор пользователя, создавшего твит (внешний ключ)
    :param content: Текстовое содержание твита
    :param timestamp: Временная метка создания твита
    """

    __tablename__ = "tweets"

    tweet_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now(), index=True)

    user = relationship("User", back_populates="tweets")
    likes = relationship("Like", back_populates="tweet", cascade="all, delete-orphan")
    media = relationship(
        "Media",
        back_populates="tweet",
        cascade="all, delete-orphan",
        single_parent=True,
    )


class Follower(Base):
    """
    Модель подписчика

    :param follower_id: (подписчик) указывает на пользователя, который подписывается на какого-то другого пользователя.
    :param followee_id: (подписанный) указывает на пользователя, на которого подписываются другие пользователи.
    """

    __tablename__ = "followers"

    follower_id = Column(
        Integer, ForeignKey("users.user_id"), primary_key=True, index=True
    )
    followee_id = Column(
        Integer, ForeignKey("users.user_id"), primary_key=True, index=True
    )

    follower = relationship(
        "User", foreign_keys=[follower_id], back_populates="followers", lazy="joined"
    )
    followee = relationship(
        "User", foreign_keys=[followee_id], back_populates="followees", lazy="joined"
    )


class Like(Base):
    """
    Модель лайка

    :param like_id: Идентификатор лайка (первичный ключ)
    :param user_id: Идентификатор пользователя, поставившего лайк (внешний ключ)
    :param tweet_id: Идентификатор твита, на который поставлен лайк (внешний ключ)
    """

    __tablename__ = "likes"

    like_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    tweet_id = Column(
        Integer, ForeignKey("tweets.tweet_id"), nullable=False, index=True
    )

    user = relationship("User", back_populates="likes")
    tweet = relationship("Tweet", back_populates="likes")

    # Добавление уникального индекса на столбцы user_id и tweet_id
    __table_args__ = (UniqueConstraint("user_id", "tweet_id", name="unique_like"),)


class Media(Base):
    """
    Модель медиа (изображения)

    :param media_id: Идентификатор медиа (первичный ключ)
    :param media_url: URL медиа (уникальный)
    :param tweet_id: Идентификатор твита (внешний ключ)
    """

    __tablename__ = "media"

    media_id = Column(Integer, primary_key=True, index=True)
    media_url = Column(String, nullable=False, unique=True)
    media_path = Column(String, nullable=False, unique=True)
    tweet_id = Column(Integer, ForeignKey("tweets.tweet_id"), index=True)

    tweet = relationship("Tweet", back_populates="media")
