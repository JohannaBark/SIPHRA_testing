'''Script to configure UCD D2 SIPHRA ASICs and reconfigure during flight'''
import mmap
import logging
from construct import BitStruct, Nibble, BitsInteger, ByteSwapped, BitsSwapped
import time
import spidev

# define Python user-defined exceptions


class SPIError(Exception):
    'spidev1.0 not available'


class UIOError(Exception):
    'uio0 not available'


class SIPHRAWriteError(Exception):
    'SIPHRA write error'
    def __init__(self, chip, reg):
        self.chip = chip
        self.reg = reg






SIPHRA_REG_LENS = [26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 14, 24, 23, 6, 8, 18, 6, 19, 15, 6, 2, 2]

def compareUpTo(a, b, len):
    a_zeroed = int.from_bytes(a, byteorder='big') & (2**len - 1)
    b_zeroed = int.from_bytes(b, byteorder='big') & (2**len - 1)
    return a_zeroed == b_zeroed


CHIP2BIN = {'A':1, 'B':2, 'C':4, 'D':8, 'All':15}
ANTICHIP2BIN = {'A':0b1110, 'B':0b1101, 'C':0b1011, 'D':0b0111, 'All':0b0000}
HOLDRATES = {'Off':0, '1Hz':2, '1kHz':1}

CTRL_ADDR_0 = 4096
CTRL_0 = BitStruct(
        'hold'   / Nibble,
        'reset'  / Nibble,
        'cs'     / Nibble,
        'sysclk' / Nibble,
    )

DATA_ADDR_0 = 4104
DATA_0 = BitsSwapped( BitStruct(
        'error' / Nibble,
        'tempA' / BitsInteger(12),
        'tempB' / BitsInteger(12),
        'pad'   / Nibble,
    ))

DATA_ADDR_1 = 0
DATA_1 = BitsSwapped(BitStruct(
        'tempC'  / BitsInteger(12),
        'tempD'  / BitsInteger(12)

    ))


class D2a:
    '''
    Contains all functions required to interface with hardware devices through OS.
    '''
    def __init__(self, uio='/dev/uio0', spi='/dev/spi'):
        try:
            self.uio = uio
            with open(self.uio, "r+b", 0) as f:
                self.reg = mmap.mmap(f.fileno(), length = 4108)
            self.deassertCS()
        except Exception as exc:
            raise UIOError from exc

        try:
            self.spi = spidev.SpiDev()
            self.spi.open(1,0)
            self.spi.mode = 0
        except Exception as exc:
            raise SPIError from exc        

    def readMMap(self, addr, len=2):
        '''
        Read [len] bytes at [addr] from the memory mapped uio file.
        '''
        self.reg.seek(addr)
        print(self.reg.read(4))
        self.reg.seek(addr)
        return self.reg.read(4)

    def writeMMap(self, val, addr):
        '''
        Write however many bytes are supplied to the memory mapped
        uio file beginning at [addr].
        '''
        self.reg.seek(addr)
        self.reg.write(val)

    def readStruct(self, addr, struct):
        '''
        Read the appropriate number of bytes from the memmory mapped
        uio file beginning at [addr] and parse them through [struct]. 
        '''
        readBytes = self.readMMap(addr, len = struct.sizeof())        
        parsedStruct = struct.parse(readBytes)
        return parsedStruct

    def readParam(self, param, addr, struct):
        '''
        Like reasdStruct, but returns the value for a single parameter 
        contained within the struct.
        '''
        parsedStruct = self.readStruct(addr, struct)
        print(parsedStruct)
        return parsedStruct[param]

    def writeParam(self, param, addr, struct, value, clearbits=False):
        '''
        Writes a value to a parameter stored in a register.
        If the value given is one of the keys of CHIP2BIN (i.e. 'A', 'B', 'C', 'D', 'All'),
        then only the bit corresponding to that chip will be set, respecting the existing values
        of other chips' bits. Setting clearbits to True clears bits instead of setting them.
        '''        
        parsedStruct = self.readStruct(addr, struct)

        if value in CHIP2BIN:
            if clearbits:
                parsedStruct[param] &= ANTICHIP2BIN[value] # clear the bit corresponding to chip.
            else:
                parsedStruct[param] |= CHIP2BIN[value] # set the bit corresponding to chip.

        else:
            parsedStruct[param] = value

        bytesToWrite = struct.build(parsedStruct)
        self.writeMMap(bytesToWrite, addr)


    def keepReset(self, chip):
        '''
        Set a reset pin high.
        Useful to keep one particular SIPHRA disabled.
        '''
        self.writeParam('reset', CTRL_ADDR_0, CTRL_0, chip)

    def releaseReset(self, chip):
        '''
        Set a reset pin low.
        Used to activate a SIPHRA which had previously been disabled.
        '''
        self.writeParam('reset', CTRL_ADDR_0, CTRL_0, chip, clearbits = True)

    def reset(self, chip, toggle_time=0.01):
        '''
        Set a reset pin high and then low again after toggle_time.
        I.e. actually reset a SIPHRA.
        '''
        self.keepReset(chip)
        time.sleep(toggle_time)
        self.releaseReset(chip)


    def holdOff(self):
        '''
        Disable external triggering.
        '''
        self.writeParam('hold', CTRL_ADDR_0, CTRL_0, HOLDRATES['Off'])

    def hold1Hz(self):
        '''
        Enable external triggering at a rate of 1Hz.
        '''
        self.writeParam('hold', CTRL_ADDR_0, CTRL_0, HOLDRATES['1Hz'])

    def hold1kHz(self):
        '''
        Enable external triggering at a rate of 1kHz.
        '''
        self.writeParam('hold', CTRL_ADDR_0, CTRL_0, HOLDRATES['1kHz'])


    def sysclk(self, freq):
        '''
        Write a value to the sysclk register to control the sysclk frequency.

        TODO: Make a list of the values and corresponding frequencies.
        '''
        self.writeParam('sysclk', CTRL_ADDR_0, CTRL_0, freq)


    def assertCS(self, chip):
        '''
        CS is active low, so we want to set the bit corresponding to chip low
        and make sure all the others are high. Probably shouldn't call this with 'All',
        but I won't stop you!
        '''
        self.writeParam('cs', CTRL_ADDR_0, CTRL_0, ANTICHIP2BIN[chip])

    def deassertCS(self):
        '''
        CS is active low. There isn't really a use case to deassert one at a time.
        So we'll just deassert everything by setting them high.
        '''
        self.writeParam('cs', CTRL_ADDR_0, CTRL_0, 15)


    def error(self):
        '''
        Returns a single value error 0-15 corresponding to
        bitmask of error pins on SIPHRAs A, B, C, D.
        '''
        return self.readParam('error', DATA_ADDR_0, DATA_0)


    def temp(self):
        '''
        Returns a dictionary of the four SIPHRA temperatures.
        Temperature values are in raw ADC counts.
        '''
        tempAB = self.readStruct(DATA_ADDR_0, DATA_0)
        tempCD = self.readStruct(DATA_ADDR_1, DATA_1)
        temps = {
                'A': tempAB['tempA'],
                'B': tempAB['tempB'],
                'C': tempCD['tempC'],
                'D': tempCD['tempD'],
            }
        return temps


    def spiXfer(self, bytelist, chip):
        '''
        Version of spi.xfer2 that asserts CS using the D2a GPIOs. 
        '''
        self.assertCS(chip)
        readback = self.spi.xfer2(bytelist, 100_000)
        self.deassertCS()
        return readback

    def writeSIPHRA(self, val, addr, chip):
        '''
        Write a SIPHRA register.
        
          val:  4-byte bytearray with register contents.
          addr: register address.
          chip: 'A', 'B', 'C', 'D' or 'All'.
                'All' definitely not recommended.
        '''
        write_addr = addr << 1 | 1
        bytes_to_send = [write_addr] + list(val)
        self.spiXfer(bytes_to_send, chip)

    def readSIPHRA(self, addr, chip):
        '''
        Read a register from SIPHRA.
            
          addr: register address.
          chip: 'A', 'B', 'C', 'D' or 'All'.
                'All' definitely not recommended.
        
        Returns a four-byte bytearray with register contents.
        '''
        read_addr = addr << 1
        bytes_to_send = [read_addr] + [0] * 4
        return bytes(self.spiXfer(bytes_to_send, chip)[1:])

    def writeSIPHRAwithCheck(self, val, addr, chip):
        '''
        Keep writing a register to SIPHRA until 
        the value you get when reading it back out 
        matches the expected input.
        
        TODO: Make the function give up eventually
        or try something else like resetting SIPHRA.
        '''
        self.writeSIPHRA(val, addr, chip)
        remaining_tries = 3
        match = False
        while remaining_tries > 0 and match is False:
            readback = self.readSIPHRA(addr, chip)
            match = compareUpTo(val, readback, SIPHRA_REG_LENS[addr])
            if match is True:
                break
            else:
                remaining_tries -= 1
        if remaining_tries == 0 and match is False:
            raise SIPHRAWriteError(chip = chip,reg = addr)

    def writeSIPHRAfromFile(self, filename, chip):
        '''
        Write registers to a given SIPHRA chip.
        
        Assumes every four bytes in a binary file
        is a new register value. Will start at 
        register 0 and keep going while there are
        bytes in the file.

        If 'All' is selected for chip, every SIPHRA
        gets the same configuration.
        '''
        chips = ['A', 'B', 'C', 'D'] if chip == 'All' else [chip]
        
        vals = []
        with open(filename, 'r+b', 0) as f:
            while (val := f.read(4)):
                vals.append(val)

        for chip in chips:
            for addr, val in enumerate(vals):
               print("value:",val)
               print("address:",addr)
               print("chp:",chip)
               self.writeSIPHRAwithCheck(val, addr, chip)



