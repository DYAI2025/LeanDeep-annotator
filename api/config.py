"""Configuration for the LeanDeep API."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "LeanDeep Marker API"
    version: str = "6.0-LD6"
    debug: bool = False

    # Paths
    registry_path: str = str(
        Path(__file__).resolve().parent.parent / "build" / "markers_normalized" / "marker_registry.json"
    )
    personas_dir: str = str(Path(__file__).resolve().parent.parent / "personas")

    # Auth — production default: enabled. Override with LEANDEEP_REQUIRE_AUTH=false for dev.
    api_keys_file: str = str(Path(__file__).resolve().parent / "api_keys.json")
    require_auth: bool = True

    # CORS — explicit origins list. Override with LEANDEEP_CORS_ORIGINS (comma-separated).
    cors_origins: str = "http://localhost:8420,http://localhost:3000"

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # Engine
    default_threshold: float = 0.5
    max_text_length: int = 50_000
    max_conversation_messages: int = 200

    model_config = {"env_prefix": "LEANDEEP_"}

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
