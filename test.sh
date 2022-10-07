#!/bin/bash

SERVER="192.168.86.23"
API_URL="http://$SERVER:8000"
REDIS_URL="$SERVER:6379"
REDIS_PASS="eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81"
REDIS_CONNECT="redis-cli -h $SERVER -p 6379 --pass $REDIS_PASS"
echo "Running our tests..."

GET_SERVER=`curl -s -X GET $API_URL`
echo "Does the server respond?: $GET_SERVER"

REDIS_RESPONSE=`$REDIS_CONNECT ping`
echo "Can we connect to redis?: $REDIS_RESPONSE"
REDIS_PUB_RESPONSE=`$REDIS_CONNECT publish ch-zoom testing1234`
echo "Can we publish to redis?: $REDIS_PUB_RESPONSE"
# this is hard to do in a one-liner, needs a client really
#REDIS_SUB_RESPONSE=`$REDIS_CONNECT subscribe ch-zoom`
#echo "Can we subscribe to redis?: $REDIS_SUB_RESPONSE"


PUT_ZOOM_MUTED=`curl -s -X PUT $API_URL/zoom/muted`
echo "Putting muted zoom state: $PUT_ZOOM_MUTED"
#echo "Did a message show up in redis?" # this is hard to do in a one-liner, needs a client really/ thus the limitations of not-a-framework

#REDIS_CHECK_PUT_ZOOM_MUTED=`$REDIS_CONNECT get zoom_state`
#echo "Did the call show up in redis?: $REDIS_CHECK_PUT_ZOOM_MUTED"

PUT_ZOOM_UNMUTED=`curl -s -X PUT $API_URL/zoom/unmuted`
echo "Putting unmuted zoom state: $PUT_ZOOM_UNMUTED"

PUT_ZOOM_INACTIVE=`curl -s -X PUT $API_URL/zoom/inactive`
echo "Putting inactive zoom state: $PUT_ZOOM_INACTIVE"



# echo "Puting a new zoom state: unmuted"
# echo "Getting zoom state, should be unmuted."
#
# echo "Puting a new zoom state: muted"
# echo "Getting zoom state, should be muted."
#
# echo "Done running our tests."
