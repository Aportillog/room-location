import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import os
import operator as op

from localizationpy import simulation as sm
from localizationpy import metrics as met
import plotter


def sum_list_of_lists(list_array):
    res = list()
    for lst in list_array:
        if len(res) < 1:
            res = lst
            continue
        res = list(map(op.add, lst, res))
    return res


fprints_path = os.path.abspath("data/simulation_5/resul_4antenas_huellas_cada05m")
fprints_sim = sm.Simulation(fprints_path)

mobiles_path = os.path.abspath("data/simulation_5/resul_4antenas_puntos_aleatorios")
mobiles_sim = sm.Simulation(mobiles_path)

# Plot configure
fig = plt.figure()
fig.suptitle('Power scatter')

legend_elements = [Line2D([0], [0], marker='o', color='w', label='Static pt',
                          mec='black', mfc='black', markersize=10, alpha=0.6),
                   Line2D([0], [0], marker='o', color='w', label='Random pt',
                          mec='blue', mfc='blue', markersize=10, alpha=0.6),
                   Line2D([0], [0], marker='o', color='w', label='Estimated pt',
                          mec='red', mfc='red', markersize=10)]
fig.legend(handles=legend_elements, loc="upper left")


fpowers = list()
fpowers.append([fv.power for fv in fprints_sim.get_field_value('1')])
fpowers.append([fv.power for fv in fprints_sim.get_field_value('2')])
fpowers.append([fv.power for fv in fprints_sim.get_field_value('3')])
fpowers.append([fv.power for fv in fprints_sim.get_field_value('4')])
mpowers = list()
mpowers.append([fv.power for fv in mobiles_sim.get_field_value('1')])
mpowers.append([fv.power for fv in mobiles_sim.get_field_value('2')])
mpowers.append([fv.power for fv in mobiles_sim.get_field_value('3')])
mpowers.append([fv.power for fv in mobiles_sim.get_field_value('4')])

estimation = met.get_raytracing_estimation(mobiles_sim, fprints_sim, ['1', '2', '3', '4'])

plotter.plot_estimation_powers('Aerial 1 + 2 + 3 + 4',
                               fig,
                               sum_list_of_lists(fpowers),
                               sum_list_of_lists(mpowers),
                               fprints_sim.points,
                               estimation)

plt.show()
