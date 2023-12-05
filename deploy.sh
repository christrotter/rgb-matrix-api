#!/bin/bash
SERVER="192.168.86.185"

rsync -az --force --delete --progress \
    --exclude-from=.gitignore \
    -e "ssh -p22" ./ \
    pi@$SERVER:/home/pi/git/rgb-matrix-api


echo "Triggering the build on the remote Raspberry Pi..."
ssh pi@$SERVER 'bash -s' < ./build-n-run.sh

echo "Sleeping to let the client app spool up..."
sleep 5

echo "Running the tests..."
source ./test.sh
