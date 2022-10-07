# rgb-matrix-api
Overly complicated way of using Python FastAPI/async and Redis to create an API for things like zoom mute status indication.

![](images/rgb-matrix-new_icons.png)

* When Zoom is not running/not in a meeting, you get a simple date/time display.
* When you are in a meeting and muted, a red 'muted' image is displayed.
* When you are in a meeting and unmuted, a green 'on the air' image is displayed.

# Early demo
https://www.youtube.com/watch?v=dxMZ7T-pGdI

# Future ideas
- [ ] Text endpoints
- [x] Pre-loaded image/gif endpoints
- [ ] Other application endpoints

# Architecture
![](images/rgb-matrix-diagram.png)

# API documentation
FastAPI is kinda nifty, so you can get api docs at http://localhost:8000/docs , like this:
![](images/rgb-matrix-fastapi.png)

# Setup
Swiftbar: https://github.com/swiftbar/SwiftBar

I found the script code guts here: https://dustin.lol/post/2021/better-zoom-mute/

## SwiftBar timing
Note that the filename is used by SwiftBar for timing: `zoom-mute.500ms.sh`
So if you want to adjust timing, you change the filename.

# Panel stand
Quick DIY job on my part...
![](images/rgb-matrix-fusion.png)
![](images/rgb-matrix-3dprint.png)

# Raspberry Pi Setup
You are sudo installing a lot because the matrix libraries require sudo access for performance reasons.

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
## SSH access
Don't forget to add your ssh public key to: `~/.ssh/authorized_keys`

## Setting up the rgb libraries
This needs to be done on the Raspberry Pi, I could not get it to run on my Mac - but that could be due to work local dev enviro stuff.
```
git clone git@github.com:hzeller/rpi-rgb-led-matrix.git
cd ~/git/rpi-rgb-led-matrix/bindings/python
make build-python PYTHON=$(command -v python3)
sudo make install-python PYTHON=$(command -v python3)
```

# Docker environment
We need to run the api, redis, and the matrix-runner.
- [ ] TODO: move api and matrix-runner into docker

# Development
The dev workflow looks like this...
- Run deploy.sh
  - this copies all files over rsync
  - restarts the service
- Run deploy-swiftbar.sh
  - this copies your swiftbar plugin to the right place, and it should automatically start working
- Run test.sh
  - this makes curl calls to test the functionality of your changes
- Look at the logging output to see what's happening
