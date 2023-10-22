[![Code size](https://img.shields.io/github/languages/code-size/enesbcs/rpieasy)]() [![Last commit](https://img.shields.io/github/last-commit/enesbcs/rpieasy)]()

# To support the development you can:
- Be a patron at [Patreon](https://www.patreon.com/enesbcs)
- Buy a [coffee](https://ko-fi.com/I3I5UT4H)
- Donate by [PayPal](https://www.paypal.me/rpieasy)
- Add Python code by [Pull Request](https://github.com/enesbcs/rpieasy/pulls)

# RPIEasy

Easy MultiSensor device based on Raspberry PI

![RPIEasy](https://m.blog.hu/bi/bitekmindenhol/image/rpi_devs.png)

Based on Python 3.x and Raspberry PI (Raspbian Linux) this project tries to mimic the magnificent [ESPEasy](https://www.letscontrolit.com/wiki/index.php/ESPEasy) project functions.
Main goal is to create a multisensor device, that can be install and setup quickly. 

# Requirements
- Debian/Ubuntu/Raspbian Linux
- Python3

Tested with Raspberry Pi Zero W/Raspbian Buster and PC/Ubuntu 20.04. (may work with other Debian/Ubuntu derivatives)
For obvious reasons GPIO based devices needs GPIO support, mainly targeted for Raspberry Pi. 
However experimental Orange Pi, USB FTDI and Rock Pi S GPIO support also added for testing purposes. Some basic devices (dummy, system informations...) and controllers will work on a normal PC.

# Installation

    sudo apt install python3-pip screen alsa-utils wireless-tools wpasupplicant zip unzip git
    git clone https://github.com/enesbcs/rpieasy.git
    cd rpieasy
    sudo pip3 install jsonpickle --break-system-packages

In case of Debian Stretch or other linux that misses "ifconfig" command:

`sudo apt install net-tools`

In case you are using Debian 12, please remove 'EXTERNALLY-MANAGED' file from your system to be able to use pip3.
https://www.jeffgeerling.com/blog/2023/how-solve-error-externally-managed-environment-when-installing-pip3

Other dependencies can be reached and installed through the webGUI after starting with: (See Hardware page)

`sudo ./RPIEasy.py`

# Update
There are an external updater and command line manager script by [haraldtux](/haraldtux):

https://github.com/haraldtux/rpieasy-update

Or you can use the integrated updater at Tools->System Updates, but be warned: save your "data" directory before update if it is containing data that you can't or won't readd manually!

# FAQ
In case of questions or problems:
- [Check the Wiki](https://github.com/enesbcs/rpieasy/wiki)
- [Check the Forum](https://www.letscontrolit.com/forum/viewforum.php?f=24&sid=73480306697e27e1e89fe9e67c18c7d6)
- [Make a new Issue](https://github.com/enesbcs/rpieasy/issues)

# Special Thanks
I would especially like to thank the two biggest supporter, happytm and budman1758 for their ideas and donations which made it possible to acquire a lot of IoT sensors/devices. :)
