from typing import Literal

from dependency_injector.wiring import inject, Provide
from fastapi import Depends, APIRouter

from steam_trade_bot.api.models.market_item import EntireMarketStatsResponse
from steam_trade_bot.containers import Container
from steam_trade_bot.domain.interfaces.unit_of_work import IUnitOfWork


router = APIRouter()


@router.get("/get_entire_market_stats/", response_model=EntireMarketStatsResponse)
@inject
async def get_entire_market_stats(
        mode: Literal["monthly", "weekly", "daily"] = "daily",
        count: int | None = None,
        offset: int | None = None,
        uow: IUnitOfWork = Depends(Provide[Container.repositories.unit_of_work]),
):
    async with uow:
        stats = await uow.entire_market_daily_stats.get_all(mode=mode, count=count, offset=offset)
    return EntireMarketStatsResponse(
        total_volume=round(sum(x.volume for x in stats), 2),
        total_volume_no_fee=round(sum(x.volume_no_fee for x in stats), 2),
        total_volume_game_fee=round(sum(x.volume_game_fee for x in stats), 2),
        total_volume_steam_fee=round(sum(x.volume_steam_fee for x in stats), 2),
        total_quantity=round(sum(x.quantity for x in stats), 2),
        items=stats
    )
