# SPDX-FileCopyrightText: 2017 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_seesaw.seesaw`
====================================================

An I2C to whatever helper chip.

* Author(s): Dean Miller
* Adapted to RPIEasy by Alexander Nagy @ bitekmindenhol.blog.hu
"""

from lib.seesaw.adafruit_pixelbuf import PixelBuf
import time
import struct

_STATUS_BASE = 0x00
_STATUS_HW_ID = 0x01
_STATUS_VERSION = 0x02
_STATUS_OPTIONS = 0x03
_STATUS_TEMP = 0x04
_STATUS_SWRST = 0x7F

_SAMD09_HW_ID_CODE = 0x55
_ATTINY806_HW_ID_CODE = 0x84
_ATTINY807_HW_ID_CODE = 0x85
_ATTINY816_HW_ID_CODE = 0x86
_ATTINY817_HW_ID_CODE = 0x87
_ATTINY1616_HW_ID_CODE = 0x88
_ATTINY1617_HW_ID_CODE = 0x89

_ENCODER_BASE = 0x11
_ENCODER_STATUS = 0x00
_ENCODER_INTENSET = 0x10
_ENCODER_INTENCLR = 0x20
_ENCODER_POSITION = 0x30
_ENCODER_DELTA = 0x40

_INTERRUPT_BASE = 0x0B

_GPIO_BASE = 0x01
_GPIO_DIRSET_BULK = 0x02
_GPIO_DIRCLR_BULK = 0x03
_GPIO_BULK = 0x04
_GPIO_BULK_SET = 0x05
_GPIO_BULK_CLR = 0x06
_GPIO_INTENSET = 0x08
_GPIO_INTENCLR = 0x09
_GPIO_INTFLAG = 0x0A
_GPIO_PULLENSET = 0x0B
_GPIO_PULLENCLR = 0x0C

_NEOPIXEL_BASE = 0x0E
_NEOPIXEL_STATUS = 0x00
_NEOPIXEL_PIN = 0x01
_NEOPIXEL_SPEED = 0x02
_NEOPIXEL_BUF_LENGTH = 0x03
_NEOPIXEL_BUF = 0x04
_NEOPIXEL_SHOW = 0x05

# try lower values if IO errors
_OUTPUT_BUFFER_SIZE = 24

# Pixel color order constants
RGB = "RGB"
"""Red Green Blue"""
GRB = "GRB"
"""Green Red Blue"""
RGBW = "RGBW"
"""Red Green Blue White"""
GRBW = "GRBW"
"""Green Red Blue White"""

class Seesaw:

    INPUT = 0x00
    OUTPUT = 0x01
    INPUT_PULLUP = 0x02
    INPUT_PULLDOWN = 0x03

    def __init__(self, twowire_bus, reset=True):
        self.bus = twowire_bus
        self.encbase = False
        try:
         if self.bus.I2C_SLAVE > 0 and self.bus.i2c_bus_num>=0:
            pass
         else:
            raise RuntimeError(
                f"Not supported bus type!"
            )
        except:
            raise RuntimeError(
                f"Twowire bus required!"
            )
        if self.bus.i2cr is None:
           self.bus.connect()
        self.bus.setEndDelay(0.001)

        if reset:
            self.sw_reset()

        self.chip_id = self.read8(_STATUS_BASE, _STATUS_HW_ID)
        if self.chip_id not in (
            _ATTINY806_HW_ID_CODE,
            _ATTINY807_HW_ID_CODE,
            _ATTINY816_HW_ID_CODE,
            _ATTINY817_HW_ID_CODE,
            _ATTINY1616_HW_ID_CODE,
            _ATTINY1617_HW_ID_CODE,
            _SAMD09_HW_ID_CODE,
        ):
            raise RuntimeError(
                f"Seesaw hardware ID returned 0x{self.chip_id} is not "
                "correct! Please check your wiring."
            )
        opt = self.get_options()
        if (opt & (1 << _GPIO_BASE)) != 0:
            self.gpiobase = True
        else:
            self.gpiobase = False
        if (opt & (1 << _INTERRUPT_BASE)) != 0:
            self.intbase = True
        else:
            self.intbase = False
        if (opt & (1 << _NEOPIXEL_BASE)) != 0:
            self.neopixbase = True
        else:
            self.neopixbase = False
        if (opt & (1 << _ENCODER_BASE)) != 0:
            self.encbase = True
        else:
            self.encbase = False

    def sw_reset(self, post_reset_delay=0.5):
        """Trigger a software reset of the SeeSaw chip"""
        self.write8(_STATUS_BASE, _STATUS_SWRST, 0xFF)
        time.sleep(post_reset_delay)

    def get_options(self):
        """Retrieve the 'options' word from the SeeSaw board"""
        buf = bytearray(4)
        buf = self.read(_STATUS_BASE, _STATUS_OPTIONS, buf)
        ret = struct.unpack(">I", buf)[0]
        return ret

    def get_version(self):
        """Retrieve the 'version' word from the SeeSaw board"""
        buf = bytearray(4)
        buf = self.read(_STATUS_BASE, _STATUS_VERSION, buf)
        ret = struct.unpack(">I", buf)[0]
        return ret

    def encoder_position(self, encoder=0):
        """The current position of the encoder"""
        buf = bytearray(4)
        buf = self.read(_ENCODER_BASE, _ENCODER_POSITION + encoder, buf)
        return struct.unpack(">i", buf)[0]

    def set_encoder_position(self, pos, encoder=0):
        """Set the current position of the encoder"""
        cmd = struct.pack(">i", pos)
        self.write(_ENCODER_BASE, _ENCODER_POSITION + encoder, cmd)

    def encoder_delta(self, encoder=0):
        """The change in encoder position since it was last read"""
        buf = bytearray(4)
        buf = self.read(_ENCODER_BASE, _ENCODER_DELTA + encoder, buf)
        return struct.unpack(">i", buf)[0]

    def enable_encoder_interrupt(self, encoder=0):
        """Enable the interrupt to fire when the encoder changes position"""
        self.write8(_ENCODER_BASE, _ENCODER_INTENSET + encoder, 0x01)

    def disable_encoder_interrupt(self, encoder=0):
        """Disable the interrupt from firing when the encoder changes"""
        self.write8(_ENCODER_BASE, _ENCODER_INTENCLR + encoder, 0x01)
        
    def pin_mode(self, pin, mode):
        """Set the mode of a pin by number"""
        if pin >= 32:
            self.pin_mode_bulk_b(1 << (pin - 32), mode)
        else:
            self.pin_mode_bulk(1 << pin, mode)        

    def pin_mode_bulk(self, pins, mode):
        """Set the mode of all the pins on the 'A' port as a bitmask"""
        self._pin_mode_bulk_x(4, 0, pins, mode)

    def pin_mode_bulk_b(self, pins, mode):
        """Set the mode of all the pins on the 'B' port as a bitmask"""
        self._pin_mode_bulk_x(8, 4, pins, mode)

    def _pin_mode_bulk_x(self, capacity, offset, pins, mode):
        cmd = bytearray(capacity)
        cmd[offset:] = struct.pack(">I", pins)
        if mode == self.OUTPUT:
            self.write(_GPIO_BASE, _GPIO_DIRSET_BULK, cmd)
        elif mode == self.INPUT:
            self.write(_GPIO_BASE, _GPIO_DIRCLR_BULK, cmd)
            self.write(_GPIO_BASE, _GPIO_PULLENCLR, cmd)

        elif mode == self.INPUT_PULLUP:
            self.write(_GPIO_BASE, _GPIO_DIRCLR_BULK, cmd)
            self.write(_GPIO_BASE, _GPIO_PULLENSET, cmd)
            self.write(_GPIO_BASE, _GPIO_BULK_SET, cmd)

        elif mode == self.INPUT_PULLDOWN:
            self.write(_GPIO_BASE, _GPIO_DIRCLR_BULK, cmd)
            self.write(_GPIO_BASE, _GPIO_PULLENSET, cmd)
            self.write(_GPIO_BASE, _GPIO_BULK_CLR, cmd)

        else:
            raise ValueError("Invalid pin mode")        

    def digital_read(self, pin):
        """Get the value of an input pin by number"""
        if pin >= 32:
            return self.digital_read_bulk_b((1 << (pin - 32))) != 0
        return self.digital_read_bulk((1 << pin)) != 0

    def digital_read_bulk(self, pins, delay=0.008):
        """Get the values of all the pins on the 'A' port as a bitmask"""
        buf = bytearray(4)
        buf = self.read(_GPIO_BASE, _GPIO_BULK, buf, delay=delay)
        try:
            ret = struct.unpack(">I", buf)[0]
        except OverflowError:
            buf[0] = buf[0] & 0x3F
            ret = struct.unpack(">I", buf)[0]
        return ret & pins

    def digital_read_bulk_b(self, pins, delay=0.008):
        """Get the values of all the pins on the 'B' port as a bitmask"""
        buf = bytearray(8)
        buf = self.read(_GPIO_BASE, _GPIO_BULK, buf, delay=delay)
        ret = struct.unpack(">I", buf[4:])[0]
        return ret & pins

    def set_GPIO_interrupts(self, pins, enabled):
        """Enable or disable the GPIO interrupt"""
        cmd = struct.pack(">I", pins)
        if enabled:
            self.write(_GPIO_BASE, _GPIO_INTENSET, cmd)
        else:
            self.write(_GPIO_BASE, _GPIO_INTENCLR, cmd)

    def get_GPIO_interrupt_flag(self, delay=0.008):
        """Read and clear GPIO interrupts that have fired"""
        buf = bytearray(4)
        buf = self.read(_GPIO_BASE, _GPIO_INTFLAG, buf, delay=delay)
        return struct.unpack(">I", buf)[0]

    def write8(self, reg_base, reg, value):
        """Write an arbitrary I2C byte register on the device"""
        self.write(reg_base, reg, bytearray([value]))

    def read8(self, reg_base, reg):
        """Read an arbitrary I2C byte register on the device"""
        ret = bytearray(1)
        ret = self.read(reg_base, reg, ret)
        return bytes(ret)[0]

    def read(self, reg_base, reg, buf, delay=0.008):
        """Read an arbitrary I2C register range on the device"""
        full_buffer = bytearray([reg_base, reg])
        datasize = len(buf)
        if datasize < 1:
           datasize = 1
        transid = 0
        ct = 0
        while transid<=0 and ct<20:
         transid = int(self.bus.beginTransmission(reg_base,True))
         ct=ct+1
         if transid<=0:
            time.sleep(0.002)
        try:
         if int(transid) > 0:
          self.bus.write(full_buffer,transid)
          time.sleep(delay)
          buf = self.bus.read(datasize,transid)
          self.bus.endTransmission(transid)
        except Exception as e:
         print(e)
        #print(''.join('{:02x}'.format(x) for x in buf)) #debug
        return bytearray(buf)

    def write(self, reg_base, reg, buf=None):
        """Write an arbitrary I2C register range on the device"""
        full_buffer = bytearray([reg_base, reg])
        if buf is not None:
            full_buffer += buf
        transid = 0
        ct = 0
        while transid<=0 and ct<20:
         transid = int(self.bus.beginTransmission(reg_base,True))
         ct=ct+1
         if transid<=0:
            time.sleep(0.002)
        try:
         if int(transid) > 0:
          self.bus.write(full_buffer,transid)
          self.bus.endTransmission(transid)
        except Exception as e:
         print(e)

class Neopixel(PixelBuf):
    """Control NeoPixels connected to a seesaw

    :param ~adafruit_seesaw.seesaw.Seesaw seesaw: The device
    :param int pin: The pin number on the device
    :param int n: The number of pixels
    :param int bpp: The number of bytes per pixel
    :param float brightness: The brightness, from 0.0 to 1.0
    :param bool auto_write: Automatically update the pixels when changed
    :param tuple pixel_order: The layout of the pixels.
        Use one of the order constants such as RGBW."""

    def __init__(
        self,
        seesaw,
        pin,
        n,
        *,
        bpp=None,
        brightness=1.0,
        auto_write=True,
        pixel_order="GRB"
    ):
        self._seesaw = seesaw
        self._pin = pin
        if not pixel_order:
            pixel_order = GRB if bpp == 3 else GRBW
        elif isinstance(pixel_order, tuple):
            # convert legacy pixel order into PixelBuf pixel order
            order_list = ["RGBW"[order] for order in pixel_order]
            pixel_order = "".join(order_list)

        super().__init__(
            n,
            byteorder=pixel_order,
            brightness=brightness,
            auto_write=auto_write,
        )

        cmd = bytearray([pin])
        self._seesaw.write(_NEOPIXEL_BASE, _NEOPIXEL_PIN, cmd)
        cmd = struct.pack(">H", n * self.bpp)
        self._seesaw.write(_NEOPIXEL_BASE, _NEOPIXEL_BUF_LENGTH, cmd)
        self.output_buffer = bytearray(_OUTPUT_BUFFER_SIZE)

    def _transmit(self, buffer: bytearray) -> None:
        """Update the pixels even if auto_write is False"""

        step = _OUTPUT_BUFFER_SIZE - 2
        for i in range(0, len(buffer), step):
            self.output_buffer[0:2] = struct.pack(">H", i)
            self.output_buffer[2:] = buffer[i : i + step]
            self._seesaw.write(_NEOPIXEL_BASE, _NEOPIXEL_BUF, self.output_buffer)

        self._seesaw.write(_NEOPIXEL_BASE, _NEOPIXEL_SHOW)

    def deinit(self):
        pass

