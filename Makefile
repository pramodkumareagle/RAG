SHELL := /bin/bash

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200 api

ingest:
	docker compose run --rm ingest

curl-ask:
	curl -s -X POST http://localhost:8000/v1/ask \
	  -H "Content-Type: application/json" \
	  -d '{"query":"What does this system do?"}' | jq
