#!/bin/bash
testnum="$counter"
echo "How many times should I test?"
read counter
echo "And how long between tests?"
read delay
until [ $counter -lt 1 ];
do
./speedtest_cli.py; sleep $delay
let counter=counter-1
done
