# https://www.dexterindustries.com
#
# Copyright (c) 2017 Dexter Industries
# Released under the MIT license (http://choosealicense.com/licenses/mit/).
# For more information see https://github.com/DexterInd/DI_Sensors/blob/master/LICENSE.md
#
# Python drivers for the VL53L0X laser distance sensor

import smbus
import time

# Constants
SYSRANGE_START                              = 0x00

SYSTEM_THRESH_HIGH                          = 0x0C
SYSTEM_THRESH_LOW                           = 0x0E

SYSTEM_SEQUENCE_CONFIG                      = 0x01
SYSTEM_RANGE_CONFIG                         = 0x09
SYSTEM_INTERMEASUREMENT_PERIOD              = 0x04

SYSTEM_INTERRUPT_CONFIG_GPIO                = 0x0A

GPIO_HV_MUX_ACTIVE_HIGH                     = 0x84

SYSTEM_INTERRUPT_CLEAR                      = 0x0B

RESULT_INTERRUPT_STATUS                     = 0x13
RESULT_RANGE_STATUS                         = 0x14

RESULT_CORE_AMBIENT_WINDOW_EVENTS_RTN       = 0xBC
RESULT_CORE_RANGING_TOTAL_EVENTS_RTN        = 0xC0
RESULT_CORE_AMBIENT_WINDOW_EVENTS_REF       = 0xD0
RESULT_CORE_RANGING_TOTAL_EVENTS_REF        = 0xD4
RESULT_PEAK_SIGNAL_RATE_REF                 = 0xB6

ALGO_PART_TO_PART_RANGE_OFFSET_MM           = 0x28

I2C_SLAVE_DEVICE_ADDRESS                    = 0x8A

MSRC_CONFIG_CONTROL                         = 0x60

PRE_RANGE_CONFIG_MIN_SNR                    = 0x27
PRE_RANGE_CONFIG_VALID_PHASE_LOW            = 0x56
PRE_RANGE_CONFIG_VALID_PHASE_HIGH           = 0x57
PRE_RANGE_MIN_COUNT_RATE_RTN_LIMIT          = 0x64

FINAL_RANGE_CONFIG_MIN_SNR                  = 0x67
FINAL_RANGE_CONFIG_VALID_PHASE_LOW          = 0x47
FINAL_RANGE_CONFIG_VALID_PHASE_HIGH         = 0x48
FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN_LIMIT = 0x44

PRE_RANGE_CONFIG_SIGMA_THRESH_HI            = 0x61
PRE_RANGE_CONFIG_SIGMA_THRESH_LO            = 0x62

PRE_RANGE_CONFIG_VCSEL_PERIOD               = 0x50
PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI          = 0x51
PRE_RANGE_CONFIG_TIMEOUT_MACROP_LO          = 0x52

SYSTEM_HISTOGRAM_BIN                        = 0x81
HISTOGRAM_CONFIG_INITIAL_PHASE_SELECT       = 0x33
HISTOGRAM_CONFIG_READOUT_CTRL               = 0x55

FINAL_RANGE_CONFIG_VCSEL_PERIOD             = 0x70
FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI        = 0x71
FINAL_RANGE_CONFIG_TIMEOUT_MACROP_LO        = 0x72
CROSSTALK_COMPENSATION_PEAK_RATE_MCPS       = 0x20

MSRC_CONFIG_TIMEOUT_MACROP                  = 0x46

SOFT_RESET_GO2_SOFT_RESET_N                 = 0xBF
IDENTIFICATION_MODEL_ID                     = 0xC0
IDENTIFICATION_REVISION_ID                  = 0xC2

OSC_CALIBRATE_VAL                           = 0xF8

GLOBAL_CONFIG_VCSEL_WIDTH                   = 0x32
GLOBAL_CONFIG_SPAD_ENABLES_REF_0            = 0xB0
GLOBAL_CONFIG_SPAD_ENABLES_REF_1            = 0xB1
GLOBAL_CONFIG_SPAD_ENABLES_REF_2            = 0xB2
GLOBAL_CONFIG_SPAD_ENABLES_REF_3            = 0xB3
GLOBAL_CONFIG_SPAD_ENABLES_REF_4            = 0xB4
GLOBAL_CONFIG_SPAD_ENABLES_REF_5            = 0xB5

GLOBAL_CONFIG_REF_EN_START_SELECT           = 0xB6
DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD         = 0x4E
DYNAMIC_SPAD_REF_EN_START_OFFSET            = 0x4F
POWER_MANAGEMENT_GO1_POWER_FORCE            = 0x80

VHV_CONFIG_PAD_SCL_SDA__EXTSUP_HV           = 0x89

ALGO_PHASECAL_LIM                           = 0x30
ALGO_PHASECAL_CONFIG_TIMEOUT                = 0x30

class VL53L0X(object):
    """Drivers for VL53L0X laser distance sensor"""

    # "global variables"
    io_timeout = 0
    did_timeout = False

    def __init__(self, busnum=1, i2c_address=0x29, timeout = 0.5):
        self.address = i2c_address
        self.initialized = False
        self.big_endian = True
        try:
         self.i2c_bus = smbus.SMBus(busnum)
         self.initialized = self.init()                   # initialize the sensor
         self.set_timeout(timeout) # set the timeout
        except:
         self.initialized = False

    def transfer(self, outArr, inBytes = 0):
        #Conduct an I2C transfer (write and/or read)
        for b in range(len(outArr)):
            outArr[b] &= 0xFF
        try:
                    if(len(outArr) >= 2 and inBytes == 0):
                        self.i2c_bus.write_i2c_block_data(self.address, outArr[0], outArr[1:])
                    elif(len(outArr) == 1 and inBytes == 0):
                        self.i2c_bus.write_byte(self.address, outArr[0])
                    elif(len(outArr) == 1 and inBytes >= 1):
                        return self.i2c_bus.read_i2c_block_data(self.address, outArr[0], inBytes)
                    elif(len(outArr) == 0 and inBytes == 1):
                        return self.i2c_bus.read_byte(self.address)
                    else:
                        raise IOError("I2C operation not supported")
        except:
         raise


    def write_reg_8(self, reg, val):
        """Write an 8-bit value to a register
        Keyword arguments:
        reg -- register to write to
        val -- byte to write"""
        val = int(val)
        self.transfer([reg, val])

    def read_8(self, reg = None, signed = False):
        """Read a 8-bit value
        Keyword arguments:
        reg (default None) -- Register to read from or None
        signed (default False) -- True (signed) or False (unsigned)
        Returns the value
        """
        # write the register to read from?
        if reg != None:
            outArr = [reg]
        else:
            outArr = []

        val = self.transfer(outArr, 1)

        value = val[0]

        # signed value?
        if signed:
            # negative value?
            if value & 0x80:
                value = value - 0x100

        return value

    def read_list(self, reg, len):
        """Read a list of bytes from a register
        Keyword arguments:
        reg -- Register to read from or None
        len -- Number of bytes to read
        Returns a list of the bytes read"""

        # write the register to read from?
        if reg != None:
            outArr = [reg]
        else:
            outArr = []
        return self.transfer(outArr, len)

    def write_reg_list(self, reg, list):
        """Write a list of bytes to a register
        Keyword arguments:
        reg -- regester to write to
        list -- list of bytes to write"""
        arr = [reg]
        arr.extend(list)
        self.transfer(arr)

    def write_reg_16(self, reg, val, big_endian = None):
        """Write a 16-bit value to a register
        Keyword arguments:
        reg -- register to write to
        val -- data to write
        big_endian (default None) -- True (big endian), False (little endian), or None (use the pre-defined endianness for the object)"""
        val = int(val)
        if big_endian == None:
            big_endian = self.big_endian
        if big_endian:
            self.transfer([reg, ((val >> 8) & 0xFF), (val & 0xFF)])
        else:
            self.transfer([reg, (val & 0xFF), ((val >> 8) & 0xFF)])

    def read_16(self, reg = None, signed = False, big_endian = None):
        """Read a 16-bit value
        Keyword arguments:
        reg (default None) -- Register to read from or None
        signed (default False) -- True (signed) or False (unsigned)
        big_endian (default None) -- True (big endian), False (little endian), or None (use the pre-defined endianness for the object)
        Returns the value
        """
        # write the register to read from?
        if reg != None:
            outArr = [reg]
        else:
            outArr = []

        val = self.transfer(outArr, 2)

        if big_endian == None:
            big_endian = self.big_endian

        # big endian?
        if big_endian:
            value = (val[0] << 8) | val[1]
        else:
            value = (val[1] << 8) | val[0]

        # signed value?
        if signed:
            # negative value?
            if value & 0x8000:
                value = value - 0x10000

        return value

    def init(self):
        self.write_reg_8(VHV_CONFIG_PAD_SCL_SDA__EXTSUP_HV, (self.read_8(VHV_CONFIG_PAD_SCL_SDA__EXTSUP_HV) | 0x01)) # set bit 0

        # "Set I2C standard mode"
        self.write_reg_8(0x88, 0x00)

        self.write_reg_8(0x80, 0x01)
        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(0x00, 0x00)
        self.stop_variable = self.read_8(0x91)
        self.write_reg_8(0x00, 0x01)
        self.write_reg_8(0xFF, 0x00)
        self.write_reg_8(0x80, 0x00)

        # disable SIGNAL_RATE_MSRC (bit 1) and SIGNAL_RATE_PRE_RANGE (bit 4) limit checks
        self.write_reg_8(MSRC_CONFIG_CONTROL, (self.read_8(MSRC_CONFIG_CONTROL) | 0x12))

        # set final range signal rate limit to 0.25 MCPS (million counts per second)
        self.set_signal_rate_limit(0.25)

        self.write_reg_8(SYSTEM_SEQUENCE_CONFIG, 0xFF)

        # VL53L0X_DataInit() end

        # VL53L0X_StaticInit() begin

        spad_count, spad_type_is_aperture, success = self.get_spad_info()
        if not success:
            return False

        # The SPAD map (RefGoodSpadMap) is read by VL53L0X_get_info_from_device() in
        # the API, but the same data seems to be more easily readable from
        # GLOBAL_CONFIG_SPAD_ENABLES_REF_0 through _6, so read it from there
        ref_spad_map = self.read_list(GLOBAL_CONFIG_SPAD_ENABLES_REF_0, 6)

        # -- VL53L0X_set_reference_spads() begin (assume NVM values are valid)

        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(DYNAMIC_SPAD_REF_EN_START_OFFSET, 0x00)
        self.write_reg_8(DYNAMIC_SPAD_NUM_REQUESTED_REF_SPAD, 0x2C)
        self.write_reg_8(0xFF, 0x00)
        self.write_reg_8(GLOBAL_CONFIG_REF_EN_START_SELECT, 0xB4)

        if spad_type_is_aperture:
            first_spad_to_enable = 12 # 12 is the first aperture spad
        else:
            first_spad_to_enable = 0

        spads_enabled = 0

        for i in range(48):
            if i < first_spad_to_enable or spads_enabled == spad_count:
                # This bit is lower than the first one that should be enabled, or
                # (reference_spad_count) bits have already been enabled, so zero this bit
                ref_spad_map[int(i / 8)] &= ~(1 << (i % 8))
            elif (ref_spad_map[int(i / 8)] >> (i % 8)) & 0x1:
                spads_enabled += 1

        self.write_reg_list(GLOBAL_CONFIG_SPAD_ENABLES_REF_0, ref_spad_map)

        # -- VL53L0X_set_reference_spads() end

        # -- VL53L0X_load_tuning_settings() begin
        # DefaultTuningSettings from vl53l0x_tuning.h

        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(0x00, 0x00)

        self.write_reg_8(0xFF, 0x00)
        self.write_reg_8(0x09, 0x00)
        self.write_reg_8(0x10, 0x00)
        self.write_reg_8(0x11, 0x00)

        self.write_reg_8(0x24, 0x01)
        self.write_reg_8(0x25, 0xFF)
        self.write_reg_8(0x75, 0x00)

        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(0x4E, 0x2C)
        self.write_reg_8(0x48, 0x00)
        self.write_reg_8(0x30, 0x20)

        self.write_reg_8(0xFF, 0x00)
        self.write_reg_8(0x30, 0x09)
        self.write_reg_8(0x54, 0x00)
        self.write_reg_8(0x31, 0x04)
        self.write_reg_8(0x32, 0x03)
        self.write_reg_8(0x40, 0x83)
        self.write_reg_8(0x46, 0x25)
        self.write_reg_8(0x60, 0x00)
        self.write_reg_8(0x27, 0x00)
        self.write_reg_8(0x50, 0x06)
        self.write_reg_8(0x51, 0x00)
        self.write_reg_8(0x52, 0x96)
        self.write_reg_8(0x56, 0x08)
        self.write_reg_8(0x57, 0x30)
        self.write_reg_8(0x61, 0x00)
        self.write_reg_8(0x62, 0x00)
        self.write_reg_8(0x64, 0x00)
        self.write_reg_8(0x65, 0x00)
        self.write_reg_8(0x66, 0xA0)

        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(0x22, 0x32)
        self.write_reg_8(0x47, 0x14)
        self.write_reg_8(0x49, 0xFF)
        self.write_reg_8(0x4A, 0x00)

        self.write_reg_8(0xFF, 0x00)
        self.write_reg_8(0x7A, 0x0A)
        self.write_reg_8(0x7B, 0x00)
        self.write_reg_8(0x78, 0x21)

        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(0x23, 0x34)
        self.write_reg_8(0x42, 0x00)
        self.write_reg_8(0x44, 0xFF)
        self.write_reg_8(0x45, 0x26)
        self.write_reg_8(0x46, 0x05)
        self.write_reg_8(0x40, 0x40)
        self.write_reg_8(0x0E, 0x06)
        self.write_reg_8(0x20, 0x1A)
        self.write_reg_8(0x43, 0x40)

        self.write_reg_8(0xFF, 0x00)
        self.write_reg_8(0x34, 0x03)
        self.write_reg_8(0x35, 0x44)

        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(0x31, 0x04)
        self.write_reg_8(0x4B, 0x09)
        self.write_reg_8(0x4C, 0x05)
        self.write_reg_8(0x4D, 0x04)

        self.write_reg_8(0xFF, 0x00)
        self.write_reg_8(0x44, 0x00)
        self.write_reg_8(0x45, 0x20)
        self.write_reg_8(0x47, 0x08)
        self.write_reg_8(0x48, 0x28)
        self.write_reg_8(0x67, 0x00)
        self.write_reg_8(0x70, 0x04)
        self.write_reg_8(0x71, 0x01)
        self.write_reg_8(0x72, 0xFE)
        self.write_reg_8(0x76, 0x00)
        self.write_reg_8(0x77, 0x00)

        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(0x0D, 0x01)

        self.write_reg_8(0xFF, 0x00)
        self.write_reg_8(0x80, 0x01)
        self.write_reg_8(0x01, 0xF8)

        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(0x8E, 0x01)
        self.write_reg_8(0x00, 0x01)
        self.write_reg_8(0xFF, 0x00)
        self.write_reg_8(0x80, 0x00)

        # -- VL53L0X_load_tuning_settings() end

        # "Set interrupt config to new sample ready"
        # -- VL53L0X_SetGpioConfig() begin

        self.write_reg_8(SYSTEM_INTERRUPT_CONFIG_GPIO, 0x04)
        self.write_reg_8(GPIO_HV_MUX_ACTIVE_HIGH, self.read_8(GPIO_HV_MUX_ACTIVE_HIGH) & ~0x10) # active low
        self.write_reg_8(SYSTEM_INTERRUPT_CLEAR, 0x01)

        # -- VL53L0X_SetGpioConfig() end

#        self.measurement_timing_budget_us = self.get_measurement_timing_budget()

        # "Disable MSRC and TCC by default"
        # MSRC = Minimum Signal Rate Check
        # TCC = Target CentreCheck
        # -- VL53L0X_SetSequenceStepEnable() begin

        self.write_reg_8(SYSTEM_SEQUENCE_CONFIG, 0xE8)

        # -- VL53L0X_SetSequenceStepEnable() end

        # "Recalculate timing budget"
#        self.set_measurement_timing_budget(self.measurement_timing_budget_us)

        # VL53L0X_StaticInit() end

        # VL53L0X_PerformRefCalibration() begin (VL53L0X_perform_ref_calibration())

        # -- VL53L0X_perform_vhv_calibration() begin

        self.write_reg_8(SYSTEM_SEQUENCE_CONFIG, 0x01)
        if not self.perform_single_ref_calibration(0x40):
            return False

        # -- VL53L0X_perform_vhv_calibration() end

        # -- VL53L0X_perform_phase_calibration() begin

        self.write_reg_8(SYSTEM_SEQUENCE_CONFIG, 0x02)
        if not self.perform_single_ref_calibration(0x00):
            return False

        # -- VL53L0X_perform_phase_calibration() end

        # "restore the previous Sequence Config"
        self.write_reg_8(SYSTEM_SEQUENCE_CONFIG, 0xE8)

        # VL53L0X_PerformRefCalibration() end

        return True

    # based on VL53L0X_perform_single_ref_calibration()
    def perform_single_ref_calibration(self, vhv_init_byte):
        self.write_reg_8(SYSRANGE_START, 0x01 | vhv_init_byte) # VL53L0X_REG_SYSRANGE_MODE_START_STOP

        self.start_timeout()
        while ((self.read_8(RESULT_INTERRUPT_STATUS) & 0x07) == 0):
            if self.check_timeout_expired():
                return False

        self.write_reg_8(SYSTEM_INTERRUPT_CLEAR, 0x01)

        self.write_reg_8(SYSRANGE_START, 0x00)

        return True

    def set_signal_rate_limit(self, limit_Mcps):
        if (limit_Mcps < 0 or limit_Mcps > 511.99):
            return False

        # Q9.7 fixed point format (9 integer bits, 7 fractional bits)
        self.write_reg_16(FINAL_RANGE_CONFIG_MIN_COUNT_RATE_RTN_LIMIT, int(limit_Mcps * (1 << 7)))
        return True

    # Get reference SPAD (single photon avalanche diode) count and type
    # based on VL53L0X_get_info_from_device(),
    # but only gets reference SPAD count and type
    def get_spad_info(self):
        self.write_reg_8(0x80, 0x01)
        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(0x00, 0x00)

        self.write_reg_8(0xFF, 0x06)
        self.write_reg_8(0x83, self.read_8(0x83) | 0x04)
        self.write_reg_8(0xFF, 0x07)
        self.write_reg_8(0x81, 0x01)

        self.write_reg_8(0x80, 0x01)

        self.write_reg_8(0x94, 0x6b)
        self.write_reg_8(0x83, 0x00)
        self.start_timeout()
        while (self.read_8(0x83) == 0x00):
            if (self.check_timeout_expired()):
                return 0, 0, False

        self.write_reg_8(0x83, 0x01)
        tmp = self.read_8(0x92)

        count = tmp & 0x7f
        type_is_aperture = (tmp >> 7) & 0x01

        self.write_reg_8(0x81, 0x00)
        self.write_reg_8(0xFF, 0x06)
        self.write_reg_8(0x83, self.read_8(0x83  & ~0x04))
        self.write_reg_8(0xFF, 0x01)
        self.write_reg_8(0x00, 0x01)

        self.write_reg_8(0xFF, 0x00)
        self.write_reg_8(0x80, 0x00)

        return count, type_is_aperture, True


    # Check if timeout is enabled (set to nonzero value) and has expired
    def check_timeout_expired(self):
        if(self.io_timeout > 0 and (time.time() - self.timeout_start) > self.io_timeout):
            return True
        return False

    # Record the current time to check an upcoming timeout against
    def start_timeout(self):
        self.timeout_start = time.time()

    def set_timeout(self, timeout):
        self.io_timeout = timeout

    # Returns a range reading in millimeters when continuous mode is active
    # (read_range_single_millimeters() also calls this function after starting a
    # single-shot range measurement)
    def read_range_continuous_millimeters(self):
        self.start_timeout()
        while ((self.read_8(RESULT_INTERRUPT_STATUS) & 0x07) == 0):
            if self.check_timeout_expired():
                self.did_timeout = True
                raise IOError("read_range_continuous_millimeters timeout")
        # assumptions: Linearity Corrective Gain is 1000 (default)
        # fractional ranging is not enabled
        range = self.read_16(RESULT_RANGE_STATUS + 10)
        self.write_reg_8(SYSTEM_INTERRUPT_CLEAR, 0x01)
        return range

    # Performs a single-shot range measurement and returns the reading in
    # millimeters
    # based on VL53L0X_PerformSingleRangingMeasurement()
    def read_range_single_millimeters(self):
        self.write_reg_8(0x80, 0x01);
        self.write_reg_8(0xFF, 0x01);
        self.write_reg_8(0x00, 0x00);
        self.write_reg_8(0x91, self.stop_variable);
        self.write_reg_8(0x00, 0x01);
        self.write_reg_8(0xFF, 0x00);
        self.write_reg_8(0x80, 0x00);

        self.write_reg_8(SYSRANGE_START, 0x01);

        # "Wait until start bit has been cleared"
        self.start_timeout()
        while (self.read_8(SYSRANGE_START) & 0x01):
            if self.check_timeout_expired():
                self.did_timeout = true
                raise IOError("read_range_single_millimeters timeout")
        return self.read_range_continuous_millimeters()

