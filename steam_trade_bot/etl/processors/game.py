from steam_trade_bot.database import upsert_many
from steam_trade_bot.etl.models import GameRaw, GameStage, GameDWH
from steam_trade_bot.etl.settings import create_session
from steam_trade_bot.infrastructure.repositories import GameRepository

from steam_trade_bot.infrastructure.models.raw_market import game_table as raw_game_table
from steam_trade_bot.infrastructure.models.stg_market import game_table as stg_game_table
from steam_trade_bot.infrastructure.models.dwh_market import game_table as dwh_game_table


def process_game(
        obj: GameRaw
) -> tuple[GameStage, GameDWH]:
    return (
        GameStage(**obj),
        GameDWH(**obj),
    )


async def process_game_batch(batch):
    stage_list = []
    dwh_list = []

    async_session = create_session()
    async with async_session() as session:
        async with session.begin():
            respository = GameRepository(session, table=raw_game_table, type_=GameRaw)
            pairs = [x.app_id for x in batch]
            async for rows in respository.yield_all_by_app_ids(pairs, 1000):
                for row in rows:
                    stage, dwh = process_game(row)
                    stage_list.append(stage)
                    dwh_list.append(dwh)

            await upsert_many(session, stg_game_table, stage_list, ["app_id"],
                               ["name", "icon_url", "is_publisher_valve"])
            await upsert_many(session, dwh_game_table, dwh_list, ["app_id"],
                               ["name", "icon_url", "is_publisher_valve"])
