from dotenv import load_dotenv

load_dotenv(".env")  # take environment variables from .env.

from steam_trade_bot.etl.settings import get_jdbc_creds
from steam_trade_bot.etl.async_run import surround_async
from steam_trade_bot.etl.jobs.game_market_item.game import process_game_batch
from steam_trade_bot.etl.jobs.game_market_item.market_item import process_market_item_batch
from steam_trade_bot.etl.jobs.game_market_item.market_item import process_market_item_sell_history_batch
from steam_trade_bot.etl.jobs.game_market_item.market_item import process_market_item_orders_batch
from pyspark.sql import SparkSession

# from steam_trade_bot.etl.spark_conf import create_spark_instance


def run_job(spark):
    jdbc_url, username, password = get_jdbc_creds()
    df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "raw.market_item_sell_history") \
        .option("user", username) \
        .option("password", password) \
        .option("driver", "org.postgresql.Driver") \
        .load()
    app_id_market_name_df_partitions = max(1, round(df.count() / 1000))
    app_id_market_name_df = df.select("app_id", "market_hash_name").repartition(
        app_id_market_name_df_partitions).cache()
    app_id_df = df.select("app_id").distinct().repartition(1).cache()
    app_id_df.foreachPartition(surround_async(process_game_batch))
    app_id_market_name_df.foreachPartition(surround_async(process_market_item_batch))
    app_id_market_name_df.foreachPartition(surround_async(process_market_item_sell_history_batch))
    app_id_market_name_df.foreachPartition(surround_async(process_market_item_orders_batch))


if __name__ == '__main__':
    run_job(SparkSession.builder.getOrCreate())
