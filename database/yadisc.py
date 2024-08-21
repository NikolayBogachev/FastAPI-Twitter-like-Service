from fastapi import HTTPException
from yadisk import AsyncClient
from yadisk.objects import AsyncPublicResourceObject

from config import TOKEN
from database.dekorators import with_tempfile

async_client = AsyncClient(token=TOKEN)


class YadiskDAL:
    """
    Класс для работы с Яндекс.Диском.

    Аргументы:
        token (str): Токен для доступа к Яндекс.Диску.

    Атрибуты:
        async_client (AsyncClient): Асинхронный клиент для работы с API Яндекс.Диска.
    """

    def __init__(self, token: str):
        self.async_client = AsyncClient(token=token)

    async def create_folder_on_yadisk(self, user_id: str):
        """
        Создает папку на Яндекс.Диске для указанного пользователя.

        Аргументы:
            user_id (str): Идентификатор пользователя, для которого создается папка.

        Исключения:
            HTTPException: Ошибка при создании папки на Яндекс.Диске.
        """
        try:
            folder_path = f"/{user_id}/"
            if not await self.async_client.exists(folder_path):
                # Если папка не существует, создаем её
                await self.async_client.mkdir(folder_path)
                # Делаем папку публичной
                await self.async_client.publish(folder_path)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при создании папки на Яндекс.Диске: {str(e)}",
            )

    @with_tempfile
    async def upload_to_yadisk(
        self, temp_file_path: str, user_id: str, dst_filename: str
    ) -> tuple[str | None, str | None]:
        """
        Загружает временный файл на Яндекс.Диск и публикует его.

        Аргументы:
            temp_file_path (str): Путь к временному файлу.
            user_id (str): Идентификатор пользователя.
            dst_filename (str): Имя файла для сохранения на Яндекс.Диске.

        Возвращает:
            tuple[str | None, str | None]: Ссылка на ресурс и путь к файлу.

        Исключения:
            HTTPException: Ошибка при загрузке файла на Яндекс.Диск.
        """
        try:
            folder_path = f"/{user_id}/"
            # Загружаем временный файл на Яндекс.Диск
            await self.async_client.upload(
                temp_file_path, f"{folder_path}{dst_filename}"
            )
            resource_link = await self.async_client.publish(
                f"{folder_path}{dst_filename}"
            )
            url = await self.async_client.get_meta(resource_link.path)

            return url.public_url, resource_link.path
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при загрузке файла на Яндекс.Диск: {str(e)}",
            )

    async def delete_folder_on_yadisk(self, user_id: str):
        """
        Удаляет папку на Яндекс.Диске для указанного пользователя.

        Аргументы:
            user_id (str): Идентификатор пользователя, для которого удаляется папка.

        Исключения:
            HTTPException: Ошибка при удалении папки на Яндекс.Диске.
        """
        try:
            folder_path = f"/{user_id}/"
            await self.async_client.remove(folder_path, permanently=True)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при удалении папки на Яндекс.Диске: {str(e)}",
            )

    async def delete_file_on_yadisk(self, file_url: str):
        """
        Удаляет файл на Яндекс.Диске по указанному URL.

        Аргументы:
            file_url (str): URL файла для удаления.

        Исключения:
            HTTPException: Ошибка при удалении файла на Яндекс.Диске.
        """
        try:
            await self.async_client.remove(file_url, permanently=True)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при удалении файла на Яндекс.Диске: {str(e)}",
            )

    async def delete_media_files(self, media_urls: list):
        """
        Удаляет несколько медиафайлов на Яндекс.Диске по списку URL.

        Аргументы:
            media_urls (list): Список URL медиафайлов для удаления.

        Исключения:
            HTTPException: Ошибка при удалении медиафайлов на Яндекс.Диске.
        """
        try:
            for url in media_urls:
                await self.delete_file_on_yadisk(url)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при удалении медиафайлов на Яндекс.Диске: {str(e)}",
            )

    async def get_public_meta(self, url: str) -> AsyncPublicResourceObject:
        """
        Получает метаданные публичного ресурса по публичному ключу.

        Аргументы:
            public_key (str): Публичный ключ ресурса.

        Возвращает:
            AsyncPublicResourceObject: Объект с метаданными публичного ресурса.

        Исключения:
            HTTPException: Ошибка при получении метаданных публичного ресурса.
        """
        try:
            return await self.async_client.get_public_meta(url)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении метаданных публичного ресурса: {str(e)}",
            )

# @image_router.post(
#     "/api/medias",
#     response_model=MediaResponse,
#     response_model_exclude_unset=True,
# )
# async def upload_media(
#     api_key: Annotated[str | None, Header()],
#     file: UploadFile = File(...),
#     session: AsyncSession = Depends(get_db),
# ) -> MediaResponse:
#     """
#     Эндпоинт для загрузки медиафайла.
#
#     Аргументы:
#         request (Request): Объект запроса.
#         temp_file (UploadFile): Загружаемый файл.
#         session (AsyncSession): Асинхронная сессия для работы с базой данных.
#
#     Возвращает:
#         MediaResponse: Ответ с идентификатором медиа.
#     """
#     logger.info("Received upload_media request", extra={"api_key": api_key, "filename": file.filename})
#     if not api_key:
#         raise HTTPException(status_code=401, detail="API key is missing")
#
#     user_dal = UserDAL(session)
#     yadisk_dal = YadiskDAL(token=TOKEN)
#     media_dal = MediaDAL(session)
#
#     if api_key is None:
#         logger.error("API key is missing")
#         raise HTTPException(status_code=400, detail="API key is required")
#
#     user = await user_dal.get_user_by_api_key(api_key)
#     logger.info("User fetched", extra={"user_id": user.user_id})
#
#     try:
#         await yadisk_dal.create_folder_on_yadisk(user.user_id)
#         file_bytes = await file.read()
#         link, path = await yadisk_dal.upload_to_yadisk(
#             file_bytes, user.user_id, file.filename
#         )
#         print(link)
#         print(path)
#
#         new_media = await media_dal.create_media_record(link, path)
#         logger.info("Media uploaded and record created", extra={"media_id": new_media.media_id})
#
#         return MediaResponse(result=True, media_id=new_media.media_id)
#
#     except HTTPException as e:
#         logger.error(f"HTTP Exception: {e.detail}")
#         raise e
#
#     except Exception as e:
#         logger.exception("Internal server error")
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")