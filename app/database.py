"""Database schema and connection configuration."""

import databases
import sqlalchemy

from app.config import config

# Registry containing all SQLAlchemy table definitions.
metadata = sqlalchemy.MetaData()


post_table = sqlalchemy.Table(
    "posts",
    metadata,
    # id column - auto incremented
    sqlalchemy.Column(
        "id",
        sqlalchemy.Integer,
        primary_key=True,
    ),
    # body column, post must contain a body; NULL values are rejected by the database.
    sqlalchemy.Column(
        "body",
        sqlalchemy.String,
        nullable=False,
    ),
)

""" DataBase Tables Schema """

comment_table = sqlalchemy.Table(
    "comments",
    metadata,
    # id column - auto incremented
    sqlalchemy.Column(
        "id",
        sqlalchemy.Integer,
        primary_key=True,
    ),
    # body column, comment must contain a body; NULL values are rejected by the database.
    sqlalchemy.Column(
        "body",
        sqlalchemy.String,
        nullable=False,
    ),
    # post_id column, enforces the parent-child relationship between comments and posts.
    sqlalchemy.Column(
        "post_id",
        sqlalchemy.ForeignKey("posts.id"),
        nullable=False,
    ),
)


# check_same_thread is a SQLite-specific connection option.
#
# SQLite normally restricts a connection to the thread that created it.
# Disabling this check allows the connection to be used safely by the
# application's database infrastructure across different threads.
connect_args = {}

if config.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False


# Synchronous SQLAlchemy engine used for schema creation.
engine = sqlalchemy.create_engine(
    config.DATABASE_URL,
    connect_args=connect_args,
)


# Create any tables that do not already exist.
#
# Important: create_all() does not modify an existing table when its schema
# changes. A migration tool such as Alembic should eventually be used for that.
metadata.create_all(engine)


# Asynchronous database connection used by the FastAPI endpoints.
#
# During tests, force_rollback=True ensures that database changes are rolled
# back instead of being permanently committed.
database = databases.Database(
    config.DATABASE_URL,
    force_rollback=config.DB_FORCE_ROLL_BACK,
)
