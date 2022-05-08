import os

import localizationpy.fieldvalue as fv
import localizationpy.mapping as mp
import localizationpy.metrics as mt

import pickle


def _parse_file_puntos(file_path: str) -> list:
    """
    Parses "puntos.dat" file given its absolute path

    :param file_path: string containing the absolute path to the file
    :return: list of Point objects
    """
    point_list = []

    file = open(file_path, 'r')
    lines = file.readlines()
    file.close()
    num = int(lines.pop(0))

    for idx, line in enumerate(lines):
        coord_values = str.split(line)
        point = mp.Point(float(coord_values[0]), float(coord_values[1]), float(coord_values[2]), id=(idx + 1))
        point_list.append(point)

    assert(len(point_list) == num)

    return point_list


def _parse_file_aerial_measure(file_path: str) -> (float, list):
    """
    Parses "project_ord_tot_ant_X.cer" file given its absolute path

    :param file_path: string containing the absolute path to the file
    :return: tuple[float frequency value, list of FieldValue]
    """
    field_value_list = []

    file = open(file_path, 'r')
    lines = file.readlines()
    file.close()
    freq = float(lines.pop(0).split()[2])

    headers = lines.pop(0).split()

    for line in lines:
        line = line.split()
        field_value = fv.FieldValue(id=int(line[0]),
                                    ex=complex(float(line[1]), float(line[2])),
                                    ey=complex(float(line[3]), float(line[4])),
                                    ez=complex(float(line[5]), float(line[6])))
        field_value_list.append(field_value)

    return freq, field_value_list


def create_points_file(file_path: str, points: list):
    """
    Creates a file with a given list of points, using the specified path.
    The file will have "puntos.dat" same structure.

    :param file_path: string with the desired path, including file name
    :param points: list of Point objects to be stored in the file
    """
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'w') as f:
        f.write(str(len(points)) + '\n')
        for p in points:
            f.write(str(p.x) + " " + str(p.y) + " " + str(p.z) + '\n')


def create_power_estimation_file(file_path: str, estimations: list, check_threshold=False):
    """
    Creates a csv file to hold the power values (fingerprints and mobiles) of an estimation

    :param file_path: string with the desired path, including file name
    :param estimations: List containing Estimation objects
    :param check_threshold: bool, if True, power values included will be checked to be inside the threshold
    :return:
    """
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    header = "Mobile,Fingerprint,Aerial,Mobile Power,Fingerprint Power\n"
    with open(file_path, 'w') as f:
        f.write(header)
        for estimation in estimations:
            for einput in estimation.inputs:
                for measure in einput.power_measures:
                    if check_threshold and not measure.in_threshold:
                        continue
                    row = str(einput.mpoint.id)
                    row += ',' + str(einput.fpoint.id)
                    row += ',' + str(measure.aerial)
                    row += ',' + str(measure.mpower)
                    row += ',' + str(measure.fpower)
                    row += '\n'
                    f.write(row)


def create_fprints_in_radius_power_file(file_path: str, estimations: list, radius: float):
    """
    Creates a csv file to hold the power values of the fingerprints phisically close to every mobile of the estimation

    :param file_path: string with the desired path, including file name
    :param estimations: List containing Estimation objects
    :param radius: float value holding the radius to be applied to get those "close" fingerprints
    :return:
    """
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    header = "Mobile,Fingerprint,Aerial,Mobile Power,Fingerprint Power\n"
    with open(file_path, 'w') as f:
        f.write(header)
        for estimation in estimations:
            for einput in estimation.inputs:
                if mt.get_euclidean_distance(einput.fpoint, einput.mpoint) > radius:
                    continue
                for measure in einput.power_measures:
                    row = str(einput.mpoint)
                    row += ',' + str(einput.fpoint)
                    row += ',' + str(measure.aerial)
                    row += ',' + str(measure.mpower)
                    row += ',' + str(measure.fpower)
                    row += '\n'
                    f.write(row)


def create_estimation_file(file_path: str, estimations: list):
    """
    Creates a csv file to hold the position estimations of an online simulation

    :param file_path: string with the desired path, including file name
    :param estimations: List containing Estimation objects
    :return:
    """
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'w') as f:
        f.write("Original point,Estimated point,Number of Estimation Fingerprints,Estimation Fingerprints,Error\n")
        for entry in estimations:
            f.write(str(entry.mpoint) + ',' +
                    str(entry.epoint) + ',' +
                    str(len(entry.fpoints)) + ',' +
                    str(" | ".join(str(p) for p in entry.fpoints)) + ',' +
                    str(entry.error) + '\n')


def create_result_file(file_path: str, estimation_results: dict):
    """
    Creates a csv file to hold the statistical results of all estimations

    :param file_path: string with the desired path, including file name
    :param estimation_results: List containing Estimation objects
    :return:
    """
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'w') as f:
        f.write("Estimation, Medium Average Error, Standard deviation\n")
        for est_name, result in estimation_results.items():
            f.write(str(est_name) + ',' +
                    str("{:.2f}".format(result["mae"])) + ',' +
                    str("{:.2f}".format(result["stdev"])) + ',' +
                    str('\n'))


def save_session_file(file_path: str, session: dict):
    """
    Serializes (saves) a configuration session to a file

    :param file_path: string with the desired path, including file name
    :param session: dictionary holding the configuration
    :return:
    """
    with open(file_path, 'wb') as session_file:
        pickle.dump(session, session_file)


def load_session_file(file_path: str):
    """
    Deserializes (loads) a configuration session from a file

    :param file_path: string with the desired path, including file name
    :return:
    """
    with open(file_path, 'rb') as session_file:
        session = pickle.load(session_file)
        return session
