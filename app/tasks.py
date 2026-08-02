import logging
from json.decoder import JSONDecodeError

import httpx
from databases import Database

from app.config import config
from app.database import post_table

logger = logging.getLogger(__name__)


class APIResponseError(Exception):
    """Custom exception for API response errors."""

    pass


async def send_simple_email(
    to: str,
    subject: str,
    body: str,
) -> httpx.Response:
    """Send a simple email using the Mailgun API."""

    logger.debug(
        "Sending email to '%s' with subject '%s'",
        to[:3],
        subject[:20],
    )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages",
                auth=("api", config.MAILGUN_API_KEY),
                data={
                    "from": (f"Abdelrahman Haloda <mailgun@{config.MAILGUN_DOMAIN}>"),
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
                timeout=30.0,
            )

            response.raise_for_status()
            logger.debug(response.content)

            return response

        except httpx.HTTPStatusError as error:
            raise APIResponseError(
                f"API request failed with status code {error.response.status_code}"
            ) from error

        except httpx.RequestError as error:
            raise APIResponseError("Could not connect to the Mailgun API") from error


async def send_user_registeration_email(
    email: str,
    confirmation_url: str,
) -> httpx.Response:
    """Send a registration confirmation email to the user."""

    return await send_simple_email(
        email,
        "Successfully signed up",
        (
            f"Hi {email}! You have successfully signed up to the "
            "social media REST API. Please confirm your email by "
            f"clicking the following link: {confirmation_url}"
        ),
    )


async def _generate_cute_creature_api(prompt: str):
    """Generate a cute creature image using the DeepAI API."""

    logger.debug("Generating new creature: %s", prompt)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.deepai.org/api/cute-creature-generator",
                data={"text": prompt},
                headers={"api-key": config.DEEPAI_API_KEY},
                timeout=60.0,
            )

            logger.debug(response)
            response.raise_for_status()

            data = response.json()

            if not data.get("output_url"):
                raise APIResponseError("API response does not contain an output URL")

            return data

        except httpx.HTTPStatusError as error:
            raise APIResponseError(
                f"API request failed with status code {error.response.status_code}"
            ) from error

        except httpx.RequestError as error:
            raise APIResponseError("Could not connect to the DeepAI API") from error

        except (JSONDecodeError, TypeError) as error:
            raise APIResponseError(
                "API response parsing failed or missing expected data"
            ) from error


async def generate_and_add_to_post(
    email: str,
    post_id: int,
    post_url: str,
    database: Database,
    prompt: str = (
        "A blue british shorthair cat with a red bow tie, "
        "sitting on a wooden table, photorealistic"
    ),
):
    """Generate an image using DeepAI and add it to the post."""

    try:
        response = await _generate_cute_creature_api(prompt)

    except APIResponseError:
        await send_simple_email(
            email,
            "Error generating image for your post",
            (
                f"Hi {email}! We encountered an error while "
                f"generating an image for your post "
                f"(ID: {post_id}). Please try again later."
            ),
        )
        return

    logger.debug(
        "Updating post %s with generated image URL",
        post_id,
    )

    query = (
        post_table.update()
        .where(post_table.c.id == post_id)
        .values(image_url=response["output_url"])
    )

    logger.debug(query)

    await database.execute(query)

    logger.debug("Background task updated the post successfully")

    await send_simple_email(
        email,
        "Image generation completed",
        (
            f"Hi {email}! The image for your post "
            f"(ID: {post_id}) has been successfully generated. "
            f"You can view it here: {post_url}"
        ),
    )

    return response
