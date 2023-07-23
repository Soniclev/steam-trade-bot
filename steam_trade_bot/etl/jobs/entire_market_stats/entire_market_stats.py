import argparse

from dotenv import load_dotenv

from steam_trade_bot.infrastructure.models.stg_market import entire_market_daily_stats as stg_entire_market_daily_stats
from steam_trade_bot.infrastructure.models.dwh_market import entire_market_daily_stats as dwh_entire_market_daily_stats

load_dotenv(".env")  # take environment variables from .env.

from steam_trade_bot.etl.settings import get_jdbc_creds
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, regexp_replace, explode, to_timestamp
import pyspark.sql.functions as func
from pyspark.sql.types import ArrayType, DecimalType

from steam_trade_bot.etl.spark_conf import create_spark_instance


def run_job(spark):
    jdbc_url, username, password = get_jdbc_creds()
    num_partitions = 100
    partition_column = "partition"

    df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "stg_market.market_item_sell_history") \
        .option("user", username) \
        .option("password", password) \
        .option("driver", "org.postgresql.Driver") \
        .option("numPartitions", num_partitions) \
        .option("partitionColumn", partition_column) \
        .option("lowerBound", "0") \
        .option("upperBound", str(num_partitions)) \
        .load()
    df2 = df.withColumn("history", regexp_replace(col("history"), '"', ""))
    df3 = df2.withColumn('history',
                         from_json(col('history'), ArrayType(ArrayType(DecimalType(18, 2)))))
    df4 = df3.select('app_id', 'market_hash_name', 'timestamp',
                     explode('history').alias('exploded_history'))
    df5 = df4.select(
        col("app_id"),
        col("market_hash_name"),
        col("timestamp"),
        to_timestamp(col('exploded_history')[0].cast('bigint')).alias("point_timestamp"),
        col("exploded_history")[1].alias("price"),
        col("exploded_history")[2].alias("price_no_fee"),
        col("exploded_history")[3].alias("price_game_fee"),
        col("exploded_history")[4].alias("price_steam_fee"),
        col("exploded_history")[5].cast('integer').alias("sold_quantity")
    ).cache()
    df6 = df5.withColumn("point_timestamp", func.date_trunc("day", col("point_timestamp"))).groupBy("point_timestamp").agg(
        func.round(func.avg((col("price"))), 2).alias("daily_avg_price"),
        func.sum((col("price") * col("sold_quantity"))).alias("daily_volume"),
        func.sum((col("price_no_fee") * col("sold_quantity"))).alias("daily_volume_no_fee"),
        func.sum((col("price_game_fee") * col("sold_quantity"))).alias("daily_volume_game_fee"),
        func.sum((col("price_steam_fee") * col("sold_quantity"))).alias("daily_volume_steam_fee"),
        func.sum(col("sold_quantity")).alias("daily_quantity"),
        func.approx_count_distinct("market_hash_name").alias("sold_unique_items"),
    ).sort("point_timestamp", ascending=False).cache()
    df6.write \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", f"{stg_entire_market_daily_stats}") \
        .option("user", username) \
        .option("password", password) \
        .option("driver", "org.postgresql.Driver") \
        .mode("overwrite") \
        .option("truncate", True) \
        .save()
    df6.write \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", f"{dwh_entire_market_daily_stats}") \
        .option("user", username) \
        .option("password", password) \
        .option("driver", "org.postgresql.Driver") \
        .mode("overwrite") \
        .option("truncate", True) \
        .save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PySpark job with an option to start a local Spark instance.')
    parser.add_argument('--local', action='store_true', help='Use this flag to start a local Spark instance.')
    args = parser.parse_args()
    if args.local:
        spark = create_spark_instance()
    else:
        spark = SparkSession.builder.getOrCreate()
    run_job(spark)
