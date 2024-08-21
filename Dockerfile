# Используйте официальный образ Python
FROM python:3.10-slim

# Установите рабочую директорию
WORKDIR /api

# Установите зависимости
COPY requirements.txt /api/
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода

COPY app/ /api/app/
COPY static/ /api/static/
COPY database/ /api/database/
COPY pictures/ /api/pictures/
COPY config.py /api/
COPY .env /api/
COPY main.py /api/
COPY entrypoint.sh /api/

# Установите Nginx
RUN apt-get update && apt-get install -y netcat-openbsd nginx

# Скопируйте конфигурацию Nginx для Docker
COPY nginx.docker.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf
# Откройте порты
EXPOSE 80
EXPOSE 8000
# Укажите команду для запуска приложения

ENTRYPOINT ["/api/entrypoint.sh"]