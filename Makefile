# Start environment normally
up:
	docker compose up -d --remove-orphans

# Start and force recreate
up-force:
	docker compose up -d --force-recreate --remove-orphans

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
