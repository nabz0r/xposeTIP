from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://xpose:xpose@postgres:5432/xpose"
    DATABASE_URL_SYNC: str = "postgresql://xpose:xpose@postgres:5432/xpose"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-please-use-a-real-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    HIBP_API_KEY: str = ""
    MAXMIND_LICENSE: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
