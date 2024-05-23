#!/bin/sh
echo "Launching 3DBionotes-WS API (BWS) in PRODUCTION mode"

docker compose --env-file .env-prod -f compose-prod.yaml up -d
