import dataclasses
import json

from dependency_injector.wiring import inject, Provide
from fastapi import Depends, APIRouter

from steam_trade_bot.api.models.market_item import MarketItemsListResponse, MarketItemResponse, MarketItemSellHistoryResponse
from steam_trade_bot.containers import Container
from steam_trade_bot.domain.entities.market import MarketItem, MarketItemOrders
from steam_trade_bot.domain.interfaces.unit_of_work import IUnitOfWork

router = APIRouter()


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
        items=[MarketItemResponse(**item.dict()) for item in items],
    )


@router.get("/get_market_item/", response_model=MarketItem)
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
    return item


@router.get("/get_market_item_orders/", response_model=MarketItemOrders)
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
    return item


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
        total_volume_approx_fee=round(float(stats.total_volume) * 0.13, 2),
        first_sale_datetime=stats.first_sale_timestamp,
        last_sale_datetime=stats.last_sale_timestamp,
        history=json.loads(history.history),
    )
