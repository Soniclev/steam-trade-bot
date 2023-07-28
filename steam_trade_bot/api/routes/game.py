from dependency_injector.wiring import inject, Provide
from fastapi import Depends, APIRouter

from steam_trade_bot.api.models.market_item import GamesListResponse
from steam_trade_bot.containers import Container
from steam_trade_bot.domain.entities.game import GameStatsResponse
from steam_trade_bot.domain.interfaces.unit_of_work import IUnitOfWork


router = APIRouter()


@router.get("/get_games/", response_model=GamesListResponse)
@inject
async def get_games(
        count: int = 100,
        offset: int = 0,
        uow: IUnitOfWork = Depends(Provide[Container.repositories.unit_of_work]),
):
    async with uow:
        games = await uow.game.get_all(
            count=count,
            offset=offset,
        )
    return GamesListResponse(
        count=len(games),
        offset=offset,
        items=games,
    )


@router.get("/get_apps_stats/", response_model=list[GameStatsResponse])
@inject
async def get_apps_stats(
        count: int | None = None,
        offset: int | None = None,
        uow: IUnitOfWork = Depends(Provide[Container.repositories.unit_of_work]),
):
    async with uow:
        stats = await uow.app_stats.get_all(
            count=count,
            offset=offset
        )

    return stats
