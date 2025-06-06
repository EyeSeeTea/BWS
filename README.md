# BWS (3DBionotes Web Service API)

## Project Overview 

This repository includes a Django-based API and an Elasticsearch service, both deployed as Docker instances. The Django application serves as the backbone for handling all API requests on 3DBionotes, while Elasticsearch is utilized for providing search suggestions in the 3DBionotes COVID-19 tab.

## Installation

Follow these steps to set up and run the Django application and the Elasticsearch in a Docker container.

### Prerequisites

Before you begin, ensure you have the following installed on your machine:

- [Docker](https://www.docker.com/get-started) (latest stable version)
- [Docker Compose](https://docs.docker.com/compose/install/) (if not included with Docker)
- Manage Docker Compose as a non-root user
```shell
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

### Getting the Code

Clone this repository to your local machine:

```shell
git clone git@github.com:EyeSeeTea/BWS.git
cd BWS
```

## Setup development

1. Copy `.env` file to `.env.dev` and change the values as needed
2. Add the `db.sqlite3` file in `/app/bws/` directory (this file will be provided to you)
3. Start application (detached mode)
```shell
docker compose --env-file .env.dev -f docker-compose.development.yml up -d
```

Additional commands:
- Re-build containers in detached mode
```shell
docker compose --env-file .env.dev -f docker-compose.development.yml up -d --build

# This command should be executed in the following scenarios:
# - When you have made changes to the Dockerfile or any files that are copied into the container during the build process.
# - When you need to update the dependencies or packages installed in the container.
# - When you want to ensure that the container is using the latest version of the base image or any other dependencies.
```
- Stop all docker containers
```shell
docker compose --env-file .env.dev -f docker-compose.development.yml down
```
- Access shell (Replace `<container_name>` with the name or ID of your Docker container. You can find the container name by running `docker ps`:
```shell
docker exec -it <container_name> bash
```

## Setup production

1. Copy `.env` file to `.env.prod` and change the values as needed (including the database variables)
2. Build docker containers
```shell
docker compose --env-file .env.prod -f docker-compose.production.yml build

# This command should be executed in the following scenarios:
# - When you have made changes to the Dockerfile or any files that are copied into the container during the build process.
# - When you need to update the dependencies or packages installed in the container.
# - When you want to ensure that the container is using the latest version of the base image or any other dependencies.
```
3. Start application (detached mode)
```shell
docker compose --env-file .env.prod -f docker-compose.production.yml up -d
```

Additional commands:
- Connect to DB running in the web container for PROD:
```shell
docker exec -it bws-prod-web-1 mysql -u root -p
# Provide DB_ROOT_PASSWD
```
- MySQL Docker Container commands:
```sql
USE DB_NAME
show tables;
SELECT * FROM table_name;
SELECT * FROM table_name WHERE column_name = value;
SELECT * FROM table_name WHERE column_name LIKE '%word%';
```
- Run custom command (tools). E.g: updateDB_fromIDRAssay for assay idr0094-ellinger-sarscov2:
```shell
docker exec -it bws-prod-web-1 bash
python manage.py updateDB_fromIDRAssay /data/IDR/idr0094-ellinger-sarscov2
```
- Or alternativelly, run commands directly using the docker container command line:
```shell
docker exec -it bws-prod-web-1 <command>
```
- List of useful commands:
```shell
docker exec -it bws-prod-web-1 python manage.py flush
docker exec -it bws-prod-web-1 python manage.py createsuperuser
docker exec -it bws-prod-web-1 python manage.py makemigrations
docker exec -it bws-prod-web-1 python manage.py migrate
docker exec -it bws-prod-web-1 python manage.py initBaseTables
docker exec -it bws-prod-web-1 python manage.py updateEntriesFromDir /data/covid/
docker exec -it bws-prod-web-1 python manage.py updateDB_fromHCSAssay /data/IDR/idr0094-ellinger-sarscov2
docker exec -it bws-prod-web-1 python manage.py update_NMR_binding /data/C19-NMR-C/C19-NMR-C_pre-processed_data.csv
docker exec -it bws-prod-web-1 python manage.py update_NMR_docking /data/C19-NMR-C/C19-NMR-C_All_Proteins_pre-processed_data.csv
docker exec -it bws-prod-web-1 python manage.py initUniProtEntry /data/SARS-CoV-2/UniProtEntry_covid19-proteome.csv
docker exec -it bws-prod-web-1 python manage.py initPTMEntity /data/SARS-CoV-2/PTMEntity_covid19-proteome.csv
docker exec -it bws-prod-web-1 python manage.py initDomainEntity /data/SARS-CoV-2/DomainEntity_covid19-proteome.csv
```
- Pre-Process data from COVID19 NMR Consortium (C19-NMR-C):
```shell
docker exec -it bws-prod-web-1 python /tools/pre-process_data.py -i /data/C19-NMR-C/C19-NMR-C-Summary/Summary-ordered.csv -o /data/C19-NMR-C/C19-NMR-C_pre-processed_data.csv
docker exec -it bws-prod-web-1 python /tools/pre-process_data.py -i /data/C19-NMR-C/All_Proteins_CNB_CSIC.csv -o /data/C19-NMR-C/C19-NMR-C_All_Proteins_pre-processed_data.csv 
```
- Create superuser:
```shell
docker exec -it bws-prod-web-1 python manage.py createsuperuser
```

### Django-debug-toolbar usage for APIs in DEV
In the browser, append "?debug-toolbar" at the end of url.
 e.g.: http://localhost:8000/api/pdbentry/?debug-toolbar

### Elasticsearch
Default user: elastic

### Troubleshooting
Fixing message from Elasticsearch: `flood stage disk watermark [95%] exceeded...`

On the container console, run:
```shell
curl -XPUT -H "Content-Type: application/json" http://localhost:9200/_cluster/settings -d '{ "transient": { "cluster.routing.allocation.disk.threshold_enabled": false } }'
curl -XPUT -H "Content-Type: application/json" http://localhost:9200/_all/_settings -d '{"index.blocks.read_only_allow_delete": null}'
```
