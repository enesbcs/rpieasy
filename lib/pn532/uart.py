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
using UART (ttyS0) on the Raspberry Pi.
"""


import time
import serial
import RPi.GPIO as GPIO
from .pn532 import PN532, BusyError


# pylint: disable=bad-whitespace
DEV_SERIAL          = '/dev/ttyS0'
BAUD_RATE           = 115200


class PN532_UART(PN532):
    """Driver for the PN532 connected over UART. Pass in a hardware UART device.
    Optional IRQ pin (not used), reset pin and debugging output. 
    """
    def __init__(self, dev=DEV_SERIAL, baudrate=BAUD_RATE,
                irq=None, reset=None, debug=False):
        """Create an instance of the PN532 class using UART
        before running __init__, you should
        1.  disable serial login shell
        2.  enable serial port hardware
        using 'sudo raspi-config' --> 'Interfacing Options' --> 'Serial'
        """

        self.debug = debug
        self._gpio_init(irq=irq, reset=reset)
        self._uart = serial.Serial(dev, baudrate)
        if not self._uart.is_open:
            raise RuntimeError('cannot open {0}'.format(dev))
        super().__init__(debug=debug, reset=reset)

    def _gpio_init(self, reset=None,irq=None):
        self._irq = irq
        GPIO.setmode(GPIO.BCM)
        if reset:
            GPIO.setup(reset, GPIO.OUT)
            GPIO.output(reset, True)
        if irq:
            GPIO.setup(irq, GPIO.IN)

    def _reset(self, pin):
        """Perform a hardware reset toggle"""
        GPIO.output(pin, True)
        time.sleep(0.1)
        GPIO.output(pin, False)
        time.sleep(0.5)
        GPIO.output(pin, True)
        time.sleep(0.1)

    def _wakeup(self):
        """Send any special commands/data to wake up PN532"""
        self._uart.write(b'\x55\x55\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00') # wake up!
        self.SAM_configuration()

    def _wait_ready(self, timeout=0.001):
        """Wait for response frame, up to `timeout` seconds"""
        timestamp = time.monotonic()
        while (time.monotonic() - timestamp) < timeout:
            if self._uart.in_waiting:
                return True
            else:
                time.sleep(0.05)  # lets ask again soon!
        # Timed out!
        return False

    def _read_data(self, count):
        """Read a specified count of bytes from the PN532."""
        frame = self._uart.read(min(self._uart.in_waiting, count))
        if not frame:
            raise BusyError("No data read from PN532")
        if self.debug:
            print("Reading: ", [hex(i) for i in frame])
        else:
            time.sleep(0.005)
        return frame

    def _write_data(self, framebytes):
        """Write a specified count of bytes to the PN532"""
        self._uart.read(self._uart.in_waiting)    # clear FIFO queue of UART
        self._uart.write(framebytes)
