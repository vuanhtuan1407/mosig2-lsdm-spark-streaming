DATA_DIR = 'data/clusterdata-2011-2/'
OUTPUT_DIR = 'output/'
SCHEMA_DICT_PATH = OUTPUT_DIR + 'schema_dict.json'
LOGS_DIR = 'logs/'
TMP_DIR = 'tmp/'

KAFKA_BROKER = "kafka:29092"
TOPIC = "cluster-metrics"

ES_TASK_EVENT_INDEX = "task_events"

EVENT_TYPE = {
    "SUBMIT": 0,
    "SCHEDULE": 1,
    "EVICT": 2,
    "FAIL": 3,
    "FINISH": 4,
    "KILL": 5
}

