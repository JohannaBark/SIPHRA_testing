from unittest import case

from .d2a_lib import *
from .regs_bit_structure import *
from collections import namedtuple

CH_ADDRS = []
SIPHRA_RETURN_SIZE = 15 # bytes. Returned by SIPHRA when D2a.readSIPHRA is called
# TODO: Check the size of the packet returned by D2a.readSIPHRA
REG_SIZE = 4 # bytes. Size of the bytearray passed to D2a.writeSIPHRA

# Register map classes
RegField = namedtuple('RegField', ['name', 'size'])

class SIPHRARegister:
    def __init__(self, addr, structure):
        self.addr = addr
        self.structure = structure
        self.fields = self.structure.subcon.subcons # Includes padding
        self.field_names = [field.name for field in self.fields if field.name]
        self.size = sum([field.sizeof() for field in self.fields if field.name]) # Number of significant bits in the register

    def __getitem__(self, idx):
        '''Returns the name and bit-size of a given field. Index 0 is the padding.'''
        if idx >= (n_fields:=len(self.fields)) or idx < 0:
            raise IndexError(f"Index {idx} is out of range for register with {n_fields - 1} fields + padding")
        if idx == 0:
            return RegField(name='Padding', size=self.fields[0].sizeof())
        return RegField(name=self.fields[idx].name, size=self.fields[idx].sizeof())

    def __len__(self):
        '''Number of fields in this register (excluding padding).'''
        return len(self.fields) - 1

    def __contains__(self, field_name):
        '''True if the register has a field named ``field_name``.'''
        return field_name in self.field_names

    def parse(self, value):
        return self.structure.parse(value)

    def set_param(self, param_name, value, current_content):
        reg_content = parse(current_content)
        reg_content[param_name] = value
        return self.structure.build(reg_content)

class SIPHRA:
    def __init__(self):
        self._d2a = D2a()
        self._regs = {}

        for i in range(1, 17):
            self._regs[f"ch{i}"] = SIPHRARegister(i, CHANNEL)

        self._regs["ch17"] = SIPHRARegister(0x10, SUM_CHANNEL)
        self._regs["ch_config"] = SIPHRARegister(0x11, CHANNEL_CONFIG)
        self._regs["ch_control"] = SIPHRARegister(0x12, CHANNEL_CONTROL)
        self._regs["adc_config"] = SIPHRARegister(0x13, ADC_CONFIG)
        self._regs["cal_dac"] = SIPHRARegister(0x14, CAL_DAC)
        self._regs["pd_modules"] = SIPHRARegister(0x15, PD_MODULES)
        self._regs["cal_ctrl"] = SIPHRARegister(0x16, CAL_CTRL)
        self._regs["readout_list"] = SIPHRARegister(0x17, READOUT_FIXED_LIST)
        self._regs["readout_mode"] = SIPHRARegister(0x18, READOUT_MODE)

    def _resolve_reg_id(self, reg_id: str | int) -> tuple[str, int]:
        """Resolves a register name or address to a (name, addr) tuple."""
        match reg_id:
            case str():
                if reg_id in self._regs:
                    return reg_id, self._regs[reg_id].addr
            case int():
                for name, reg in self._regs.items():
                    if reg.addr == reg_id:
                        return name, reg_id
            case _:
                raise TypeError(f"reg_id must be str or int, got {type(reg_id).__name__}")
        raise ValueError(f"{reg_id!r} is not a valid register id")

    def _find_reg_containing_param(self, parameter, ch: int=0):
        '''
        Returns the address of the register containing the given parameter.
        :param parameter: Name of the desired parameter.
        :param ch: If the parameter is in one of the 16+1 channel addresses, this argument is used for disambiguation. ``ch`` is a number between 1 and 16 if the parameter belongs to one of the ``ctrl_ch`` registers; it is 17 if the parameter belongs to the summing channel control register, and is defaulted to 0 if the parameter belongs to any other register.
        :return: The address of the register containing the given parameter.
        '''
        addr = None
        name = None
        if not 0 <= ch <= 17:
            raise ValueError(f"Channel {ch} is out of range. Use channels 1-16 and 17 for summing channel")
        if ch == 0: # Not a channel register
            for n, reg in self._regs.items():
                if parameter in reg:
                    name = n
                    addr = reg.addr
        else: # Channel register
            # Verify that the given field exists
            reg = self._regs[f"ch{ch}"]
            if parameter in reg:
                addr = reg.addr
                name = f"ch{ch}"
        if not addr:
            raise NameError(f"Parameter {parameter} does not exist or the register containing it is not implemented.")
        return name, addr

    def get_reg_value(self, reg_id, chip='A'):
        _, addr = self._resolve_reg_id(reg_id)
        return self._d2a.readSIPHRA(addr, chip)

    def read_register(self, reg_id, chip='A'):
        name, addr = self._resolve_reg_id(reg_id)
        reg_value = self._d2a.readSIPHRA(addr, chip)
        return self._regs[name].parse(reg_value)

    def write_register(self, reg_id, value, chip='A'):
        _, addr = self._resolve_reg_id(reg_id)
        try:
            self._d2a.writeSIPHRAwithCheck(addr, chip, value)
        except Exception as e:
            print(e)
            return -1
        return 0

    def read_param(self, parameter, ch=0, reg_id=None, chip='A'):
        '''``reg_id`` can be the register name or its address'''
        if reg_id:
            name, addr = self._resolve_reg_id(reg_id)
            if not parameter in _regs[name]:
                raise NameError(f"Parameter {parameter} does not exist in register {reg_id}.")
        else:
            name, addr = self._find_reg_containing_param(parameter, ch)

        return  self.read_register(name, chip=chip)[parameter]

    def write_param(self, parameter, value, ch=0, reg_id=None, chip='A'):
        if reg_id:
            name, addr = self._resolve_reg_id(reg_id)
            if not parameter in _regs[name]:
                raise NameError(f"Parameter {parameter} does not exist in register {reg_id}.")
        else:
            name, addr = self._find_reg_containing_param(parameter, ch)

        reg = self._regs[name]
        old_value = self.get_reg_value(reg_id, chip=chip)
        new_value = reg.set_param(parameter, value, old_value)
        self.write_register(name, new_value, chip=chip)




