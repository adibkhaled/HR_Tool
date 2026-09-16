import pytest

from backend.app.core.config import Settings


def test_production_rejects_default_secret_and_local_database() -> None:
    settings = Settings(app_env="production")

    with pytest.raises(ValueError, match="JWT_SECRET"):
        settings.validate_production()


def test_development_defaults_are_valid() -> None:
    Settings(app_env="development").validate_production()
