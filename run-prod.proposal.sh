#!/bin/sh
echo "Launching 3DBionotes-WS API (BWS) in PRODUCTION mode"

# Build image locally for testing
## export environment variables IMAGE_NAME, USER_NAME, USER_UID, or write them explicitely
docker build -t ${IMAGE_NAME} --build-arg USER_NAME=${USER_NAME} --build-arg USER_UID=${USER_UID} -f app/Dockerfile-prod .

# start project from image created in previous command
docker compose --env-file .env-prod -f docker-compose.production.yml up -d