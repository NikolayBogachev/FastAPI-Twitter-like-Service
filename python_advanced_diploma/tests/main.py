from fastapi import FastAPI
import uvicorn
from fastapi.routing import APIRouter

from starlette.staticfiles import StaticFiles

from tests.handlers import user_router, image_router


app = FastAPI(title="Twits")

# Настройка для раздачи статических файлов
app.mount("/pictures", StaticFiles(directory="/home/nikolasy/PycharmProjects/python_advanced_diploma/pictures"), name="pictures")


main_api_router = APIRouter()

main_api_router.include_router(user_router)
main_api_router.include_router(image_router)

app.include_router(main_api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
