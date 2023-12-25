#!/bin/sh
SCRIPT=$(readlink -f "$0")
DIR=$(dirname "$SCRIPT")
if [ -z "$DIR" ]
then
DIR=/root/rpieasy
fi
cd $DIR
while true; do
/usr/bin/python3 $DIR/RPIEasy.py
sleep 3
done
