#!/bin/sh

# Ожидание готовности базы данных
while ! nc -z postgres 5432; do
  sleep 1
done

# Запуск Nginx
service nginx start

# Запуск Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
