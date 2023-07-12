spark-submit ^
  --master local[*] ^
  --name "Steam Trade Bot ETL" ^
  --conf spark.jars="vendors\postgresql-42.6.0.jar" ^
  --conf spark.executor.memory="10g" ^
  --conf spark.driver.memory="5g" ^
  --conf spark.sql.shuffle.partitions="30" ^
  --conf spark.sql.files.maxPartitionBytes="20971520" ^
  --conf spark.local.dir="C:\tmp\spark" ^
  --conf spark.eventLog.enabled=true ^
  --conf spark.eventLog.dir="C:\tmp\spark-logs" ^
  steam_trade_bot/etl/jobs/game_market_item/game_market_item_job.py

spark-submit ^
  --master local[*] ^
  --name "Steam Trade Bot ETL" ^
  --conf spark.jars="vendors\postgresql-42.6.0.jar" ^
  --conf spark.executor.memory="10g" ^
  --conf spark.driver.memory="5g" ^
  --conf spark.sql.shuffle.partitions="30" ^
  --conf spark.sql.files.maxPartitionBytes="20971520" ^
  --conf spark.local.dir="C:\tmp\spark" ^
  --conf spark.eventLog.enabled=true ^
  --conf spark.eventLog.dir="C:\tmp\spark-logs" ^
  steam_trade_bot/etl/jobs/entire_market_stats/entire_market_stats.py
