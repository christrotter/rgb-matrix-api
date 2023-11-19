#!/bin/bash

# <bitbar.title>Zoom Mute w/ The Key v2</bitbar.title>
# <bitbar.version>v1.0</bitbar.version>
# <bitbar.author>Dustin</bitbar.author>
# <bitbar.author.github>dustincredible</bitbar.author.github>
# <bitbar.desc>Reports the mute status of a Zoom meeting. Relies on menu bar item names, so this will only work if your Zoom app is using english. Only partially works for Zoom webinars.</bitbar.desc>
# <bitbar.image>https://user-images.githubusercontent.com/14987234/104110931-77e27f00-5291-11eb-98fb-47cf1febd84e.png</bitbar.image>


SERVER="192.168.86.37"
API_URL="http://$SERVER:8000"
ENABLED=true # or set to true if you want messages flowing

# Check the Enable Global Shortcut for Mute/unmute in Zoom settings
if [[ "$1" = "toggle" ]]; then
	osascript -e 'tell application "System Events" to keystroke "a" using {command down, shift down}'
fi

if [[ "$1" = "launch" ]]; then
	osascript -e '
		tell application "zoom.us"
			activate
		end tell
	'
fi

zm_prev=$(<~/zm.log)

zm_status=$(osascript -e'
	tell application "System Events"
		if (get name of every application process) contains "zoom.us" then
			tell application "System Events" to tell application process "zoom.us"
				if menu item "Join Audio" of menu 1 of menu bar item "Meeting" of menu bar 1 exists then
					return 1
				else
					if (menu item "Mute audio" of menu 1 of menu bar item "Meeting" of menu bar 1 exists) or (menu item "Mute telephone" of menu 1 of menu bar item "Meeting" of menu bar 1 exists) then
						return true
					else
						if (menu item "Unmute audio" of menu 1 of menu bar item "Meeting" of menu bar 1 exists) or (menu item "Unmute telephone" of menu 1 of menu bar item "Meeting" of menu bar 1 exists) then
							return false
						else
							return off
						end if
					end if
				end if
			end tell
		else
			return off
		end if
	end tell
	');

if [ "$zm_status" != "$zm_prev" ]; then
	echo "$zm_status" > ~/zm.log
fi

if [ "$zm_status" == "true" ]; then
    echo "🟢" #text version echo "Unmuted| color=#00FF00"
	echo ---
	echo "Mute| bash='$0' param1=toggle terminal=false"
    if [[ $ENABLED ]]; then
        STATE=`curl --connect-timeout 1 -X GET $API_URL/zoom/state | tr -d \"`
        if [ "$STATE" != "unmuted" ]; then
            curl --connect-timeout 1 -X PUT $API_URL/zoom/unmuted
        fi
    fi
	exit
fi

if [ "$zm_status" == "false" ]; then
	echo "🔴" #text version echo "Muted| color=#FF0000"
	echo ---
	echo "Unmute| bash='$0' param1=toggle terminal=false"
    if [[ $ENABLED ]]; then
        STATE=`curl --connect-timeout 1 -X GET $API_URL/zoom/state | tr -d \"`
        if [ "$STATE" != "muted" ]; then
            curl --connect-timeout 1 -X PUT $API_URL/zoom/muted
        fi
    fi
	exit
fi

if [ "$zm_status" == "off" ]; then
	echo "⚪️" #text version echo "Zoom Not Running"
	echo ---
	echo "Launch Zoom| bash='$0' param1=launch terminal=false"
    #if [[ $ENABLED ]]; then
    #    STATE=`curl --connect-timeout 1 -X GET $API_URL/zoom/state | tr -d \"`
    #    if [ "$STATE" != "inactive" ]; then
    #        curl --connect-timeout 1 -X PUT $API_URL/zoom/inactive
    #    fi
    #fi
    exit
fi

if [ "$zm_status" == "1" ]; then
  echo "🤐" #text version echo "Audio not connected"
  echo ---
  echo "Join Audio| bash='$0' param1=toggle terminal=false"
  exit
fi
