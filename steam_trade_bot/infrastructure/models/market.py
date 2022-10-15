from sqlalchemy import (
    Table,
    Column,
    MetaData,
    Integer,
    String,
    ForeignKey,
    Boolean,
    ForeignKeyConstraint,
    UniqueConstraint,
    DateTime,
    Float,
    BigInteger,
)

metadata = MetaData()

game_table = Table(
    "game",
    metadata,
    Column("app_id", Integer, primary_key=True),
    Column("name", String, nullable=False),
)

market_item_table = Table(
    "market_item",
    metadata,
    Column(
        "app_id",
        Integer,
        ForeignKey("game.app_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("market_fee", Float, nullable=True),
    Column("market_marketable_restriction", Float, nullable=True),
    Column("market_tradable_restriction", Float, nullable=True),
    Column("commodity", Boolean, nullable=False),
    Column("item_name_id", Integer, nullable=False),
    UniqueConstraint("app_id", "market_hash_name"),
)

market_item_sell_history_table = Table(
    "market_item_sell_history",
    metadata,
    Column("app_id", Integer, nullable=False, primary_key=True),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("currency", Integer, ForeignKey("currency.id", ondelete="CASCADE"), nullable=False, primary_key=True),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("history", String, nullable=False),
    UniqueConstraint("app_id", "market_hash_name", "currency"),
    ForeignKeyConstraint(
        ("app_id", "market_hash_name"),
        ["market_item.app_id", "market_item.market_hash_name"],
        ondelete="CASCADE",
    ),
)

currency_table = Table(
    "currency",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
)

account_table = Table(
    "account",
    metadata,
    Column("login", String, primary_key=True),
    Column("currency", Integer, ForeignKey("currency.id", ondelete="CASCADE"), nullable=False),
    Column("name", String, nullable=False),
    Column("steamid", BigInteger, nullable=False),
    Column("enabled", Boolean, nullable=False),
    UniqueConstraint("login"),
)

buy_sell_item_table = Table(
    "buy_sell_item",
    metadata,
    Column(
        "account",
        String,
        ForeignKey("account.login", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    Column("app_id", Integer, nullable=False, primary_key=True),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("currency", Integer, ForeignKey("currency.id", ondelete="CASCADE"), nullable=False),
    Column("amount", Integer, nullable=False),
    Column("buy_enabled", Boolean, nullable=False),
    Column("buy_order", Float, nullable=False),
    Column("sell_enabled", Boolean, nullable=False),
    Column("sell_order", Float, nullable=False),
    UniqueConstraint("account", "app_id", "market_hash_name"),
    ForeignKeyConstraint(
        ("app_id", "market_hash_name"),
        ["market_item.app_id", "market_item.market_hash_name"],
        ondelete="CASCADE",
    ),
)
