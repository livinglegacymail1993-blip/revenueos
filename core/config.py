import os


class Settings:
    """Canonical config. Load from env (and optional .env via env_file if needed)."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/db")
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")


settings = Settings()