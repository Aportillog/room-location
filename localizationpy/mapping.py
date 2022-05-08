import operator as op
import random as rd

import numpy as np


class Point(object):
    """
    Class containing coordinates information
    """
    def __init__(self, x: float, y: float, z: float, id=None):
        self.id = id
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        res = "X: {0} Y: {1}".format(self.x, self.y)
        if self.id is not None:
            res = 'Point {0} - '.format(self.id) + res
        return res

    def __eq__(self, other):
        return (self is other) or (self.x, self.y, self.z) == (other.x, other.y, other.z)

    def __hash__(self):
        return hash((self.id, self.x, self.y, self.z))


class VectorShape(object):
    """
    Class to define a 3D shape given its boundaries
    """
    def __init__(self, x_min: float, x_max: float, y_min: float, y_max: float, z_min: float, z_max: float):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.z_min = z_min
        self.z_max = z_max


class Shape3D(object):
    """
    This class defines a 2D shape given its points.

    Note: No ids are needed for the points used to instantiate an object of this class
    """
    def __init__(self, *args):
        for n, arg in enumerate(args):
            self.__dict__.update({"p{}".format(n): arg})

    @property
    def center(self) -> Point:
        """
        Calculates the center of the shape

        :return: Point object
        """
        x = round(sum(value.x for attr, value in self.__dict__.items()) / len(self.__dict__.items()), 2)
        y = round(sum(value.y for attr, value in self.__dict__.items()) / len(self.__dict__.items()), 2)
        z = round(sum(value.z for attr, value in self.__dict__.items()) / len(self.__dict__.items()), 2)

        return Point(x, y, z)


def get_random_points(number: int, vshape: VectorShape) -> list:
    """
    Generates an specific amount of random points within a vector shape

    :param number: int points to generate
    :param vshape: VectorShape object defining the 3D boundaries within points will be generated
    :return: list of random Point objects
    """
    coord_list = list()

    for i in range(0, number):
        x = float(f"{rd.uniform(vshape.x_min, vshape.x_max):.1f}")
        y = float(f"{rd.uniform(vshape.y_min, vshape.y_max):.1f}")
        z = float(f"{rd.uniform(vshape.z_min, vshape.z_max):.1f}")
        coord_list.append([x, y, z])

    coord_list.sort(key=op.itemgetter(0, 1, 2))

    point_list = []
    for i, coord in enumerate(coord_list):
        point_list.append(Point(coord[0], coord[1], coord[2], id=(i + 1)))

    return point_list


def get_3points_angle(points: list) -> float:
    """
    Get the angle between 3 Point objects (2D).
    First point will be used as base point.

    :param points: list of Point objects with 3 values
    :return: float with the result angle
    """

    assert 3 == len(points), "Just 3 points must be given to calculate the angle"

    def calculate_angle(point_a, point_b):
        """ Calculate angle between two points """
        ang_a = np.arctan2(*point_a[::-1])
        ang_b = np.arctan2(*point_b[::-1])
        return np.rad2deg((ang_a - ang_b) % (2 * np.pi))

    a = np.array([points[1].x, points[1].y])
    b = np.array([points[0].x, points[0].y])
    c = np.array([points[2].x, points[2].y])

    ba = a - b
    bc = c - b

    return calculate_angle(ba, bc)
