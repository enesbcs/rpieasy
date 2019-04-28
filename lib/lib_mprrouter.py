#!/usr/bin/env python3
#############################################################################
#################### Helper Library for MPR121 ##############################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
try:
 import lib.MPR121.MPR121 as MPR
except:
 raise("Unable to load MPR121 library")

mpr_devices = []

def request_mpr_device(busnum,i2caddress):
  for i in range(len(mpr_devices)):
   if (mpr_devices[i].i2c_address == int(i2caddress) and mpr_devices[i].i2c_channel==int(busnum)):
    return mpr_devices[i]
  mpr_devices.append(MPR.MPR121(i2caddress,busnum))
  mpr_devices[-1].connect()
  return mpr_devices[-1]
