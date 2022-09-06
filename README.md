BWS

3DBionotes-WS API

INSTALLATION:

DEV
- docker-compose up --build
- docker-compose up -d
- docker-compose down

 Connection to the running container "bws_web_1" in DEV
- docker exec -it bws_web_1 /bin/bash

Run custom command. E.g: updateDB_fromIDRAssay for assay idr0094-ellinger-sarscov2
- docker exec -it bws_web_1 /bin/bash
- python manage.py updateDB_fromIDRAssay /data/IDR/idr0094-ellinger-sarscov2

Or alternativelly, run commands directly using the docker container command line:
- docker exec -it bws_web_1 python manage.py flush
- docker exec -it bws_web_1 python manage.py createsuperuser
- docker exec -it bws_web_1 python manage.py makemigrations
- docker exec -it bws_web_1 python manage.py migrate
- docker exec -it bws_web_1 python manage.py initBaseTables

Create superuser
docker exec -it <runningdocker_id> python manage.py createsuperuser

Django-debug-toolbar usage for APIs in DEV
In the browser, append "?debug-toolbar" at the end of url.
 e.g.: http://localhost:8003/api/LigandToImageData/?debug-toolbar

PROD
- docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
- docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Troubleshooting
 
**Issue:** New migration are ignored
*Resolution*: Remove absolutely all the tables (even default ones) from mysql server in phpadmin UI and restart docker container