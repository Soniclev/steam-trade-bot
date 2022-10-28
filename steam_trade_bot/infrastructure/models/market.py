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
    BigInteger, MetaData,
)

market_metadata = MetaData()

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


market_item_info_table = Table(
    "market_item_info",
    market_metadata,
    Column("app_id", Integer, nullable=False, primary_key=True),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column(
        "currency",
        Integer,
        ForeignKey("currency.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    Column("sell_listings", Integer, nullable=False),
    Column("sell_price", Float, nullable=True),
    Column("sell_price_no_fee", Float, nullable=True),
    UniqueConstraint("app_id", "market_hash_name", "currency"),
    ForeignKeyConstraint(
        ("app_id", "market_hash_name"),
        ["market_item.app_id", "market_item.market_hash_name"],
        ondelete="CASCADE",
    ),
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
    Column(
        "currency",
        Integer,
        ForeignKey("currency.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("dump", String, nullable=False),
    Column("buy_count", Integer, nullable=True),
    Column("buy_order", Float, nullable=True),
    Column("sell_count", Integer, nullable=True),
    Column("sell_order", Float, nullable=True),
    Column("sell_order_no_fee", Float, nullable=True),
    UniqueConstraint("app_id", "market_hash_name", "currency"),
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
    Column(
        "currency",
        Integer,
        ForeignKey("currency.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("history", String, nullable=False),
    UniqueConstraint("app_id", "market_hash_name", "currency"),
    ForeignKeyConstraint(
        ("app_id", "market_hash_name"),
        ["market_item.app_id", "market_item.market_hash_name"],
        ondelete="CASCADE",
    ),
)

sell_history_analyze_result_table = Table(
    "sell_history_analyze_result",
    market_metadata,
    Column("app_id", Integer, nullable=False, primary_key=True),
    Column("market_hash_name", String, nullable=False, primary_key=True),
    Column("currency", Integer, nullable=False, primary_key=True),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("sells_last_day", Integer, nullable=False),
    Column("sells_last_week", Integer, nullable=False),
    Column("sells_last_month", Integer, nullable=False),
    Column("recommended", Boolean, nullable=False),
    Column("deviation", Float, nullable=True),
    Column("sell_order", Float, nullable=True),
    Column("sell_order_no_fee", Float, nullable=True),
    UniqueConstraint("app_id", "market_hash_name", "currency"),
    ForeignKeyConstraint(
        ("app_id", "market_hash_name", "currency"),
        [
            "market_item_sell_history.app_id",
            "market_item_sell_history.market_hash_name",
            "market_item_sell_history.currency",
        ],
        ondelete="CASCADE",
    ),
)

currency_table = Table(
    "currency",
    market_metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
)

account_table = Table(
    "account",
    market_metadata,
    Column("login", String, primary_key=True),
    Column("currency", Integer, ForeignKey("currency.id", ondelete="CASCADE"), nullable=False),
    Column("name", String, nullable=False),
    Column("steamid", BigInteger, nullable=False),
    Column("enabled", Boolean, nullable=False),
    UniqueConstraint("login"),
)

buy_sell_item_table = Table(
    "buy_sell_item",
    market_metadata,
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
