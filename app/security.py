"""Security utilities for password hashing, user authentication, and JWT creation."""

import datetime
import logging

from fastapi import HTTPException, status
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.database import database, user_table

logger = logging.getLogger(__name__)


# Development-only secret used to sign and verify JWTs.
# Move this to an environment variable before deploying the application.
SECRET_TOKEN_KEY = "sdy8e2dg82yrgd28yfb234827464tr24y7gf328"

# Algorithm used to sign JWT access tokens.
ALGORITHM = "HS256"

# Password-hashing configuration.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

# Generic exception used when authentication fails.
# The same message is used for both invalid emails and invalid passwords
# to avoid revealing whether a specific user exists.
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def access_token_expire_minutes() -> int:
    """Return the lifetime of an access token in minutes."""

    return 30


def create_access_token(email: str) -> str:
    """Create a signed JWT containing the user's email."""

    logger.debug("Creating access token", extra={"email": email})

    # Calculate the token's expiration time using timezone-aware UTC.
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )

    # "sub" identifies the user represented by the token.
    jwt_data = {
        "sub": email,
        "exp": expire,
    }

    # Sign and encode the JWT using the secret key.
    encoded_jwt = jwt.encode(
        jwt_data,
        SECRET_TOKEN_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt


def get_password_hash(password: str) -> str:
    """Hash a plain-text password before database storage."""

    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Check whether a plain password matches its stored hash."""

    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


async def get_user(email: str):
    """Retrieve a user by email, or return None if not found."""

    logger.debug(
        "Fetching user from the database",
        extra={"email": email},
    )

    query = user_table.select().where(user_table.c.email == email)

    return await database.fetch_one(query)


async def authenticate_user(email: str, password: str):
    """Validate the user's email and password and return the user record."""

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

async def get_current_user(token: str):
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

    # Ensure the user represented by the token still exists.
    user = await get_user(email=email)
    if user is None:
        raise credentials_exception

    return user