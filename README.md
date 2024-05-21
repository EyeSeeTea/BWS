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
- docker compose --env-file .env-dev -f compose-dev.yaml up
- docker compose --env-file .env-dev -f compose-dev.yaml up --build
- docker compose --env-file .env-dev -f compose-dev.yaml down
- docker compose --env-file .env-dev -f compose-dev.yaml down -v

 Connection to the running container "bws-web-1" in DEV
- docker exec -it bws-web-1 /bin/bash

Connection to running db container "bws-db-1" in DEV
- docker exec -it bws-db-1 mysql -uroot -p
  Provide DB_ROOT_PASSWD

MySQL Docker Container commands:
- USE DB_NAME
- show tables;
- SELECT * FROM table_name;
- SELECT * FROM table_name WHERE column_name = value;
- SELECT * FROM table_name WHERE column_name LIKE '%word%';

Run custom command. E.g: updateDB_fromIDRAssay for assay idr0094-ellinger-sarscov2
- docker exec -it bws-web-1 /bin/bash
- python manage.py updateDB_fromIDRAssay /data/IDR/idr0094-ellinger-sarscov2

Or alternativelly, run commands directly using the docker container command line:
- docker exec -it bws-web-1 python manage.py flush
- docker exec -it bws-web-1 python manage.py createsuperuser
- docker exec -it bws-web-1 python manage.py makemigrations
- docker exec -it bws-web-1 python manage.py migrate
- docker exec -it bws-web-1 python manage.py init_base_tables
- docker exec -it bws-web-1 python manage.py init_nmr_targets
- docker exec -it bws-web-1 python manage.py update_entries_from_dir /data/covid/
- docker exec -it bws-web-1 python manage.py updateDB_fromHCSAssay /data/IDR/idr0094-ellinger-sarscov2
- docker exec -it bws-web-1 python manage.py update_NMR_binding /data/C19-NMR-C/C19-NMR-C_pre-processed_data.csv
- docker exec -it bws-web-1 python manage.py update_NMR_docking /data/C19-NMR-C/C19-NMR-C_All_Proteins_pre-processed_data.csv
- docker exec -it bws-web-1 python manage.py initUniProtEntry /data/SARS-CoV-2/UniProtEntry_covid19-proteome.csv
- docker exec -it bws-web-1 python manage.py initPTMEntity /data/SARS-CoV-2/PTMEntity_covid19-proteome.csv
- docker exec -it bws-web-1 python manage.py initDomainEntity /data/SARS-CoV-2/DomainEntity_covid19-proteome.csv


Pre-Process data from COVID19 NMR Consortium (C19-NMR-C)
- docker exec -it bws-web-1 python3 /tools/pre-process_data.py -i /data/C19-NMR-C/C19-NMR-C-Summary/Summary-ordered.csv -o /data/C19-NMR-C/C19-NMR-C_pre-processed_data.csv
- docker exec -it bws-web-1 python3 /tools/pre-process_data.py -i /data/C19-NMR-C/All_Proteins_CNB_CSIC.csv -o /data/C19-NMR-C/C19-NMR-C_All_Proteins_pre-processed_data.csv 


Create superuser
docker exec -it <runningdocker_id> python manage.py createsuperuser

Django-debug-toolbar usage for APIs in DEV
In the browser, append "?debug-toolbar" at the end of url.
 e.g.: http://localhost:8003/api/LigandToImageData/?debug-toolbar

PROD
- docker compose --env-file .env-prod -f compose-prod.yaml up
- docker compose --env-file .env-prod -f compose-prod.yaml up --build
- docker compose --env-file .env-prod -f compose-prod.yaml up -d

Once running, some initial setup is required (create DB tables, etc)., in a separate terminal:
- docker exec -t -i bws-prod-web-1 /bin/bash
-   python manage.py collectstatic
-   python manage.py migrate
-   python manage.py createsuperuser
-   exit

- docker compose --env-file .env-prod -f compose-prod.yaml down
- docker compose --env-file .env-prod -f compose-prod.yaml down -v

# Troubleshooting
 
**Issue:** New migration are ignored
*Resolution*: Remove absolutely all the tables (even default ones) from mysql server in phpadmin UI and restart docker container