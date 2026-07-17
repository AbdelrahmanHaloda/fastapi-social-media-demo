from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentConfig(BaseSettings):
    """
    Bootstrap configuration used only to determine which environment-specific
    configuration should be loaded.
    """

    # Required value loaded from ENV_STATE.
    # Application startup will fail if it is missing.
    ENV_STATE: str

    model_config = SettingsConfigDict(
        # Load settings from the project's .env file.
        env_file=".env",
        # Ignore variables belonging to the environment-specific configurations.
        extra="ignore",
    )


class GlobalConfig(BaseSettings):
    """
    Common settings shared by development, production, and testing.

    This class intentionally does not inherit from EnvironmentConfig because
    ENV_STATE selects the configuration but is not an application setting.
    """

    # Required database connection URL.
    DATABASE_URL: str

    # Disabled by default unless an environment overrides it.
    DB_FORCE_ROLL_BACK: bool = False


class DevConfig(GlobalConfig):
    """Development environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        # Fields are loaded using the DEV_ prefix.
        # For example, DATABASE_URL is read from DEV_DATABASE_URL.
        env_prefix="DEV_",
        extra="ignore",
    )


class ProdConfig(GlobalConfig):
    """Production environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        # Fields are loaded using the PROD_ prefix.
        # For example, DATABASE_URL is read from PROD_DATABASE_URL.
        env_prefix="PROD_",
        extra="ignore",
    )


class TestConfig(GlobalConfig):
    """
    Test environment configuration.

    Tests use an isolated SQLite database and roll back database changes by
    default to reduce state leaking between tests.
    """

    # Relative SQLite path; test.db is created relative to the directory
    # from which the application or test command is executed.
    DATABASE_URL: str = "sqlite:///test.db"

    DB_FORCE_ROLL_BACK: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        # Defaults can be overridden using variables such as
        # TEST_DATABASE_URL and TEST_DB_FORCE_ROLL_BACK.
        env_prefix="TEST_",
        extra="ignore",
    )


@lru_cache
def get_config(env_state: str) -> GlobalConfig:
    """
    Create and cache the configuration for the selected environment.

    The cache ensures that settings are loaded only once for each environment
    and that the same configuration instance is reused.
    """

    # Store classes instead of instances so only the selected configuration
    # is instantiated.
    configs: dict[str, type[GlobalConfig]] = {
        "dev": DevConfig,
        "prod": ProdConfig,
        "test": TestConfig,
    }

    try:
        config_class = configs[env_state]
    except KeyError:
        # Convert the dictionary lookup error into a meaningful configuration
        # error when ENV_STATE contains an unsupported value.
        raise ValueError(
            f"Unknown ENV_STATE: {env_state}. Expected one of: {', '.join(configs)}"
        ) from None

    return config_class()


# Resolve the active configuration once when this module is imported.
# Other modules can access it with:
#
#     from app.config import config
#
config = get_config(EnvironmentConfig().ENV_STATE)
