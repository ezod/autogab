"""\
OBD-II UART connection context manager and command interface.

@author: Aaron Mavrinac
@contact: mavrinac@gmail.com
@license: GPL-3
"""

import serial


class OBDConnectionContext(object):
    "OBD-II UART connection context manager and command interface."
    def __init__(self, device='/dev/ttyUSB0'):
        self.ser = serial.Serial(port=device, baudrate=9600, 
                                 bytesize=8, parity='N', stopbits=1,
                                 xonxoff=0, rtscts=0, timeout=5)

    def __enter__(self):
        # reset UART
        self.command('ATZ')
        # turn off echo
        if not 'OK' in self.command('ATE0'):
            raise Exception('echo off failed')
        # set protocol automatically
        if not 'OK' in self.command('ATSP0'):
            raise Exception('auto protocol failed')
        # get available PIDs
        pids = self.command('0100')
        # TODO: decode PIDs and store availability
        return self

    def __exit__(self, rtype, value, traceback):
        self.ser.flushOutput()
        self.ser.flushInput()
        self.ser.close()

    def command(self, command):
        self.ser.write(command + '\r')
        self.ser.flush()
        result = ''
        while not result.endswith('\r\r>'):
            result += self.ser.read()
        return result[:-3].split('\r')
