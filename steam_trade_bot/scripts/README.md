

## Run spark

Run master:
```shell
spark-class org.apache.spark.deploy.master.Master --host localhost
```

Run worker:
```shell
spark-class org.apache.spark.deploy.worker.Worker -c 6 -m 10G spark://localhost:7077
```
