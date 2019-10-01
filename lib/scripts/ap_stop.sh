#!/bin/sh
#MIT License
#Copyright (c) 2019 VTRUST
#Modified by Alexander Nagy for RPIEasy

#1st command line parameter is the WiFi device name for example: wlan0

if test $# -ne 1
then
   echo "Illegal number of parameters: 1:wifi_device_name"
   exit 2
fi
WLAN=$1

systemctl stop hostapd.service
sudo killall hostapd 2>&1

if test -d /etc/NetworkManager; then
	sudo rm /etc/NetworkManager/NetworkManager.conf > /dev/null 2>&1
	sudo mv /etc/NetworkManager/NetworkManager.conf.backup /etc/NetworkManager/NetworkManager.conf
	sudo service network-manager restart
fi
systemctl stop dnsmasq.service
sudo pkill dnsmasq
sudo rm /etc/dnsmasq.conf > /dev/null 2>&1
sudo mv /etc/dnsmasq.conf.backup /etc/dnsmasq.conf > /dev/null 2>&1
sudo rm /etc/dnsmasq.hosts > /dev/null 2>&1
sudo ifconfig $WLAN 0.0.0.0

sudo service dhcpcd restart
