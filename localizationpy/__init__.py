version = "1.0"
license = "MIT"

import PySimpleGUI as sg
import logging, logging.handlers
import sys

import localizationpy.gui as lg

__MAIN_W = 360
__MAIN_H = 1080
__PLOT_W = 1120
__PLOT_H = 740
__INFO_W = 380
__INFO_H = 320
__RESULT_W = 640
__RESULT_H = 120


def __configure_logging():
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(1)
    ch.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(ch)


def run():
    sg.theme('SystemDefault')

    __configure_logging()

    lg.create_main_window(__MAIN_W, __MAIN_H)
    lg.create_plot_window(__PLOT_W, __PLOT_H)
    lg.create_info_window(__INFO_W, __INFO_H)
    lg.create_result_window(__RESULT_W, __RESULT_H)

    lg.main()

    lg.ExecutionManager().info_window.close()
    lg.ExecutionManager().result_window.close()
    lg.ExecutionManager().plot_window.close()
    lg.ExecutionManager().main_window.close()


if __name__ == '__main__':
    run()
