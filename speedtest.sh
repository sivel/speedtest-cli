#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

declare -a SERVERS
SERVERS[1671]="Vodafone, Utrecht"
SERVERS[4358]="KPN, Amsterdam"
SERVERS[3587]="LeaseWeb, Haarlem"
SERVERS[2104]="Luna.nl, Rotterdam"

for SERVER in ${!SERVERS[@]}
do
    echo "Location: ${SERVERS[$SERVER]}"
    ${SCRIPT_DIR}/speedtest_cli.py --server $SERVER --simple
    echo
done
