# Default scale values (can be overridden via CLI)
KAFKA_SCALE ?= 1
SPARK_WORKER_SCALE ?= 2

# Start environment normally (with scale)
up:
	docker compose up -d \
		--scale kafka=$(KAFKA_SCALE) \
		--scale spark-worker=$(SPARK_WORKER_SCALE) \
		--remove-orphans

# Start and force recreate (with scale)
up-force:
	docker compose up -d --force-recreate \
		--scale kafka=$(KAFKA_SCALE) \
		--scale spark-worker=$(SPARK_WORKER_SCALE) \
		--remove-orphans

# Stop and remove services + volumes
down:
	docker compose down -v --remove-orphans

# Clean all Docker resources
clean:
	docker compose down -v --remove-orphans
# 	docker image prune -a -f
	docker volume prune -f
	docker network prune -f
	docker builder prune -a -f

# Fully reset (clean + start)
reset: clean up

# Restart
restart: down up
