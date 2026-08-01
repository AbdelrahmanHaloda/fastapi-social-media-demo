import logging
import tempfile

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.libs.b2 import b2_upload_file

logger = logging.getLogger(__name__)

router = APIRouter()

CHUNK_SIZE = 1024 * 1024  # 1 MB


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile):
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            filename = temp_file.name

            logger.info(
                "Saving uploaded file temporarily to %s",
                filename,
            )

            async with aiofiles.open(filename, "wb") as destination:
                while chunk := await file.read(CHUNK_SIZE):
                    await destination.write(chunk)

            file_url = await run_in_threadpool(
                b2_upload_file,
                local_file=filename,
                file_name=file.filename,
            )

    except Exception as error:
        logger.exception("Error uploading file: %s", error)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file",
        ) from error

    finally:
        await file.close()

    return {
        "detail": f"Successfully uploaded {file.filename}",
        "file_url": file_url,
    }
