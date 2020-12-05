#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "Updating packages"
apt-get update

echo "Installing Python 3"
apt-get install python3

echo "Installing pip"
apt-get install python3-pip

echo "Done!"
