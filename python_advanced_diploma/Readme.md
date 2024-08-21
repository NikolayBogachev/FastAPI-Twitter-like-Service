![v](https://img.shields.io/badge/build-3.10-brightgreen?style=plastic&logo=Python&label=Python&color=orange&cacheSeconds=10000)
![](https://img.shields.io/badge/build-0.111.1-brightgreen?style=plastic&logo=FastAPI&label=FastAPI&color=orange&cacheSeconds=10000)
![v](https://img.shields.io/badge/build-2.0.31-brightgreen?style=plastic&logo=Sqlalchemy&label=Sqlalchemy&color=orange)
![v](https://img.shields.io/badge/build-16-brightgreen?style=plastic&logo=Postgresql&label=Postgresql&color=orange)
![v](https://img.shields.io/badge/build-%E2%80%8E2.29.2-brightgreen?logo=Docker&label=Docker&color=orange&cacheSeconds=1000000)

# *FastAPI Twitter-like Service*

## Описание

*Этот проект представляет собой веб-сервис на базе FastAPI, предназначенный для управления твитами и медиафайлами. 
Сервис позволяет пользователям:*

- **Загружать медиафайлы**.
- **Создавать и удалять твиты.**
- **Ставить и удалять лайки у твитов.**
- **Подписываться и отписываться от других пользователей.**
- **Получать информацию о пользователях и твитах.**

![Demo](/doc/Screenshot%20from%202024-08-12%2016-15-44.png)
___

## Инструкция по установке

**Установите Docker на свой компютер:**

- [Официальный сайт Docker ](https://www.docker.com/)

**Зарегестрируйтесь на Docker Hub:**
- [Официальный сайт Docker Hub](https://hub.docker.com/)

**Зайдите в свою учетную запись:**
```bash
docker login
```
**Скачайте образ:**
```bash
docker pull scandalist/projects:v1.0
```
**Проверьте, что образ был успешно загружен:**
```bash
docker images
```
**Запустите контейнер из загруженного образа:**
```bash
docker run -d --name my_container scandalist/projects:v1.0
```
Здесь -d запускает контейнер в фоновом режиме, а --name my_container задает имя контейнера.

**Просмотрите запущенные контейнеры:**
```bash
docker ps
```
**Проверите работу приложения:**
(http://0.0.0.0:81/login)

## Автор

Этот проект был разработан **Богачевым Николаем Константиновичем** [Email me](mailto:Bogachev.pro@gmail.com)
.
