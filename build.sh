#!/bin/bash
# Build the image
docker build --build-arg UID=$(id -u) \
    --build-arg GID=$(id -g) \
    -t hemna/goesutils:latest \
    .
