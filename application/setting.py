from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Auth
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ALGORITHM: str
    SIGN_UP_TEMPORARY_TOKEN_EXP_MIN: int
    ACCESS_TOKEN_EXP_MIN: int
    REFRESH_TOKEN_EXP_MIN: int

    # Telegram
    TELEGRAM_TOKEN: str
    TELEGRAM_CHAT_ID: int
    ERR_THREAD_ID: int
    NEW_USER_THREAD_ID: int

    # Celery
    CELERY_BROKER_URL: str

    class Config:
        env_file = "../.env"
        case_sensitive = True

settings = Settings()
