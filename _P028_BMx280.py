#!/usr/bin/env python3
#############################################################################
###################### BMP280/BME280 plugin for RPIEasy #####################
#############################################################################
#
# Copyright (C) 2018-2019 by Alexander Nagy - https://bitekmindenhol.blog.hu/
#
# BME280 code used from:
# https://github.com/cmur2/python-bme280
# The MIT License (MIT)
# Copyright (c) 2016 Christian Nicolai

import plugin
import webserver
import rpieGlobals
import rpieTime
import misc
import gpios
import smbus
import time

class Plugin(plugin.PluginProto):
 PLUGIN_ID = 28
 PLUGIN_NAME = "Environment - BMP280/BME280"
 PLUGIN_VALUENAME1 = "Temperature"
 PLUGIN_VALUENAME2 = "Humidity"
 PLUGIN_VALUENAME3 = "Pressure"

 def __init__(self,taskindex): # general init
  plugin.PluginProto.__init__(self,taskindex)
  self.dtype = rpieGlobals.DEVICE_TYPE_I2C
  self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_HUM_BARO
  self.readinprogress = 0
  self.valuecount = 3
  self.senddataoption = True
  self.timeroption = True
  self.timeroptional = False
  self.formulaoption = True
  self._nextdataservetime = 0
  self.bme = None
  self.hashumidity = False

 def plugin_init(self,enableplugin=None):
  plugin.PluginProto.plugin_init(self,enableplugin)
  self.uservar[0] = 0
  self.uservar[1] = 0
  self.uservar[2] = 0
  sensoraddress = int(self.taskdevicepluginconfig[0])
  if self.enabled and sensoraddress in [0x76,0x77]:
   try:
    self.bme = None
    i2cok = gpios.HWPorts.i2c_init()
    self.bme = Bme280(i2c_bus=gpios.HWPorts.i2cbus,sensor_address=sensoraddress)
    if i2cok:
     if self.interval>2:
      nextr = self.interval-2
     else:
      nextr = self.interval
     self._lastdataservetime = rpieTime.millis()-(nextr*1000)
    else:
     misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,"BME through I2C can not be initialized!")
     self.enabled = False
   except Exception as e:
    misc.addLog(rpieGlobals.LOG_LEVEL_ERROR,str(e))
    self.enabled = False
  if self.enabled:
   chiptype = self.bme.get_chip_id()
   self.hashumidity = False
   chipname = "Unknown"
   if chiptype == 0x60:
    chipname = "BME280"
    self.hashumidity = True
    self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_HUM_BARO
   elif chiptype in [0x56,0x57,0x58]:
    chipname = "BMP280"
    self.vtype = rpieGlobals.SENSOR_TYPE_TEMP_EMPTY_BARO
   misc.addLog(rpieGlobals.LOG_LEVEL_INFO,chipname+" ("+str(chiptype)+") initialized, Humidity: "+str(self.hashumidity))

 def webform_load(self): # create html page for settings
  choice1 = self.taskdevicepluginconfig[0]
  options = ["0x76","0x77"]
  optionvalues = [0x76,0x77]
  webserver.addFormSelector("Address","plugin_028_addr",2,options,optionvalues,None,int(choice1))
  webserver.addFormNote("Enable <a href='pinout'>I2C bus</a> first, than <a href='i2cscanner'>search for the used address</a>!")
  return True

 def webform_save(self,params): # process settings post reply
  initpar = self.taskdevicepluginconfig[0]
  par = webserver.arg("plugin_028_addr",params)
  if par == "":
   par = 0
  self.taskdevicepluginconfig[0] = int(par)
  if initpar != self.taskdevicepluginconfig[0]:
   self.plugin_init()
  return True

 def plugin_read(self): # deal with data processing at specified time interval
  result = False
  if self.initialized and self.readinprogress==0 and self.enabled:
   self.readinprogress = 1
   temp, press, hum = self.bme.get_data()
   self.set_value(1,temp,False)
   self.set_value(2,hum,False)
   self.set_value(3,press,False)
   self.plugin_senddata()
   self._lastdataservetime = rpieTime.millis()
   result = True
   self.readinprogress = 0
  return result

class Bme280(object):
    ADDR = 0x76
    HO_1 = 0x01
    PO_1 = 0x01
    TO_1 = 0x01
    MODE_SLEEP = 0x00
    MODE_FORCED = 0x01 # and 0x02
    TSTANDBY_1000 = 0x05
    FILTER_OFF = 0x00
    REGISTER_ID = 0xD0
    REGISTER_CTRL_HUM = 0xF2
    REGISTER_CTRL_MEAS = 0xF4
    REGISTER_CONFIG = 0xF5

    def __init__(self, i2c_bus=None, sensor_address=ADDR):
       if i2c_bus != None:
        self.bus = i2c_bus # smbus.SMBus(1)
        self.sensor_address = sensor_address
        self.ho = self.HO_1
        self.po = self.PO_1
        self.to = self.TO_1
        self.mode = self.MODE_SLEEP
        self.tstandy = self.TSTANDBY_1000
        self.filter = self.FILTER_OFF
        self.readinprogress = 0
        self.read_calibration_parameters()
        # initialize once
        self.bus.write_byte_data(self.sensor_address, self.REGISTER_CTRL_HUM, self.get_reg_ctrl_hum())
        self.bus.write_byte_data(self.sensor_address, self.REGISTER_CTRL_MEAS, self.get_reg_ctrl_meas())
        self.bus.write_byte_data(self.sensor_address, self.REGISTER_CONFIG, self.get_reg_config())

    def get_chip_id(self):
        return self.bus.read_byte_data(self.sensor_address, self.REGISTER_ID)

    def set_mode(self, mode):
        self.mode = mode
        self.bus.write_byte_data(self.sensor_address, self.REGISTER_CTRL_MEAS, self.get_reg_ctrl_meas())

    def get_reg_ctrl_hum(self):
        """
        returns the bit pattern for CTRL_HUM corresponding to the desired state of this class
        """
        return self.ho & 0x07

    def get_reg_ctrl_meas(self):
        """
        returns the bit pattern for CTRL_MEAS corresponding to the desired state of this class
        """
        return ((self.to & 0x07) << 5) | ((self.po & 0x07) << 2) | self.mode

    def get_reg_config(self):
        """
        returns the bit pattern for CONFIG corresponding to the desired state of this class
        """
        # SPI permanently disabled
        return ((self.tstandy & 0x07) << 5) | ((self.filter & 0x07) << 2) | 0x00

    def read_calibration_parameters(self):
        # read all calibration registers from chip NVM
        calibration_regs = []
        for i in range(0x88, 0x88+24):
            calibration_regs.append(self.bus.read_byte_data(self.sensor_address, i))
        calibration_regs.append(self.bus.read_byte_data(self.sensor_address, 0xA1))
        for i in range(0xE1, 0xE1+7):
            calibration_regs.append(self.bus.read_byte_data(self.sensor_address, i))
        # pylint: disable=bad-whitespace
        # reorganize 8-bit words into compensation words (without correct sign)
        self.digT = []
        self.digT.append((calibration_regs[1] << 8) | calibration_regs[0])
        self.digT.append((calibration_regs[3] << 8) | calibration_regs[2])
        self.digT.append((calibration_regs[5] << 8) | calibration_regs[4])
        self.digP = []
        self.digP.append((calibration_regs[7] << 8) | calibration_regs[6])
        self.digP.append((calibration_regs[9] << 8) | calibration_regs[8])
        self.digP.append((calibration_regs[11]<< 8) | calibration_regs[10])
        self.digP.append((calibration_regs[13]<< 8) | calibration_regs[12])
        self.digP.append((calibration_regs[15]<< 8) | calibration_regs[14])
        self.digP.append((calibration_regs[17]<< 8) | calibration_regs[16])
        self.digP.append((calibration_regs[19]<< 8) | calibration_regs[18])
        self.digP.append((calibration_regs[21]<< 8) | calibration_regs[20])
        self.digP.append((calibration_regs[23]<< 8) | calibration_regs[22])
        self.digH = []
        self.digH.append( calibration_regs[24] )
        self.digH.append((calibration_regs[26]<< 8) | calibration_regs[25])
        self.digH.append( calibration_regs[27] )
        self.digH.append((calibration_regs[28]<< 4) | (0x0F & calibration_regs[29]))
        self.digH.append((calibration_regs[30]<< 4) | ((calibration_regs[29] >> 4) & 0x0F))
        self.digH.append( calibration_regs[31] )
        # fix sign for integers in two's complement
        for i in [1,2]:
            if self.digT[i] & 0x8000:
                self.digT[i] = (-self.digT[i] ^ 0xFFFF) + 1
        for i in [1,2,3,4,5,6,7,8]:
            if self.digP[i] & 0x8000:
                self.digP[i] = (-self.digP[i] ^ 0xFFFF) + 1
        for i in [1]:
            if self.digH[i] & 0x8000:
                self.digH[i] = (-self.digH[i] ^ 0xFFFF) + 1
        for i in [3,4]:
            if self.digH[i] & 0x0800:
                self.digH[i] = (-self.digH[i] ^ 0x0FFF) + 1
        for i in [5]:
            if self.digH[i] & 0x0080:
                self.digH[i] = (-self.digH[i] ^ 0x00FF) + 1
    # Code from Bosch datasheet translated to Python

    def get_data(self):
      if self.readinprogress == 0:
        self.readinprogress = 1
        self.set_mode(self.MODE_FORCED)
        t_measure_max = 1.25 + (2.3 * self.to) + (2.3 * self.po + 0.575) + (2.3 * self.ho + 0.575)
        time.sleep(t_measure_max/1000.0)
        data = []
        for i in range(0xF7, 0xF7+8):
            data.append(self.bus.read_byte_data(self.sensor_address, i))
        pressure_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temperature_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        humidity_raw = (data[6] << 8) | data[7]
        t_fine = self.calc_t_fine(temperature_raw)
        t = self.calc_compensated_temperature(t_fine)
        p = self.calc_compensated_pressure(t_fine, pressure_raw)
        h = self.calc_compensated_humidity(t_fine, humidity_raw)
        # chip returns to sleep after data readout automatically, mirror it
        self.mode = self.MODE_SLEEP
        self.readinprogress = 0
        return (t, p, h)

    def calc_t_fine(self, adc_T):
        var1 = (adc_T / 16384.0 - self.digT[0] / 1024.0) * self.digT[1]
        var2 = (adc_T / 131072.0 - self.digT[0] / 8192.0) * (adc_T / 131072.0 - self.digT[0] / 8192.0) * self.digT[2]
        return var1 + var2

    def calc_compensated_temperature(self, t_fine):
        return t_fine / 5120.0

    def calc_compensated_pressure(self, t_fine, adc_P):
        var1 = (t_fine/2.0) - 64000.0
        var2 = var1 * var1 * (self.digP[5]) / 32768.0
        var2 = var2 + var1 * (self.digP[4]) * 2.0
        var2 = (var2/4.0)+(self.digP[3] * 65536.0)
        var1 = (self.digP[2] * var1 * var1 / 524288.0 + self.digP[1] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0)*self.digP[0]
        if var1 == 0.0:
            return 0 # avoid exception caused by division by zero
        p = 1048576.0 - adc_P
        p = (p - (var2 / 4096.0)) * 6250.0 / var1
        var1 = self.digP[8] * p * p / 2147483648.0
        var2 = p * self.digP[7] / 32768.0
        return p + (var1 + var2 + self.digP[6]) / 16.0

    def calc_compensated_humidity(self, t_fine, adc_H):
        var_H = t_fine - 76800.0
        var_H = (adc_H - (self.digH[3] * 64.0 + self.digH[4] / 16384.0 * var_H)) * (self.digH[1] / 65536.0 * (1.0 + self.digH[5] / 67108864.0 * var_H * (1.0 + self.digH[2] / 67108864.0 * var_H)))
        var_H = var_H * (1.0 - self.digH[0] * var_H / 524288.0)
        if var_H > 100.0:
            var_H = 100.0
        elif var_H < 0.0:
            var_H = 0.0
        return var_H

