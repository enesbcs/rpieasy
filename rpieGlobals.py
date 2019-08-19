#!/usr/bin/env python3
#############################################################################
################ Global constants and runtime variables #####################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
# 
PROGNAME = "RPIEasy"
BUILD   = 19231
PROGVER = "0."+str(BUILD/1000)

gpMenu = []
gpMenu.append(['\u2302 Main','.'])
gpMenu.append(['\u2699 Config','config'])
gpMenu.append(['\U0001f4ac Controllers','controllers'])
gpMenu.append(['\U0001f4cc Hardware','hardware'])
gpMenu.append(['\U0001f50c Devices','devices'])
gpMenu.append(['\u29f4 Rules','rules'])
gpMenu.append(['\u2709 Notifications','notifications'])
gpMenu.append(['\U0001f527 Tools','tools'])

webLoggedIn = False
osinuse = ""
ossubtype = ""
wifiSetup = False

deviceselector = [[0,0,"- None -"]]
controllerselector = [[0,0,"- None -"]]
notifierselector = [[0,0,"- None -"]]

NODE_TYPE_ID_ESP_EASY_STD        =   1
NODE_TYPE_ID_ESP_EASYM_STD       =  17
NODE_TYPE_ID_ESP_EASY32_STD      =  33
NODE_TYPE_ID_ARDUINO_EASY_STD    =  65
NODE_TYPE_ID_NANO_EASY_STD       =  81
NODE_TYPE_ID_RPI_EASY_STD        =   5

LOG_LEVEL_ERROR                  =   1
LOG_LEVEL_INFO                   =   2
LOG_LEVEL_DEBUG                  =   3
LOG_LEVEL_DEBUG_MORE             =   4
LOG_LEVEL_DEBUG_DEV              =   9

LOG_MAXLINES                     = 120

CMD_REBOOT                       =  89
CMD_WIFI_DISCONNECT              = 135

DEVICES_MAX                      = 75
TASKS_MAX                        = 48

CONTROLLER_MAX                   =  4
NOTIFICATION_MAX                 =  4
VARS_PER_TASK                    =  4
PLUGIN_MAX                       = DEVICES_MAX
PLUGIN_CONFIGVAR_MAX             =  12
PLUGIN_CONFIGFLOATVAR_MAX        =   4
PLUGIN_CONFIGLONGVAR_MAX         =   4
PLUGIN_EXTRACONFIGVAR_MAX        =  16
CPLUGIN_MAX                      =  16
NPLUGIN_MAX                      =   4
UNIT_MAX                         =  32
RULES_TIMER_MAX                  =  16
SYSTEM_TIMER_MAX                 =  16
SYSTEM_CMD_TIMER_MAX             =   4
RULES_MAX_SIZE                   = 8192
RULES_MAX_NESTING_LEVEL          =   4
RULESETS_MAX                     =   4
RULES_BUFFER_SIZE                =  64

RULE_USER     = 65530 # user defined event
RULE_SYSTEM   = 65531 # System#Boot MQTT#Connected MQTT#Disconnected
RULE_CLOCK    = 65532 # Clock#Time=
RULE_TIMER    = 65533 # Rules#Timer=

DEVICE_TYPE_SINGLE               =   1  # connected through 1 datapin
DEVICE_TYPE_DUAL                 =   2  # connected through 2 datapins
DEVICE_TYPE_TRIPLE               =   3  # connected through 3 datapins
DEVICE_TYPE_QUAD                 =   4  # connected through 4 datapins
DEVICE_TYPE_ANALOG               =  10  # AIN/tout pin
DEVICE_TYPE_I2C                  =  20  # connected through I2C
DEVICE_TYPE_SPI                  =  30  # connected through SPI
DEVICE_TYPE_DUMMY                =  99  # Dummy device, has no physical connection
DEVICE_TYPE_USB                  = 110  # USB connected device
DEVICE_TYPE_BLE                  = 120  # BLE connected device
DEVICE_TYPE_SND                  = 130  # Sound device/Alsa-PyGame-Vlc
DEVICE_TYPE_W1                   = 140  # OneWire W1-GPIO
DEVICE_TYPE_SER                  = 150  # Serial

SENSOR_TYPE_NONE                 =  0
SENSOR_TYPE_SINGLE               =  1
SENSOR_TYPE_TEMP_HUM             =  2
SENSOR_TYPE_TEMP_BARO            =  3
SENSOR_TYPE_TEMP_HUM_BARO        =  4
SENSOR_TYPE_DUAL                 =  5
SENSOR_TYPE_TRIPLE               =  6
SENSOR_TYPE_QUAD                 =  7
SENSOR_TYPE_TEMP_EMPTY_BARO      =  8
SENSOR_TYPE_SWITCH               = 10
SENSOR_TYPE_DIMMER               = 11
SENSOR_TYPE_LONG                 = 20
SENSOR_TYPE_WIND                 = 21
SENSOR_TYPE_TEXT                 = 101

NODE_TYPE_ID = NODE_TYPE_ID_RPI_EASY_STD

FILE_RULES        = "files/rules1.txt"
