#!/bin/bash
_SYSTEM=""
if [ "$EUID" -ne 0 ]
then
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
if [[ $PIP_RESULT = *"not found"* ]]; then
   echo "jsonpickle install failed, trying to force package installation"
   mkdir -p ~/.config/pip
   cat > ~/.config/pip/pip.conf << EOL
[global]
break-system-packages = true
EOL
   $PIP_CMD install jsonpickle
fi
