#!/usr/bin/env bash

REGISTRY=docker.mercator-ocean.fr
REGISTRY_URI="https://${REGISTRY}"
REGISTRY_REPOSITORY=${REGISTRY}/moi-docker
CONTAINER_IMAGE_NAME=eddy-tracking
CONTAINER_IMAGE_TAG=$(grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | tr -d '\r' | cut -d' ' -f3)

docker login ${REGISTRY_URI}
if docker manifest inspect ${REGISTRY_REPOSITORY}/${CONTAINER_IMAGE_NAME}:${CONTAINER_IMAGE_TAG} > /dev/null ; then
    echo "Image tag found on the Nexus, skipping build and publish"
else
    echo "Image tag does not exists on Nexus"
    docker build --ulimit nofile=65536:65536 --tag ${REGISTRY_REPOSITORY}/${CONTAINER_IMAGE_NAME}:${CONTAINER_IMAGE_TAG} --platform linux/amd64 .
    docker push ${REGISTRY_REPOSITORY}/${CONTAINER_IMAGE_NAME}:${CONTAINER_IMAGE_TAG}
fi
echo "Image link: $REGISTRY_REPOSITORY/$CONTAINER_IMAGE_NAME:$CONTAINER_IMAGE_TAG"
