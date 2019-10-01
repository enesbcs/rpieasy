#!/bin/sh
#MIT License
#Copyright (c) 2019 VTRUST
#Modified by Alexander Nagy for RPIEasy

#1st command line parameter is the WiFi device name for example: wlan0
#2nd parameter is the AP name to create
#3rd parameter is the WiFi password
#4th parameter is the WiFi channel number (1-13)

#sudo apt install dnsmasq hostapd
#sudo systemctl disable dnsmasq
#sudo systemctl disable hostapd

if test $# -ne 4
then
   echo "Illegal number of parameters: 1:wifi_device_name 2:AP_name 3:AP_passw 4: wifi_channel"
   exit 2
fi
WLAN=$1
AP=$2
PASS=$3
CHAN=$4

if test -d /etc/NetworkManager; then
	echo "Backing up NetworkManager.cfg..."
	sudo cp /etc/NetworkManager/NetworkManager.conf /etc/NetworkManager/NetworkManager.conf.backup

	cat <<- EOF > /etc/NetworkManager/NetworkManager.conf
		[main]
		plugins=keyfile

		[keyfile]
		unmanaged-devices=interface-name:$WLAN
	EOF

	echo "Restarting NetworkManager..."
	sudo service network-manager restart
fi

echo "Stopping network services..."
sudo systemctl stop hostapd.service
sudo systemctl stop dnsmasq.service
sudo systemctl stop dhcpcd.service
sudo killall wpa_supplicant > /dev/null 2>&1

sudo ifconfig $WLAN up

echo "Backing up /etc/dnsmasq.conf..."
sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup


echo "Writing dnsmasq config file..."
echo "Creating new /etc/dnsmasq.conf..."
cat <<- EOF >/etc/dnsmasq.conf
	# disables dnsmasq reading any other files like /etc/resolv.conf for nameservers
	no-resolv
	# Interface to bind to
	interface=$WLAN
	#Specify starting_range,end_range,lease_time
	dhcp-range=192.168.4.2,192.168.4.250,12h
	# dns addresses to send to the clients
	server=192.168.4.1
	address=/rpieasy.local/192.168.4.1
EOF

echo "Writing hostapd config file..."
cat <<- EOF >/etc/hostapd/hostapd.conf
	interface=$WLAN
	driver=nl80211
	ssid=$AP
	hw_mode=g
	channel=$CHAN
	macaddr_acl=0
	auth_algs=1
	ignore_broadcast_ssid=0
	wpa=2
	wpa_passphrase=$PASS
	wpa_key_mgmt=WPA-PSK
	wpa_pairwise=TKIP
	rsn_pairwise=CCMP
EOF

echo "Configuring AP interface..."
sudo ifconfig $WLAN up 192.168.4.1 netmask 255.255.255.0

echo "Starting DNSMASQ server..."
sudo /etc/init.d/dnsmasq stop > /dev/null 2>&1
sudo pkill dnsmasq
sudo dnsmasq
sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null 2>&1
sudo ip route add 192.168.4.0/24 dev $WLAN

echo "Starting AP on $WLAN..."
#sudo hostapd /etc/hostapd/hostapd.conf
sudo systemctl start hostapd.service
