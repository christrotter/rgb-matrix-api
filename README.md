# rgb-matrix-api
Overly complicated way of using Python FastAPI/async and Redis to create an API for things like zoom mute status indication.

* When Zoom is not running/not in a meeting, a white fill is applied.
* When you are in a meeting and muted, a red fill is applied.
* When you are in a meeting and unmuted, a green fill is applied.

Future ideas are...
- Text endpoints
- Pre-loaded image/gif endpoints
- Other application endpoints

# Architecture
![](images/rgb-matrix-diagram.png)

# API documentation
FastAPI is kinda nifty, so you can get api docs at http://localhost:8000/docs , like this:
![](images/rgb-matrix-fastapi.png)

# Setup
Swiftbar: https://github.com/swiftbar/SwiftBar


# Raspberry Pi Setup
```
brew install fastapi OR pip install fastapi
sudo pip install "uvicorn[standard]"
sudo pip install aioredis
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker pi
docker run hello-world
sudo systemctl enable docker
sudo curl -SL https://github.com/docker/compose/releases/download/v2.11.2/docker-compose-linux-armv6 -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
echo "alias redis-cli='docker exec -it rgb-matrix-api-cache-1 redis-cli'" >> ~/.bashrc
```
## Setting up the rgb libraries
```
cd ~/git/rpi-rgb-led-matrix/bindings/python
make build-python PYTHON=$(command -v python3)
sudo make install-python PYTHON=$(command -v python3)
```

# Docker environment
We need to run the api, redis, and the matrix-runner.
todo: move api and matrix-runner into docker

# Development

- Run deploy.sh
  - this copies all files over rsync
  - restarts the service
- Run deploy-swiftbar.sh
  - this copies your swiftbar plugin to the right place, and it should automatically start working
- Run test.sh
  - this makes curl calls to test the functionality of your changes

## Available api calls
### get
- zoom state (muted, unmuted, inactive)

### post
- change zoom state to

## using the api
curl get api/zoom/state
curl post api/zoom/statechange

## testing the api
- change zoom state to muted
- change zoom state to unmuted
- get zoom state
