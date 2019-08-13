# Waveshare PN532 NFC Hat control library.
# Author: Yehui from Waveshare
#
# The MIT License (MIT)
#
# Copyright (c) 2015-2018 Adafruit Industries
# Copyright (c) 2019 Waveshare
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
This module will let you communicate with a PN532 RFID/NFC chip
using I2C on the Raspberry Pi.
"""

import fcntl
import os
import time
import RPi.GPIO as GPIO
from .pn532 import PN532, BusyError

# pylint: disable=bad-whitespace
# PN532 address without R/W bit, i.e. (0x48 >> 1)
I2C_ADDRESS                    = 0x24

# ctypes defines for i2c, see <linux/i2c-dev.h>
I2C_SLAVE                      = 1795


class I2CDevice:
    """Implements I2C device on ioctl"""
    def __init__(self, channel, addr):
        self.addr = addr
        self.i2c = os.open('/dev/i2c-%d' % channel, os.O_RDWR)
        if self.i2c < 0:
            raise RuntimeError('i2c device does not exist')
        if fcntl.ioctl(self.i2c, I2C_SLAVE, addr) < 0:
            raise RuntimeError('i2c slave does not exist')

    def write(self, buf):
        """Wrapper method of os.write"""
        return os.write(self.i2c, buf)

    def read(self, count):
        """Wrapper method of os.read"""
        return os.read(self.i2c, count)


class PN532_I2C(PN532):
    """Driver for the PN532 connected over I2C."""
    def __init__(self, irq=None, reset=None, req=None, debug=False, i2c_c=1):
        """Create an instance of the PN532 class using I2C. Note that PN532
        uses clock stretching. Optional IRQ pin (not used),
        reset pin and debugging output.
        """
        self.debug = debug
        self._gpio_init(irq=irq, req=req, reset=reset)
        self._i2c = I2CDevice(i2c_c, I2C_ADDRESS)
        super().__init__(debug=debug, reset=reset)

    def _gpio_init(self, reset, irq=None, req=None):
        self._irq = irq
        self._req = req
        GPIO.setmode(GPIO.BCM)
        if reset:
            GPIO.setup(reset, GPIO.OUT)
            GPIO.output(reset, True)
        if irq:
            GPIO.setup(irq, GPIO.IN)
        if req:
            GPIO.setup(req, GPIO.OUT)
            GPIO.output(req, True)

    def _reset(self, pin):
       """Perform a hardware reset toggle"""
       if pin:
        GPIO.output(pin, True)
        time.sleep(0.1)
        GPIO.output(pin, False)
        time.sleep(0.5)
        GPIO.output(pin, True)
        time.sleep(0.1)

    def _wakeup(self): # pylint: disable=no-self-use
        """Send any special commands/data to wake up PN532"""
        if self._req:
            GPIO.output(self._req, True)
            time.sleep(0.1)
            GPIO.output(self._req, False)
            time.sleep(0.1)
            GPIO.output(self._req, True)
        time.sleep(0.5)

    def _wait_ready(self, timeout=10):
        """Poll PN532 if status byte is ready, up to `timeout` seconds"""
        time.sleep(0.01) # required after _wait_ready()
        status = bytearray(1)
        timestamp = time.monotonic()
        while (time.monotonic() - timestamp) < timeout:
            try:
                status[0] = self._i2c.read(1)[0]
            except OSError:
                self._wakeup()
                continue
            if status == b'\x01':
                return True  # No longer busy
            time.sleep(0.005)  # lets ask again soon!
        # Timed out!
        return False

    def _read_data(self, count):
        """Read a specified count of bytes from the PN532."""
        try:
            status = self._i2c.read(1)[0]
            if status != 0x01:             # not ready
                raise BusyError
            frame = bytes(self._i2c.read(count+1))
        except OSError as err:
            if self.debug:
                print(err)
            return

        if self.debug:
            print("Reading: ", [hex(i) for i in frame[1:]])
        else:
            time.sleep(0.1)
        return frame[1:]   # don't return the status byte

    def _write_data(self, framebytes):
        """Write a specified count of bytes to the PN532"""
        self._i2c.write(framebytes)
