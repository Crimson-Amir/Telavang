from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    PUBLIC_URL: str

    # Auth
    ACCESS_TOKEN_SECRET_KEY: str
    REFRESH_TOKEN_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXP_MIN: int
    REFRESH_TOKEN_EXP_MIN: int

    # Telegram
    TELEGRAM_TOKEN: str
    TELEGRAM_CHAT_ID: int
    ERR_THREAD_ID: int
    NEW_USER_THREAD_ID: int
    INFO_THREAD_ID: int
    VISITS_THREAD_ID: int

    # Celery
    CELERY_BROKER_URL: str

    class Config:
        env_file = "../.env"
        case_sensitive = True

settings = Settings()
