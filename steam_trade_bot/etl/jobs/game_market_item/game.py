from steam_trade_bot.database import upsert_many_by_index
from steam_trade_bot.etl.models import GameRaw, GameStage, GameDWH, AppIdKey
from steam_trade_bot.etl.settings import create_session
from steam_trade_bot.infrastructure.repositories import GameRepository

from steam_trade_bot.infrastructure.models.raw_market import game_table as raw_game_table
from steam_trade_bot.infrastructure.models.stg_market import game_table as stg_game_table
from steam_trade_bot.infrastructure.models.dwh_market import game_table as dwh_game_table


async def _upsert_many_by_app(session, table, values):
    await upsert_many_by_index(session, table, values, ["app_id"])


def process_game(
        obj: GameRaw
) -> tuple[GameStage, GameDWH]:
    return (
        GameStage(**obj, icon_url=None, is_publisher_valve=False),
        GameDWH(**obj, icon_url=None, is_publisher_valve=False),
    )


def _split_column_by_upsert(table, index_elements: set[str]) -> list[str]:
    result = []
    for column in table.c:
        if column.name not in index_elements:
            result.append(column.name)
    return result


async def process_game_batch(batch: list[AppIdKey]):
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

            await _upsert_many_by_app(session, stg_game_table, stage_list)
            await _upsert_many_by_app(session, dwh_game_table, dwh_list)
