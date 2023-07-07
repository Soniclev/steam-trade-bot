from steam_trade_bot.etl.models import GameRaw, GameStage, GameDWH


def process_game(
        obj: GameRaw
) -> tuple[GameStage, GameDWH]:
    return (
        GameStage(**obj),
        GameDWH(**obj),
    )
