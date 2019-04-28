#!/usr/bin/env python
# W. H. Bell
#
# A SMBus based driver for the MPR121 touch sensor.
#
# This driver has been tested with a
# "Adafruit Capacitive Touch HAT for Raspberry Pi"
# and a Raspberry Pi 2.
#
import smbus
import time

MAX_I2C_RETRIES = 5

class MPR121(object):

  # Addresses taken from the MPR121 Quick Start Guide (app_note AN3944)
  __MHD_Rising = 0x2B
  __NHD_Amount_Rising = 0x2C
  __NCL_Rising = 0x2D
  __FDL_Rising = 0x2E
  __MHD_Falling = 0x2F
  __NHD_Amount_Falling = 0x30 
  __NCL_Falling = 0x31 
  __FDL_Falling = 0x32
  __ELE0_Touch_Threshold = 0x41
  __ELE0_Release_Threshold = 0x42
  __ELE1_Touch_Threshold = 0x43
  __ELE1_Release_Threshold = 0x44
  __ELE2_Touch_Threshold = 0x45
  __ELE2_Release_Threshold = 0x46
  __ELE3_Touch_Threshold = 0x47
  __ELE3_Release_Threshold = 0x48
  __ELE4_Touch_Threshold = 0x49
  __ELE4_Release_Threshold = 0x4A
  __ELE5_Touch_Threshold = 0x4B
  __ELE5_Release_Threshold = 0x4C
  __ELE6_Touch_Threshold = 0x4D
  __ELE6_Release_Threshold = 0x4E
  __ELE7_Touch_Threshold = 0x4F
  __ELE7_Release_Threshold = 0x50
  __ELE8_Touch_Threshold = 0x51
  __ELE8_Release_Threshold = 0x52
  __ELE9_Touch_Threshold = 0x53
  __ELE9_Release_Threshold = 0x54
  __ELE10_Touch_Threshold = 0x55
  __ELE10_Release_Threshold = 0x56
  __ELE11_Touch_Threshold = 0x57
  __ELE11_Release_Threshold = 0x58
  __Filter_Configuration = 0x5D
  __Electrode_Configuration = 0x5E
  __AUTO_CONFIG_Control_Register_0 = 0x7B
  __AUTO_CONFIG_USL_Register = 0x7D
  __AUTO_CONFIG_LSL_Register = 0x7E
  __AUTO_CONFIG_Target_Level_Register = 0x7F

  # Other addresses taken from the datasheet
  __Software_Reset_Register = 0x80
  __Debounce_Register = 0x5B
  #__AFE_Configuration_Register_1 = 0x5C
  #__AFE_Configuration_Register_2 = 0x5D

  def defaultSettings(self):
    self.__settings = []
    # Default settings taken from the MPR121 Quick Start Guide (app_note AN3944)
    self.__settings += [ (self.__MHD_Rising, 0x01) ]
    self.__settings += [ (self.__NHD_Amount_Rising, 0x01) ]
    self.__settings += [ (self.__NCL_Rising, 0x00) ]
    self.__settings += [ (self.__FDL_Rising, 0x00) ]
    self.__settings += [ (self.__MHD_Falling, 0x01) ]
    self.__settings += [ (self.__NHD_Amount_Falling, 0x01) ]
    self.__settings += [ (self.__NCL_Falling, 0xFF) ]
    self.__settings += [ (self.__FDL_Falling, 0x02) ]
    self.__settings += [ (self.__ELE0_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE0_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE1_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE1_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE2_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE2_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE3_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE3_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE4_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE4_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE5_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE5_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE6_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE6_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE7_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE7_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE8_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE8_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE9_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE9_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE10_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE10_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__ELE11_Touch_Threshold, 0x0F) ]
    self.__settings += [ (self.__ELE11_Release_Threshold, 0x0A) ]
    self.__settings += [ (self.__Filter_Configuration, 0x04) ]
    self.__settings += [ (self.__Debounce_Register, 0x00) ]

  def __init__(self, i2c_address = 0x5A, i2c_channel=-1):
    self.i2c_address = i2c_address
    self.i2c_channel = i2c_channel

    # If the i2c channel has not been set, then use the default
    if self.i2c_channel < 0:
      return false

    # Set the default bus value
    self.bus = None

    # Set the settings to their defaults
    self.defaultSettings()

  def connect(self):
    self.bus = smbus.SMBus(self.i2c_channel)

    # Software reset (documented in data sheet for MPR121)
    self.bus.write_byte_data(self.i2c_address, self.__Software_Reset_Register, 0x63)

    # Put the device into stand-by, ready to write settings.
    # (Cannot write settings if the device is running.)
    self.bus.write_byte_data(self.i2c_address, self.__Electrode_Configuration, 0x00)

    # Write the default settings to the device
    for (addr, value) in self.__settings:
      self.bus.write_byte_data(self.i2c_address, addr, value)

    # Enable all 12 electrodes and put the device into run mode.
    self.bus.write_byte_data(self.i2c_address, self.__Electrode_Configuration, 0x0C)

  def readTouch(self):
    # Read the low and high registers for the touch sensors.
    # (The registers are documented in Table 1 of the datasheet MPR121.pdf
    # This command retrieves the values of both registers)
    word = self._i2c_retry(self.bus.read_word_data,self.i2c_address, 0x00)

    # The high byte contains data from electrodes 9-12 and other bits above.
    # Therefore, mask out any bits that are not the 12 electrodes.
    return word & 0x0FFF

  def isTouched(self, sensorNumber):
    assert pin >= 0 and pin < 12, 'ERROR: The sensor number must be within the range 0-11'
    word = self.readTouch()
    bit = (word & (1 << sensorNumber))
    if bit > 0:
      return True
    return False

  def _i2c_retry(self, func, *params):
        # Run specified I2C request and ignore IOError 110 (timeout) up to
        # retries times.  For some reason the Pi 2 hardware I2C appears to be
        # flakey and randomly return timeout errors on I2C reads.  This will
        # catch those errors, reset the MPR121, and retry.
        count = 0
        while True:
            try:
                return func(*params)
            except Exception as e:
                print(e)
            # Else there was a timeout, so reset the device and retry.
            self.connect()
            # Increase count and fail after maximum number of retries.
            count += 1
            if count >= MAX_I2C_RETRIES:
               raise RuntimeError('Exceeded maximum number or retries attempting I2C communication!')

  def get_key_map(self,scancode):
       sv = 1
       for i in range(12):
        if scancode & sv:
         return i
         break
        sv = sv<<1
       return 0

# This main function is for testing the driver.
if __name__ == "__main__":
  m = MPR121(0x5a,1)
  m.connect()
  while 1:
    time.sleep(0.5)
    val = m.readTouch()
    if val != 0:
      print("Touch register=" + str(val))
