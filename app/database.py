"""Database table definitions and connection configuration."""

import databases
import sqlalchemy

from app.config import config

# Registry containing all SQLAlchemy table definitions.
metadata = sqlalchemy.MetaData()


# Users table
user_table = sqlalchemy.Table(
    "users",
    metadata,
    # unique id for each user
    sqlalchemy.Column(
        "id",
        sqlalchemy.Integer,
        primary_key=True,
    ),
    sqlalchemy.Column(
        "email",
        sqlalchemy.String,
        unique=True,
        nullable=False,
    ),
    sqlalchemy.Column(
        "password",
        sqlalchemy.String,
        nullable=False,
    ),
    sqlalchemy.Column(
        "confirmed",
        sqlalchemy.Boolean,
        server_default=sqlalchemy.false(),
        nullable=False,),
)


# Posts table
post_table = sqlalchemy.Table(
    "posts",
    metadata,
    # unique id for each post
    sqlalchemy.Column(
        "id",
        sqlalchemy.Integer,
        primary_key=True,
    ),
    sqlalchemy.Column(
        "body",
        sqlalchemy.String,
        nullable=False,
    ),
    # Identifies the user who created the post.
    sqlalchemy.Column(
        "user_id",
        sqlalchemy.ForeignKey("users.id"),
        nullable=False,
    ),
)


# Comments table
comment_table = sqlalchemy.Table(
    "comments",
    metadata,
    # unique id for each comment
    sqlalchemy.Column(
        "id",
        sqlalchemy.Integer,
        primary_key=True,
    ),
    sqlalchemy.Column(
        "body",
        sqlalchemy.String,
        nullable=False,
    ),
    # Identifies the post that contains the comment.
    sqlalchemy.Column(
        "post_id",
        sqlalchemy.ForeignKey("posts.id"),
        nullable=False,
    ),
    # Identifies the user who created the comment.
    sqlalchemy.Column(
        "user_id",
        sqlalchemy.ForeignKey("users.id"),
        nullable=False,
    ),
)

# like_table table
like_table = sqlalchemy.Table(
    "likes",
    metadata,
    # unique id for each like
    sqlalchemy.Column(
        "id",
        sqlalchemy.Integer,
        primary_key=True,
    ),
    # Identifies the liked post.
    sqlalchemy.Column(
        "post_id",
        sqlalchemy.ForeignKey("posts.id"),
        nullable=False,
    ),
    # Identifies the user who liked the post.
    sqlalchemy.Column(
        "user_id",
        sqlalchemy.ForeignKey("users.id"),
        nullable=False,
    ),
)

# SQLite normally restricts a connection to the thread that created it.
# Disable that restriction because the application may use the connection
# from different threads.
connect_args = {}

if config.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False


# Synchronous engine used to create the database schema.
engine = sqlalchemy.create_engine(
    config.DATABASE_URL,
    connect_args=connect_args,
)


# Create tables that do not already exist.
#
# create_all() does not update existing tables after their definitions change.
# Schema migrations should eventually be handled using a tool such as Alembic.
metadata.create_all(engine)


# Asynchronous connection used by the FastAPI endpoints.
#
# During tests, force_rollback prevents test changes from being permanently
# committed to the database.
database = databases.Database(
    config.DATABASE_URL,
    force_rollback=config.DB_FORCE_ROLL_BACK,
)
