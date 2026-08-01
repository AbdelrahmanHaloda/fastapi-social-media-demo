import logging

import httpx

from app.config import config

logger = logging.getLogger(__name__)


class APIResponseError(Exception):
    """Custom exception for API response errors."""

    pass


async def send_simple_email(
    to: str,
    subject: str,
    body: str,
) -> httpx.Response:
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
            )

            response.raise_for_status()
            logger.debug(response.content)

            return response

        except httpx.HTTPStatusError as error:
            raise APIResponseError(
                f"API request failed with status code {error.response.status_code}"
            ) from error


async def send_user_registeration_email(
    email: str,
    confirmation_url: str,
) -> httpx.Response:
    return await send_simple_email(
        email,
        "Successfully signed up",
        (
            f"Hi {email}! You have successfully signed up to the "
            "social media REST API. Please confirm your email by "
            f"clicking the following link: {confirmation_url}"
        ),
    )
