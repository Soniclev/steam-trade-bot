from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


load_dotenv()


class SparkSettings(BaseSettings):
    database: str


spark_settings = SparkSettings()
engine = create_async_engine(spark_settings.database, pool_size=5, max_overflow=10)

# TODO: make another function to create spark session
def get_jdbc_creds() -> tuple[str, str, str]:
    parsed = urlparse(spark_settings.database)
    username = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port or 5432
    database = parsed.path.lstrip('/')
    jdbc_url = f"jdbc:postgresql://{host}:{port}/{database}"
    return jdbc_url, username, password  # type: ignore


def create_session():
    return sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
