IMAGE_NAME := pokemon-airflow
CONTAINER_NAME := pokemon-airflow-container
PORT := 8080

# Get current directory
PWD := $(shell pwd)

.PHONY: help build run stop clean query shell

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the Docker image using Python 3.14
	docker build -t $(IMAGE_NAME) .

run: ## Run Airflow in a container (Mounts ./airflow/dags and ./data)
	@mkdir -p data
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(PORT):8080 \
		-v $(PWD)/airflow/dags:/opt/airflow/dags \
		-v $(PWD)/data:/opt/airflow/data \
		$(IMAGE_NAME)
	@echo "Airflow is starting..."
	@echo "1. Wait a few seconds."
	@echo "2. Run 'make logs' to see the admin password."
	@echo "3. Go to http://localhost:$(PORT)"

logs: ## Follow container logs (Use this to find the Admin Password)
	docker logs -f $(CONTAINER_NAME)

stop: ## Stop and remove the container
	docker rm -f $(CONTAINER_NAME) || true

shell: ## Open a bash shell inside the container
	docker exec -it $(CONTAINER_NAME) bash

query: ## Query the SQLite DB inside the container
	@echo "Checking top 10 movies..."
	@docker exec -it $(CONTAINER_NAME) sqlite3 /opt/airflow/data/pokemon_movies.db \
	".mode column" ".headers on" \
	"SELECT title, release_date, last_updated FROM pokemon_movies ORDER BY last_updated DESC LIMIT 10;"

#clean: stop ## Remove the image and local data
#	docker rmi $(IMAGE_NAME) || true
#	rm -rf data/*.db

#admin: ## Create a default admin/admin user so you can log in easily
#	@echo "Creating user: admin / password: admin"
#	docker exec -it $(CONTAINER_NAME) airflow users create \
#		--username admin \
#		--password admin \
#		--firstname Admin \
#		--lastname User \
#		--role Admin \
#		--email admin@example.com

config: ## Create a default admin/admin user so you can log in easily
	docker exec -it $(CONTAINER_NAME) \
		 airflow config list --defaults
		 # > "/opt/airflow/airflow.cfg"