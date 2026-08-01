import contextlib
import os
import pathlib
import tempfile

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.fixture()
def sampleimage(fs) -> pathlib.Path:
    """Create a fake image in pyfakefs for upload tests."""

    path = (pathlib.Path(__file__).parent / "assests" / "myfile.png").resolve()

    fs.create_file(path)
    return path


@pytest.fixture(autouse=True)
def mock_b2_upload_file(mocker):
    """Prevent tests from uploading files to the real B2 service."""

    return mocker.patch(
        "app.routers.upload.b2_upload_file",
        return_value="https://fakeurl.com",
    )


@pytest.fixture(autouse=True)
def aiofiles_mock_open(mocker, fs):
    """
    Replace aiofiles.open with an asynchronous context manager that operates
    on pyfakefs files.

    The application expects an asynchronous file object, while pyfakefs
    provides normal synchronous files. AsyncMock adapts the synchronous
    read/write operations to the interface expected by the application.
    """

    mock_open = mocker.patch("aiofiles.open")

    @contextlib.asynccontextmanager
    async def async_file_open(fname: str, mode: str = "r"):
        # Create an object whose read and write methods can be awaited.
        async_file_mock = mocker.AsyncMock(name=f"async_file_open:{fname!r}/{mode!r}")

        # Open the actual pyfakefs file and delegate asynchronous operations
        # to its synchronous read and write methods.
        with open(fname, mode) as file_handle:
            async_file_mock.read.side_effect = file_handle.read
            async_file_mock.write.side_effect = file_handle.write

            # Make the mock available inside the application's `async with`.
            yield async_file_mock

    mock_open.side_effect = async_file_open
    return mock_open


async def call_upload_endpoint(
    async_client: AsyncClient,
    token: str,
    sample_image: pathlib.Path,
):
    """Upload the sample image using an authenticated API request."""

    # Keep the image open until httpx has finished creating the request.
    with open(sample_image, "rb") as image_file:
        return await async_client.post(
            "/upload",
            files={"file": image_file},
            headers={"Authorization": f"Bearer {token}"},
        )


@pytest.mark.anyio
async def test_upload_image(
    async_client: AsyncClient,
    logged_in_token: str,
    sampleimage: pathlib.Path,
):
    """Verify that a file is uploaded and its B2 URL is returned."""

    response = await call_upload_endpoint(
        async_client=async_client,
        token=logged_in_token,
        sample_image=sampleimage,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "detail": f"Successfully uploaded {sampleimage.name}",
        "file_url": "https://fakeurl.com",
    }


@pytest.mark.anyio
async def test_temp_file_removed_after_upload(
    async_client: AsyncClient,
    logged_in_token: str,
    sampleimage: pathlib.Path,
    mocker,
):
    """Verify that temporary storage is cleaned after the upload finishes."""

    # Observe NamedTemporaryFile without replacing its real behavior.
    named_temp_file_spy = mocker.spy(
        tempfile,
        "NamedTemporaryFile",
    )

    response = await call_upload_endpoint(
        async_client,
        logged_in_token,
        sampleimage,
    )

    assert response.status_code == status.HTTP_201_CREATED

    # The temporary file should have been deleted when its context ended.
    created_temp_file = named_temp_file_spy.spy_return
    assert not os.path.exists(created_temp_file.name)
