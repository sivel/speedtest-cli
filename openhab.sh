#!/bin/bash
#
# Intergration in OpenHAB
#########

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

# Check if connection is up
ping -c 1 duckduckgo.com > /dev/null
if [ $? -ne 0 ]
then
        PING=0
        DOWN=0
        UP=0
else
    # Check if a specific device is on, where you don't want high ping or slow connection (e. g. gaming or streaming)
    ping -c 1 111.222.333.444 > /dev/null
    if [ $? -eq 0 ]
    then
      exit
    fi
      data=$(./speedtest-cli --simple)
      PING=$(echo $data | grep Ping | cut -d " " -f 2)
      DOWN=$(echo $data | grep Download | cut -d " " -f 5)
      UP=$(echo $data | grep Upload | cut -d " " -f 8)
fi


/usr/bin/curl -s --header "Content-Type: text/plain" --request POST --data $PING http://IP_OPENHAB:PORT/rest/items/INTERNET_PING
/usr/bin/curl -s --header "Content-Type: text/plain" --request POST --data $DOWN http://IP_OPENHAB:PORT/rest/items/INTERNET_DOWN
/usr/bin/curl -s --header "Content-Type: text/plain" --request POST --data $UP http://IP_OPENHAB:PORT/rest/items/INTERNET_UP
