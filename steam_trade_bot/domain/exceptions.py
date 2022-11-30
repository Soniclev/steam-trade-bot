class BotException(Exception):
    ...


class CurrencyNotSupported(BotException):
    def __init__(self, currency: int):
        super().__init__(f"Currency {currency} is not supported!")


class ItemNameIdNotFound(BotException):
    def __init__(self, app_id: int, market_hash_name: str):
        super().__init__(f"Item_name_id for pair {app_id=} {market_hash_name=} not found!")


class SerializationError(BotException):
    ...
