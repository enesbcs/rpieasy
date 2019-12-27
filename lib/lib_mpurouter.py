#!/usr/bin/env python3
#############################################################################
##################### Helper Library for MPU6050 ############################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
from mpu6050 import mpu6050

class MPUEntity():

 SIGNAL_PATH_RESET = 0x68
 I2C_SLV0_ADDR     = 0x37
 ACCEL_CONFIG      = 0x1C 
 MOT_THR           = 0x1F
 MOT_DUR           = 0x20
 MOT_DETECT_CTRL   = 0x69
 INT_ENABLE        = 0x38

 def __init__(self, i2cAddress, busnum=1):
  self.busy = False
  self.initialized = False
  self.i2cAddress = int(i2cAddress)
  self.busnum = int(busnum)
  self.ax = 0
  self.ay = 0
  self.az = 0
  self.gx = 0
  self.gy = 0
  self.gz = 0
  try:
   self.mpu = mpu6050(i2cAddress,bus=busnum)
   self.mpu.set_gyro_range(mpu6050.GYRO_RANGE_250DEG)

   self.mpu.bus.write_byte_data(i2cAddress, self.SIGNAL_PATH_RESET, 0x07)
   self.mpu.bus.write_byte_data(i2cAddress, self.I2C_SLV0_ADDR, 0x80 | 0x40)
#   self.mpu.bus.write_byte_data(i2cAddress, self.ACCEL_CONFIG, 0x01)
   self.mpu.bus.write_byte_data(i2cAddress, self.MOT_THR, 2) # 0x14
   self.mpu.bus.write_byte_data(i2cAddress, self.MOT_DUR, 1)
   self.mpu.bus.write_byte_data(i2cAddress, self.MOT_DETECT_CTRL, 0x15)
   self.mpu.bus.write_byte_data(i2cAddress, self.INT_ENABLE, 0x40)
   self.mpu.set_accel_range(mpu6050.ACCEL_RANGE_2G)

   self.initialized = True
  except Exception as e:
   print(e)
   self.initialized = False

 def buf_read_accel(self):
  try:
   if (self.busy==False):
    self.busy=True
    val = self.mpu.get_accel_data()
    self.ax = val['x']
    self.ay = val['y']
    self.az = val['z']
    self.busy=False
  except:
    self.busy=False

 def buf_read_gyro(self):
  try:
   if (self.busy==False):
    self.busy=True
    val = self.mpu.get_gyro_data()
    self.gx = val['x']
    self.gy = val['y']
    self.gz = val['z']
    self.busy=False
  except:
    self.busy=False

 def buf_read(self): 
  try:
   if (self.busy==False):
    self.busy=True
    val = self.mpu.get_accel_data()
    self.ax = val['x']
    self.ay = val['y']
    self.az = val['z']
    val = self.mpu.get_gyro_data()
    self.gx = val['x']
    self.gy = val['y']
    self.gz = val['z']
    self.busy=False
  except Exception as e:
    self.busy=False

mpu_devices = []

def request_mpu_device(i2caddress,busnum):
  for i in range(len(mpu_devices)):
   if (mpu_devices[i].i2cAddress == int(i2caddress)):
    return mpu_devices[i]
  mpu_devices.append(MPUEntity(i2caddress,busnum))
  return mpu_devices[-1]

