import os
import warnings

import localizationpy.aerial_measure as am
import localizationpy.file_manager as fm


class Simulation(object):
    """
    Class containing all the relative information of a simulation, including mapped points coordinates values and
    Electromagnetic field values for matching points
    """
    def __init__(self, simulation_path: str):
        self.simulation_path = simulation_path
        self.name = os.path.basename(simulation_path)
        aerial_paths = []
        self.__points = []
        for file in os.listdir(simulation_path):
            if file.endswith('.cer'):
                aerial_paths.append(os.path.join(simulation_path, file))
            elif file.endswith('.dat'):
                self.__points = fm._parse_file_puntos(os.path.join(simulation_path, file))
        self.__original_points = self.__points.copy()
        self.__build_aerial__measures(aerial_paths)

    def __repr__(self):
        return (f'Simulation: {self.name!r}\r\n'
                f'------------------------------\r\n'                
                f'\tPath: {self.simulation_path!r}\r\n')

    def __build_aerial__measures(self, path_list: list):
        self.aerial_measures = dict()
        for path in path_list:
            aerial_measure = am.AerialMeasure(path)
            self.aerial_measures.update({aerial_measure.id: aerial_measure})

    def get_field_value(self, aerial: str, id=None, point_coord=None):
        """
        Get the specific field value of an aerial in a determined point.
        id and/or point coordinates can be used as arguments optionally. If no argument is provided,
        it returns a list with all the values.

        :param aerial: string with the aerial id. Example: "1", "7" or "all"
        :param id: [optional] int with the specific id of the field value (it matches the id of the point)
        :param point_coord: [optional] array with X, Y and Z coordinates of a specific point. Example: [0.5, 1.5, 0.5]
        :return: FieldValue object matching the given point, None if no value was found. Returns a list of field values
                for the given aerial if id and point_coord are None.
        """

        if id is None and point_coord is None:
            return [fv for fv in self.aerial_measures[aerial].entries.values()]

        res = None

        if id is not None:
            if isinstance(id, list):
                res = list()
                for pid in id:
                    res.append(self.aerial_measures[aerial].entries[pid])
            elif id in self.aerial_measures[aerial].entries:
                res = self.aerial_measures[aerial].entries[id]
        elif point_coord is not None:
            if len(self.__points) > 0:
                point_id = None
                for pt in self.points:
                    if pt.x == point_coord[0] and pt.y == point_coord[1] and pt.z == point_coord[2]:
                        point_id = pt.id
                        break
                if point_id is None:
                    res = None
                else:
                    res = self.aerial_measures[aerial].entries[point_id]
            else:
                raise ValueError("List of points for simulation {} is empty".format(self.name))

        return res

    def get_point(self, id: int):
        """
        Function to get a specific point based on id

        :param id: point targeted id
        :return: Point object matching the parameters provided, None otherwise
        """
        res = None
        if len(self.__points) > 0:
            for pt in self.points:
                if pt.id == id:
                    res = pt
                    break
        else:
            raise ValueError("List of points for simulation {} is empty".format(self.name))

        return res

    def cohort_points(self, selected_points=None, restore=False):
        """
        Creates a subgroup of points from a given list of ids. If restore is specified,
        point list will be restored to original.

        :param selected_points: list of int with desired point ids.
        :param restore: bool value to restore point list to its original.
        :return:
        """
        if restore:
            self.__points = self.__original_points.copy()
        elif selected_points is not None:
            self.__points = [pt for pt in self.__original_points if pt.id in selected_points]
        else:
            warnings.warn("Cohort point ids not specified, subgroup not created".format(self.name))

    @property
    def points(self):
        """List containing all the points used in the simulation"""
        if len(self.__points) < 1:
            warnings.warn("Point list for simulation {} is empty".format(self.name))
        return self.__points
