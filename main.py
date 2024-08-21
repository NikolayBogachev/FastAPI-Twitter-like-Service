from fastapi import FastAPI
import uvicorn
from fastapi.routing import APIRouter

from starlette.staticfiles import StaticFiles

from app.handlers import user_router, image_router, logger

from database.func import create_and_fill_tables, wait_for_db

app = FastAPI(title="Twits")

# Настройка для раздачи статических файлов
app.mount("/pictures", StaticFiles(directory="/api/pictures"), name="pictures")

@app.on_event("startup")
async def startup_event():
    logger.info("Запуск приложения")
    await wait_for_db()
    await create_and_fill_tables()
    logger.info("Приложение успешно запущено")


main_api_router = APIRouter()

main_api_router.include_router(user_router)
main_api_router.include_router(image_router)

app.include_router(main_api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
