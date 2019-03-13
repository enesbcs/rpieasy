#!/usr/bin/env python3
#############################################################################
#################### Helper Library for MLX90614 ############################
#############################################################################
#
# Copyright (C) 2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
try:
 import lib.MLX90614.mlx90614 as MLX
except:
 raise("Unable to load MLX90614 library")

mlx_devices = []

def request_mlx_device(busnum,i2caddress):
  for i in range(len(mlx_devices)):
   if (mlx_devices[i].address == int(i2caddress) and mlx_devices[i].bus==int(busnum)):
    return mlx_devices[i]
  mlx_devices.append(MLX.MLX90614(address=i2caddress,bus_num=busnum))
  return mlx_devices[-1]
