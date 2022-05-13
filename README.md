BWS

3DBionotes-WS API

INSTALLATION:

DEV
- docker-compose up --build
- docker-compose up -d
- docker-compose down

 Connection to the running container "bws_web_1" in DEV
- docker exec -it bws_web_1 /bin/bash

PROD
- docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
- docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Troubleshooting
 
**Issue:** New migration are ignored
*Resolution*: Remove absolutely all the tables (even default ones) from mysql server in phpadmin UI and restart docker container