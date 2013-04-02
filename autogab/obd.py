"""\
OBD-II UART connection context manager and command interface.

@author: Aaron Mavrinac
@contact: mavrinac@gmail.com
@license: GPL-3
"""

import yaml
import serial
import pkg_resources as pr


class OBDConnectionContext(object):
    "OBD-II UART connection context manager and command interface."
    def __init__(self, device='/dev/ttyUSB0'):
        self.pids = {}
        self.supported = []
        self.load_pids(pr.resource_filename(__name__,
                                            'resources/standard_pids.yaml'))
        self.ser = serial.Serial(port=device, baudrate=9600, 
                                 bytesize=8, parity='N', stopbits=1,
                                 xonxoff=0, rtscts=0, timeout=5)

    def __enter__(self):
        # reset UART
        self.command('ATZ')
        # turn off echo
        if not 'OK' in self.command('ATE0'):
            raise RuntimeError('echo off failed')
        # set protocol automatically
        if not 'OK' in self.command('ATSP0'):
            raise RuntimeError('auto protocol failed')
        # restrict responses to engine ECU (TODO: fix for non-CAN?)
        if not 'OK' in self.command('ATSH7E0'):
            raise RuntimeError('set headers failed')
        # get available PIDs
        self.read_supported_pids()
        return self

    def __exit__(self, rtype, value, traceback):
        self.ser.flushOutput()
        self.ser.flushInput()
        self.ser.close()

    def load_pids(self, path):
        pids = yaml.load(open(path, 'r'))
        for pid in pids:
            pids[pid]['formula'] = eval(pids[pid]['formula'])
            self.pids[pid] = pids[pid]

    def command(self, command):
        self.ser.write(command + '\r')
        self.ser.flush()
        response = ''
        while not response.endswith('\r\r>'):
            response += self.ser.read()
        return response[:-3].split('\r')

    def send_pid(self, mode, pid, lines=''):
        # send command and obtain response
        response = self.command(mode + pid + str(lines))
        if 'NO DATA' in response:
            raise RuntimeError('no response for PID %s' % pid)
        if response[0] == 'SEARCHING...':
            response.pop(0)
        # parse response into bytes
        raw_values = [s.strip() for s in response][0].split(' ')
        # convert bytes to integers
        values = [int(raw_value, 16) for raw_value in raw_values]
        # check integrity of response against original pid
        if not (values.pop(0) == int(mode, 16) + 64 and
                values.pop(0) == int(pid, 16)):
            raise RuntimeError('got bad response for PID %s' % pid)
        return values

    def read_supported_pids(self):
        self.supported = []
        for pid in ['00', '20', '40', '60', '80', 'A0', 'C0']:
            try:
                values = self.send_pid('01', pid)
            except RuntimeError:
                break
            binary = reduce(lambda a, b: a + b,
                            ['{0:08b}'.format(v) for v in values])
            self.supported += [bool(int(c)) for c in binary]

    @property
    def supported_values(self):
        return [pid for pid in self.pids \
                if self.supported[int(self.pids[pid]['pid'], 16)]]

    def request_value(self, pid):
        # check for support
        if not self.supported[int(self.pids[pid]['pid'], 16)]:
            raise ValueError('PID %s not supported' % pid)
        values = self.send_pid(self.pids[pid]['mode'],
                               self.pids[pid]['pid'],
                               lines=self.pids[pid]['lines'])
        # return interpreted response
        return self.pids[pid]['formula'](*values)
