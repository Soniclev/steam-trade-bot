import dataclasses
import json
from dataclasses import asdict
from datetime import timedelta, datetime
from typing import Union, Callable
import asyncio

from fastapi import FastAPI, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel

from steam_trade_bot.api.models.market_item import MarketItemSellHistoryResponse
    # MarketItemHeatmapItem, MarketItemHeatmap, MarketItemWeeklyResponse
from steam_trade_bot.containers import Container
from steam_trade_bot.domain.entities.market import MarketItem, Game
from steam_trade_bot.domain.services.sell_history_analyzer import steam_date_str_to_datetime
from steam_trade_bot.settings import BotSettings

from steam_trade_bot.domain.interfaces.unit_of_work import IUnitOfWork
from steam_trade_bot.type import CurrencyValue

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
router = APIRouter(prefix="/api/v1")


@router.get("/")
def read_root():
    return {"Hello": "World"}


class MarketItemPydantic(BaseModel):
    app_id: int
    market_hash_name: str
    market_fee: str | None
    market_marketable_restriction: int | None
    market_tradable_restriction: int | None
    commodity: bool

    def is_tradable(self) -> bool:
        return self.market_tradable_restriction != -1  # -1 means not tradable at all


class GamePydantic(BaseModel):
    app_id: int
    name: str


class MarketItemsListResponse(BaseModel):
    count: int
    offset: int
    items: list[MarketItemPydantic]


class GamesListResponse(BaseModel):
    count: int
    offset: int
    items: list[GamePydantic]


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
        items=[GamePydantic(**dataclasses.asdict(item)) for item in games],
    )


@router.get("/get_market_items/", response_model=MarketItemsListResponse)
@inject
async def get_market_items(
        app_id: int = 730,
        count: int = 100,
        offset: int = 0,
        uow: IUnitOfWork = Depends(Provide[Container.repositories.unit_of_work]),
):
    async with uow:
        items = await uow.market_item.get_all(
            app_id=app_id,
            count=count,
            offset=offset,
        )
    return MarketItemsListResponse(
        count=len(items),
        offset=offset,
        items=[MarketItemPydantic(**dataclasses.asdict(item)) for item in items],
    )


@router.get("/get_market_item/", response_model=MarketItemPydantic)
@inject
async def get_market_item(
        app_id: int = 730,
        market_hash_name: str = "Sticker | Skull Lil Boney",
        uow: IUnitOfWork = Depends(Provide[Container.repositories.unit_of_work]),
):
    async with uow:
        item = await uow.market_item.get(
            app_id=app_id,
            market_hash_name=market_hash_name,
        )
    return MarketItemPydantic(**dataclasses.asdict(item))


class MarketItemOrdersPydantic(BaseModel):
    app_id: int
    market_hash_name: str
    timestamp: datetime
    buy_count: int | None
    buy_order: CurrencyValue | None
    sell_count: int | None
    sell_order: CurrencyValue | None
    sell_order_no_fee: CurrencyValue | None


@router.get("/get_market_item_orders/", response_model=MarketItemOrdersPydantic)
@inject
async def get_market_item_orders(
        app_id: int = 730,
        market_hash_name: str = "Sticker | Skull Lil Boney",
        uow: IUnitOfWork = Depends(Provide[Container.repositories.unit_of_work]),
):
    async with uow:
        item = await uow.market_item_orders.get(
            app_id=app_id,
            market_hash_name=market_hash_name,
        )
    return MarketItemOrdersPydantic(**dataclasses.asdict(item))


@router.get("/get_item_sell_history/", response_model=MarketItemSellHistoryResponse)
@inject
async def get_item_sell_history(
        app_id: int = 730,
        market_hash_name: str = "Sticker | Skull Lil Boney",
        uow: IUnitOfWork = Depends(Provide[Container.repositories.unit_of_work]),
):
    async with uow:
        history = await uow.sell_history.get(
            app_id=app_id,
            market_hash_name=market_hash_name,
        )
        stats = await uow.sell_history_stats.get(
            app_id=app_id,
            market_hash_name=market_hash_name
        )

    return MarketItemSellHistoryResponse(
        app_id=history.app_id,
        market_hash_name=history.market_hash_name,
        timestamp=history.timestamp,
        total_sold=stats.total_sold,
        total_volume=stats.total_volume,
        total_volume_approx_fee=round(float(stats.total_volume)*0.13, 2),
        first_sale_datetime=stats.first_sale_timestamp,
        last_sale_datetime=stats.last_sale_timestamp,
        history=json.loads(history.history),
    )


app.include_router(router)

container = Container()
container.config.from_pydantic(BotSettings())
container.wire(modules=[__name__])
