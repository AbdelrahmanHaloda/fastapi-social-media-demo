"""Security utilities for password hashing, authentication, and JWT handling."""

import datetime
import logging
from typing import Annotated, Literal

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
def create_credentials_exception(detail: str) -> HTTPException: 
    return HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail= detail,
    headers={"WWW-Authenticate": "Bearer"},
)


def access_token_expire_minutes() -> int:
    """Return the access-token lifetime in minutes."""
    return 30

def confirm_token_expire_minutes() -> int:
    """Return the confirm-token lifetime in minutes."""
    return 1440


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
        "type": "access",
    }

    return jwt.encode(
        payload,
        SECRET_TOKEN_KEY,
        algorithm=ALGORITHM,
    )

def create_confirmation_token(email: str) -> str:
    """Create a signed JWT for confirming a user's email address."""

    logger.debug(
        "Creating confirmation token",
        extra={"email": email},
    )
    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirm_token_expire_minutes()
    )
    payload = {
        "sub": email,
        "exp": expiration,
        "type": "confirmation",
    }
    return jwt.encode(
        payload,
        SECRET_TOKEN_KEY,
        algorithm=ALGORITHM,
    )

def get_subject_from_token_type(token: str, type: Literal["access", "confirmation"]) -> str:
    try:
        # Validate the token's signature and expiration.
        payload = jwt.decode(
            token,
            key=SECRET_TOKEN_KEY,
            algorithms=[ALGORITHM],
        )
    
    except ExpiredSignatureError as error:
        raise create_credentials_exception("Token has expired") from error
    
    except JWTError as error:
        raise create_credentials_exception("Invalid token") from error

    # The subject claim contains the authenticated user's email.
    email = payload.get("sub")
    if email is None:
        raise create_credentials_exception("Token is missing 'sub' field")

    token_type = payload.get("type")
    if token_type is None or token_type != type:
        raise create_credentials_exception(f"Token has incorrect type, expected '{type}'")
    return email


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
        raise create_credentials_exception("Invalid email or password")

    # Reject authentication when the password is incorrect.
    if not verify_password(password, user.password):
        raise create_credentials_exception("Invalid email or password")
    
    # Reject authentication when the email is not confirmed.
    if not user.confirmed:
        raise create_credentials_exception("User email is not confirmed")

    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme),]):
    """Validate a JWT and return the user identified by its subject claim."""

    email = get_subject_from_token_type(token, type="access")
    # The token may be valid even if its user was later deleted.
    user = await get_user(email)

    if user is None:
        raise create_credentials_exception("Could not find user for this token")

    return user
