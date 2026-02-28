import os


class Settings:
    """Canonical config. Load from env (and optional .env via env_file if needed)."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/db")
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")

    # Session and Stripe Connect OAuth (safe defaults for local dev)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    STRIPE_CLIENT_ID: str = os.getenv("STRIPE_CLIENT_ID", "")
    STRIPE_CLIENT_SECRET: str = os.getenv("STRIPE_CLIENT_SECRET", "")
    STRIPE_REDIRECT_URI: str = os.getenv("STRIPE_REDIRECT_URI", "")


settings = Settings()
