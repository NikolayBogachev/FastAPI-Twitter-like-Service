import tempfile
import os


from fastapi import HTTPException
from functools import wraps


# Декоратор для работы с временными файлами
def with_tempfile(func):
    @wraps(func)
    async def wrapper(
        self, media_request: bytes, user_id: str, dst_filename: str, *args, **kwargs
    ):
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(media_request)
                temp_file_path = temp_file.name
                return await func(
                    self, temp_file_path, user_id, dst_filename, *args, **kwargs
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при создании или загрузке временного файла: {str(e)}",
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    return wrapper
