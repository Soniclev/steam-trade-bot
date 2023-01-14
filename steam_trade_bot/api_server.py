import json
from dataclasses import asdict
from typing import Union, Callable
import asyncio

from fastapi import FastAPI, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from dependency_injector.wiring import Provide, inject

from steam_trade_bot.api.models.market_item import MarketItemSellHistoryResponse
from steam_trade_bot.containers import Container
from steam_trade_bot.domain.services.sell_history_analyzer import steam_date_str_to_datetime
from steam_trade_bot.settings import BotSettings

from steam_trade_bot.domain.interfaces.unit_of_work import IUnitOfWork

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


@router.get("/get_item_sell_history/", response_model=MarketItemSellHistoryResponse)
@inject
async def get_item_sell_history(
        app_id: int = 730,
        market_hash_name: str = "Sticker | Skull Lil Boney",
        currency: int = 1,
        uow: IUnitOfWork = Depends(Provide[Container.repositories.unit_of_work]),
):
    async with uow:
        history = await uow.sell_history.get(
            app_id=app_id,
            market_hash_name=market_hash_name,
            currency=currency
        )
    return MarketItemSellHistoryResponse(
        app_id=history.app_id,
        market_hash_name=history.market_hash_name,
        currency=history.currency,
        timestamp=history.timestamp,
        history=[
            (
                steam_date_str_to_datetime(x[0]),
                round(x[1], 2),
                int(x[2])
            )
            for x in json.loads(history.history)
        ]
    )


app.include_router(router)

container = Container()
container.config.from_pydantic(BotSettings())
container.wire(modules=[__name__])
