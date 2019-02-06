| PayPal |
|-------|
|  [![donate](https://img.shields.io/badge/donate-PayPal-blue.svg)](https://www.paypal.me/rpieasy) |
If you like this project, or you wants to support the development, you can do that the links above or by doing pull requests, if you knew Python language.

# RPIEasy

Easy MultiSensor device based on Raspberry PI

![RPIEasy](https://m.blog.hu/bi/bitekmindenhol/image/rpi_devs.png)

Based on Python 3.x and Raspberry PI (Raspbian Linux) this project tries to mimic the magnificent [ESPEasy](https://www.letscontrolit.com/wiki/index.php/ESPEasy) project functions.
Main goal is to create a multisensor device, that can be install and setup quickly. 

:warning:THIS IS A BETA TEST VERSION!:warning:

Expect major changes in later versions that may cause incompatibility with earlier versions!

Currently feedbacks and test results needed to fix core functions. New plugins and controllers may be added to expose hidden bugs. :)

# Requirements
- Debian/Ubuntu/Raspbian Linux
- Python3

Tested with Raspberry Pi Zero W/Raspbian Stretch and PC/Ubuntu 18.04. (may work with other Debian/Ubuntu derivatives)
For obvious reasons GPIO based devices needs GPIO support, which only works with Raspberry Pi. Some basic devices and controllers will work on a normal PC.

# Installation

    git clone https://github.com/enesbcs/rpieasy.git
    cd rpieasy
    sudo apt install python3-pip screen alsa-utils wireless-tools wpasupplicant zip unzip
    sudo pip3 install jsonpickle

In case of Debian Stretch or other linux that misses "ifconfig" command:

`sudo apt install net-tools`

Other dependencies can be reached and installed through the webGUI after starting with:

`sudo ./RPIEasy.py`

# Update
There are an external update script at:
https://github.com/haraldtux/rpieasy-update
