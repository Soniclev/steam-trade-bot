from pydantic import BaseSettings, Field


class BotSettings(BaseSettings):
    database: str
