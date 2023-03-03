BWS

3DBionotes-WS API

PREREQUISITES:

Manage Docker Compose as a non-root user
```
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

INSTALLATION:

DEV
- docker-compose up --build / docker compose up --build
- docker-compose up -d / docker compose up -d
- docker-compose down / docker compose down

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
- docker exec -it bws_web_1 python manage.py updateDB_fromHCSAssay /data/IDR/idr0094-ellinger-sarscov2

Pre-Process data from COVID19 NMR Consortium (C19-NMR-C)
- docker exec -it bws_web_1 python3 /tools/pre-process_data.py -i /data/C19-NMR-C/C19-NMR-C-Summary/Summary-ordered.csv -o /data/C19-NMR-C/C19-NMR-C_pre-processed_data.csv
- docker exec -it bws_web_1 python3 /tools/pre-process_data.py -i /data/C19-NMR-C/All_Proteins_CNB_CSIC.csv -o /data/C19-NMR-C/C19-NMR-C_All_Proteins_pre-processed_data.csv 


Create superuser
docker exec -it <runningdocker_id> python manage.py createsuperuser

Django-debug-toolbar usage for APIs in DEV
In the browser, append "?debug-toolbar" at the end of url.
 e.g.: http://localhost:8003/api/LigandToImageData/?debug-toolbar

PROD
- docker-compose up --build
- docker-compose down -v

# Troubleshooting
 
**Issue:** New migration are ignored
*Resolution*: Remove absolutely all the tables (even default ones) from mysql server in phpadmin UI and restart docker container