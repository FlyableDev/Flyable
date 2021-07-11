import math
import time


class CirclePoint:

    def __init__(self, x, y):
        self._x = x
        self._y = y


def main():
    results = []
    radius = 12.3
    points = 5000000
    angle_by_points = (3.1415 * 2) / points
    for e in range(0, points):
        x = math.cos(angle_by_points * e) * radius
        y = math.sin(angle_by_points * e) * radius
        results.append(CirclePoint(x, y))

    return 0
