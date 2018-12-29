#!/bin/bash
SCRIPT=$(readlink -f "$0")
DIR=$(dirname "$SCRIPT")
if [ -z "$DIR" ]
then
DIR=/home/pi/rpieasy
fi
cd $DIR
while true; do
/usr/bin/python3 $DIR/RPIEasy.py
sleep 3
done
