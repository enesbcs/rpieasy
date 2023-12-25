#!/bin/sh
echo "RPIEasy basic dependency solver script"
_SYSTEM=""
if [ "$(id -u)" -ne 0 ]; then
  echo "Please run with root or sudo!"
  exit
fi
if [ -z `command -v command` ]
then
   echo "Command not found!"
   exit
fi
PIP_BLOCKER=""
if [ ! -z `command -v find` ]
then
 PIP_BLOCKER=`find /usr/lib -name EXTERNALLY-MANAGED`
else
 echo "Warning: Find not found!"
fi
if [ ! -z "$PIP_BLOCKER" ]
then
   echo "Removing pip blocker file from system: $PIP_BLOCKER"
   rm $PIP_BLOCKER
fi
if [ ! -z `command -v apt-get` ]
then
   _SYSTEM="apt-get"
elif [ ! -z `command -v pacman` ]
then
   _SYSTEM="pacman"
elif [ ! -z `command -v apk` ]
then
   _SYSTEM="apk"
else
   echo "Not supported system!"
   exit
fi
if [ "$_SYSTEM" = "apt-get" ]
then
  apt-get update
  apt-get install -y python3-pip screen alsa-utils zip unzip
  if [ -z `command -v ifconfig` ]
  then
   apt-get install -y net-tools
  fi
  apt-get install -y wireless-tools wpasupplicant
fi
if [ "$_SYSTEM" = "pacman" ]
then
 echo -ne '\n' | pacman -S python-pip screen alsa-utils zip unzip
 if [ -z `command -v ifconfig` ]
 then
   echo -ne '\n' | pacman -S net-tools
 fi
fi
if [ "$_SYSTEM" = "apk" ]
then
  sed -i '/community/s/^#//' /etc/apk/repositories
  apk update
  apk add --no-cache python3 screen alsa-utils zip unzip wireless-tools util-linux lm-sensors
  apk add --no-cache py3-pip
  apk add --no-cache wireless-tools
  if [ -z `command -v ifconfig` ]
  then
   apk add --no-cache net-tools
  fi
  if [ -z `command -v pip3` ]
  then
   python3 -m ensurepip
  fi
fi
PIP_CMD=""
PIP_RESULT=""
if [ ! -z `command -v pip3` ]
then
 PIP_CMD="pip3"
elif [ ! -z `command -v python3` ]
then
 PIP_CMD="python3 -m pip"
elif [ ! -z `command -v pip` ]
then
 PIP_CMD="pip"
elif [ ! -z `command -v python` ]
then
 PIP_CMD="python -m pip"
else
 echo "No valid python/pip found"
fi
if [ ! -z "$PIP_CMD" ]
then
 $PIP_CMD install jsonpickle
 PIP_RESULT=`$PIP_CMD show jsonpickle 2>&1`
fi
case "$PIP_RESULT" in
*"not found"*)
   echo "jsonpickle install failed, trying to force package installation"
   mkdir -p ~/.config/pip
   cat > ~/.config/pip/pip.conf << EOL
[global]
break-system-packages = true
EOL
   $PIP_CMD install jsonpickle
esac
