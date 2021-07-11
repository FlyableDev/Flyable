from numba import jit
import numba
from numba import int32, float32
from numba.experimental import jitclass
import math
import time

spec = [
    ('_x', int32),
    ('_y', int32),
]


@jitclass(spec)
class CirclePoint:

    def __init__(self, x, y):
        self._x = x
        self._y = y


@jit
def main():
    results = []
    radius = 12.3
    points = 5000000
    angle_by_points = (3.1415 * 2) / points
    for e in range(0, points):
        x = math.cos(angle_by_points * e) * radius
        y = math.sin(angle_by_points * e) * radius
        results.append(CirclePoint(x, y))
