# how to run docker compose

1. Create a docker volume and point it to your data folder: `docker volume create --drive


# How to build images

### Setup
1. Allow insecure registries on docker, in docker-engine add "docker-registry.tracksandwheels.com:5050" to the insecure registry list.

## Build Images
1. CD into project directory.
    If on new computer pull latest images from docker registry
    ```
    docker image pull -a docker-registry.tracksandwheels.com:5050/log_processor
    docker image pull -a docker-registry.tracksandwheels.com:5050/log_webserver
    ```
2. Build the images (may need sudo)
```
 docker build -t docker-registry.tracksandwheels.com:5050/log_processor:latest -f .\processor\Dockerfile .
 docker build -t docker-registry.tracksandwheels.com:5050/log_webserver:latest -f .\webserver\Dockerfile .
```
3. Tag images if versions are required
```
docker image tag docker-registry.tracksandwheels.com:5050/log_processor:latest docker-registry.tracksandwheels.com:5050/log_processor:v0.3.9
docker image tag docker-registry.tracksandwheels.com:5050/log_webserver:latest docker-registry.tracksandwheels.com:5050/log_webserver:v0.3.9
``` 
4. Push images to server 
```
docker image push -a docker-registry.tracksandwheels.com:5050/log_processor
docker image push -a docker-registry.tracksandwheels.com:5050/log_webserver
```

# Run with built images
`docker compose up`


docker build -t docker-registry.tracksandwheels.com:5050/log_processor:latest -f .\processor\Dockerfile .
docker build -t docker-registry.tracksandwheels.com:5050/log_webserver:latest -f .\webserver\Dockerfile .
 
docker image tag docker-registry.tracksandwheels.com:5050/log_processor:latest docker-registry.tracksandwheels.com:5050/log_processor:v0.2
docker image tag docker-registry.tracksandwheels.com:5050/log_webserver:latest docker-registry.tracksandwheels.com:5050/log_webserver:v0.2

docker image push -a docker-registry.tracksandwheels.com:5050/log_processor
docker image push -a docker-registry.tracksandwheels.com:5050/log_webserver
