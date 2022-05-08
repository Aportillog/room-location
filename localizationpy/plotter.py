import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import localizationpy.mapping as mp


def __add_squared_subplot(figure):
    """
    Adds a subplot to the given figure, in a "squared" shape (first extend row, then column)

    :param figure: Figure matplotlib object
    :return: ax matplotlib object containing the "axe" or reference to new subplot added
    """
    n_axes = len(figure.axes)
    rows = 1
    cols = 1
    if n_axes > 0:
        geom = figure.axes[0].get_subplotspec().get_gridspec().get_geometry()
        rows = geom[0]
        cols = geom[1]
        if n_axes + 1 > rows * cols:
            if geom[0] < geom[1]:
                rows += 1
            else:
                cols += 1
            for i in range(n_axes):
                figure.axes[i].change_geometry(rows, cols, i + 1)
    ax = figure.add_subplot(rows, cols, n_axes + 1)
    return ax


def add_estimation_legend(figure):
    """
    Adds the legend to a figure

    :param figure: Figure matplotlib object
    :return:
    """
    legend_elements = [Line2D([0], [0], marker='x', color='w', label='Fingerprint',
                              mec='black', mfc='black', markersize=10),
                       Line2D([0], [0], marker='o', color='w', label='Mobile',
                              mec='green', mfc='green', markersize=10),
                       Line2D([0], [0], marker='o', color='w', label='Estimation',
                              mec='red', mfc='red', markersize=10)]
    figure.legend(handles=legend_elements, loc="upper left")


def __add_estimation_connectors(ax, estimations: list):
    """
    Add lines between every point and its estimated pair, given an estimation result, to the current plot.
    See also localizationpy.metrics.get_raytracing_estimation

    :param ax: Matplotlib axis object that will be updated
    :param estimations: list containing Estimation objects
    :return:
    """
    # Connect markers
    for entry in estimations:
        # Avoid drawing the connector if there is no estimation
        if not entry.estimated:
            continue
        v_x = list()
        v_y = list()
        v_x.append(entry.mpoint.x)
        v_x.append(entry.epoint.x)
        v_y.append(entry.mpoint.y)
        v_y.append(entry.epoint.y)
        ax.plot(v_x, v_y, color='purple', linewidth=0.2, alpha=0.5)


def __add_points_ids(ax, points):
    """
    Add id labels to every point of a given list to current plot.

    :param ax: Matplotlib axis object that will be updated
    :param points: List of Point which ids are going to be added
    :return:
    """
    for pt in points:
        label = "{}".format(pt.id)
        ax.annotate(label,  # text
                    (pt.x, pt.y),  # point to label
                    textcoords="offset points",  # how to position the text
                    xytext=(0, 3),  # distance from text to points (x,y)
                    ha='center',  # horizontal alignment can be left, right or center
                    size=7)


def __add_estimation_polygons(ax, estimations, **kwargs):
    """
    Add the estimation polygons for every mpoint to current plot.

    :param ax: Matplotlib axis object that will be updated
    :param estimations: list containing Estimation objects
    :key escolor: string containing the desired color for the shape
    :return:
    """
    for est in estimations:
        # Avoid drawing the polygons if there is no estimation
        if not est.estimated:
            continue
        points = est.fpoints.copy()

        # In order to draw a proper polygon, the center of the shape will be used
        # to get the angle of every other point with the first one chosen as reference
        # and then ordered clockwise (smallest angle to biggest)
        first_point = points[0]
        for pt in points:
            if pt.x < first_point.x:
                first_point = pt
        points_angles = [(first_point, 0)]
        for pt in points:
            if first_point == pt:
                continue
            angle = mp.get_3points_angle([est.epoint, first_point, pt])
            points_angles.append((pt, angle))

        points_angles.sort(key=lambda x: x[1])
        points = [[i[0].x, i[0].y] for i in points_angles]

        polygon = plt.Polygon(points, fill=None, edgecolor=kwargs.get("escolor"), capstyle='projecting')
        ax.add_patch(polygon)


def create_subplot(figure, name: str):
    """
    Auxiliary function to create a subplot for an estimation

    :param figure: Figure matplotlib object
    :param name: string with the desired name
    :return:
    """
    ax = __add_squared_subplot(figure)
    ax.set_title(name)
    ax.set_xlim(0, 21)
    ax.set_ylim(0, 8)
    ax.set_xlabel("x coord (meters)")
    ax.set_ylabel("y coord (meters)")

    return ax


def __add_estimation_points(ax, estimations, fpoints):
    """


    :param ax:  Matplotlib axis object that will be updated
    :param estimations: list containing Estimation objects
    :param fpoints: list containing Point objects with the fingerprints
    :return: Matplotlib collection holding the mobiles points
    """
    estimations_x = [est.epoint.x for est in estimations if est.estimated]
    estimations_y = [est.epoint.y for est in estimations if est.estimated]
    fpoints_x = [coord.x for coord in fpoints]
    fpoints_y = [coord.y for coord in fpoints]
    mpoints_x = [est.mpoint.x for est in estimations]
    mpoints_y = [est.mpoint.y for est in estimations]
    ax.scatter(fpoints_x, fpoints_y, s=10, c='black', marker='x')
    col = ax.scatter(mpoints_x, mpoints_y, s=10, c='green', marker='o')
    col.set_picker(True)
    ax.scatter(estimations_x, estimations_y, s=10, c='red', marker='o')

    return col


def plot_position_estimation(ax, fpoints, estimations, **kwargs):
    """
    Add a subplot to given figure containing the position estimations of mobile points.

    :param ax:  Matplotlib axis object that will be updated
    :param fpoints: list of Point objects containing the fingerprints of the simulation
    :param estimations: list containing Estimation objects
    :key escolor: string containing the desired color for the shape
    :key plot_m_ids: bool if True plots mobile ids
    :key plot_f_ids: bool if True plots fingerprints ids
    :key plot_polygons: bool if True plots decision polygons
    :return: tuple(mobile points Matplotlib collection, information annotation element)
    """
    mpoints_col = __add_estimation_points(ax, estimations, fpoints)

    __add_estimation_connectors(ax, estimations)

    if kwargs.get("plot_m_ids", False):
        __add_points_ids(ax, [x.mpoint for x in estimations])
    if kwargs.get("plot_f_ids", False):
        for est in estimations:
            __add_points_ids(ax, est.fpoints)
    if kwargs.get("plot_polygons", False):
        __add_estimation_polygons(ax, estimations, escolor=kwargs.get("escolor"))

    annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points", color='white',
                        bbox=dict(boxstyle="round", fc="grey", alpha=1),
                        arrowprops=dict(arrowstyle="->"))
    annot.set_visible(False)

    return mpoints_col, annot


def plot_aerial_powers(name, fprints, mobiles, figure):
    """
    Add an aerial power plot to an existing figure.
    Plot scatter which points will vary on size depending on the power value for every point.

    :param name: Name of the plot (ex: Aerial 1)
    :param fprints: list of tuples (Point, Float) specifying fingerprint Point objects and their matching power
    :param mobiles: list of tuples (Point, Float) specifying mobile Point objects and their matchign power
    :param figure: matplotlib figure to add the plot
    :return:
    """

    ax = __add_squared_subplot(figure)
    ax.set_title(name)

    ax.set_xlim(0, 21)
    ax.set_ylim(0, 8)

    markersize = 30

    def rescale(x, pmax, pmin):
        y = (x[1] - (pmax + pmin) / 2) / (pmax - pmin)
        return [x[0], y * (markersize - 0) + (markersize + 0) / 2]

    fprints = [item for item in fprints if item[1] != -200]
    mobiles = [item for item in mobiles if item[1] != -200]

    fpowers = [pt[1] for pt in fprints]
    mpowers = [pt[1] for pt in mobiles]

    max_power = max(fpowers)
    min_power = min(fpowers)

    fprints = [rescale(item, max_power, min_power) for item in fprints]
    fpoints_x = [pt[0].x for pt in fprints]
    fpoints_y = [pt[0].y for pt in fprints]

    mobiles = [rescale(item, max_power, min_power) for item in mobiles]
    mpoints_x = [pt[0].x for pt in mobiles]
    mpoints_y = [pt[0].y for pt in mobiles]

    ax.scatter(fpoints_x, fpoints_y, s=[x[1] for x in fprints], c='black', marker='o', alpha=0.6)
    ax.scatter(mpoints_x, mpoints_y, s=[x[1] for x in mobiles], c='green', marker='o', alpha=0.6)

    ax.set_xlabel("x coord (meters)")
    ax.set_ylabel("y coord (meters)")


def plot_estimation_powers(name, figure, fpowers, mpowers, fpoints, estimations):
    """
    Add an estimation power plot to an existing figure.
    Plot scatter which points will vary on size depending on the power value for every point.
    Estimated points are also drawn in this plot.

    :param name: Name of the plot (ex: Aerial 1)
    :param fpowers: list of FieldValue.power for every fingerprint due to target aerial
    :param mpowers: list of FieldValue.power for every mobile due to target aerial
    :param fpoints: list of Point objects containing the fingerprints of the simulation
    :param estimations: list containing Estimation objects
    :param figure: matplotlib figure to add the plot
    """

    estimations_x = [est.epoint.x for est in estimations]
    estimations_y = [est.epoint.y for est in estimations]
    fpoints_x = [coord.x for coord in fpoints]
    fpoints_y = [coord.y for coord in fpoints]
    mpoints_x = [entry.mpoint.x for entry in estimations]
    mpoints_y = [entry.mpoint.y for entry in estimations]

    ax = __add_squared_subplot(figure)
    ax.set_title(name)

    ax.set_xlim(0, 21)
    ax.set_ylim(0, 8)

    max_power = max(max(fpowers), max(mpowers))
    sms = [50 * (x / max_power) for x in fpowers]
    ax.scatter(fpoints_x, fpoints_y, s=sms, c='black', marker='o', alpha=0.6)
    rms = [50 * (x / max_power) for x in mpowers]
    ax.scatter(mpoints_x, mpoints_y, s=rms, c='blue', marker='o', alpha=0.6)
    ax.scatter(estimations_x, estimations_y, s=10, c='red', marker='o')

    ax.set_xlabel("x coord (meters)")
    ax.set_ylabel("y coord (meters)")

    __add_estimation_connectors(estimations)
