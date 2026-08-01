import logging
from functools import lru_cache

import b2sdk.v2 as b2

from app.config import config

logger = logging.getLogger(__name__)


@lru_cache()
def b2_api() -> b2.B2Api:
    """Create and authorize a cached B2 API client."""

    logger.debug("Creating and authorizing B2 API")

    info = b2.InMemoryAccountInfo()
    api = b2.B2Api(info)

    api.authorize_account(
        "production",
        config.B2_KEY_ID,
        config.B2_APPLICATION_KEY,
    )

    return api


@lru_cache()
def b2_get_bucket(api: b2.B2Api) -> b2.Bucket:
    """Return the configured B2 bucket."""

    return api.get_bucket_by_name(config.B2_BUCKET_NAME)


def b2_upload_file(local_file: str, file_name: str) -> str:
    """Upload a local file and return its B2 download URL."""

    api = b2_api()

    logger.debug(
        "Uploading %s to B2 as %s",
        local_file,
        file_name,
    )

    uploaded_file = b2_get_bucket(api).upload_local_file(
        local_file=local_file,
        file_name=file_name,
    )

    download_url = api.get_download_url_for_fileid(uploaded_file.id_)

    logger.debug(
        "Uploaded %s to B2 successfully",
        local_file,
    )

    return download_url
