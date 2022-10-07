#!/bin/bash
SERVER="192.168.86.23"

rsync -az --force --delete --progress \
    --exclude-from=.gitignore \
    -e "ssh -p22" ./ \
    pi@$SERVER:/home/pi/git/rgb-matrix-api

# TODO: change this to a docker deploy...
