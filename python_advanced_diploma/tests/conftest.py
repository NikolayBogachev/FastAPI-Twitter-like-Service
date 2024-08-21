import pytest_asyncio
from httpx import AsyncClient

from tests.main import app
from tests.funcs import fill_test_data
from tests.initdb import create_db_and_tables, DATABASE_URL


@pytest_asyncio.fixture(scope="function")
async def setup_database():
    await create_db_and_tables()
    fill_test_data(DATABASE_URL)


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Универсальная функция для проверки ответа
def check_response(response, expected_status, expected_json):
    assert response.status_code == expected_status
    assert response.json() == expected_json
