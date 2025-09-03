# Running with Docker Compose

This guide explains how to build, tag, push, and run the project images using Docker Compose.

The file `docer-compose.yml` is a basic configuration that will work for most setups.

## 1. Prepare a Data Volume
Create a Docker volume that points to your data folder:

``` bash
docker volume create \
  --driver local \
  --opt type=none \
  --opt device=/path/to/your/data/folder \
  --opt o=bind \
  your_volume_name
```

## 2. Setup Environment

#### Set registry URL (if using an external registry):

``` bash
export DOCKER_REGISTRY_URL=docker-registry.test.com:5050/
```

(On Windows PowerShell: `setx DOCKER_REGISTRY_URL "docker-registry.test.com:5050/"`)


Note: if not using an external registry, set DOCKER_REGISTRY_URL to empty string:

``` bash
export DOCKER_REGISTRY_URL=""
```

#### Allow insecure registries

Add ${DOCKER_REGISTRY_URL} to Docker’s insecure registry list (configure in Docker Engine settings).

## 3. Build Images

### Option 1: Build Locally
For Linux
``` bash
sudo docker build -t ${DOCKER_REGISTRY_URL}log_processor:latest -f ./processor/Dockerfile .
sudo docker build -t ${DOCKER_REGISTRY_URL}log_webserver:latest -f ./webserver/Dockerfile .
```

For Windows
``` powershell
docker build -t ${DOCKER_REGISTRY_URL}log_processor:latest -f .\processor\Dockerfile .
docker build -t ${DOCKER_REGISTRY_URL}log_webserver:latest -f .\webserver\Dockerfile .
```

Tag Versions (If required)
``` bash
docker image tag ${DOCKER_REGISTRY_URL}log_processor:latest ${DOCKER_REGISTRY_URL}log_processor:v0.3.11
docker image tag ${DOCKER_REGISTRY_URL}log_webserver:latest ${DOCKER_REGISTRY_URL}log_webserver:v0.3.11
```

Push to registry (if required):
```bash
docker image push -a ${DOCKER_REGISTRY_URL}log_processor
docker image push -a ${DOCKER_REGISTRY_URL}log_webserver
```

### Option 2: Pull existing images (optional, if docker registry is set up)

``` bash
docker image pull -a ${DOCKER_REGISTRY_URL}log_processor
docker image pull -a ${DOCKER_REGISTRY_URL}log_webserver
```

1. Create a docker volume and point it to your data folder: `docker volume create --driver local --opt type=none --opt device=/path/to/your/data/folder --opt o=bind your_volume_name`


## 4. Run with Docker Compose
``` bash
docker compose up
```
Note: sudo may be required on Linux