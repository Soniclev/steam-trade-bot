from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
    ForeignKeyConstraint,
    UniqueConstraint,
    DateTime,
    Float,
    MetaData,
)

SCHEMA_NAME = "raw"
market_metadata = MetaData(schema=SCHEMA_NAME)

game_table = Table(
    "game",
    market_metadata,
    Column("app_id", Integer, primary_key=True),
    Column("name", String, nullable=False),
)

market_item_table = Table(
    "market_item",
    market_metadata,
    Column(
        "app_id",
        Integer,
        ForeignKey("game.app_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("market_fee", String, nullable=True),
    Column("market_marketable_restriction", Float, nullable=True),
    Column("market_tradable_restriction", Float, nullable=True),
    Column("commodity", Boolean, nullable=False),
    UniqueConstraint("app_id", "market_hash_name"),
)


market_item_name_id_table = Table(
    "market_item_name_id",
    market_metadata,
    Column(
        "app_id",
        Integer,
        nullable=False,
        primary_key=True,
    ),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("item_name_id", Integer, nullable=False),
    UniqueConstraint("app_id", "market_hash_name"),
    ForeignKeyConstraint(
        ("app_id", "market_hash_name"),
        ["market_item.app_id", "market_item.market_hash_name"],
        ondelete="CASCADE",
    ),
)


market_item_orders_table = Table(
    "market_item_orders",
    market_metadata,
    Column("app_id", Integer, nullable=False, primary_key=True),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("dump", String, nullable=False),
    UniqueConstraint("app_id", "market_hash_name"),
    ForeignKeyConstraint(
        ("app_id", "market_hash_name"),
        ["market_item.app_id", "market_item.market_hash_name"],
        ondelete="CASCADE",
    ),
)


market_item_sell_history_table = Table(
    "market_item_sell_history",
    market_metadata,
    Column("app_id", Integer, nullable=False, primary_key=True),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("history", String, nullable=False),
    UniqueConstraint("app_id", "market_hash_name"),
    ForeignKeyConstraint(
        ("app_id", "market_hash_name"),
        ["market_item.app_id", "market_item.market_hash_name"],
        ondelete="CASCADE",
    ),
)
