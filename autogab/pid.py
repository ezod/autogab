"""\
OBD-II PID manager.

@author: Aaron Mavrinac
@contact: mavrinac@gmail.com
@license: GPL-3
"""

import yaml
import pkg_resources as pr


class OBDParameterManager(object):
    def __init__(self):
        self.pids = {}
        self.load_pids(pr.resource_filename(__name__,
                                            'resources/standard_pids.yaml'))

    def load_pids(self, path):
        pids = yaml.load(open(path, 'r'))
        for pid in pids:
            pids[pid]['formula'] = eval(pids[pid]['formula'])
            self.pids[pid] = pids[pid]
