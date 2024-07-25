#!/bin/sh
echo "Launching 3DBionotes-WS API (BWS) in development mode"

docker compose --env-file .env-dev -f docker-compose.develop.yml -f docker-compose.elastic.yml up -d