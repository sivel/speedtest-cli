#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

${SCRIPT_DIR}/speedtest.sh >${SCRIPT_DIR}/data/speedtest-`date +%Y%m%d%H%M`.txt
