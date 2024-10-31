BWS

3DBionotes-WS API

PREREQUISITES:

Manage Docker Compose as a non-root user
```
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

START DEV INSTANCE:

1. Create .env-dev file from sample.env-dev

2. Add the `db.sqlite3` file in `/app/bws/` directory

3. Start/stop application

Start application and elasticsearch containers in deteched mode:

```
bash run-dev.sh
or
docker compose --env-file .env-dev -f docker-compose.develop.yml up -d
```

Re-build application or elasticsearch containers:

```
docker compose --env-file .env-dev -f docker-compose.develop.yml up -d --build
```

Stop all docker containers:

```
docker compose --env-file .env-dev -f docker-compose.develop.yml down
```

Connect to the running app container "web":

```
docker exec -it web bash
```

Connect to the elasticsearch container "elasticsearch"

```
docker exec -it elasticsearch bash
```

START PROD INSTANCE:

1. Create docker image and push to registry

```
docker build -t bws_container_image_name -f app/Dockerfile-prod ./app
docker push bws_container_image_name
```
If registry.gitlab.com will be used, example of bws_container_image_name should be something like registry.gitlab.com/jrmacias/bws/web:production

2. Copy docker-compose.production.yml to the targeting production server

3. Copy ./nginx and ./tools directories to the same location as docker-compose.production.yml on targeting production server

4. Create .env-prod file from sample.env-prod on same location as docker-compose.production.yml on targeting production server

5. Start application

```
bash run-prod.sh
or
docker compose --env-file .env-prod -f docker-compose.production.yml up -d
```

Connect to DB running in "bws-db-1" container in PROD:

```
docker exec -it bws-db-1 mysql -uroot -p
Provide DB_ROOT_PASSWD
```

MySQL Docker Container commands:

```
USE DB_NAME
show tables;
SELECT * FROM table_name;
SELECT * FROM table_name WHERE column_name = value;
SELECT * FROM table_name WHERE column_name LIKE '%word%';
```

Connect to the running app container "bws-web-1":

```
docker exec -it bws-web-1 /bin/bash
```

Run custom command. E.g: updateDB_fromIDRAssay for assay idr0094-ellinger-sarscov2:

```
docker exec -it bws-web-1 /bin/bash
python manage.py updateDB_fromIDRAssay /data/IDR/idr0094-ellinger-sarscov2
```

Or alternativelly, run commands directly using the docker container command line:

```
docker exec -it bws-web-1 python manage.py flush
docker exec -it bws-web-1 python manage.py createsuperuser
docker exec -it bws-web-1 python manage.py makemigrations
docker exec -it bws-web-1 python manage.py migrate
docker exec -it bws-web-1 python manage.py initBaseTables
docker exec -it bws-web-1 python manage.py updateEntriesFromDir /data/covid/
docker exec -it bws-web-1 python manage.py updateDB_fromHCSAssay /data/IDR/idr0094-ellinger-sarscov2
docker exec -it bws-web-1 python manage.py update_NMR_binding /data/C19-NMR-C/C19-NMR-C_pre-processed_data.csv
docker exec -it bws-web-1 python manage.py update_NMR_docking /data/C19-NMR-C/C19-NMR-C_All_Proteins_pre-processed_data.csv
docker exec -it bws-web-1 python manage.py initUniProtEntry /data/SARS-CoV-2/UniProtEntry_covid19-proteome.csv
docker exec -it bws-web-1 python manage.py initPTMEntity /data/SARS-CoV-2/PTMEntity_covid19-proteome.csv
docker exec -it bws-web-1 python manage.py initDomainEntity /data/SARS-CoV-2/DomainEntity_covid19-proteome.csv
```

Pre-Process data from COVID19 NMR Consortium (C19-NMR-C):

```
docker exec -it bws-web-1 python /tools/pre-process_data.py -i /data/C19-NMR-C/C19-NMR-C-Summary/Summary-ordered.csv -o /data/C19-NMR-C/C19-NMR-C_pre-processed_data.csv
docker exec -it bws-web-1 python /tools/pre-process_data.py -i /data/C19-NMR-C/All_Proteins_CNB_CSIC.csv -o /data/C19-NMR-C/C19-NMR-C_All_Proteins_pre-processed_data.csv 
```

Create superuser:

```
docker exec -it bws-web-1 python manage.py createsuperuser
```

Django-debug-toolbar usage for APIs in DEV
In the browser, append "?debug-toolbar" at the end of url.
 e.g.: http://localhost:8003/api/LigandToImageData/?debug-toolbar

ELASTICSEARCH

- default user: elastic

Troubleshooting

Fixing message from Elasticsearch:
 - flood stage disk watermark [95%] exceeded...

ON the container console, run:
- curl -XPUT -H "Content-Type: application/json" http://localhost:9200/_cluster/settings -d '{ "transient": { "cluster.routing.allocation.disk.threshold_enabled": false } }'
- curl -XPUT -H "Content-Type: application/json" http://localhost:9200/_all/_settings -d '{"index.blocks.read_only_allow_delete": null}'

