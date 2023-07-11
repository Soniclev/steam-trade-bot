
from pyspark.sql import SparkSession


def create_spark_instance(name: str | None = None, **kwargs):
    spark = SparkSession.builder \
        .master('local[*]') \
        .appName(name or 'Steam Trade Bot ETL') \
        .config("spark.jars", "vendors/postgresql-42.6.0.jar") \
        .config("spark.executor.memory", "10g") \
        .config("spark.driver.memory", "5g") \
        .config("spark.sql.shuffle.partitions", "30") \
        .config('spark.sql.files.maxPartitionBytes', str(20 * 1024 * 1024)) \

    for key, value in kwargs.items():
        spark = spark.config(key, value)

    return spark.getOrCreate()
