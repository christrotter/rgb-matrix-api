# rgb-matrix-api
Overly complicated way of using Python FastAPI/async and Redis to create an API for things like zoom mute status indication.

# Functionality

# Setup
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

# Docker environment
We need to run the api, redis, and the matrix-runner.
todo: move api and matrix-runner into docker

# How the old scoreboard worked

updatematrix
- init
  - set threading.lock
- message
  - acquire lock
  - MatrixWrapper.Instance().drawText(message)
  - release lock
- image
  - acquire lock
  - MatrixWrapper.Instance().drawAnimationFromFile(image)
  - release lock
- default
  - acquire lock
  - redis setup
  - get current score from redis
  - if no score, draw the time
  - else
    - load score(arrow, scoredata)
  - release lock

listener
- init, set up pubsub connection, subscribe to channels
- run, look at items in self.pubsub.listen
  - if channel X, UpdateMatrix.Instance().message/image/anim/aud

if main
- conf
- create listener client
- start listener client w. daemon
- print interface text
- while True
  - UpdateMatrix.Instance().default()
  - sleep .25s


## Setting up the rgb libraries
```
cd ~/git/rpi-rgb-led-matrix/bindings/python
make build-python PYTHON=$(command -v python3)
sudo make install-python PYTHON=$(command -v python3)
```


# Development

- Run deploy.sh
  - this copies all files over rsync
  - restarts the service
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
