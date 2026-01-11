#!/bin/bash
set -e

HOSTNAME=$(hostname)
echo "Starting Kafka host: $HOSTNAME"

# Wait for Zookeeper
while ! nc -z zookeeper 2181; do
  sleep 1
done
echo "Zookeeper ready"

# Check stale brokers
BROKER_IDS=$(echo "ls /brokers/ids" | zookeeper-shell zookeeper:2181 2>&1 | grep -E '^\[' | tr -d '[],' | tr ',' ' ' || echo "")

if [ -n "$BROKER_IDS" ]; then
  for BROKER_ID in $BROKER_IDS; do
    BROKER_INFO=$(echo "get /brokers/ids/$BROKER_ID" | zookeeper-shell zookeeper:2181 2>&1 || echo "")
    REGISTERED_HOST=$(echo "$BROKER_INFO" | grep -o '"host":"[^"]*"' | cut -d'"' -f4 || echo "")
    
    if [ "$REGISTERED_HOST" = "$HOSTNAME" ]; then
      echo "Deleting stale broker $BROKER_ID"
      echo "delete /brokers/ids/$BROKER_ID" | zookeeper-shell zookeeper:2181 2>/dev/null || true
      sleep 1
    fi
  done
fi

# Kafka config
export KAFKA_BROKER_ID_GENERATION_ENABLE=true
export KAFKA_RESERVED_BROKER_MAX_ID=1000
export KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
export KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:29092
export KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://$HOSTNAME:29092
export KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT
export KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT
export KAFKA_DELETE_TOPIC_ENABLE=true
export KAFKA_AUTO_CREATE_TOPICS_ENABLE=true

exec /etc/confluent/docker/run