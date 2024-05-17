#!/bin/sh
echo "Launching 3DBionotes-WS API (BWS) in PRODUCTION mode"

docker compose --env-file .env-prod -f docker-compose.production.yml up -d
