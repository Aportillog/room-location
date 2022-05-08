# Make a position estimation for 100 random points, given their EM field values simulated (rand_points_sim)
# with new fasant program and the field values for a static point map (static_points_sim).
# The script will calculate the ED between a random point and all of the fingerprints, using the power for
# different aerials. The 4 smallest distances, will be taken to estimate the position for every random point,
# using the shape-center of those 4 fingerprints.

import os
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from localizationpy import simulation as sm
from localizationpy import metrics as met

output_path = 'output/simulation_5/position_estimation/raytracing/'

fprints_path = os.path.abspath("data/simulation_5/resul_4antenas_huellas_cada05m")
fprints_sim = sm.Simulation(fprints_path)

mobiles_path = os.path.abspath("data/simulation_5/resul_4antenas_puntos_aleatorios")
mobiles_sim = sm.Simulation(mobiles_path)

# Plot configure
fig = plt.figure(figsize=(19.20, 10.80))
fig.suptitle('100 Random points position estimations')

legend_elements = [Line2D([0], [0], marker='x', color='w', label='Static pt',
                          mec='black', mfc='black', markersize=10),
                   Line2D([0], [0], marker='o', color='w', label='Random pt',
                          mec='green', mfc='green', markersize=10),
                   Line2D([0], [0], marker='o', color='w', label='Estimated pt',
                          mec='red', mfc='red', markersize=10)]
fig.legend(handles=legend_elements, loc="upper left")


# Estimation 1: aerials 1
config = {
    "aerials": ['1'],
    "plot_figure": fig,
    "subplot_name": 'Estimation_1 (aerials: 1)',
    "output": output_path + '/1_aerials.csv'
}
met.get_estimation('raytracing', mobiles_sim, fprints_sim, **config)

# Estimation 1: aerials 1 & 2
config = {
    "aerials": ['1', '2'],
    "plot_figure": fig,
    "subplot_name": 'Estimation_2 (aerials: 2)',
    "output": output_path + '/2_aerials.csv'
}
met.get_estimation('raytracing', mobiles_sim, fprints_sim, **config)


# Estimation 2: aerials 1, 2 & 3
config = {
    "aerials": ['1', '2', '3'],
    "plot_figure": fig,
    "subplot_name": 'Estimation_3 (aerials: 3)',
    "output": output_path + '/3_aerials.csv'
}
met.get_estimation('raytracing', mobiles_sim, fprints_sim, **config)

# Estimation 3: aerials 1, 2, 3 & 4
config = {
    "aerials": ['1', '2', '3', '4'],
    "plot_figure": fig,
    "subplot_name": 'Estimation_4 (aerials: 4)',
    "output": output_path + '/4_aerials.csv'
}
met.get_estimation('raytracing', mobiles_sim, fprints_sim, **config)


fig.savefig(output_path + 'plot.png', bbox_inches='tight', dpi=150)

plt.show()
