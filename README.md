# steam-trade-bot

# Computing market fees
You can check these [functions](steam_trade_bot/domain/fee_calculator.py) in order to compute the market fee for any game. The `compute_fee_from_payload` and `compute_fee_from_total` functions will allow you to calculate the total cost, game fee, steam fee, and payload, given either the payload or total cost and an optional game fee. The default game fee is set to 0.1 and the steam fee is calculated as 5% of the payload. The output will be returned as a named tuple with fields ('total', 'payload', 'game', 'steam').

Example usage:

```python
>>> compute_fee_from_payload(10.0)
ComputedFee(total=11.5, payload=10.0, game=1.0, steam=0.5)

>>> compute_fee_from_payload(10.0, 0.15)  # for app_id=321360
ComputedFee(total=12.0, payload=10.0, game=1.5, steam=0.5)

>>> compute_fee_from_total(11.5)
ComputedFee(total=11.5, payload=10.0, game=1.0, steam=0.5)

>>> compute_fee_from_total(12.0, 0.15)  # for app_id=321360
ComputedFee(total=12.0, payload=10.0, game=1.5, steam=0.5)
```

# PostgresSQL dump for all items that available on the Steam market
You can download the Steam market data dump covering the period from 2012-12 to 2022-11 from the following link: https://steam-bot-public.s3.eu-central-1.amazonaws.com/dump2.zip (619 MB, unzipped ~8GB). This dump includes information on all market item sales during this period and can be loaded into your PostgreSQL database to be used for analysis and research purposes. Also, you can check this [notebook](notebooks/Analyze%20Steam%20market.ipynb) in order to see plots showing summarized sold items amount and knifes by cheap price covering the period.

Here's a brief description of the tables:

`game_table`: Holds information about the games in the market. Has columns for the app ID (primary key) and the name of the game.

`market_item_table`: Holds information about the items available in the market. Has columns for the app ID (which is a foreign key to the game_table), market hash name (primary key), market fee, market marketable/tradable restrictions, and a flag indicating if the item is a commodity.

`market_item_info_table`: Holds information about the item's sell price, sell listings, and the currency being used. Has columns for the app ID, market hash name, and currency (which is a foreign key to the currency table).

`market_item_name_id_table`: Holds information linking the market hash name of the item to its name ID. Has columns for the app ID, market hash name, and item name ID.

`market_item_orders_table`: Holds information about the orders of an item in the market. Has columns for the app ID, market hash name, currency (which is a foreign key to the currency table), timestamp, dump, buy/sell count, and buy/sell order.

`market_item_sell_history_table`: Holds information about the selling history of an item in the market. Has columns for the app ID, market hash name, currency (which is a foreign key to the currency table), timestamp, and dump.


To import the "dump2.sql" file into a PostgreSQL database using the command line, you can use the following command:
`psql -U [user] -d [database_name] -f [path_to_sql_file]`

To import the "dump2.sql" file into your PostgreSQL database using DBeaver, follow these steps:

1. Open DBeaver and connect to your PostgreSQL database.
2. Right-click on the database name in the DB Navigator panel and select "Import" from the context menu.
3. In the "Import wizard" window, select the "SQL script" option.
4. Click "Next" and select the "dump2.sql" file.
5. On the next page, select the schema where you want to import the data.
6. Click "Start" to start the import process.

Note: The import process may take a while, depending on the size of the "dump2.sql" file and the performance of your database system.
