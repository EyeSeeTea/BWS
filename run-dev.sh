#!/bin/sh
echo "Launching 3DBionotes-WS API (BWS) in development mode"

docker compose --env-file .env-dev -f docker-compose.develop.yml up -d