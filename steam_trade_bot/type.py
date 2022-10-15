from typing import TypeAlias, Callable

from sqlalchemy.ext.asyncio import AsyncSession

DbSession: TypeAlias = Callable[..., AsyncSession]
CurrencyValue: TypeAlias = float
