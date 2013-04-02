"""\
OBD polling tachometer display.

@author: Aaron Mavrinac
@contact: mavrinac@gmail.com
@license: GPL-3
"""

import argparse
from math import sin, cos, radians
import pygame as pg

from autogab.obd import OBDConnectionContext


def tachometer(self, device='/dev/ttyUSB0'):
    with OBDConnectionContext(device=device) as obd:
        while(True):
            yield obd.request_value('engine_rpm')


def main(device):
    pg.init()
    screen = pg.display.set_mode((640, 480))
    back = pg.image.load('tachometer_back.png')
    center = pg.image.load('tachometer_center.png')
    for rpm in tachometer(device):
        angle = radians((rpm / 1000.0) * 45.0 - 126.0)
        points = [(int(cos(angle) * x - sin(angle) * y) + 320,
                   int(sin(angle) * x + cos(angle) * y) + 240) \
                   for (x, y) in [(0, -160), (-10, 0), (10, 0)]]
        screen.fill((0, 0, 0))
        screen.blit(back, (80, 0, 480, 480))
        pg.draw.polygon(screen, (255, 0, 0), points)
        screen.blit(center, (288, 208, 64, 64))
        pg.display.flip()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', dest='device', type=str,
                        default='/dev/ttyUSB0')
    args = parser.parse_args()
    main(args.device)
