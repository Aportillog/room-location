from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import matplotlib.pyplot as plt
import time
import warnings
import logging
import os
import errno
from pathlib import Path

import PySimpleGUI as sg


import localizationpy.file_manager as fm
import localizationpy.metrics as met
import localizationpy.plotter as lplot
import localizationpy.simulation as sm
from localizationpy import version
from localizationpy import license

matplotlib.use("TkAgg")
logging.getLogger("matplotlib").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


PLOT_WINDOW_NAME = 'Result plot'
INFO_WINDOW_NAME = 'Point information'
RESULT_WINDOW_NAME = 'Results'

# Error messages
ERROR_ESTIMATION_RUN = "Estimation not run"
ERROR_MOBILE_SIM_PATH = "Mobile sim not specified"
ERROR_MOBILE_SIM = "Mobile sim not parsed"
ERROR_STATIC_SIM_PATH = "Static sim not specified"
ERROR_STATIC_SIM = "Static sim not parsed"
ERROR_OUTPUT_PATH = "Output path not specified"
ERROR_NO_EST_CFG = "Estimation list is empty"
ERROR_NO_EST_RESULT = "No estimation result for current configuration"


class EstimationConfig(object):
    """
    Class to contain estimation configurations specified within the GUI
    """
    def __init__(self, name):
        self.name = name
        self.aerials = list()
        self.selected_aerials = list()
        self.points = list()
        self.selected_points = list()
        self.algorithm = 'raytracing'
        self.threshold = '0.5'
        self.plot_m_ids = False
        self.plot_f_ids = False
        self.plot_polygons = False


class ExecutionManager(object):
    """
    Class defined as singleton to hold all the "globals" needed during the program run lifetime.
    Note: it would make sense to split its attributes into different managers to be less confusing but for its size,
    is ok as it is right now.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExecutionManager, cls).__new__(cls)
            # graphic management
            cls.main_window = None
            cls.plot_window = None
            cls.info_window = None
            cls.result_window = None
            cls.figure = None
            cls.figure_canvas_agg = None
            cls.subplots = dict()
            cls.graphic_elements = dict()
            # execution management
            cls.mobile_sim = None
            cls.fprint_sim = None
            cls.est_configs = list()
            cls.estimations = dict()
            cls.info_wd_current_estimation = None
            cls.first_run = True
            # path management
            cls.mob_sim_path = ''
            cls.fprint_sim_path = ''
            cls.output_path = ''

        return cls._instance


# Auxiliary functions


def __parse_estimation_params(index):
    """
    Parses the parameters from an estimation configuration specified by "index" within the Exec manager list

    :param index: int number specifying the target index of the configuration within the Exec manager list
    :return: tuple with all the parsed parameters (aerials, algorithm, points, threshold)
    """
    est_config = ExecutionManager().est_configs[index]
    algorithm = est_config.algorithm
    points = [int(pt) for pt in est_config.points]
    threshold = float(est_config.threshold)
    return est_config.selected_aerials, algorithm, est_config, points, threshold


def __build_subplot_name(aerials, algorithm, estimation_name, mobiles_sim, threshold):
    """
    Builds the subplot name for the estimation using its parameters.
    
    :param aerials: list cointaining the aerials to use
    :param algorithm: str specifiying the algorithm (raytracing/fuzzymap)
    :param estimation_name: str with the estimation name itself
    :param mobiles_sim: Simulation object with mobiles information
    :param threshold: float value for the fuzzymap threshold
    :return: str with the result name
    """
    if len(aerials) > 0:
        aerials_num = len(aerials)
    else:
        aerials_num = len(mobiles_sim.aerial_measures)
    subplot_name = '{} (alg:{}, aerials: {}'.format(estimation_name, algorithm, aerials_num)
    if algorithm == 'fuzzymap':
        subplot_name += ', th: {}'.format(threshold)
    subplot_name += ')'
    return subplot_name


def _update_exec_manager(values):
    """
    Updates Execution Manager so simulations are parsed using the specified paths

    :param values: tuple holding the values of PySimplegui window read
    :return:
    """
    logger.debug("Updating exec manager")
    if values['-FPSIM-'] != ExecutionManager().fprint_sim_path:
        if not os.path.exists(values['-FPSIM-']):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), values['-FPSIM-'])
        if ExecutionManager().mob_sim_path != '':
            assert os.path.dirname(ExecutionManager().mob_sim_path) == os.path.dirname(values['-FPSIM-']), "Simulation folder unmatch"
        ExecutionManager().fprint_sim_path = values['-FPSIM-']
        ExecutionManager().fprint_sim = sm.Simulation(ExecutionManager().fprint_sim_path)
    if values['-MOBSIM-'] != ExecutionManager().mob_sim_path:
        if not os.path.exists(values['-MOBSIM-']):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), values['-MOBSIM-'])
        if ExecutionManager().fprint_sim_path != '':
            assert os.path.dirname(ExecutionManager().fprint_sim_path) == os.path.dirname(values['-MOBSIM-']), "Simulation folder unmatch"
        ExecutionManager().mob_sim_path = values['-MOBSIM-']
        ExecutionManager().mobile_sim = sm.Simulation(ExecutionManager().mob_sim_path)


def __get_mobile_id_from_plot_offset(est_name, indx):
    """
    Gets the id of a mobile given its index within the plotted point list (Matplotlib collection/artist)

    :param est_name: str with the name of the estimation
    :param indx: int holding the index of the point
    :return:
    """
    est_cfg = next((k for k in ExecutionManager().est_configs if k.name == est_name), None)
    return int(est_cfg.selected_points[indx])


def _get_info_wd_fpowers(index):
    """
    Gets the id of the selected fingerprint within the fpoint listbox given its index and fetch the estimation info
    associated with it as estimation inputs objects are unique pairs of mpoint-fpoint

    :param index:
    :return:
    """
    estimation = ExecutionManager().info_wd_current_estimation
    fpid = estimation.fpoints[index].id
    fpowers = list()
    einput = next((e for e in estimation.inputs if e.fpoint.id == fpid), None)
    if einput is None:
        logger.error("Estimation input not found for fpoint id {}".format(fpid))
    for measure in einput.power_measures:
        fpowers.append([str(measure.aerial), measure.fpower])
    return fpowers

# Graphics


def create_main_layout(width, height):
    """
    Creates the main layout.

    :return:
    """
    base_path = str(Path.home())

    box_w = width * 0.3
    box_h = height * 0.3
    txt_box_h = 1
    listbox_w = 30
    half_listbox_w = int(listbox_w / 2)
    inbox_size = (25, txt_box_h)
    med_inbox_size = (15, txt_box_h)
    small_inbox_size = (5, txt_box_h)
    checkbox_size = (15, txt_box_h)
    logbox_size = (40, txt_box_h)

    # ------ Menus ------ #
    menu_def = [
        ['&File', ['&Load Session', '&Save Session', 'E&xit']],
        ['&Help', '&About'],
    ]

    # Keys for menus entries match the keys of their listboxes so they can be identified when an event is triggered
    # Example: Antennas ListBox > right click > Select all --> event triggered: "Select all::-CFG_ARLIN-"
    estimation_click_menu = ['&Right', ['Edit name::-ESTIMT-', 'Cancel']]
    mobiles_click_menu = ['&Right', ['Select all::-CFG_PTLIN-', 'Select none::-CFG_PTLIN-', 'Cancel']]
    aerials_click_menu = ['&Right', ['Select all::-CFG_ARLIN-', 'Select none::-CFG_ARLIN-', 'Cancel']]

    # ------ Gui sections ------ #

    input_section = [
        [
            sg.Frame('Input simulation', [
                [sg.Text("Mobiles"),
                 sg.In(size=inbox_size, key="-MOBSIM-", readonly=True, enable_events=True),
                 sg.FolderBrowse(initial_folder=base_path)],
                [sg.Text("Static"),
                 sg.In(size=inbox_size, key="-FPSIM-", readonly=True, enable_events=True),
                 sg.FolderBrowse(initial_folder=base_path)],
            ]),
        ]
    ]

    estimation_section = [
        [
            sg.Frame('Estimations', [
                [sg.Column(justification='left', element_justification='center', layout=[
                    [sg.Listbox(values=(), enable_events=True, size=(listbox_w, txt_box_h * 5), key='-ESTIMT-',
                                right_click_menu=estimation_click_menu)],
                    [sg.Button(button_text='Add', key="-ADD-"), sg.Button(button_text='Delete', key="-DEL-")],
                    [sg.Frame('Configuration', layout=[
                        [sg.Text('Antennas'),
                         sg.Listbox(values=(), key='-CFG_ARLIN-', size=(half_listbox_w, txt_box_h * 6),
                                    select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                                    right_click_menu=aerials_click_menu,
                                    enable_events=True,
                                    disabled=True)
                         ],
                        [sg.Text('Algorithm'),
                         sg.InputCombo(('raytracing', 'fuzzymap'),
                                       disabled=True,
                                       enable_events=True,
                                       size=med_inbox_size,
                                       default_value='raytracing',
                                       key='-CFG_ALGIN-')],
                        [sg.Text('Threshold', key='-THTXT-'),
                         sg.InputText('0.5', size=small_inbox_size, key='-CFG_THVAL-', enable_events=True, disabled=True)]
                    ])],
                    [sg.Button(button_text='Run', key="-RUN-")]
                ])]
            ]),
        ]
    ]

    plotting_section = [
        [
            sg.Frame('Plotting options', [
                [sg.Column(justification='left', layout=[
                    [sg.Checkbox('Mobile ids', size=checkbox_size, enable_events=True,
                                 disabled=True, key='-CFG_PLMID-')],
                    [sg.Checkbox('Fprint ids', size=checkbox_size, enable_events=True,
                                 disabled=True, key='-CFG_PLFID-')],
                    [sg.Checkbox('Polygons', size=checkbox_size, enable_events=True,
                                 disabled=True, key='-CFG_PLPOL-')],
                ])],
                [sg.Column(justification='left', element_justification='c', layout=[
                    [sg.Text('Mobiles')],
                    [sg.Listbox(values=(), key='-CFG_PTLIN-', size=(listbox_w, txt_box_h * 5),
                                select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                                right_click_menu=mobiles_click_menu, enable_events=True, disabled=True)],
                    [sg.Button(button_text='Apply', key='-APPLY-')]
                ])]
            ])
        ]
    ]

    save_section = [
        [
            sg.Frame('Save options', [
                [sg.Column(justification='left', layout=[
                    [sg.Checkbox('Save plot file', size=checkbox_size, default=True, key='-PLTSV-')],
                    [sg.Checkbox('Save estimation file', size=checkbox_size, default=True, key='-SVESTFL-')],
                    [sg.Checkbox('Save power file', size=checkbox_size, key='-SVPOWFL-'),
                     sg.Checkbox('Just threshold', size=checkbox_size, key='-SVPOWFLTH-')],
                    [sg.Checkbox('Save fprints in radius power file', size=checkbox_size, key='-SVRADPOWFL-'),
                     sg.Text('Radius', key='-RADTXT-'), sg.InputText('1.0', size=checkbox_size, key='-RADVAL-', enable_events=True)]
                ])],
                [sg.Column(justification='center', layout=[
                    [sg.Button(button_text='Save', key='-SVFILES-')]
                ])],
            ]),
        ],
    ]

    right_footer = [
        [sg.Text("", key='-LOG-', size=logbox_size, justification='left')]
    ]

    # ----- Full layout -----
    layout = [
        [sg.Menu(menu_def)],
        [sg.Column(layout=input_section, justification='center', element_justification='center')],
        [sg.Column(layout=estimation_section, justification='center', element_justification='center')],
        [sg.Column(layout=plotting_section, justification='center', element_justification='center')],
        [sg.Column(layout=save_section, justification='center', element_justification='center')],
        [sg.Column(layout=right_footer, justification='left', element_justification='left', vertical_alignment='r')]
    ]

    return layout


def _draw_figure():
    """
    Draws an spcified figure in the plot window canvas

    :return: FigureCanvasTkAgg object
    """
    if ExecutionManager().first_run:
        canvas = ExecutionManager().plot_window["-CANVAS-"].TKCanvas
        fig_canvas = FigureCanvasTkAgg(ExecutionManager().figure, canvas)
        fig_canvas.mpl_connect("pick_event", _on_pick)
        fig_canvas.get_tk_widget().pack(side="top", fill="both", expand=1)
        ExecutionManager().figure_canvas_agg = fig_canvas

    ExecutionManager().figure_canvas_agg.draw()


def create_main_window(width, height):
    """
    Creates the aplication main window, given its resolution

    :param width: int value specifying the width of the window
    :param height: int value specifying the height of the window
    :return:
    """
    layout = create_main_layout(width, height)
    window = sg.Window("LocalizationPy", layout=layout, location=(0, 0), size=(width, height))
    ExecutionManager().main_window = window


def create_plot_window(width, height):
    """
    Creates the window for plotting the results of the estimations

    :return:
    """
    logger.debug('Creating plot window')
    layout = [[sg.Canvas(key="-CANVAS-")]]

    window = sg.Window(PLOT_WINDOW_NAME,
                       layout,
                       finalize=True,
                       location=(800, 0),
                       size=(width, height),
                       resizable=True,
                       disable_close=True,
                       modal=False)

    ExecutionManager().plot_window = window

    logger.debug('Plot window created')


def create_info_window(width, height):
    """
    Creates a window for showing further information, related to plotted points

    :return:
    """
    txtbox_w = 50
    txtbox_h = 1
    logger.debug('Creating info window')
    mpower_layout = [
        [sg.Text('Mobile power')],
        [sg.Table(values=[['None', 'None']], headings=['Antenna', 'Power'], key='INF-MPOW',
                  justification='center',
                  auto_size_columns=False,
                  col_widths=[8, 8],
                  max_col_width=8,
                  num_rows=6)
         ]
    ]
    fpower_layout = [
        [sg.Text('Fingerprint power')],
        [sg.Table(values=[['None', 'None']], headings=['Antenna', 'Power'], key='INF-FPOW',
                  justification='center',
                  auto_size_columns=False,
                  col_widths=[8, 8],
                  max_col_width=8,
                  num_rows=6)]
    ]
    layout = [
        [sg.Text('No point selected', key='INF-MPOINT', size=(txtbox_w, txtbox_h))],
        [sg.Text('Estimation:'), sg.Text('', key='INF-EPOINT', size=(txtbox_w, txtbox_h))],
        [sg.Text('Error: '), sg.Text('', key='INF-ERROR', size=(txtbox_w, txtbox_h))],
        [sg.Text('Estimation Fingerprints: '), sg.Text('', key='INF-NEFP', size=(txtbox_w, txtbox_h))],
        [sg.Listbox(values=(), enable_events=True, disabled=True, size=(txtbox_w, txtbox_h * 4), key='INF-EFP')],
        [sg.Column(layout=mpower_layout), sg.Column(layout=fpower_layout)]
    ]

    window = sg.Window(INFO_WINDOW_NAME,
                       layout,
                       finalize=True,
                       location=(400, 0),
                       size=(width, height),
                       disable_close=True,
                       resizable=False,
                       modal=False)

    ExecutionManager().info_window = window
    logger.debug('Info window created')


def create_result_window(width=860, height=120, extra_headers=None):
    """
    Creates a window for showing analysis results

    :return:
    """
    logger.debug('Creating result window')
    headers = ['Estimation', 'Mean average error', 'Standard deviation']
    values = [['None', 'None', 'None']]
    if extra_headers is not None:
        headers.extend(extra_headers)
        values.extend(['None'] * len(extra_headers))
    layout = [
        [sg.Column(justification='c', element_justification='center', expand_x=True, layout=[
            [sg.Table(values=values,
                      headings=headers,
                      key='RESULT-TABLE',
                      justification='center',
                      auto_size_columns=False,
                      col_widths=[25, 20, 20],
                      max_col_width=30,
                      num_rows=4
                      )]
        ])]
    ]

    window = sg.Window(RESULT_WINDOW_NAME,
                       layout,
                       finalize=True,
                       location=(400, 820),
                       size=(width, height),
                       disable_close=True,
                       resizable=False,
                       modal=False)

    ExecutionManager().result_window = window
    logger.debug('Result window created')


def __update_plot():
    """
    Perform an update of the current plot to apply the values changed within the main gui in "Plotting options" tab

    :return:
    """
    assert len(ExecutionManager().subplots) > 0, ERROR_ESTIMATION_RUN
    for est in ExecutionManager().est_configs:
        if len(est.selected_points) < 1:
            continue
        ax = ExecutionManager().subplots[est.name]
        tittle = ax.get_title()
        ax.cla()
        ax.set_title(tittle)
        est_result = ExecutionManager().estimations[est.name]["result"]
        new_est_result = [i for i in est_result if str(i.mpoint.id) in est.selected_points]
        collection, info_annotation = lplot.plot_position_estimation(ax, ExecutionManager().fprint_sim.points,
                                                                     new_est_result,
                                                                     plot_m_ids=est.plot_m_ids,
                                                                     plot_f_ids=est.plot_f_ids,
                                                                     plot_polygons=est.plot_polygons)
        ExecutionManager().graphic_elements.update({est.name: {"mpoint": collection, "info_annotation": info_annotation}})
    # Redraw
    ExecutionManager().figure_canvas_agg.draw()


# Actions functions


def _add_estimation_entry():
    """
    Adds another estimation entry to the list

    :return:
    """
    assert ExecutionManager().mobile_sim is not None, ERROR_MOBILE_SIM

    window = ExecutionManager().main_window
    values = window['-ESTIMT-'].GetListValues()
    name = sg.popup_get_text("Specify estimation name")
    if name is None or len(str(name)) == 0:
        name = 'Estimation_{}'.format(len(values) + 1)
    values = values + (name,)
    window['-ESTIMT-'].update(values=values, set_to_index=(len(values) - 1))

    est_cfg = EstimationConfig(name)
    est_cfg.points = [str(i.id) for i in ExecutionManager().mobile_sim.points]
    est_cfg.aerials = sorted(ExecutionManager().mobile_sim.aerial_measures.keys())

    ExecutionManager().est_configs.append(est_cfg)
    # Just if is the first value
    if len(values) == 1:
        window['-CFG_ARLIN-'].update(disabled=False)
        window['-CFG_PTLIN-'].update(disabled=False)
        window['-CFG_ALGIN-'].update(disabled=False)
        window['-CFG_THVAL-'].update(disabled=False)
        window['-CFG_PLMID-'].update(disabled=False)
        window['-CFG_PLFID-'].update(disabled=False)
        window['-CFG_PLPOL-'].update(disabled=False)

    _load_estimation_entry()


def _edit_estimation_entry_name():
    """
    Edits the name of the currently selected estimation entry within the list.

    :return:
    """
    window = ExecutionManager().main_window
    values = list(window['-ESTIMT-'].GetListValues())
    assert len(values) > 0, "Estimation list empty"

    target_idx = window['-ESTIMT-'].GetIndexes()[0]
    current_name = values[target_idx]

    # Get new name
    name = sg.popup_get_text("Specify estimation name", default_text=current_name)
    if name == current_name:
        return
    assert name not in values, "Specified name already in use"
    assert name is not None, "Name not specified"
    assert len(str(name)) != 0, "Name not specified"

    values[target_idx] = name
    window['-ESTIMT-'].update(values=values, set_to_index=target_idx)
    ExecutionManager().est_configs[target_idx].name = name


def _delete_estimation_entry():
    """
    Deletes the currently selected estimation entry from the list.

    :return:
    """
    logger.debug('Deleting estimation entry')
    window = ExecutionManager().main_window
    values = list(window['-ESTIMT-'].GetListValues())
    indexes = window['-ESTIMT-'].GetIndexes()
    if len(indexes) < 1:
        logger.error('Estimation list empty')
        return
    del(values[indexes[0]])
    del(ExecutionManager().est_configs[indexes[0]])
    window['-ESTIMT-'].update(values=tuple(values), set_to_index=(len(values) - 1))

    if len(values) == 0:
        window['-CFG_ARLIN-'].update(disabled=True)
        window['-CFG_PTLIN-'].update(disabled=True)
        window['-CFG_ALGIN-'].update(disabled=True)
        window['-CFG_THVAL-'].update(disabled=True)
        window['-CFG_PLMID-'].update(disabled=True)
        window['-CFG_PLFID-'].update(disabled=True)
        window['-CFG_PLPOL-'].update(disabled=True)
    else:
        _load_estimation_entry()


def _save_estimation_entry():
    """
    Saves the current estimation entry configuration to its matching EstimationConfig object of the Exec manager list

    :return:
    """
    window = ExecutionManager().main_window
    indexes = window['-ESTIMT-'].GetIndexes()
    if len(indexes) < 1:
        logger.error('Estimation list empty')
        return
    config = ExecutionManager().est_configs[indexes[0]]
    logger.debug('Saving estimation entry {}'.format(config.name))
    config.selected_aerials = window['-CFG_ARLIN-'].get()
    config.selected_points = window['-CFG_PTLIN-'].get()
    config.algorithm = window['-CFG_ALGIN-'].get()
    config.threshold = window['-CFG_THVAL-'].get()
    config.plot_m_ids = window['-CFG_PLMID-'].get()
    config.plot_f_ids = window['-CFG_PLFID-'].get()
    config.plot_polygons = window['-CFG_PLPOL-'].get()


def _load_estimation_entry():
    """
    Loads the configuration of an estimation to the GUI using its EstimationConfig object of the Exec manager list

    :return:
    """
    window = ExecutionManager().main_window
    indexes = window['-ESTIMT-'].GetIndexes()
    if len(indexes) < 1:
        logger.error('Estimation list empty')
        return
    config = ExecutionManager().est_configs[indexes[0]]
    logger.debug('Loading estimation entry {}'.format(config.name))
    window['-CFG_ARLIN-'].update(config.aerials, disabled=False)
    window['-CFG_ARLIN-'].SetValue(config.selected_aerials)
    window['-CFG_PTLIN-'].update(config.points, disabled=False)
    window['-CFG_PTLIN-'].SetValue(config.selected_points)
    window['-CFG_ALGIN-'].update(config.algorithm, disabled=False)
    disabled = config.algorithm != 'fuzzymap'
    window['-CFG_THVAL-'].update(config.threshold, disabled=disabled)
    window['-CFG_PLMID-'].update(config.plot_m_ids, disabled=False)
    window['-CFG_PLFID-'].update(config.plot_f_ids, disabled=False)
    window['-CFG_PLPOL-'].update(config.plot_polygons, disabled=False)


def _select_all_in_listbox(lb_key: str):
    """
    Selects all the entries in a specified listbox with multiple mode select

    :param lb_key: str with the key of the element to update
    :return:
    """
    logger.debug('Select all in listbox {}'.format(lb_key))
    lb_element = ExecutionManager().main_window[lb_key]
    if len(lb_element.GetListValues()) == 0:
        warnings.warn("Point list empty")
        return False
    lb_element.SetValue(lb_element.GetListValues())


def _select_none_in_listbox(lb_key: str):
    """
    Selects none of the entries in a specified listbox with multiple mode select

    :param lb_key: str with the key of the element to update
    :return:
    """
    logger.debug('Select none in listbox {}'.format(lb_key))
    lb_element = ExecutionManager().main_window[lb_key]
    if len(lb_element.GetListValues()) == 0:
        warnings.warn("Point list empty")
        return False
    lb_element.SetValue([])


def _save_session(values):
    """
    Saves the current session to a file (all GUI parameters configured so far)

    :param values: tuple holding the values of PySimplegui window read
    :return: True if successful, False if not file path was specified
    """
    base_path = str(Path.home()) + '/localizationpy'
    file_path = sg.popup_get_file('Save session as...',
                                  location=(50, 50),
                                  initial_folder=base_path,
                                  save_as=True,
                                  file_types=(("Locpy session", "*.session"),))
    if file_path is None:
        return False

    values.pop(0)
    values.pop('-ESTIMT-')
    config = {"main": values,
              "estimations": ExecutionManager().est_configs}
    fm.save_session_file(file_path, config)

    return True


def _load_session():
    """
    Loads a previously saved session (all GUI parameters)

    :return: True if successful, False if not file path was specified
    """
    base_path = str(Path.home()) + '/localizationpy'
    file_path = sg.popup_get_file('Load session',
                                  location=(50, 50),
                                  initial_folder=base_path,
                                  file_types=(("Locpy session", "*.session"),))
    if file_path is None:
        return False

    window = ExecutionManager().main_window
    session = fm.load_session_file(file_path)
    for entry in session['main']:
        if '-' not in entry:
            continue
        window[entry].update(session['main'][entry])
    if len(session['estimations']) > 0:
        ExecutionManager().est_configs = session['estimations']
        window['-ESTIMT-'].update(values=tuple([est.name for est in ExecutionManager().est_configs]), set_to_index=0)
        _load_estimation_entry()
    _update_exec_manager(session['main'])
    window.finalize()
    return True


def _save_files(values):
    """
    Saves all the specified files with estimations results.

    :param values: tuple holding the values of PySimplegui window read
    :return:
    """
    # output_path = ExecutionManager().output_path
    # assert len(output_path) > 0, ERROR_OUTPUT_PATH
    assert len(ExecutionManager().estimations) > 0, ERROR_ESTIMATION_RUN

    out_path = sg.popup_get_folder('Save', location=(50, 50), default_path=ExecutionManager().output_path,
                                   initial_folder=str(Path.home()))
    assert out_path is not None, ERROR_OUTPUT_PATH
    assert len(out_path) != 0, ERROR_OUTPUT_PATH
    ExecutionManager().output_path = out_path

    logger.debug('Saving files to {}'.format(out_path))

    fm.create_result_file(out_path + '/results.csv', ExecutionManager().estimations)

    for name, value in ExecutionManager().estimations.items():
        if values['-SVESTFL-']:
            fm.create_estimation_file(out_path + '/{}.csv'.format(name), value["result"])
        if values['-SVPOWFL-']:
            fm.create_power_estimation_file(out_path + '/{}_powers.csv'.format(name), value["result"],
                                            check_threshold=values['-SVPOWFLTH-'])
        if values['-SVRADPOWFL-']:
            fprint_radius = float(values['-RADVAL-'])
            fm.create_fprints_in_radius_power_file(out_path + '/{}_radius_{}_powers.csv'.format(name, fprint_radius),
                                                   value["result"], fprint_radius)

    if values['-PLTSV-']:
        ExecutionManager().figure.savefig(out_path + '/plot.png', bbox_inches='tight', dpi=200)

    logger.debug('Files saved')


def _run():
    """
    Runs the estimation.

    :return: float number holding the time it took to execute
    """
    logger.info('Running estimation...')

    fprints_sim = ExecutionManager().fprint_sim
    assert fprints_sim is not None, ERROR_STATIC_SIM
    mobile_sim = ExecutionManager().mobile_sim
    assert mobile_sim is not None, ERROR_MOBILE_SIM
    assert len(ExecutionManager().est_configs) > 0, ERROR_NO_EST_CFG

    # Plot configure
    if ExecutionManager().first_run:
        logger.debug('Configuring plot for the first time')
        fig = plt.figure(figsize=(19.20, 10.80), tight_layout=True)
        lplot.add_estimation_legend(fig)
        ExecutionManager().figure = fig
    else:
        logger.debug('Clearing Exec manager graphics objects')
        ExecutionManager().estimations.clear()
        ExecutionManager().graphic_elements.clear()
        ExecutionManager().subplots.clear()
        ExecutionManager().figure.clear()

    tic = time.perf_counter()  # Excution time counter start

    for i, est in enumerate(ExecutionManager().main_window['-ESTIMT-'].GetListValues()):

        aerials, algorithm, est_config, points, threshold = __parse_estimation_params(i)
        if len(aerials) < 1 or len(points) < 1:
            continue
        subplot_name = __build_subplot_name(aerials, algorithm, est, mobile_sim, threshold)

        config = {
            "aerials": aerials,
            "points": points,
            "threshold": threshold,
        }
        # Calculate all estimations but plot just the points specified within the plotting options
        estimation = met.get_estimation(algorithm, mobile_sim, fprints_sim, **config)
        est_plot = [e for e in estimation if str(e.mpoint.id) in ExecutionManager().est_configs[i].selected_points]

        ax = lplot.create_subplot(ExecutionManager().figure, subplot_name)
        collection, info_annotation = lplot.plot_position_estimation(ax, fprints_sim.points, est_plot,
                                                                     plot_m_ids=est_config.plot_m_ids,
                                                                     plot_f_ids=est_config.plot_f_ids,
                                                                     plot_polygons=est_config.plot_polygons)

        ExecutionManager().subplots.update({est: ax})
        ExecutionManager().graphic_elements.update({est: {"mpoint": collection, "info_annotation": info_annotation}})
        ExecutionManager().estimations.update({est: {
            "result": estimation,
            "mae": met.get_mae(estimation),
            "stdev": met.get_stdev(estimation)
        }
        })

    assert len(ExecutionManager().estimations) > 0, ERROR_NO_EST_RESULT

    __update_result_window(ExecutionManager().estimations)

    toc = time.perf_counter()  # Excution time counter stop

    _draw_figure()

    logger.info('Estimation ran in {:0.2f} secs'.format(toc-tic))

    ExecutionManager().first_run = False

    return toc - tic


def __update_result_window(estimations: dict):
    """
    Updates the info window for a specific point, given its estimation

    :param estimations: Estimation object containing all the info regarding one mobile
    :return:
    """
    wd = ExecutionManager().result_window
    results = list()

    for est, value in estimations.items():
        results.append([str(est),
                        str("{:.2f}".format(value["mae"])),
                        str("{:.2f}".format(value["stdev"]))
                        ])
    wd['RESULT-TABLE'].update(results)
    wd['RESULT-TABLE'].expand()
    wd.BringToFront()


def _update_info_window(estimation: met.Estimation):
    """
    Updates the info window for a specific point, given its estimation

    :param estimation: Estimation object containing all the info regarding one mobile
    :return:
    """
    wd = ExecutionManager().info_window
    ExecutionManager().info_wd_current_estimation = estimation

    wd['INF-MPOINT'].update(value=estimation.mpoint)
    est = "No point was estimated"
    if estimation.estimated:
        est = estimation.epoint
    wd['INF-EPOINT'].update(value=est)
    error = -1
    if estimation.error is not None:
        error = estimation.error
    wd['INF-ERROR'].update(value=error)
    wd['INF-NEFP'].update(value=len(estimation.fpoints))
    wd['INF-EFP'].update(values=estimation.fpoints, set_to_index=0, disabled=False)
    mpowers = list()
    for measure in estimation.inputs[0].power_measures:
        mpowers.append([str(measure.aerial), measure.mpower])
    wd['INF-MPOW'].update(mpowers)

    _update_fpowers_info_wd()

    wd.BringToFront()


def _update_fpowers_info_wd():
    """
    Updates the values shown within the info window fpowers listbox when selecting different fingerprints

    :return:
    """
    wd = ExecutionManager().info_window
    if len(wd['INF-EFP'].GetListValues()) > 0:
        fpowers = _get_info_wd_fpowers(wd['INF-EFP'].GetIndexes()[0])
    else:
        fpowers = [['None', 'None']]
    wd['INF-FPOW'].update(fpowers)


def _on_pick(event):
    """
    Callback function to be triggered when a mobile point of the plot window is picked (clicked).

    :param event: str holding the event read by PySimpleGUI window read
    :return:
    """
    artist = event.artist
    xmouse, ymouse = event.mouseevent.xdata, event.mouseevent.ydata
    ind = event.ind[0]
    est_name = next((key for key, val in ExecutionManager().subplots.items() if val == artist.axes), None)
    pid = __get_mobile_id_from_plot_offset(est_name, ind)
    point_estimation = next((v for v in ExecutionManager().estimations[est_name]["result"] if v.mpoint.id == pid), None)
    logger.debug("Clicked point {} of {}".format(point_estimation.mpoint, est_name))
    logger.debug('x, y of mouse: {:.2f},{:.2f}'.format(xmouse, ymouse))
    _update_info_window(point_estimation)


def _update_annot(est_name, indx):
    """
    Updates the annotation matching a point of the plot window for a specific estimation.

    :param est_name: str with the name of the estimation holding the point
    :param indx: int number with the index of said point in the selected points list
    :return:
    """
    pid = __get_mobile_id_from_plot_offset(est_name, indx)
    estimation = next((e for e in ExecutionManager().estimations[est_name]["result"] if e.mpoint.id == pid), None)
    if estimation is None:
        logger.error("Estimation for hovered point not found. Point id searched: {}".format(pid))
    pos = ExecutionManager().graphic_elements[est_name]["mpoint"].get_offsets()[indx]
    annot = ExecutionManager().graphic_elements[est_name]["info_annotation"]
    annot.xy = pos
    text = "{}".format(estimation.mpoint)
    text += "\nEstimation - {}".format(estimation.epoint)
    text += "\nError: {}".format(estimation.error)
    annot.set_text(text)


def _on_hover(event):
    """
    Callback function to be triggered when a point of the plot window is hovered (mouse above it).

    Warning: This functionality has been deactivated as it shows less info than "_on_pick" function and it causes
    strange behaviour of the GUI.
    If it must be activated again in the future, is enough to add this code to "_draw_figure" function:
        fig_canvas.mpl_connect("motion_notify_event", _on_hover)
    The same thing that is done with "_on_hover".

    :param event: str holding the event read by PySimpleGUI window read
    :return:
    """
    est_name = next((key for key, val in ExecutionManager().subplots.items() if val == event.inaxes), None)

    if est_name is None:
        return

    # Check if the event belongs to the collection holding the "mpoints" of the subplot
    # "ind" is a dictionary containing the index selected within the collection {'ind': array([1], dtype=int32)}
    # that means that if the points plotted are 14, 32 and 62, a index of "1" corresponds to point "32"
    cont, ind = ExecutionManager().graphic_elements[est_name]["mpoint"].contains(event)
    annot = ExecutionManager().graphic_elements[est_name]["info_annotation"]
    visible = annot.get_visible()
    if cont:
        _update_annot(est_name, ind["ind"][0])
        annot.set_visible(True)
        ExecutionManager().figure_canvas_agg.draw_idle()
    else:
        if visible:
            annot.set_visible(False)
            ExecutionManager().figure_canvas_agg.draw_idle()

# Execution functions


def __proces_cfg_event(event, values):
    """
    Grouping function to process Config estimation related events

    :param event: str holding the event read by PySimpleGUI window read
    :param values: tuple holding the values of PySimplegui window read
    :return:
    """
    window = ExecutionManager().main_window
    if 'Select all' in event:
        _select_all_in_listbox(event.split('::')[1])
    elif 'Select none' in event:
        _select_none_in_listbox(event.split('::')[1])
    elif '-CFG_ALGIN-' == event:
        disabled = window['-CFG_ALGIN-'].get() != 'fuzzymap'
        window['-CFG_THVAL-'].update(disabled=disabled)
    elif '-CFG_THVAL-' == event:
        if len(values['-CFG_THVAL-']) < 1:
            window['-CFG_THVAL-'].update(value='0.5')
        elif values['-CFG_THVAL-'][-1] not in '0123456789.':
            window['-CFG_THVAL-'].update(values['-CFG_THVAL-'][:-1])

    _save_estimation_entry()


def main():
    """
    Main loop event process

    :return:
    """
    logger.debug('Executing main program')
    main_window = ExecutionManager().main_window

    while True:
        event, values = main_window.read(timeout=100)
        if "Exit" == event or sg.WIN_CLOSED == event:
            break
        if ExecutionManager().info_window is not None:
            ev2, vals2 = ExecutionManager().info_window.read(timeout=100)
            if ev2 != sg.TIMEOUT_EVENT:
                logger.debug('Event callback: ' + ev2)

            if 'INF-EFP' == ev2:
                _update_fpowers_info_wd()

        if event != sg.TIMEOUT_EVENT:
            logger.debug('Event callback: ' + event)
            # logger.debug('GUI elements Values: ' + str(values))

        if "-RUN-" == event:
            main_window['-LOG-'].update(value='Running estimation...')
            main_window.finalize()
            try:
                runtime = _run()
                main_window['-LOG-'].update(value='Estimation ran in {:0.2f} secs'.format(runtime))
            except AssertionError as e:
                logger.error("%s", e)
                main_window['-LOG-'].update(value='Error: {}'.format(e))
        elif "-MOBSIM-" == event or "-FPSIM-" == event:
            try:
                _update_exec_manager(values)
            except FileNotFoundError as e:
                logger.error("%s", e)
                main_window['-LOG-'].update(value='Error: {}'.format(e))
            except AssertionError as a:
                logger.error("%s", a)
                main_window['-LOG-'].update(value='Error: {}'.format(a))
                main_window[event].update(value='')
        elif "-APPLY-" == event:
            try:
                __update_plot()
            except AssertionError as e:
                logger.error("%s", e)
                main_window['-LOG-'].update(value='Error: {}'.format(e))
        elif '-ADD-' == event:
            try:
                _add_estimation_entry()
            except AssertionError as e:
                logger.error("%s", e)
                main_window['-LOG-'].update(value='Error: {}'.format(e))
        elif 'Edit name' in event:
            try:
                _edit_estimation_entry_name()
            except AssertionError as e:
                logger.error("%s", e)
                main_window['-LOG-'].update(value='Error: {}'.format(e))
        elif '-DEL-' == event:
            _delete_estimation_entry()
        elif '-ESTIMT-' == event:
            _load_estimation_entry()
        elif 'CFG' in event:
            __proces_cfg_event(event, values)
        elif '-SVFILES-' == event:
            main_window['-LOG-'].update(value='Saving files...')
            try:
                _save_files(values)
                main_window['-LOG-'].update(value='Files saved!')
            except AssertionError as e:
                logger.error("%s", e)
                main_window['-LOG-'].update(value='Error: {}'.format(e))
        elif '-RADVAL-' == event:
            if len(values['-RADVAL-']) < 1:
                main_window['-RADVAL-'].update(value='1.0')
            elif values['-RADVAL-'][-1] not in '0123456789.':
                main_window['-RADVAL-'].update(values['-RADVAL-'][:-1])
        elif 'Load Session' == event:
            main_window['-LOG-'].update(value='Loading session...')
            if _load_session():
                main_window['-LOG-'].update(value='Loaded session file')
            else:
                main_window['-LOG-'].update(value='No session was loaded')
        elif 'Save Session' == event:
            main_window['-LOG-'].update(value='Saving session...')
            if _save_session(values):
                main_window['-LOG-'].update(value='Saved session file')
            else:
                main_window['-LOG-'].update(value='No session was saved')
        elif 'About' == event:
            sg.popup('Localizationpy', 'Version {}'.format(version),
                     'License: {}'.format(license),
                     title='About',
                     grab_anywhere=True)
