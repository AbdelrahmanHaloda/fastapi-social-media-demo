"""Security utilities for password hashing, authentication, and JWT handling."""

import datetime
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.database import database, user_table

logger = logging.getLogger(__name__)

# Development-only key used to sign and verify JWTs.
# Move it to an environment variable before production deployment.
SECRET_TOKEN_KEY = "sdy8e2dg82yrgd28yfb234827464tr24y7gf328"
ALGORITHM = "HS256"

# Defines how FastAPI extracts Bearer tokens from requests.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configure bcrypt for password hashing.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

# Reusable response for invalid credentials or tokens.
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def access_token_expire_minutes() -> int:
    """Return the access-token lifetime in minutes."""

    return 30


def create_access_token(email: str) -> str:
    """Create a signed JWT that identifies a user by email."""

    logger.debug(
        "Creating access token",
        extra={"email": email},
    )

    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )

    payload = {
        "sub": email,
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        SECRET_TOKEN_KEY,
        algorithm=ALGORITHM,
    )


def get_password_hash(password: str) -> str:
    """Hash a plain-text password for database storage."""

    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Check whether a plain-text password matches a stored hash."""

    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


async def get_user(email: str):
    """Return the user with the given email, or None if not found."""

    logger.debug(
        "Fetching user from the database",
        extra={"email": email},
    )

    query = user_table.select().where(user_table.c.email == email)

    return await database.fetch_one(query)


async def authenticate_user(email: str, password: str):
    """Validate login credentials and return the authenticated user."""

    logger.debug(
        "Authenticating user",
        extra={"email": email},
    )

    user = await get_user(email)

    # Reject authentication when the email does not exist.
    if not user:
        raise credentials_exception

    # Reject authentication when the password is incorrect.
    if not verify_password(password, user.password):
        raise credentials_exception

    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme),]):
    """Validate a JWT and return the user identified by its subject claim."""

    try:
        # Validate the token's signature and expiration.
        payload = jwt.decode(
            token,
            key=SECRET_TOKEN_KEY,
            algorithms=[ALGORITHM],
        )

        # The subject claim contains the authenticated user's email.
        email = payload.get("sub")
        if email is None:
            raise credentials_exception

    except ExpiredSignatureError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    except JWTError as error:
        raise credentials_exception from error

    # The token may be valid even if its user was later deleted.
    user = await get_user(email)

    if user is None:
        raise credentials_exception

    return user
