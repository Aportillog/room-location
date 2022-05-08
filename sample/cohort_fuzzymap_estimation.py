import os
import matplotlib.pyplot as plt
import random as rd

from localizationpy import simulation as sm
from localizationpy import metrics as met
from localizationpy import file_manager as fm
import localizationpy.plotter as lplot

fprints_path = os.path.abspath("data/simulation_5/resul_4antenas_huellas_cada05m")
fprints_sim = sm.Simulation(fprints_path)

mobiles_path = os.path.abspath("data/simulation_5/resul_4antenas_puntos_aleatorios")
mobiles_sim = sm.Simulation(mobiles_path)

output_path = 'output/simulation_5/cohort_position_estimation/fuzzymap/'

# Plot configure
fig = plt.figure(figsize=(19.20, 10.80))
fig.suptitle('Cohort fuzzymap estimation')
plt.tight_layout()
lplot.add_estimation_legend(fig)

threshold = 0.1

# mpoint_idx = [rd.randint(0, len(mobiles_sim.points)) for i in range(1)]
# mpoint_idx = [90, 52, 41, 39, 19]
mpoint_idx = [19]

output_path += "threshold_{}/".format(str(threshold).replace('.', ''))
output_path += "{}/".format(mpoint_idx)

mobiles_sim.cohort_points(mpoint_idx)

configs = list()

# Estimation 1
configs.append({
    "aerials": ['1'],
    "threshold": threshold,
    "subplot_name": 'Aerials: 1, threshold:{}dB'.format(threshold),
    "output": output_path + '1_aerials.csv',
    "power_output": output_path + '1_aerials_powers.csv'
})

# Estimation 2
configs.append({
    "aerials": ['1', '2'],
    "threshold": threshold,
    "subplot_name": 'Aerials: 2, threshold:{}dB'.format(threshold),
    "output": output_path + '2_aerials.csv',
    "power_output": output_path + '2_aerials_powers.csv'
})

# Estimation 3
configs.append({
    "aerials": ['1', '2', '3'],
    "threshold": threshold,
    "subplot_name": 'Aerials: 3, threshold:{}dB'.format(threshold),
    "output": output_path + '3_aerials.csv',
    "power_output": output_path + '3_aerials_powers.csv'
})

# Estimation 4
configs.append({
    "aerials": ['1', '2', '3', '4'],
    "threshold": threshold,
    "subplot_name": 'Aerials: 4, threshold:{}dB'.format(threshold),
    "output": output_path + '4_aerials.csv',
    "power_output": output_path + '4_aerials_powers.csv'
})

for cfg in configs:
    estimations = met.get_fuzzymap_estimation(mobiles_sim, fprints_sim, aerials=cfg['aerials'], threshold=cfg['threshold'])
    fm.create_power_estimation_file(cfg['power_output'], estimations)

    sel_fpoints = list()
    for est in estimations:
        sel_fpoints.extend([fpoint for fpoint in est.fpoints])

    fm.create_estimation_file(cfg['output'], estimations)
    lplot.plot_position_estimation(cfg['subplot_name'], fig, sel_fpoints, estimations,
                                   escolor="blue", plot_ids=True, plot_polygons=True)


fig.savefig(output_path + 'plot.png', bbox_inches='tight', dpi=150)
# plt.show()
