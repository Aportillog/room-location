import operator as op
import warnings
import math
import logging
import statistics as st

import localizationpy.mapping as mp

logger = logging.getLogger(__name__)


class Estimation(object):
    """Class holding the result of an estimation"""
    def __init__(self, mpoint, fpoints=None, inputs=None):
        self.mpoint = mpoint
        if len(fpoints) > 0:
            shape = mp.Shape3D(*fpoints)
            self.epoint = shape.center
            self.error = get_euclidean_distance(mpoint, shape.center)
            self.estimated = True
        else:
            self.epoint = None
            self.error = None
            self.estimated = False
        self.fpoints = fpoints
        self.inputs = inputs

    def __repr__(self):
        return (f'Original {self.mpoint}\r\n'
                f'Estimated: {self.epoint}\r\n'
                f'Fpoints: {[str(i) for i in self.fpoints]!r}\r\n'
                f'Error: {self.error!r}\r\n'
                f'Inputs: {"%s" % self.inputs}'
                )


class EstimationInput(object):
    """Class holding the input of an estimation"""
    def __init__(self, mpoint, fpoint, power_measures):
        self.mpoint = mpoint
        self.fpoint = fpoint
        self.power_measures = power_measures

    def __repr__(self):
        return '\n'.join('%s: %s' % t for t in zip(self.__dict__, self.__dict__.values()))

    def get_power_measure(self, aerial: str):
        """
        Get power measure object based on aerial
        :param aerial: str specifying the target aerial
        :return: PowerMeasure object for the specified aerial, None if no measure found
        """
        for pw_measure in self.power_measures:
            if pw_measure.aerial == aerial:
                return pw_measure
        return None


class PowerMeasure(object):
    """Class holding just a measure of power mobile-fingerprint for an aerial"""
    def __init__(self, aerial, mpower, fpower):
        self.aerial = aerial
        self.mpower = mpower
        self.fpower = fpower
        self.distance = (mpower - fpower) ** 2
        self.in_threshold = False

    def __repr__(self):
        return ', '.join('%s: %s' % t for t in zip(self.__dict__, self.__dict__.values()))


def get_euclidean_distance(a: mp.Point, b: mp.Point) -> float:
    """
    Calculates the euclidean distance between two given points

    :param a: Point object containing coordinates of a point
    :param b: Point object containing coordinates of b point
    :return: float value of the euclidean distance
    """
    return float('%.2f' % math.sqrt(math.fsum([math.pow(b.x - a.x, 2),
                                               math.pow(b.y - a.y, 2),
                                               math.pow(b.z - a.z, 2)])))


def get_min_ed_distance(a: mp.Point, point_map: list):
    """
    Gets the min distance between a given point and a list of points (map).
    All euclidean distances are calculated one by one between "a" and every other point in the list.

    :param a: Point object to be matched with the given list
    :param point_map: list of Point objects representing the fixed map to search for the min distance
    :return: list of Point objects fitting the min ed distance, float value with that min ed distance
    """
    ed_distances = []
    min_dist = None
    res_points = []
    for point in point_map:
        current_dist = get_euclidean_distance(a, point)
        ed_distances.append((current_dist, point))

        if min_dist is None or current_dist < min_dist:
            min_dist = current_dist

    for entry in ed_distances:
        if entry[0] == min_dist:
            res_points.append(entry[1])

    return res_points, min_dist


def get_complex_module(z: complex):
    """
    Calculates the module of a given complex number

    :param z: complex number to obtain the module from
    :return: float with module result
    """
    return float(math.sqrt(z.real**2 + z.imag**2))


def check_threshold(a, b, threshold):
    """
    Checks if a is in b +- threshold
    :param a: float number to check if in threshold
    :param b: float number used to apply the threshold
    :param threshold: float number to stablish the frame to check
    :return: True if a in threshold, False otherwise
    """
    return (a >= (b - threshold)) and (a <= (b + threshold))


def __calculate_power_ed(mobile_sim, fprint_sim, aerials, dbm):
    """
    Calculates the power euclidean distances given a pair of static-generated simulations, for specified list of aerials

    Base formula (Pa1mi-Pa1fj)^2+(Pa2mi-Pa2fj)^2+(Pa3mi-Pa3fj)^2 where:
        - Paxmi: power of electromagnetic field at "i" mobile point due tu aerial x
        - Paxfj: power of electromagnetic field at "j" fingerprint point due tu aerial x

    :param mobile_sim: Simulation object of the mobiles files
    :param fprint_sim: Simulation object of the fingerprints files
    :param aerials: list of Strings with target aerials
    :return:
    """
    if aerials is None:
        aerials = [entry for entry in mobile_sim.aerial_measures]
    # For every random point
    power_eds = dict()
    for mpoint in mobile_sim.points:
        power_eds.update({mpoint.id: []})
        power_eds[mpoint.id] = list(__estimation_input_generator(aerials, fprint_sim, mobile_sim, mpoint, dbm))
    return power_eds


def __power_measure_generator(mpoint, fingerprint, aerials, mobile_sim, fprint_sim, dbm):
    """
    Generator auxiliary function to create PowerMeasure objects.

    :param mpoint: Point object for the target mobile
    :param fingerprint: Point object for the target fingerprint
    :param aerials: list of strings containing aerials ids (ex: ['1', '2', '4'])
    :param mobile_sim: Simulation object containing the info of the points to estimate
    :param fprint_sim: Simulation object containing the info of the fingerprints
    :param dbm: bool specifying power units (True for using dBm)
    :return:
    """
    for aerial in aerials:
        mpower = mobile_sim.get_field_value(aerial, id=mpoint.id).power(dbm)
        if mpower == -200:
            continue
        fpower = fprint_sim.get_field_value(aerial, id=fingerprint.id).power(dbm)
        yield PowerMeasure(aerial, mpower, fpower)


def __estimation_input_generator(aerials, fprint_sim, mobile_sim, mpoint, dbm):
    """
    Generator auxiliary function to create EstimationInput objects.

    :param aerials: list of strings containing aerials ids (ex: ['1', '2', '4'])
    :param fprint_sim: Simulation object containing the info of the fingerprints
    :param mobile_sim: Simulation object containing the info of the points to estimate
    :param mpoint: Point object for the target mobile
    :param dbm: bool specifying power units (True for using dBm)
    :return:
    """
    for fingerprint in fprint_sim.points:
        est_input = EstimationInput(mpoint=mpoint, fpoint=fingerprint, power_measures=list())
        est_input.power_measures = list(__power_measure_generator(mpoint, fingerprint, aerials, mobile_sim, fprint_sim, dbm))
        est_input.ed = float('%.2f' % sum(pwm.distance for pwm in est_input.power_measures))
        yield est_input


def get_raytracing_estimation(mobile_sim, fprint_sim, aerials, fprints_used=4, dbm=True):
    """
    Calculates the position of a list of points, following a ray-tracing approach.

    :param mobile_sim: Simulation object containing the info of the points to estimate
    :param fprint_sim: Simulation object containing the info of the fingerprints
    :param aerials: list of strings containing aerials ids (ex: ['1', '2', '4'])
    :param fprints_used: int number of fingerprints to be used
    :param dbm: bool specifying power units (True for using dBm)
    :return:
    """

    power_eds = __calculate_power_ed(mobile_sim, fprint_sim, aerials, dbm)

    estimations = list()

    for mpoint in mobile_sim.points:
        if mpoint.id in power_eds:
            fpoints = [est.fpoint for est in sorted(power_eds[mpoint.id], key=lambda x: x.ed)[:fprints_used]]
            estimations.append(Estimation(mpoint, fpoints, inputs=power_eds[mpoint.id]))
        else:
            warnings.warn("No point estimated for mobile {}".format(mpoint))
            estimations.append(Estimation(mpoint))

    return estimations


def get_fuzzymap_estimation(mobile_sim, fprint_sim, aerials=None, threshold=0.5, dbm=True):
    """
    Calculates the position of a list of points, following a fuzzy-map approach.

    :param mobile_sim: Simulation object containing the info of the points to estimate
    :param fprint_sim: Simulation object containing the info of the fingerprints
    :param aerials: list of strings containing aerials ids (ex: ['1', '2', '4'])
    :param threshold: float number in which power values will be checked
    :param dbm: bool specifying power units (True for using dBm)
    :return:
    """
    estimations = list()

    for mpoint in mobile_sim.points:
        powers = dict()
        inputs = list(__estimation_input_generator(aerials, fprint_sim, mobile_sim, mpoint, dbm))
        for aerial in aerials:
            powers.update({aerial: []})
        for einput in inputs:
            for pw_measure in einput.power_measures:
                fpower = pw_measure.fpower
                mpower = pw_measure.mpower
                if check_threshold(fpower, mpower, threshold):
                    powers[pw_measure.aerial].append(einput.fpoint)
                    pw_measure.in_threshold = True
        if len(powers.values()) > 0:
            fpoints = get_list_intersection([lst for lst in powers.values()])
            estimations.append(Estimation(mpoint, fpoints, inputs=inputs))
        else:
            estimations.append(Estimation(mpoint, inputs=inputs))

    return estimations


def get_estimation(model, mobile_sim, fprint_sim, **kwargs):
    """
    Calculates an estimation.

    :param model: string specifying the approach taken ('raytracing' or 'fuzzymap')
    :param mobile_sim: Simulation object containing the info of the points to estimate
    :param fprint_sim: Simulation object containing the info of the fingerprints
    :key aerials: list of strings containing aerials ids (ex: ['1', '2', '4'])
    :key threshold: float number in which power values will be checked for fuzzymap model
    :key fprints_used: int number to specify the number of fingerprints to use when estimating the decision polygon
    :key points: list[int] holding the ids of the points to estimate
    :return:
    """
    allowed_models = {'raytracing', 'fuzzymap'}

    logger.debug('Running {} estimation: '.format(model) + ' ' + str(kwargs))

    assert model in allowed_models, "Specified model is not supported"

    aerials = kwargs.get("aerials")
    assert isinstance(aerials, list)
    if len(aerials) == 0:
        aerials = [a for a in mobile_sim.aerial_measures.keys()]

    fprints_used = kwargs.get("fprints_used", 4)
    threshold = kwargs.get('threshold', 0.5)

    points_ids = kwargs.get("points")
    assert isinstance(points_ids, list)
    if len(points_ids) != 0:
        mobile_sim.cohort_points(points_ids)

    estimation = []

    if model == 'raytracing':
        estimation = get_raytracing_estimation(mobile_sim, fprint_sim, aerials, fprints_used=fprints_used,
                                               dbm=kwargs.get('dbm'))
    elif model == 'fuzzymap':
        estimation = get_fuzzymap_estimation(mobile_sim, fprint_sim, aerials, threshold=threshold,
                                             dbm=kwargs.get('dbm'))

    if len(estimation) == 0:
        logger.warning("Simulation for specified values produced no estimation".format())

    mobile_sim.cohort_points(restore=True)

    return estimation


def get_mae(estimations: list):
    """
    Calculates the minimun average error (mae) of an estimation

    :param estimations: list containing Estimation objects
    :return: float with mae if estimation list is not empty, -1 otherwise
    """
    est = [e.error for e in estimations if e.estimated]
    if len(est) > 0:
        return st.mean(est)
    else:
        return -1


def get_stdev(estimations: list):
    """
    Calculates the standard deviation of an estimation

    :param estimations: list containing Estimation objects
    :return: float with stdev if estimation list is not empty, -1 otherwise
    """
    est = [e.error for e in estimations if e.estimated]
    if len(est) > 0:
        return st.stdev(est)
    else:
        return -1


def calculate_mae_rate(mae1: float, mae2: float):
    """
    Calculates the average error rate comparing two estimations mae

    :param mae1: Mean average error one
    :param mae2: Mean average error two
    :return: float with rate percentage
    """
    return (1 - mae1/mae2)


def get_list_intersection(d):
    """
    Calculates the intersection of a list of lists [[1,2],[3,4],[3,1]]

    :param d: list of list objects to intersect
    :return: list with intersected values
    """
    res = [lst for lst in d if len(lst) != 0]
    if len(res):
        return list(set(res[0]).intersection(*res))
    else:
        return []


def get_smallest_eds(distances, n):
    """DEPRECATED: Get the n smallest euclidean distances of a list"""
    return dict(sorted(distances.items(), key=op.itemgetter(1))[:n])
