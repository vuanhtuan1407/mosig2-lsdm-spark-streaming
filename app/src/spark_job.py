import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import split, col, window, concat_ws, avg, sum, count, max, when
from pyspark.sql.types import FloatType, BooleanType, StringType, TimestampType, LongType
import configs

# Load schema
with open(configs.SCHEMA_DICT_PATH, "r", encoding="utf-8") as f:
    schema_dict = json.load(f)

task_cols = schema_dict["task_events"]["col_content"]
task_formats = schema_dict["task_events"]["col_format"]

type_map = {
    "INTEGER": LongType(),
    "FLOAT": FloatType(),
    "BOOLEAN": BooleanType(),
    "STRING_HASH": StringType(),
    "STRING": StringType()
}

col_types = [type_map[t] for t in task_formats]

# Create Spark session
spark = SparkSession.builder \
    .appName("TaskEventMetrics") \
    .getOrCreate()

spark.sparkContext.setLogLevel("INFO")

# Read from Kafka
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", configs.KAFKA_BROKER) \
    .option("subscribe", configs.TOPIC) \
    .option("startingOffsets", "earliest") \
    .load()

df_str = df_raw.selectExpr("CAST(value AS STRING) as csv_str")
df_split = df_str.withColumn("cols", split(col("csv_str"), ","))

# Parse columns
df_parsed = df_split
for i, (c, t) in enumerate(zip(task_cols, col_types)):
    df_parsed = df_parsed.withColumn(c, col("cols").getItem(i).cast(t))

# Convert milliseconds timestamp to TimestampType
df_parsed = df_parsed.withColumn("time_ts", (col("time") / 1000).cast(TimestampType()))

# Calculate metrics
metrics_df = df_parsed.withWatermark("time_ts", "2 seconds") \
    .groupBy(
        window(col("time_ts"), "5 seconds", "1 second"),
        col("machine_ID"),
        col("job_ID")
    ) \
    .agg(
        count("*").alias("total_events"),
        
        # Count by event type
        sum(when(col("event_type") == configs.EVENT_TYPE["SUBMIT"], 1).otherwise(0)).alias("submit_count"),
        sum(when(col("event_type") == configs.EVENT_TYPE["SCHEDULE"], 1).otherwise(0)).alias("schedule_count"),
        sum(when(col("event_type") == configs.EVENT_TYPE["EVICT"], 1).otherwise(0)).alias("evict_count"),
        sum(when(col("event_type") == configs.EVENT_TYPE["FAIL"], 1).otherwise(0)).alias("fail_count"),
        sum(when(col("event_type") == configs.EVENT_TYPE["FINISH"], 1).otherwise(0)).alias("finish_count"),
        sum(when(col("event_type") == configs.EVENT_TYPE["KILL"], 1).otherwise(0)).alias("kill_count"),
        
        # Resource metrics
        avg("CPU_request").alias("avg_cpu_request"),
        avg("memory_request").alias("avg_memory_request"),
        max("CPU_request").alias("max_cpu_request"),
        max("memory_request").alias("max_memory_request")
    ) \
    .selectExpr(
        "window.start as window_start",
        "window.end as window_end",
        "machine_ID",
        "job_ID",
        "total_events",
        "submit_count",
        "schedule_count",
        "evict_count",
        "fail_count",
        "finish_count",
        "kill_count",
        "avg_cpu_request",
        "avg_memory_request",
        "max_cpu_request",
        "max_memory_request"
    )

# Calculate derived metrics
metrics_df = metrics_df.withColumn(
    "failure_count", col("fail_count") + col("evict_count") + col("kill_count")
).withColumn(
    "success_count", col("finish_count")
).withColumn(
    "failure_rate", 
    when(col("total_events") > 0, col("failure_count") / col("total_events")).otherwise(0)
).withColumn(
    "success_rate",
    when(col("total_events") > 0, col("success_count") / col("total_events")).otherwise(0)
)

# Add document ID
metrics_with_id = metrics_df.withColumn(
    "doc_id",
    concat_ws("_", 
              col("window_start").cast("string"), 
              col("machine_ID").cast("string"),
              col("job_ID").cast("string"))
)

# Write to Elasticsearch mỗi 1 giây
query = metrics_with_id.writeStream \
    .format("org.elasticsearch.spark.sql") \
    .option("checkpointLocation", "/tmp/spark/checkpoint_metrics") \
    .option("es.nodes", "elasticsearch") \
    .option("es.port", "9200") \
    .option("es.resource", f"{configs.ES_TASK_EVENT_INDEX}_metrics") \
    .option("es.mapping.id", "doc_id") \
    .option("es.batch.size.entries", "1000") \
    .option("es.batch.size.bytes", "1mb") \
    .outputMode("update") \
    .trigger(processingTime="1 second") \
    .start()

spark.streams.awaitAnyTermination()