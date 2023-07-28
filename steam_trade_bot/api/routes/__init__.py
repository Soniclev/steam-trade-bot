from fastapi import APIRouter

from .entire_market import router as entire_market_router
from .market_item import router as market_item_router
from .game import router as game_router

router = APIRouter()
router.include_router(entire_market_router)
router.include_router(market_item_router)
router.include_router(game_router)
