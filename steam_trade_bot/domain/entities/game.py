from pydantic import BaseModel


class Game(BaseModel):
    app_id: int
    name: str
    icon_url: str | None
    is_publisher_valve: bool


class GameStatsResponse(BaseModel):
    app_id: int
    avg_price: float
    volume: float
    volume_no_fee: float
    volume_game_fee: float
    volume_steam_fee: float
    quantity: int
    items_amount: int
    min_price: float
    max_price: float

