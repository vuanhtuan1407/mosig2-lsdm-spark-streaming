import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import split, col, from_unixtime, window, concat_ws
from pyspark.sql.types import IntegerType, FloatType, BooleanType, StringType, TimestampType
import configs

KAFKA_BROKER = "kafka:29092"
TOPIC = "cluster-metrics"
ES_INDEX = "task_events"

with open(configs.SCHEMA_DICT_PATH, "r", encoding="utf-8") as f:
    schema_dict = json.load(f)

task_cols = schema_dict["task_events"]["col_content"]
task_formats = schema_dict["task_events"]["col_format"]

type_map = {
    "INTEGER": IntegerType(),
    "FLOAT": FloatType(),
    "BOOLEAN": BooleanType(),
    "STRING_HASH": StringType(),
    "STRING": StringType()
}

col_types = [type_map[t] for t in task_formats]

spark = SparkSession.builder \
    .appName("TaskEventStream") \
    .getOrCreate()

spark.sparkContext.setLogLevel("INFO")

df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER) \
    .option("subscribe", TOPIC) \
    .option("startingOffsets", "earliest") \
    .load()

df_str = df_raw.selectExpr("CAST(value AS STRING) as csv_str")
df_split = df_str.withColumn("cols", split(col("csv_str"), ","))

df_parsed = df_split
for i, (c, t) in enumerate(zip(task_cols, col_types)):
    df_parsed = df_parsed.withColumn(c, col("cols").getItem(i).cast(t))

df_parsed = df_parsed.withColumn("time_ts", from_unixtime(col("time")).cast(TimestampType()))

agg_df = df_parsed.withWatermark("time_ts", "5 seconds") \
    .groupBy(window(col("time_ts"), "10 seconds")) \
    .count() \
    .selectExpr("window.start as window_start", "window.end as window_end", "count")

# Add a unique ID for Elasticsearch upsert
agg_df_with_id = agg_df.withColumn(
    "doc_id", 
    concat_ws("_", col("window_start").cast("string"), col("window_end").cast("string"))
)

query = agg_df_with_id.writeStream \
    .format("es") \
    .option("checkpointLocation", configs.TMP_DIR + "/spark_checkpoint") \
    .option("es.nodes", "elasticsearch") \
    .option("es.port", "9200") \
    .option("es.resource", ES_INDEX) \
    .option("es.mapping.id", "doc_id") \
    .option("es.nodes.wan.only", "true") \
    .outputMode("update") \
    .start()

query.awaitTermination()