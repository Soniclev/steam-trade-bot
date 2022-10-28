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
    Enum,
)

from steam_trade_bot.domain.entities.proxy import ProxyProtocolEnum

proxy_metadata = MetaData()

proxy_table = Table(
    "proxy",
    proxy_metadata,
    Column(
        "_id",
        Integer,
        autoincrement=True,
        primary_key=True,
    ),
    Column("protocol", Enum(ProxyProtocolEnum), nullable=False),
    Column("host", String, nullable=False),
    Column("port", Integer, nullable=False),
    Column("login", String, nullable=True),
    Column("password", String, nullable=True),
    UniqueConstraint("protocol", "host", "port", "login", "password"),
)
