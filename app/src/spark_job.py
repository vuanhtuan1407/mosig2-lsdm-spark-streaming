import json
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import split, col, window, concat_ws, count, sum, when, date_format
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

# Filter out NULL machine_ID and job_ID
df_parsed_clean = df_parsed.filter(
    col("machine_ID").isNotNull() & col("job_ID").isNotNull()
)

# Calculate simplified metrics
metrics_df = df_parsed_clean.withWatermark("time_ts", "30 seconds") \
    .groupBy(
        window(col("time_ts"), "2 minutes", "30 seconds"),
        col("machine_ID"),
        col("job_ID")
    ) \
    .agg(
        count("*").alias("total_events"),
        
        # Count fail events (FAIL + EVICT + KILL)
        sum(when(col("event_type") == configs.EVENT_TYPE["FAIL"], 1).otherwise(0)).alias("fail_count"),
        sum(when(col("event_type") == configs.EVENT_TYPE["EVICT"], 1).otherwise(0)).alias("evict_count"),
        sum(when(col("event_type") == configs.EVENT_TYPE["KILL"], 1).otherwise(0)).alias("kill_count")
    ) \
    .select(
        date_format(col("window.start"), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").alias("window_start"),
        date_format(col("window.end"), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").alias("window_end"),
        col("machine_ID"),
        col("job_ID"),
        col("total_events"),
        col("fail_count"),
        col("evict_count"),
        col("kill_count")
    )

# Calculate total fail count and fail rate
metrics_df = metrics_df.withColumn(
    "total_fail_count", col("fail_count") + col("evict_count") + col("kill_count")
).withColumn(
    "fail_rate",
    when(col("total_events") > 0, col("total_fail_count") / col("total_events")).otherwise(0)
)

# Add document ID (handle potential NULL values)
metrics_with_id = metrics_df.withColumn(
    "doc_id",
    concat_ws("_",
              col("window_start"),
              when(col("machine_ID").isNotNull(), col("machine_ID").cast("string")).otherwise("null"),
              when(col("job_ID").isNotNull(), col("job_ID").cast("string")).otherwise("null"))
)

# Write to Elasticsearch
query = metrics_with_id.writeStream \
    .format("org.elasticsearch.spark.sql") \
    .option("checkpointLocation", f"/tmp/spark/checkpoint_metrics_{int(time.time())}") \
    .option("es.nodes", "elasticsearch") \
    .option("es.port", "9200") \
    .option("es.resource", f"{configs.ES_TASK_EVENT_INDEX}_metrics") \
    .option("es.mapping.id", "doc_id") \
    .option("es.mapping.date.rich", "true") \
    .option("es.batch.size.entries", "1000") \
    .option("es.batch.size.bytes", "1mb") \
    .outputMode("update") \
    .trigger(processingTime="1 second") \
    .start()

spark.streams.awaitAnyTermination()