#!/bin/bash

SERVER="192.168.86.23"
API_URL="http://$SERVER:8000"
REDIS_URL="$SERVER:6379"
REDIS_PASS="eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81"
REDIS_CONNECT="redis-cli -h $SERVER -p 6379 --pass $REDIS_PASS"
echo "Running our tests..."

GET_SERVER=`curl -s -X GET $API_URL`
echo "Is the API server up?: $GET_SERVER"

REDIS_RESPONSE=`$REDIS_CONNECT ping`
echo "Is Redis up?: $REDIS_RESPONSE"

echo "Testing network indicator colours..."
PUT_NETWORK_RED=`curl -s -X PUT $API_URL/network/red`
echo "Red..."
sleep 2
PUT_NETWORK_YELLOW=`curl -s -X PUT $API_URL/network/yellow`
echo "Yellow..."
sleep 2
PUT_NETWORK_GREEN=`curl -s -X PUT $API_URL/network/green`
echo "Green..."
sleep 2

echo "Testing Zoom screens..."
PUT_ZOOM_MUTED=`curl -s -X PUT $API_URL/zoom/muted`
echo "Putting muted zoom state..."
sleep 2

PUT_ZOOM_UNMUTED=`curl -s -X PUT $API_URL/zoom/unmuted`
echo "Putting unmuted zoom state..."
sleep 2


# echo "Puting a new zoom state: unmuted"
# echo "Getting zoom state, should be unmuted."
#
# echo "Puting a new zoom state: muted"
# echo "Getting zoom state, should be muted."
#
# echo "Done running our tests."
