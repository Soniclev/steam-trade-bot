from sqlalchemy.ext.asyncio import create_async_engine


class DbEngine:
    def __init__(self, host: str, db: str, user: str, password: str):
        self._host = host
        self._db = db
        self._user = user
        self._password = password

    async def create(self):
        return create_async_engine(
            f"postgresql+asyncpg://{self._user}:{self._password}@{self._host}/{self._db}",
            isolation_level="REPEATABLE READ",
        )
