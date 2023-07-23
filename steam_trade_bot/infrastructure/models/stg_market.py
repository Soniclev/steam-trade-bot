from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    DateTime,
    Float,
    MetaData,
    Numeric,
    BigInteger,
)
from sqlalchemy.dialects.postgresql import JSONB

SCHEMA_NAME = "stg_market"
market_metadata = MetaData(schema=SCHEMA_NAME)

game_table = Table(
    "game",
    market_metadata,
    Column("app_id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("icon_url", String, nullable=True),
    Column("is_publisher_valve", Boolean, nullable=False, server_default="false"),
)

market_item_table = Table(
    "market_item",
    market_metadata,
    Column("partition", Integer, nullable=False),
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
    Column("icon_url", Boolean, nullable=True),
    UniqueConstraint("app_id", "market_hash_name"),
)

market_item_stats_table = Table(
    "market_item_stats",
    market_metadata,
    Column("partition", Integer, nullable=False),
    Column(
        "app_id",
        Integer,
        ForeignKey("game.app_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("total_sold", BigInteger, nullable=False),
    Column("total_volume", Numeric(precision=10, scale=2), nullable=False),
    Column("total_volume_steam_fee", Numeric(precision=10, scale=2), nullable=False),
    Column("total_volume_publisher_fee", Numeric(precision=10, scale=2), nullable=False),
    Column("min_price", Numeric(precision=10, scale=2), nullable=True),
    Column("max_price", Numeric(precision=10, scale=2), nullable=True),
    Column("first_sale_timestamp", DateTime, nullable=True),
    Column("last_sale_timestamp", DateTime, nullable=True),
    UniqueConstraint("app_id", "market_hash_name"),
)

market_item_orders_table = Table(
    "market_item_orders",
    market_metadata,
    Column("partition", Integer, nullable=False),
    Column("app_id", Integer, nullable=False, primary_key=True),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("buy_orders", JSONB, nullable=False),
    Column("sell_orders", JSONB, nullable=False),
    UniqueConstraint("app_id", "market_hash_name"),
)

market_item_sell_history_table = Table(
    "market_item_sell_history",
    market_metadata,
    Column("partition", Integer, nullable=False),
    Column("app_id", Integer, nullable=False, primary_key=True),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("history", JSONB, nullable=False),
    UniqueConstraint("app_id", "market_hash_name"),
)

entire_market_daily_stats = Table(
    "entire_market_daily_stats",
    market_metadata,
    Column("point_timestamp", DateTime, nullable=False, primary_key=True),
    Column("daily_avg_price", Numeric(precision=18, scale=2), nullable=False),
    Column("daily_volume", Numeric(precision=18, scale=2), nullable=False),
    Column("daily_volume_no_fee", Numeric(precision=18, scale=2), nullable=False),
    Column("daily_volume_game_fee", Numeric(precision=18, scale=2), nullable=False),
    Column("daily_volume_steam_fee", Numeric(precision=18, scale=2), nullable=False),
    Column("daily_quantity", BigInteger, nullable=False),
    Column("sold_unique_items", BigInteger, nullable=False),
)

app_stats_view_name = "app_stats_view"
app_stats_view_select = """SELECT 
app_id,
COUNT(1) as items_amount,
SUM(total_sold) AS total_sold, 
SUM(total_volume) AS total_volume, 
SUM(total_volume_steam_fee) AS total_volume_steam_fee, 
SUM(total_volume_publisher_fee) AS total_volume_publisher_fee,
MIN(min_price) AS min_price,
MAX(max_price) AS max_price,
MIN(first_sale_timestamp) AS first_sale_timestamp,
MAX(last_sale_timestamp) AS last_sale_timestamp
FROM stg_market.market_item_stats
GROUP BY app_id;"""
