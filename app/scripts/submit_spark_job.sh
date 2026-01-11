spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.jars.ivy=/workspace/app/opt/ivy2 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.3,org.elasticsearch:elasticsearch-spark-30_2.12:8.8.2 \
  src/spark_job.py