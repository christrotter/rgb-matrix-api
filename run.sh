#!/bin/bash
echo "Building docker images..."

cd app-api
echo "Building app-api image..."
docker build -t rgb-matrix-api:latest .
cd ..

cd app-client
echo "Building app-client image..."
docker build -t rgb-matrix-client:latest .
cd ..

