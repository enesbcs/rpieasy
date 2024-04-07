#!/usr/bin/env python3
#############################################################################
################# Helper Library for I2C mini encoder #######################
#############################################################################
#
# Copyright (C) 2024 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
try:
 import lib.i2cencodermini.i2cEncoderMiniLib as menc
except:
 raise("Unable to load I2C mini encoder library")

menc_devices = []

def request_menc_device(busnum,i2caddress):
  global menc_devices
  for i in range(len(menc_devices)):
   if (menc_devices[i].i2cadd == int(i2caddress) and menc_devices[i].i2c==int(busnum)):
    return menc_devices[i]
  encoder = menc.i2cEncoderMiniLib(busnum, i2caddress)
  encconfig = ( menc.WRAP_DISABLE | menc.DIRE_RIGHT | menc.IPUP_ENABLE | menc.RMOD_X1)
  encoder.begin(encconfig)
  menc_devices.append(encoder)
  return menc_devices[-1]
