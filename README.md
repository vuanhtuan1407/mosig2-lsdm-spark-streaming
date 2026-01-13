1. Pre-requirements

- Docker
- GNU Make

2. Build docker environment using Make

Run the following command to build docker enviroment (or active docker enviroment if not the first build)

```
make
```

Other command with `make` are found in `Makefile`

3. Active Client App in docker container

Client App is the simulation enviroment of client system, where we mainly working in.

```
bash active-env.sh
```

4. Run process

After we entered the client-app container, we can run the simulation to simulate data generating process, run the producer and submit spark job

- Run simulation:

```
python3 src/simulation.py --rate 0.01
```

or simply

```
bash scripts/run_simulation.sh
```

- Run producer process:

```
python3 src/producer.py
```

or simply

```
bash scripts/producer.sh
```

- Submit spark job

```
spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.jars.ivy=/workspace/app/opt/ivy2 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.3,org.elasticsearch:elasticsearch-spark-30_2.12:8.8.2 \
  src/spark_job.py
```

or simply

```
bash scripts/submit_spark_job.sh
```

**Note**: This Spark streaming job reads task events from Kafka, calculates failure metrics (fail count, evict count, kill count, and failure rate) per machine and job using 2-minute sliding windows, and writes the results to Elasticsearch for real-time monitoring.

5. Some frequently used commands for Elasticsearch (in Terminal)

List all indices

```
curl -X GET "localhost:9200/_cat/indices?v"
```

Count documents

```
curl -X GET "localhost:9200/<index_name>/_count?pretty"
```

Search all documents in an index

```
curl -X GET "localhost:9200/<index_name>/_search?pretty"
```

Delete an index

```
curl -X DELETE "localhost:9200/<index_name>"
```

6. Query and visualisation with Kibana

- Query with Kibana Dev Tools

Open Kibana Dev Tools (Menu → Management → Dev Tools) to execute Elasticsearch queries directly.

Example 1: Search for failed tasks in the last hour

```
GET /task_events_metrics/_search
{
  "query": {
    "bool": {
      "must": [
        { "range": { "window_start": { "gte": "now-1h" } } },
        { "range": { "fail_rate": { "gt": 0 } } }
      ]
    }
  },
  "sort": [ { "fail_rate": { "order": "desc" } } ]
}
```

Example 2: Aggregate failure metrics by machine

```
GET /task_events_metrics/_search
{
  "size": 0,
  "aggs": {
    "by_machine": {
      "terms": { "field": "machine_ID" },
      "aggs": {
        "avg_fail_rate": { "avg": { "field": "fail_rate" } },
        "total_fails": { "sum": { "field": "total_fail_count" } }
      }
    }
  }
}
```

- Visualisation

**Step 1: Create Data View**
    
1/ Go to Menu → Management → Stack Management → Data Views

2/ Click Create data view

3/ Enter name (e.g., "Task Metrics") and index pattern (e.g., task_events_metrics*)

4/ Select timestamp field (e.g., window_start)

5/ Click Save data view

**Step 2: Create Visualisation**

1/ Go to Menu → Analytics → Visualize Library

2/ Click Create visualization

3/ Select visualization type (e.g., Line chart, Bar chart, Pie chart)

4/ Choose your data view created in Step 1

5/ Configure the visualization:

- Vertical axis: Select metric (e.g., Average of fail_rate)
- Horizontal axis: Select time field (e.g., window_start)
- Break down by: Add dimensions (e.g., machine_ID, job_ID)

6/ Click Save and name your visualization

