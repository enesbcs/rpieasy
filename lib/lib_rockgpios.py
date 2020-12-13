#!/usr/bin/env python3
#############################################################################
############## Helper Library for RockPI GPIO handling ######################
#############################################################################
#
# Copyright (C) 2020 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
import Settings
import os
import time
import webserver
import misc
import rpieGlobals
import threading
try:
 import linux_os as OS
except:
 print("Linux OS functions can not be imported!")
try:
 import mraa
except:
 print("mraa not installed!")
try:
 import smbus #generic i2c
except:
 pass
 
PINOUT40 = [
{"ID":0,
"BCM":-1,
"name":["None"],
"canchange":2,
"altfunc": 0,
"ver":"0"},
]

PINOUT26RSv13 = [
{"ID":0,
"BCM":-1,
"name":["None"],
"canchange":2,
"altfunc": 0,
"ver":"13"},
{"ID":1,
"BCM":-1,
"name":["3V3"],
"canchange":0,
"altfunc": 0},
{"ID":2,
"BCM":-1,
"name":["5V"],
"canchange":0,
"altfunc": 0},
{"ID":3,
"BCM":11,
"name":["GPIO11","I2C1-SDA"],
"fullname":"GPIO0_B3","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":4,
"BCM":-1,
"name":["5V"],
"canchange":0,
"altfunc": 0},
{"ID":5,
"BCM":12,
"name":["GPIO12","I2C1-SCL"],
"fullname":"GPIO0_B4","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":6,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":7,
"BCM":68,
"name":["GPIO68","I2S0-MCLK"],
"fullname":"GPIO2_A4","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":8,
"BCM":65,
"name":["GPIO65","UART0-TX"],
"fullname":"GPIO2_A1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":9,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":10,
"BCM":64,
"name":["GPIO64","UART0-RX"],
"fullname":"GPIO2_A0","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":11,
"BCM":15,
"name":["GPIO15/PWM2","I2C3-SDA"],
"fullname":"GPIO0_B7","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":12,
"BCM":69,
"name":["GPIO69","I2S0-SCLK"],
"fullname":"GPIO2_A5","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":13,
"BCM":16,
"name":["GPIO16/PWM3","I2C3-SCL"],
"fullname":"GPIO0_C0","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":14,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":15,
"BCM":17,
"name":["GPIO17","SPDIF_TX"],
"fullname":"GPIO0_C1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":16,
"BCM":74,
"name":["GPIO74","I2S0-SDO1"],
"fullname":"GPIO2_B2","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":17,
"BCM":-1,
"name":["3V3"],
"canchange":0,
"altfunc": 0},
{"ID":18,
"BCM":73,
"name":["GPIO73","I2S0-SDO0"],
"fullname":"GPIO2_B1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":19,
"BCM":55,
"name":["GPIO55","UART2-TX","SPI2-MOSI"],
"fullname":"GPIO1_C7","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":20,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":21,
"BCM":54,
"name":["GPIO54","UART2-RX","SPI2-MISO"],
"fullname":"GPIO1_C6","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":22,
"BCM":71,
"name":["GPIO71","I2S0-TX"],
"fullname":"GPIO2_A7","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":23,
"BCM":56,
"name":["GPIO56","UART1-RX","I2C0-SDA","SPI2-CLK"],
"fullname":"GPIO1_D0","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":24,
"BCM":57,
"name":["GPIO57","UART1-TX","I2C0-SCL","SPI2-CE0"],
"fullname":"GPIO1_D1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":25,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":26,
"BCM":0, #ADC_IN0
"name":["ADC_IN0"],
"fullname":"","canchange":1,
"altfunc": 0,
"startupstate":10,
"actualstate":10},
{"ID":27, #second header, not entirely accessible with mraa
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":28,
"BCM":77,
"name":["GPIO77","I2S0-SDI0"],
"fullname":"GPIO2_B5","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":29,
"BCM":-1,
"name":["ADC_KEY_IN1"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":30,
"BCM":78,
"name":["GPIO78","I2S0-SDI1"],
"fullname":"GPIO2_B6","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":31,
"BCM":-1,
"name":["MCBIAS2"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":32,
"BCM":79,
"name":["GPIO79","I2S0-SDI2"],
"fullname":"GPIO2_B7","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":33,
"BCM":-1,
"name":["MCBIAS1"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":34,
"BCM":80,
"name":["GPIO80","I2S0-SDI3"],
"fullname":"GPIO2_C0","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":35,
"BCM":-1,
"name":["MICN8"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":36,
"BCM":-1,
"name":["MCIP8"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":37,
"BCM":-1,
"name":["MICN7"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":38,
"BCM":-1,
"name":["MCIP7"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":39,
"BCM":109,
"name":["GPIO109","SPI1-CE0","I2C3-SCL","UART3-TX"],
"fullname":"GPIO3_B5","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":40,
"BCM":108,
"name":["GPIO108","SPI1-MOSI","I2C3-SDA","UART3-RX"],
"fullname":"GPIO3_B4","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":41,
"BCM":107,
"name":["GPIO107","SPI1-CLK"],
"fullname":"GPIO3_B3","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":42,
"BCM":106,
"name":["GPIO106","SPI1-MISO"],
"fullname":"GPIO3_B2","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":43,
"BCM":76,
"name":["GPIO76","I2S0-SDO3"],
"fullname":"GPIO2_B4","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":44,
"BCM":75,
"name":["GPIO75","I2S0-SDO2"],
"fullname":"GPIO2_B3","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":45,
"BCM":72,
"name":["GPIO72","I2S0-LRCK"],
"fullname":"GPIO2_B0","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":46,
"BCM":70,
"name":["GPIO70","I2S0-SCLK"],
"fullname":"GPIO2_A6","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":47,
"BCM":-1,
"name":["MICN2"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":48,
"BCM":-1,
"name":["MCIP2"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":49,
"BCM":-1,
"name":["MICN1"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":50,
"BCM":-1,
"name":["MCIP1"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":51,
"BCM":-1,
"name":["LINEOUT_R"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":52,
"BCM":-1,
"name":["LINEOUT_L"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
]

PINOUT26RSv11 = [
{"ID":0,
"BCM":-1,
"name":["None"],
"canchange":2,
"altfunc": 0,
"ver":"11"},
{"ID":1,
"BCM":-1,
"name":["3V3"],
"canchange":0,
"altfunc": 0},
{"ID":2,
"BCM":-1,
"name":["5V"],
"canchange":0,
"altfunc": 0},
{"ID":3,
"BCM":11,
"name":["GPIO11","I2C1-SDA"],
"fullname":"GPIO0_B3","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":4,
"BCM":-1,
"name":["5V"],
"canchange":0,
"altfunc": 0},
{"ID":5,
"BCM":12,
"name":["GPIO12","I2C1-SCL"],
"fullname":"GPIO0_B4","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":6,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":7,
"BCM":69,
"name":["GPIO69","I2S0-SCLK"],
"fullname":"GPIO2_A5","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":8,
"BCM":65,
"name":["GPIO65","UART0-TX","SPI0-MOSI"],
"fullname":"GPIO2_A1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":9,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":10,
"BCM":64,
"name":["GPIO64","UART0-RX","SPI0-MISO"],
"fullname":"GPIO2_A0","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":11,
"BCM":15,
"name":["GPIO15/PWM2","I2C3-SDA"],
"fullname":"GPIO0_B7","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":12,
"BCM":66,
"name":["GPIO66","I2C2-SDA","SPI0-CLK"],
"fullname":"GPIO2_A2","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":13,
"BCM":16,
"name":["GPIO16/PWM3","I2C3-SCL"],
"fullname":"GPIO0_C0","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":14,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":15,
"BCM":17,
"name":["GPIO17","SPDIF_TX"],
"fullname":"GPIO0_C1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":16,
"BCM":67,
"name":["GPIO67","I2C2-SCL","SPI0-CE0"],
"fullname":"GPIO2_A3","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":17,
"BCM":-1,
"name":["3V3"],
"canchange":0,
"altfunc": 0},
{"ID":18,
"BCM":73,
"name":["GPIO73","I2S0-SDO0"],
"fullname":"GPIO2_B1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":19,
"BCM":55,
"name":["GPIO55","UART2-TX","SPI2-MOSI"],
"fullname":"GPIO1_C7","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":20,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":21,
"BCM":54,
"name":["GPIO54","UART2-RX","SPI2-MISO"],
"fullname":"GPIO1_C6","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":22,
"BCM":14,
"name":["GPIO14/PWM1"],
"fullname":"GPIO0_B6","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":23,
"BCM":56,
"name":["GPIO56","UART1-RX","I2C0-SDA","SPI2-CLK"],
"fullname":"GPIO1_D0","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":24,
"BCM":57,
"name":["GPIO57","UART1-TX","I2C0-SCL","SPI2-CE0"],
"fullname":"GPIO1_D1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":25,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":26,
"BCM":0, #ADC_IN0
"name":["ADC_IN0"],
"fullname":"","canchange":1,
"altfunc": 0,
"startupstate":10,
"actualstate":10},
{"ID":27, #second header, not entirely accessible with mraa
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":28,
"BCM":70,
"name":["GPIO70","I2S0-SCLK"],
"fullname":"GPIO2_A6","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":29,
"BCM":-1,
"name":["ADC_KEY_IN1"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":30,
"BCM":77,
"name":["GPIO77","I2S0-SDI0"],
"fullname":"GPIO2_B5","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":31,
"BCM":-1,
"name":["MCBIAS2"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":32,
"BCM":78,
"name":["GPIO78","I2S0-SDI1"],
"fullname":"GPIO2_B6","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":33,
"BCM":-1,
"name":["MCBIAS1"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":34,
"BCM":79,
"name":["GPIO79","I2S0-SDI2"],
"fullname":"GPIO2_B7","canchange":1,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":35,
"BCM":-1,
"name":["MICN8"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":36,
"BCM":-1,
"name":["MCIP8"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":37,
"BCM":-1,
"name":["MICN7"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":38,
"BCM":-1,
"name":["MCIP7"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":39,
"BCM":-1,
"name":["MICN6"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":40,
"BCM":-1,
"name":["MCIP6"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":41,
"BCM":-1,
"name":["MICN5"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":42,
"BCM":-1,
"name":["MCIP5"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":43,
"BCM":-1,
"name":["MICN4"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":44,
"BCM":-1,
"name":["MCIP4"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":45,
"BCM":-1,
"name":["MICN3"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":46,
"BCM":-1,
"name":["MCIP3"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":47,
"BCM":-1,
"name":["MICN2"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":48,
"BCM":-1,
"name":["MCIP2"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":49,
"BCM":-1,
"name":["MICN1"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":50,
"BCM":-1,
"name":["MCIP1"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":51,
"BCM":-1,
"name":["LINEOUT_R"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
{"ID":52,
"BCM":-1,
"name":["LINEOUT_L"],
"canchange":0,
"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None},
]

PINOUT26RSv10 = [
{"ID":0,
"BCM":-1,
"name":["None"],
"canchange":2,
"altfunc": 0,
"ver":"10"},
{"ID":1,
"BCM":-1,
"name":["3V3"],
"canchange":0,
"altfunc": 0},
{"ID":2,
"BCM":-1,
"name":["5V"],
"canchange":0,
"altfunc": 0},
{"ID":3,
"BCM":12,
"name":["GPIO12","I2C1-SCL"],
"fullname":"GPIO0_B4","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":4,
"BCM":-1,
"name":["5V"],
"canchange":0,
"altfunc": 0},
{"ID":5,
"BCM":11,
"name":["GPIO11","I2C1-SDA"],
"fullname":"GPIO0_B3","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":6,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":7,
"BCM":69,
"name":["GPIO69","I2S0-SCLK"],
"fullname":"GPIO2_A5","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":8,
"BCM":-1,
"name":["SDMMC"],
"fullname":"GPIO4_D3","canchange":0,
"altfunc": 0},
{"ID":9,
"BCM":64,
"name":["GPIO64","UART0-RX","SPI0-MISO"],
"fullname":"GPIO2_A0","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":10,
"BCM":-1,
"name":["SDMMC"],
"fullname":"GPIO4_D2","canchange":0,
"altfunc": 0},
{"ID":11,
"BCM":65,
"name":["GPIO65","UART0-TX","SPIO0-MISO"],
"fullname":"GPIO2_A1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":12,
"BCM":16,
"name":["GPIO16/PWM3","I2C3-SCL"],
"fullname":"GPIO0_C0","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":13,
"BCM":66,
"name":["GPIO66","SPI0-CLK","I2C2-SDA"],
"fullname":"GPIO2_A2","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":14,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":15,
"BCM":67,
"name":["GPIO67","I2C2-SCL","SPI0-CE0"],
"fullname":"GPIO2_A3","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":16,
"BCM":71,
"name":["GPIO71","I2S0-LRCK"],
"fullname":"GPIO2_A7","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":17,
"BCM":-1,
"name":["3V3"],
"canchange":0,
"altfunc": 0},
{"ID":18,
"BCM":73,
"name":["GPIO73","I2S0-SDO0"],
"fullname":"GPIO2_B1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":19,
"BCM":55,
"name":["GPIO55","UART2-TX","SPI2-MOSI"],
"fullname":"GPIO1_C7","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":20,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":21,
"BCM":54,
"name":["GPIO54","UART2-RX","SPI2-MISO"],
"fullname":"GPIO1_C6","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":22,
"BCM":14,
"name":["GPIO14/PWM1"],
"fullname":"GPIO0_B6","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":23,
"BCM":56,
"name":["GPIO56","UART1-RX","I2C0-SDA","SPI2-CLK"],
"fullname":"GPIO1_D0","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":24,
"BCM":57,
"name":["GPIO57","UART1-TX","I2C0-SCL","SPI2-CE0"],
"fullname":"GPIO1_D1","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
{"ID":25,
"BCM":-1,
"name":["GND"],
"canchange":0,
"altfunc": 0},
{"ID":26,
"BCM":15,
"name":["GPIO15/PWM2","I2C3-SDA"],
"fullname":"","canchange":1,
"altfunc": 0,
"startupstate":-1,
"actualstate":-1,"gobj":None,"cb":None},
]



try:
 BOTH=mraa.EDGE_BOTH
 RISING=mraa.EDGE_RISING
 FALLING=mraa.EDGE_FALLING
 IN=mraa.DIR_IN
 OUT=mraa.DIR_OUT
 PUD_UP=mraa.MODE_PULLUP 
 PUD_DOWN=mraa.MODE_PULLDOWN
 OUT_HIGH=mraa.DIR_OUT_HIGH
 OUT_LOW=mraa.DIR_OUT_LOW
except:
 BOTH=1
 RISING=2
 FALLING=3
 IN=1
 OUT=0
 PUD_UP=1
 PUD_DOWN=2
 OUT_HIGH=2
 OUT_LOW=3

def getmraa():
 inf =["Unknown","0","0.0"]
 try:
  inf[0] = mraa.getPlatformName()
  inf[1] = str(mraa.getPinCount()-1)
  inf[2] = mraa.getVersion()
  if "rock pi s" in inf[0].lower():
   inf[1] = str(inf[1])+"rs"
 except Exception as e:
  pass
 return inf

class softPWM(threading.Thread):
  #https://github.com/evergreen-it-dev/orangepwm
  def __init__(self, gpioPin, frequency=1000):
     try:
      self.baseTime = 1.0 / frequency
     except:
      self.baseTime = 1.0 / 1000.0
     self.maxCycle = 100.0
     try:
      self.sliceTime = self.baseTime / self.maxCycle
     except:
      self.sliceTime = self.baseTime / 100.0
     self.gpioPin = gpioPin
     self.terminated = False
     self.toTerminate = False
     self.thread = None
     self.gpioo  = None

  def start(self, dutyCycle):
    """
    Start PWM output. Expected parameter is :
    - dutyCycle : percentage of a single pattern to set HIGH output on the GPIO pin
    
    Example : with a frequency of 1 Hz, and a duty cycle set to 25, GPIO pin will 
    stay HIGH for 1*(25/100) seconds on HIGH output, and 1*(75/100) seconds on LOW output.
    """
    if self.thread is not None:
     self.stop()
     self.toTerminate = False
     self.terminated = False
    self.dutyCycle = dutyCycle
    self.gpioo = mraa.Gpio(self.gpioPin,owner=False,raw=True)
    self.thread = threading.Thread(None, self.run, None, (), {})
    self.thread.start()

  def run(self):
    """
    Run the PWM pattern into a background thread. This function should not be called outside of this class.
    """
    while self.toTerminate == False:
      if self.dutyCycle > 0:
        self.gpioo.write(1)
        time.sleep(self.dutyCycle * self.sliceTime)
      if self.dutyCycle < self.maxCycle:
        self.gpioo.write(0)
        time.sleep((self.maxCycle - self.dutyCycle) * self.sliceTime)
    self.terminated = True

  def ChangeDutyCycle(self, dutyCycle):
    """
    Change the duration of HIGH output of the pattern. Expected parameter is :
    - dutyCycle : percentage of a single pattern to set HIGH output on the GPIO pin
    
    Example : with a frequency of 1 Hz, and a duty cycle set to 25, GPIO pin will 
    stay HIGH for 1*(25/100) seconds on HIGH output, and 1*(75/100) seconds on LOW output.
    """
    self.dutyCycle = dutyCycle

  def ChangeFrequency(self, frequency):
    """
    Change the frequency of the PWM pattern. Expected parameter is :
    - frequency : the frequency in Hz for the PWM pattern. A correct value may be 100.
    
    Example : with a frequency of 1 Hz, and a duty cycle set to 25, GPIO pin will 
    stay HIGH for 1*(25/100) seconds on HIGH output, and 1*(75/100) seconds on LOW output.
    """
    try:
     self.baseTime = 1.0 / frequency
    except:
     self.dutyCycle = 0
     self.toTerminate = True
    try:
     self.sliceTime = self.baseTime / self.maxCycle
    except:
     self.dutyCycle = 0
     self.toTerminate = True

  def stop(self):
    """
    Stops PWM output.
    """
    self.toTerminate = True
    while self.terminated == False:
      # Just wait
      time.sleep(0.01)
    self.gpioo.write(0)

  def enable(self,state=True):
    if state:
       self.start()
    else:
       self.stop()
 
class hwports:
 config_file_name = "/boot/uEnv.txt"

 def __init__(self): # general init
  self.i2cl = []
  self.pwml = []
  self.spil = []
  self.uartl = []

  self.i2c_channels = [] # 0,1
  self.i2c_initialized = False
  self.i2c_channels_init = []
  self.i2cbus = None
  self.spi_channels = [] # 0,1
  self.spi_cs = [0,0]
  self.serial = 0
  self.bluetooth = 0     # 0:disabled,1:enabled with SW miniUART,2:enabled with HW UART
  self.wifi = 0          # 0:disabled,1:enabled
  self.audio = 0
  self.i2s = 0
  self.pwm = [-1,-1,-1,-1,-1]          # pwm pins
  self.rtc = ""             # /lib/udev/hwclock-set
  self.pwmo = []

  try:
   rpitype = OS.getRockPIVer()
  except:
   rpitype=[]
  try:
   po = rpitype["pins"]
  except:
   po = "0"
  try:
   self.gpioinit = (mraa.init()==0) #success
  except:
   print("GPIO init failed")
   self.gpioinit = False

  self.pinnum = po
  for i in range(20):
   self.i2c_channels_init.append(None)

 def cleanup(self):
   if self.gpioinit:
    for p in range(len(self.pwmo)):
     try:
      if (self.pwmo[p]["o"] != False) and not (self.pwmo[p]["o"] is None):
       self.pwmo[p]["o"].write(1)
       self.pwmo[p]["o"].enable(True)
     except:
      pass

 def gpio_function_name(self,func):
  typestr = "Unknown"
  try:
    typeint = int(func)
    if IN==typeint:
      typestr = "Input"
    elif OUT==typeint:
      typestr = "Output"
    else:
      typestr = "Special"
  except:
   typestr = "Unknown"
  return typestr

 def gpio_function_name_from_pin(self,gpio):
  typestr = "Unknown"
  try:
   pinnum = int(gpio)
   if pinnum>0:
    typeint = self.gpio_function(pinnum)
    typestr = self.gpio_function_name(typeint)
  except Exception as e:
   typestr = "Unknown"
  return typestr

 def setup(self,pin,mode,pull_up_down=0):
  pinid = -1
  for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(pin).strip():
     pinid = b
     break
  if pinid == -1:
   return False
  if Settings.Pinout[b]["altfunc"] != 0:
   return False
  pinok = False
  try:
   Settings.Pinout[b]["gobj"].read()
   pinok = True
  except:
   Settings.Pinout[b]["gobj"] = None
  try:
   if pinok==False:
    Settings.Pinout[pinid]["gobj"] = mraa.Gpio(pin,owner=False,raw=True)
  except Exception as e:
   print("mraa:",e)#debug
   return False
  try:
   Settings.Pinout[pinid]["gobj"].dir(mode)
   if pull_up_down>0:
    Settings.Pinout[pinid]["gobj"].mode(pull_up_down)
  except Exception as e:
   print("mraa mode:",e)#debug
   return False

 def gpio_function(self,bcmpin):
  v = -1
  try:
   v = mraa.Gpio(bcmpin,owner=False,raw=True).readDir()
  except:
   v = 3
  return v

 def input(self,bcmpin):
  pinid = -1
  for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(bcmpin).strip():
     pinid = b
     break
  if pinid == -1:
    return False
  try:
   v = Settings.Pinout[pinid]["gobj"].read()
  except Exception as e:
   v = None
  return v

 def output(self,pin,value,Force=False):
  pinid = -1
  for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(pin).strip():
     pinid = b
     break
  if pinid == -1:
    return False
  if Force:
    if Settings.Pinout[pinid]["altfunc"] == 0 and Settings.Pinout[pinid]["canchange"]==1:
     if Settings.Pinout[pinid]["startupstate"]<4:
       self.setpinstate(pinid,4)
  try:
   v = Settings.Pinout[pinid]["gobj"].write(value)
  except:
   v = None
  return v
 

 def add_event_detect(self,pin, detection, pcallback,pbouncetime=0):
  for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(pin).strip():
     if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
      if Settings.Pinout[b]["startupstate"]<4:
       self.setpinstate(b,Settings.Pinout[b]["startupstate"])
      else:
       pass # i am lazy and not sure if is it can happen anyday...
     break

  pinok = False
  try:
   Settings.Pinout[b]["gobj"].read()
   pinok = True
  except:
   pass
  try:
   if pinok==False:
    Settings.Pinout[b]["gobj"] = mraa.Gpio(pin,owner=False,raw=True)
    Settings.Pinout[b]["gobj"].dir(mraa.DIR_IN)
   Settings.Pinout[b]["gobj"].edge(detection)
   Settings.Pinout[b]["cb"] = pcallback
   v = Settings.Pinout[b]["gobj"].isr(detection,isr_callback,b)
  except Exception as e:
   print("isr",e)#debug
   v = None

 def remove_event_detect(self,pin):
  pinid = -1
  for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(pin).strip():
     pinid = b
     break
  if pinid == -1:
    return False
  try:
   v = Settings.Pinout[b]["gobj"].isrExit()
   Settings.Pinout[b]["cb"] = None
  except Exception as e:
   v = None
  return v

 def i2c_init(self,channel=-1):
  if channel==-1:
   try:
    channel=self.i2cc[0]
   except:
    pass
  if channel>-1:
   succ = False
   try:
    if self.i2c_channels_init[channel] is None:
     self.i2c_channels_init[channel] = smbus.SMBus(channel)
    succ = True
   except:
    self.i2c_channels_init[channel] = None
   if succ and (self.i2c_channels_init[channel] is not None):
    if self.i2cbus is None:
      self.i2cbus = self.i2c_channels_init[channel]
    self.i2c_initialized = True
    return self.i2c_channels_init[channel]
   else:
    return None

  return None

 def i2c_read_block(self,address,cmd,bus=None):
  retval = None
  if self.i2c_initialized:
   try:
    if bus is None:
     retval = self.i2cbus.read_i2c_block_data(address,cmd)
    else:
     retval = bus.read_i2c_block_data(address,cmd)
   except:
    retval = None
  return retval

 def is_i2c_usable(self,channel):
   result = False
   if channel in self.i2cl:
    return True
   return result

 def is_i2c_enabled(self,channel):
  if channel in self.i2cc:
   return True
  else:
   return False

 def enable_i2c(self,channel):
  if self.is_i2c_usable(channel) and (self.is_i2c_enabled(channel)==False):
   self.i2cc.append(channel)
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "I2C"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = tn
   except Exception as e:
    print("i2ce",e)#debug

 def disable_i2c(self,channel):
  if self.is_i2c_enabled(channel):
   try:
    self.i2cc.remove(channel)
   except:
    pass
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "I2C"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = 0
   except:
    pass

 def is_spi_usable(self,channel):
   result = False
   if channel in self.spil:
    return True
   return result

 def is_spi_enabled(self,channel):
  if channel in self.spic:
   return True
  else:
   return False

 def enable_spi(self,channel,cs=0):
  if self.is_spi_usable(channel) and (self.is_spi_enabled(channel)==False):
   self.spic.append(channel)
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "SPI"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = tn
   except:
    pass

 def disable_spi(self,channel):
  if self.is_spi_enabled(channel):
   try:
    self.spic.remove(channel)
   except:
    pass
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "SPI"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = 0
   except:
    pass

 def is_serial_enabled(self,channel=0):
  if channel in self.uartc:
   return True
  else:
   return False

 def enable_serial(self,channel=0):
  if self.is_serial_usable(channel) and (self.is_serial_enabled(channel)==False):
   self.uartc.append(channel)
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "UART"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = tn
   except:
    pass

 def disable_serial(self,channel):
  if self.is_serial_enabled(channel):
   try:
    self.uartc.remove(channel)
   except:
    pass
   try:
    for p in range(len(Settings.Pinout)):
     n = Settings.Pinout[p]["name"]
     for tn in range(len(n)):
      if "UART"+str(channel) in n[tn]:
       Settings.Pinout[p]["altfunc"] = 0
   except:
    pass

 def is_serial_usable(self,channel=0):
   result = False
   if channel in self.uartl:
    return True
   return result

 def pwm_get_func(self,pin):
   pwmf = -1
   try:
     pf = Settings.Pinout[pin]["name"][0].find("PWM")
     if pf>=0:
      pwmf = int(Settings.Pinout[pin]["name"][0][pf+3])
   except:
     pass
   return pwmf
 
 def enable_pwm_pin(self,channel,pin,FirstRead=False): # channel not used, pin as order in pins
   if channel>-1: #find pin by channel
    for b in range(len(Settings.Pinout)):
     if "PWM"+str(channel) in Settings.Pinout[b]["name"][0]:
      pin = Settings.Pinout[b]["ID"]
      break
   else:
    channel = self.pwm_get_func(pin)
   if channel not in self.pwmc:
     self.pwmc.append(channel)
   if pin==-1:
    return False 
   if Settings.Pinout[pin]["BCM"] not in self.pwm:
    # register as pwm channel
    Settings.Pinout[pin]["startupstate"] = 7 # set to H-PWM
    if FirstRead:
     Settings.Pinout[pin]["actualstate"]=Settings.Pinout[pin]["startupstate"]
    #try to init as pwm channel
    tempobj = {"pin":0,"o":None}
    try:
      try:
       cter = 0
       tempobj["o"] = mraa.Pwm(pin,owner=True)
       retry = False
      except:
       retry = True
      while retry and cter<10:
       time.sleep(0.1)
       try:
        tempobj["o"] = mraa.Pwm(pin,owner=False)
        retry = False
       except:
        cter += 1
      if cter>=10:
         misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Pin "+str(pin)+" PWM init failed, try to restart")
      tempobj["pin"] = Settings.Pinout[pin]["BCM"]
      Settings.Pinout[pin]["gobj"] = tempobj["o"]
      self.pwmo.append(tempobj)
      self.pwm.append(Settings.Pinout[pin]["BCM"])
    except Exception as e:
      print("PWM error: ",e)

 def disable_pwm_pin(self,channel,pin):
  if channel>-1: #find pin by channel
    for b in range(len(Settings.Pinout)):
     if "PWM"+str(channel) in str(Settings.Pinout[b]["name"]):
      pin = Settings.Pinout[b]["ID"]
      break
  else:
    channel = self.pwm_get_func(pin)

  if channel in self.pwmc:
   try:
    self.pwmc.remove(channel)
   except:
    pass
  if Settings.Pinout[pin]["BCM"] in self.pwm:
   try:
    self.pwm.remove(Settings.Pinout[pin]["BCM"])
   except:
    pass
   for p in range(len(self.pwmo)):
     try:
      if (self.pwmo[p]["o"] is not None) and (self.pwmo[p]["pin"] == Settings.Pinout[pin]["BCM"]):
       self.pwmo[p]["o"].write(1)
       self.pwmo[p]["o"].enable(True)
     except:
      pass

 def output_pwm(self,bcmpin,pprop,pfreq=1000): # default 1000Hz # UNFINISHED!!!!
  pin = int(bcmpin)
  prop = float(pprop)
  if prop>100:
   prop = 100
  elif prop<0:
   prop = 0
  freq = int(pfreq)
  try:
   if freq<=0:
    freq = 1000.0
    prop = 0
   period = (1.0/ float(freq))
  except Exception as e:
   period = (1.0/1000.0)
   prop = 0
  if pin in self.pwm: # hardpwm
   try:
    prop = 1-(float(prop)/100.0) # 0..1 inverted ROCKPIS!!!!
   except Exception as e:
    prop = 1
   period = int(period * 1000000) #second to microsec
   for p in range(len(self.pwmo)):
     try:
      if self.pwmo[p]["pin"] == pin:
       if int(pprop)<=0:
        self.pwmo[p]["o"].write(1)
        self.pwmo[p]["o"].enable(True)
       else:
        self.pwmo[p]["o"].period_us(period)
        self.pwmo[p]["o"].write(prop)
        self.pwmo[p]["o"].enable(True)
       return True
     except Exception as e:
      print("pwmo",e)#debug
  else: # softpwm
   pfound = False
   for p in range(len(Settings.Pinout)):
     if int(Settings.Pinout[p]["BCM"])==pin:
      if (int(Settings.Pinout[p]["startupstate"]) not in [4,5,6]):
       return False # if not output skip

   if len(self.pwmo)>0:
    for p in range(0,len(self.pwmo)):
     if int(self.pwmo[p]["pin"])==pin:
      if (self.pwmo[p]["o"]):
       if prop<=0:
        self.pwmo[p]["o"].stop()
       else:
        self.pwmo[p]["o"].start(prop)
        self.pwmo[p]["o"].ChangeFrequency(freq)
        self.pwmo[p]["o"].ChangeDutyCycle(prop)
      pfound = True
      break
   if pfound==False and freq>0:
    tempobj = {"pin":0,"o":None}
    tempobj["pin"] = pin
    tempobj["o"] = softPWM(pin,freq)
    tempobj["o"].start(prop)
    self.pwmo.append(tempobj)
   return True

 def servo_pwm(self,bcmpin,angle):
  pin = int(bcmpin)
  freq = 50
  period = (1/ float(freq))
  startprop = 8
  prop = angle / 18. + 3.
  if prop>0:
   self.output_pwm(bcmpin,prop,freq)
   time.sleep(0.3)
  self.output_pwm(bcmpin,0,freq)
  return True


 def is_i2s_usable(self):
   result = False
   return result

 def set_i2s(self,state):
   pass

 def set1wgpio(self,bcmpin,FirstRead=False):
   for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(bcmpin).strip():
     if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
      Settings.Pinout[b]["startupstate"] = 8
      try:
       if Settings.Pinout[b]["fullname"] not in self.w1gpio:
          self.w1gpio.append(Settings.Pinout[b]["fullname"])
      except:
        pass
      if FirstRead:
       Settings.Pinout[b]["actualstate"]=Settings.Pinout[b]["startupstate"]
     break

 def setaiogpio(self,bcmpin,FirstRead=False):
   for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(bcmpin).strip():
     if "ADC_IN" in Settings.Pinout[b]["name"][0]:
      try:
       adcnum = int(Settings.Pinout[b]["name"][0][6])
      except:
       return False
      Settings.Pinout[b]["startupstate"] = 10
      if FirstRead:
       Settings.Pinout[b]["actualstate"]=Settings.Pinout[b]["startupstate"]
      pinok = False
      try:
        Settings.Pinout[b]["gobj"].read()
        pinok = True
      except:
        Settings.Pinout[b]["gobj"] = None
      try:
        if pinok==False:
         Settings.Pinout[b]["gobj"] = mraa.Aio(adcnum)
      except Exception as e:
        print("mraa:",e)#debug
        return False
     break

 def setpinstartstate(self,bcmpin,state):
   for b in range(len(Settings.Pinout)):
    if str(Settings.Pinout[b]["BCM"])==str(bcmpin).strip():
     if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
      self.setpinstate(b,state,True)
     break

 def setpinactualstate(self,pinid,state):
    if Settings.Pinout[pinid]["actualstate"]==7:
     self.disable_pwm_pin(-1,pinid)
    if Settings.Pinout[pinid]["startupstate"] == 8:
     if Settings.Pinout[pinid]["fullname"] in self.w1gpio:
       try:
        self.w1gpio.remove(Settings.Pinout[pinid]["fullname"])
       except:
        pass
    if Settings.Pinout[pinid]["actualstate"]<7 and state<7:
     Settings.Pinout[pinid]["actualstate"]=state

 def setpinstate(self,PINID,state,force=False):
   if (force==False):
    if Settings.Pinout[PINID]["altfunc"]>0 or Settings.Pinout[PINID]["canchange"]!=1 or Settings.Pinout[PINID]["BCM"]<0:
     return False
#   if (int(state)<=0 and int(Settings.Pinout[PINID]["startupstate"])>0):
   if int(state)<=0:
    self.setpinactualstate(PINID,99) # ugly hack
    Settings.Pinout[PINID]["startupstate"] = -1
    return True
   elif state==1:
    pass # input
    Settings.Pinout[PINID]["startupstate"] = state
    if self.gpioinit:
     self.setup(int(Settings.Pinout[PINID]["BCM"]), IN)
    self.setpinactualstate(PINID,1)
    return True
   elif state==2:
    pass # input pulldown
    Settings.Pinout[PINID]["startupstate"] = state
    if self.gpioinit:
     self.setup(int(Settings.Pinout[PINID]["BCM"]), IN, pull_up_down=PUD_DOWN)
    self.setpinactualstate(PINID,state)
    return True
   elif state==3:
    pass # input pullup
    Settings.Pinout[PINID]["startupstate"] = state
    if self.gpioinit:
     self.setup(int(Settings.Pinout[PINID]["BCM"]), IN, pull_up_down=PUD_UP)
    self.setpinactualstate(PINID,state)
    return True
   elif state==4 or state==5 or state==6:
    if state==5:
     if self.gpioinit:
      self.setup(int(Settings.Pinout[PINID]["BCM"]), OUT_LOW)
    elif state==6:
     if self.gpioinit:
      self.setup(int(Settings.Pinout[PINID]["BCM"]), OUT_HIGH)
    else:
     if self.gpioinit:
      self.setup(int(Settings.Pinout[PINID]["BCM"]), OUT)
    Settings.Pinout[PINID]["startupstate"] = state
    self.setpinactualstate(PINID,4)
    return True
   elif state==7:
    try:
     res = mraa.pinModeTest(Settings.Pinout[PINID]["ID"],mraa.PIN_PWM)
    except Exception as e:
     res = False
    if res==False:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Pin"+str(PINID)+" is not PWM-capable")
      self.setpinactualstate(PINID,-1)
      return False
    self.enable_pwm_pin(-1,int(Settings.Pinout[PINID]["ID"]))
    return True
   elif state==8:
    self.setpinactualstate(PINID,-1)
    self.set1wgpio(int(Settings.Pinout[PINID]["BCM"])) # W1GPIO-MISSING
    return True
   elif state==10: # analog
    self.setpinactualstate(PINID,-1)
    try:
     res = mraa.pinModeTest(Settings.Pinout[PINID]["ID"],mraa.PIN_AIO)
    except:
     res = False
    if res==False:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"Pin"+str(PINID)+" is not Analog-capable")
      return False
    self.setaiogpio(int(Settings.Pinout[PINID]["BCM"]))
    return True
   return False

 def initpinstates(self):
    if self.gpioinit:
     for b in range(len(Settings.Pinout)):
      if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
       if int(Settings.Pinout[b]["BCM"])>=0:
        if (int(Settings.Pinout[b]["startupstate"])<7 and int(Settings.Pinout[b]["startupstate"])>=0) or int(Settings.Pinout[b]["startupstate"])==10:
         self.setpinstate(b,Settings.Pinout[b]["startupstate"],True)

 def readconfig(self):

    self.i2cc = []
    self.pwmc = []
    self.spic = []
    self.uartc = []
    self.w1gpio = []

    try:
     import plugindeps
     for i in range(len(plugindeps.modulelist)):
      if plugindeps.modulelist[i]['name']=="GPIO":
       plugindeps.modulelist[i]["apt"] = ["libmraa","rockchip-overlay"]
       plugindeps.modulelist[i]["pip"] = []
       plugindeps.modulelist[i]["testcmd"] = "import mraa"
      elif plugindeps.modulelist[i]['name']=="Adafruit_DHT":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="ws2812":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="tm1637":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="ina219":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="pylora":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="epd":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="amg":
       plugindeps.modulelist[i]["pip"] = [""] # only RPI supported!
      elif plugindeps.modulelist[i]['name']=="wpi":
       plugindeps.modulelist[i]["installcmd"] = [""] # only RPI supported!
    except:
     pass
    Settings.PinStatesMax = 11
    Settings.PinStates[2] = "Input2"
    Settings.PinStates[3] = "Input3"
    Settings.PinStates[10] = "Analog"
    Settings.PinStates[11] = "Reserved"
    Settings.PinStates[12] = "Reserved"

    try:
     if Settings.Pinout[0]["ver"]=="13":
      self.i2cl = [0,1,3]
      self.pwml = [2,3]
      self.spil = [1,2]
      self.uartl = [0,1,2,3]
     elif Settings.Pinout[0]["ver"]=="12":
      self.i2cl = [0,1,3]
      self.pwml = [2,3]
      self.spil = [2]
      self.uartl = [0,1,2]
     elif Settings.Pinout[0]["ver"]=="11":
      self.i2cl = [0,1,2,3]
      self.pwml = [1,2,3]
      self.spil = [0,2]
      self.uartl = [0,1,2]
     elif Settings.Pinout[0]["ver"]=="10":
      self.i2cl = [0,1,2,3]
      self.pwml = [1,2,3]
      self.spil = [0,2]
      self.uartl = [0,1,2]
    except:
     pass
    spienabled = False
    w1enabled = False
    try:
     with open(self.config_file_name) as f:
      for line in f:
       line = line.strip()
       if "overlays=" in line:
        ts = line.split("=")
        os = ts[1].split(" ")
        for ov in os:
         if "i2c" in ov:
          try:
           c = int(ov[-1])
          except:
           c = -1
          self.enable_i2c(c)
         elif "uart" in ov and "console" not in ov:
          try:
           c = int(ov[-1])
          except:
           c = -1
          self.enable_serial(c)
         elif "pwm" in ov:
          try:
           c = int(ov[-1])
          except:
           c = -1
          if (c in self.pwml):
           self.pwmc.append(c)
         elif "spi" in ov:
           spienabled = True
         elif "w1-gpio" in ov:
           w1enabled = True
       else:
        if spienabled:
           if "param_spidev_spi_bus" in line:
            ts = line.split("=")
            self.enable_spi(int(ts[1].strip()))
        if w1enabled:
           if "param_w1_pin" in line:
            ts = line.split("=")
            self.w1gpio.append(ts[1].strip())  # W1GPIO-MISSING
    except:
     pass

    try:
     for b in range(len(Settings.Pinout)):
      if Settings.Pinout[b]["altfunc"] == 0 and Settings.Pinout[b]["canchange"]==1:
       if Settings.Pinout[b]["startupstate"] == 8:
         if Settings.Pinout[b]["fullname"] not in self.w1gpio:
           Settings.Pinout[b]["startupstate"] = 0
       else:
         if Settings.Pinout[b]["fullname"] in self.w1gpio:
           Settings.Pinout[b]["startupstate"] = 8
    except:
     pass
    for i in range(len(self.i2cl)):
     if self.i2cl[i] in self.i2cc:
      self.enable_i2c(self.i2cl[i])
     else:
      self.disable_i2c(self.i2cl[i])
    for i in range(len(self.spil)):
     if self.spil[i] in self.spic:
      self.enable_spi(self.spil[i])
     else:
      self.disable_spi(self.spil[i])
    for i in range(len(self.uartl)):
     if self.uartl[i] in self.uartc:
      self.enable_serial(self.uartl[i])
     else:
      self.disable_serial(self.uartl[i])
    for i in range(len(self.pwmc)):
     self.enable_pwm_pin(self.pwmc[i],-1,True)
    return True

 def resolvepinconflict(self):
    if Settings.Pinout[0]["ver"]=="13": # only v13 implemented, MISSING
     if (2 in self.pwmc) or (3 in self.pwmc):
       try:
        self.i2cc.remove(3)
       except:
        pass
     if (2 in self.uartc) or (1 in self.uartc) or (0 in self.i2cc):
       try:
        self.spic.remove(2)
       except:
        pass
     if (0 in self.i2cc):
       try:
        self.uartc.remove(1)
       except:
        pass
     if (3 in self.uartc) or (3 in self.i2cc):
       try:
        self.spic.remove(1)
       except:
        pass
     if (3 in self.i2cc):
       try:
        self.uartc.remove(3)
       except:
        pass


 def saveconfig(self):
  # save config.txt
    overlaylist = []
    try:
     output = os.popen("ls /boot/dtbs/$(uname -r)/rockchip/overlay/rk*.dtbo")
     for line in output:
      sp = line.split("/")
      fname = sp[-1]
      if "dtbo" in fname and "console" not in fname:
       overlaylist.append(fname.replace(".dtbo",""))
    except:
     pass
    self.resolvepinconflict()
    for i in range(len(self.i2cl)):
     if self.i2cl[i] in self.i2cc:
      self.enable_i2c(self.i2cl[i])
     else:
      self.disable_i2c(self.i2cl[i])
    for i in range(len(self.spil)):
     if self.spil[i] in self.spic:
      self.enable_spi(self.spil[i])
     else:
      self.disable_spi(self.spil[i])
    for i in range(len(self.uartl)):
     if self.uartl[i] in self.uartc:
      self.enable_serial(self.uartl[i])
     else:
      self.disable_serial(self.uartl[i])
    pwml = self.pwml
    if len(self.pwmc)>0 and (1 not in self.pwmc):
     self.pwmc.append(1) # it looks like RockPiS needs pwm1 even if it is not accessible
     self.pwml.append(1)
    for i in range(len(self.pwml)):
     if self.pwml[i] in self.pwmc:
      self.enable_pwm_pin(self.pwml[i],-1)
     else:
      self.disable_pwm_pin(self.pwml[i],-1)

    contents = []
    poverlays = []
    try:
     with open(self.config_file_name) as f:
      for line in f:
       line = line.strip()
       if len(line)>0 and line[0] == "#":
        line = ""
       if "overlays=" in line:
         tarr = line.split("=")
         poverlays1 = tarr[1].split(" ")
         for p in range(len(poverlays1)):
          if "console" in poverlays1[p]:
           poverlays.append(poverlays1[p])
          elif ("i2c" not in poverlays1[p]) and ("pwm" not in poverlays1[p]) and ("spi" not in poverlays1[p]) and ("uart" not in poverlays1[p]) and ("w1-gpio" not in poverlays1[p]):
           poverlays.append(poverlays1[p])
         line = ""
       if ("param_spidev_spi_bus" in line) or ("param_w1_pin" in line):
         line = ""
       if line != "":
        contents.append(line)
    except:
     pass
    with open(self.config_file_name,"w") as f:
     for c in range(len(contents)):
      f.write(contents[c]+"\n")

     line = "overlays="
     for i in range(len(poverlays)):
      line += poverlays[i]+" "
     for i in range(len(self.i2cc)):
       mod = ""
       for x in range(len(overlaylist)):
        if "i2c"+str(self.i2cc[i]) in overlaylist[x]:
          mod = overlaylist[x].strip()
       if mod != "":
        line += mod+" "
     for i in range(len(self.uartc)):
       mod = ""
       for x in range(len(overlaylist)):
        if "uart"+str(self.uartc[i]) in overlaylist[x]:
          mod = overlaylist[x].strip()
       if mod != "":
        line += mod+" "
     for i in range(len(self.pwmc)):
       mod = ""
       for x in range(len(overlaylist)):
        if "pwm"+str(self.pwmc[i]) in overlaylist[x]:
          mod = overlaylist[x].strip()
       if mod != "":
        line += mod+" "
     if len(self.spic)>0:
       for x in range(len(overlaylist)):
        if "spi" in overlaylist[x]:
          mod = overlaylist[x].strip()
       if mod != "":
        line += mod+" "
     if len(self.w1gpio)>0:
       for x in range(len(overlaylist)):
        if "w1-gpio" in overlaylist[x]:
          mod = overlaylist[x].strip()
       if mod != "":
        line += mod+" "
     f.write(line+"\n")
     if len(self.spic)>0:
      for i in range(len(self.spic)):
       f.write("param_spidev_spi_bus="+str(self.spic[i])+"\n")

     if len(self.w1gpio)>0:
      for i in range(len(self.w1gpio)):
       f.write("param_w1_pin="+str(self.w1gpio[i])+"\n") # W1GPIO-MISSING

 def is_i2c_lib_available(self):
  res = False
  try:
   import smbus
   res = True
  except:
   res = False
  return res

 def i2cscan(self,bus_number):
    devices = []
    try:
     bus = smbus.SMBus(bus_number)
    except Exception as e:
     devices = []
    for device in range(3, 125): 
        try:
            if (device>=0x30 and device<=0x37) or (device>=0x50 and device<=0x5f):
             bus.read_byte(device)
            else:
             bus.write_quick(device)
            devices.append(device)  # hex(number)?
        except:
            pass
    if (0x5c not in devices): # 0x5c has to be checked twice as Am2320 auto-shutdown itself?
     try: 
      bus.read_byte(0x5c)
      devices.append(0x5c)
     except:
      pass
    if (0x7f not in devices): # 0x7f is non-standard used by PME
     try: 
      bus.read_byte(0x7f)
      devices.append(0x7f)
     except:
      pass

    try:
     bus.close()
    except:
     pass
    bus = None
    return devices

 def geti2clist(self):
     import glob
     rlist = []
     try:
      devlist = glob.glob('/dev/i2c*')
      if len(devlist)>0:
       for d in devlist:
        dstr = d.split("-")
        try:
         rlist.append(int(dstr[1]))
        except:
         pass
     except:
      rlist = []
     return rlist

 def getspilist(self):
     import glob
     sch = []
     sdev = []
     try:
      devlist = glob.glob('/dev/spi*')
      if len(devlist)>0:
       for d in devlist:
        try:
         dstr = d.replace("/dev/spidev","")
         d2str = dstr.split(".")
         if int(d2str[0]) not in sch:
          sch.append(int(d2str[0]))
         if int(d2str[1]) not in sdev:
          sdev.append(int(d2str[1]))
        except:
         pass
      sch.sort()
      sdev.sort()
     except:
      rlist = []
     return sch, sdev

 def getanaloglist(self):
     res = []
     for b in range(len(Settings.Pinout)):
      if "ADC_IN" in Settings.Pinout[b]["name"][0]:
       try:
        adcnum = int(Settings.Pinout[b]["name"][0][6])
        res.append( [adcnum, Settings.Pinout[b]["name"][0] ] )
       except:
        pass
     return res

 def analog_read(self,adcnum):
     res = None
     for b in range(len(Settings.Pinout)):
      if "ADC_IN"+str(adcnum) in Settings.Pinout[b]["name"][0]:
       pinok = False
       try:
        if Settings.Pinout[b]["gobj"] is not None:
         res = Settings.Pinout[b]["gobj"].read()
         pinok = True
       except Exception as e:
        pass
       try:
        if pinok==False:
         print(adcnum)
         Settings.Pinout[b]["gobj"] = mraa.Aio(int(adcnum))
         res = Settings.Pinout[b]["gobj"].read()
         pinok = True
       except Exception as e:
        print("mraa:",e)#debug
       break
     return res

 def createpinout(self,pinout):
  global PINOUT40, PINOUT26RS, PINOUT26RSv13, PINOUT26RSv11, PINOUT26RSv10
  if pinout == "26rs" and (len(Settings.Pinout) != 27 or len(Settings.Pinout) != 53):
     vt = "0"
     try:
      res = mraa.pinModeTest(9,mraa.PIN_UART) #if pin9 is uart
     except:
      res = False
     if res:
      vt="10"
     else:
      try:
       res = mraa.pinModeTest(16,mraa.PIN_I2C) #if pin16 is i2c
      except:
       res = False
      if res:
       vt="11"
     if vt=="0":
       try:
        res = mraa.Gpio(106,owner=False,raw=True)
        vt = "13" #1.3 has GPIO106
       except:
        vt = "12"
     if vt=="13":
      Settings.Pinout = PINOUT26RSv13
     elif vt=="12":
      Settings.Pinout = PINOUT26RSv13 #modify 4 pin!!!
      Settings.Pinout[0]["ver"] = "12"
      Settings.Pinout[39] = {"ID":39,"BCM":-1,"name":["MICN6"],"canchange":0,"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None}
      Settings.Pinout[40] = {"ID":40,"BCM":-1,"name":["MCIP6"],"canchange":0,"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None}
      Settings.Pinout[41] = {"ID":41,"BCM":-1,"name":["MICN5"],"canchange":0,"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None}
      Settings.Pinout[42] = {"ID":42,"BCM":-1,"name":["MCIP5"],"canchange":0,"altfunc": 0,"startupstate":-1,"actualstate":-1,"gobj":None,"cb":None}
     elif vt=="11":
      Settings.Pinout = PINOUT26RSv11
     elif vt=="10":
      Settings.Pinout = PINOUT26RSv11
      Settings.Pinout[0]["ver"] = "10"
      for p in range(len(PINOUT26RSv10)):
        Settings.Pinout[p] = PINOUT26RSv10[p] # correct first 26pin
  else:
     Settings.Pinout = PINOUT40 #unsupported

 def webform_load(self):
  webserver.TXBuffer += "<form name='frmselect' method='post'><table class='normal'>"
  webserver.TXBuffer += "<tr><th colspan=10>GPIO pinout</th></tr>"
  webserver.addHtml("<tr><th>Detected function</th><th>Requested function</th><th>Pin name</th><th>#</th><th>Value</th><th>Value</th><th>#</th><th>Pin name</th><th>Requested function</th><th>Detected function</th></tr>")
  realpins = mraa.getPinCount()-1
  for p in range(len(Settings.Pinout)):
   if Settings.Pinout[p]["canchange"] != 2:
    idnum = int(Settings.Pinout[p]["ID"])
    if bool(idnum & 1): # left
     webserver.TXBuffer += "<TR><td>"
#     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["altfunc"]==0:
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["BCM"]>0:
      # print pin setup infos
      astate = Settings.Pinout[p]["actualstate"]
      if astate<0:
       astate=0
      astate = Settings.PinStates[astate]
      pinfunc = -1
      gs = False
      if self.gpioinit:
       gs = mraa.pinModeTest(Settings.Pinout[p]["ID"],mraa.PIN_GPIO)
       pinfunc = self.gpio_function(int(Settings.Pinout[p]["BCM"]))
       astate = str(self.gpio_function_name(pinfunc))
       if p > realpins:
        gs = True
      webserver.TXBuffer += astate
      webserver.TXBuffer += "</td>" # actual state 
     else:
      webserver.TXBuffer += "-</td>"
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["altfunc"]==0:
      webserver.addHtml("<td>") # startupstate
      webserver.addSelector("pinstate"+str(p),Settings.PinStatesMax,Settings.PinStates,False,None,Settings.Pinout[p]["startupstate"],False)
      webserver.addHtml("</td>")
     else:
      webserver.TXBuffer += "<td>-</td>"
     try:
      funcorder = int(Settings.Pinout[p]["altfunc"])
     except:
      funcorder = 0
     if funcorder>0 and len(Settings.Pinout[p]["name"])>funcorder:
      webserver.TXBuffer += "<td>"+ Settings.Pinout[p]["name"][funcorder] +"</td>"
      gs = False
     else:
      webserver.TXBuffer += "<td>"+ Settings.Pinout[p]["name"][0] +"</td>"
     webserver.TXBuffer += "<td>"+ str(Settings.Pinout[p]["ID"]) +"</td>"
     webserver.TXBuffer += "<td style='{border-right: solid 1px #000;}'>"
     if Settings.Pinout[p]["canchange"]==1 and pinfunc in [0,1] and (astate in ["Input","Output"]):
      if self.gpioinit:
       self.setpinstate(p,int(Settings.Pinout[p]["startupstate"]))
       if gs:
        try:
         webserver.TXBuffer += "("+str(self.input(int(Settings.Pinout[p]["BCM"])))+")"
        except:
         webserver.TXBuffer += "E" 
       else:
        webserver.TXBuffer += "S"
      else:
       webserver.TXBuffer += "X" 
      webserver.TXBuffer += "</td>" # add pin value
     else:
      webserver.TXBuffer += "-</td>"
    else:               # right
     gs = 0
     pinfunc = -1
     try:
      funcorder = int(Settings.Pinout[p]["altfunc"])
     except:
      funcorder = 0
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["BCM"]>0:
      webserver.TXBuffer += "<td>"
      if self.gpioinit:
       gs = mraa.pinModeTest(int(Settings.Pinout[p]["ID"]),mraa.PIN_GPIO)
       if p > realpins:
        gs = True
       if funcorder>0:
        gs = False
       pinfunc = self.gpio_function(int(Settings.Pinout[p]["BCM"]))
       if pinfunc in [0,1] and Settings.Pinout[p]["altfunc"]==0:
        self.setpinstate(p,int(Settings.Pinout[p]["startupstate"]))
        if gs:
         try:
          webserver.TXBuffer += "("+str(self.input(int(Settings.Pinout[p]["BCM"])))+")"
         except:
          webserver.TXBuffer += "E" 
        else:
         webserver.TXBuffer += "S"
      else:
       webserver.TXBuffer += "X" 
      webserver.TXBuffer += "</td>" # add pin value
     else:
      webserver.TXBuffer += "<td>-</td>"
     webserver.TXBuffer += "<td>"+ str(Settings.Pinout[p]["ID"]) +"</td>"
     if funcorder>0 and len(Settings.Pinout[p]["name"])>funcorder:
      webserver.TXBuffer += "<td>"+ Settings.Pinout[p]["name"][funcorder] +"</td>"
     else:
      webserver.TXBuffer += "<td>"+ Settings.Pinout[p]["name"][0] +"</td>"
     webserver.TXBuffer += "<td>"
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["altfunc"]==0:
      # print pin setup infos
      webserver.addSelector("pinstate"+str(p),Settings.PinStatesMax,Settings.PinStates,False,None,Settings.Pinout[p]["startupstate"],False)
      webserver.addHtml("</td>")
     else:
      webserver.TXBuffer += "-</td>"
     webserver.addHtml("<td>") # startupstate
     if Settings.Pinout[p]["canchange"]==1 and Settings.Pinout[p]["BCM"]>0:
      astate = Settings.Pinout[p]["actualstate"]
      if astate<0:
        astate=0
      astate = Settings.PinStates[astate]
      if self.gpioinit:
        astate = str(self.gpio_function_name(pinfunc))
      webserver.TXBuffer += str(astate)+"</td>" # actual state 
     else:
      webserver.TXBuffer += "<td>-</td>"
     webserver.TXBuffer += "</TR>"
  webserver.TXBuffer += "</table>"

  webserver.TXBuffer += "<table class='normal'><TR>"
  webserver.addFormHeader("Advanced features")
  for i in range(0,6):
   if self.is_i2c_usable(i):
    webserver.addFormCheckBox("Enable I2C-"+str(i),"i2c"+str(i),self.is_i2c_enabled(i))
  for i in range(0,6):
   if self.is_spi_usable(i):
    webserver.addFormCheckBox("Enable SPI-"+str(i),"spi"+str(i),self.is_spi_enabled(i))
  for i in range(0,7):
   if self.is_serial_usable(i):
    webserver.addFormCheckBox("Enable UART-"+str(i),"uart"+str(i),self.is_serial_enabled(i))
  webserver.addFormSeparator(2)
  webserver.TXBuffer += "<tr><td colspan=2>"
  if OS.check_permission():
   webserver.addSubmitButton()
  webserver.addSubmitButton("Set without save","set")
  webserver.addSubmitButton("Reread config","reread")
  webserver.TXBuffer += "</td></tr>"
  if OS.check_permission():
   if OS.checkboot_ro():
     webserver.addFormNote("<font color='red'>WARNING: Your /boot partition is mounted READONLY! Changes could not be saved! Run 'sudo mount -o remount,rw /boot' or whatever necessary to solve it!")
  webserver.addFormNote("WARNING: Some changes needed to reboot after submitting changes! And most changes requires root permission.")
  webserver.addHtml("</table></form>")

  return True

 def webform_save(self,params):
   submit = webserver.arg("Submit",params)
   setbtn = webserver.arg("set",params)
   if (submit=='Submit') or (setbtn!=''):
    for i in range(0,6):
     wset = webserver.arg("i2c"+str(i),params)
     if wset=="on":
      self.enable_i2c(i)
     else:
      self.disable_i2c(i)
    for i in range(0,6):
     wset = webserver.arg("spi"+str(i),params)
     if wset=="on":
      self.enable_spi(i)
     else:
      self.disable_spi(i)
    for i in range(0,7):
     wset = webserver.arg("uart"+str(i),params)
     if wset=="on":
      self.enable_serial(i)
     else:
      self.disable_serial(i)
    for p in range(len(Settings.Pinout)):
     try:
      pins = webserver.arg("pinstate"+str(p),params).strip()
      if pins and pins!="" and p!= "":
       try:
        self.setpinstate(p,int(pins))
       except Exception as e:
        misc.addLog(rpieGlobals.LOG_LEVEL_DEBUG,"Pin "+str(p)+" "+str(e))
     except:
      pass
    if OS.check_permission() and setbtn=='':
     try:
      self.saveconfig()
     except Exception as e:
      misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    try:
     Settings.savepinout()
    except Exception as e:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
   return True

def isr_callback(data=None):
  try:
   if data is not None:
    Settings.Pinout[data]["cb"](data) # call isr indirectly as mraa is unable to do it alone...
  except:
   pass

#Init Hardware GLOBAL ports
#HWPorts = hwports()
