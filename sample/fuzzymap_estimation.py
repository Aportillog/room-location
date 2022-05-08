import os
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from localizationpy import simulation as sm
from localizationpy import metrics as met

fprints_path = os.path.abspath("data/simulation_5/resul_4antenas_huellas_cada05m")
fprints_sim = sm.Simulation(fprints_path)

mobiles_path = os.path.abspath("data/simulation_5/resul_4antenas_puntos_aleatorios")
mobiles_sim = sm.Simulation(mobiles_path)

output_path = 'output/simulation_5/position_estimation/fuzzymap/'

threshold = 0.1
output_path += "threshold_{}/".format(str(threshold).replace('.', ''))

# Plot configure
fig = plt.figure(figsize=(19.20, 10.80))
fig.suptitle('100 Random points fuzzy map (threshold = {}dB) position estimations'.format(threshold))

legend_elements = [Line2D([0], [0], marker='x', color='w', label='Static pt',
                          mec='black', mfc='black', markersize=10),
                   Line2D([0], [0], marker='o', color='w', label='Random pt',
                          mec='green', mfc='green', markersize=10),
                   Line2D([0], [0], marker='o', color='w', label='Estimated pt',
                          mec='red', mfc='red', markersize=10)]
fig.legend(handles=legend_elements, loc="upper left")


configs = list()

# Estimation 1: aerials 1
configs.append({
    "aerials": ['1'],
    "plot_figure": fig,
    "subplot_name": 'Estimation_1 (aerials: 1)',
    "output": output_path + '/1_aerials.csv',
    "powout": output_path + '/1_aerials_power.csv',

})

# Estimation 1: aerials 1 & 2
configs.append({
    "aerials": ['1', '2'],
    "plot_figure": fig,
    "subplot_name": 'Estimation_2 (aerials: 2)',
    "output": output_path + '/2_aerials.csv',
    "powout": output_path + '/2_aerials_power.csv',
})

# Estimation 3: aerials 1, 2 & 3
configs.append({
    "aerials": ['1', '2', '3'],
    "plot_figure": fig,
    "subplot_name": 'Estimation_3 (aerials: 3)',
    "output": output_path + '/3_aerials.csv',
    "powout": output_path + '/3_aerials_power.csv',
})

# Estimation 4: aerials 1, 2, 3 & 4
configs.append({
    "aerials": ['1', '2', '3', '4'],
    "plot_figure": fig,
    "subplot_name": 'Estimation_4 (aerials: 4)',
    "output": output_path + '/4_aerials.csv',
    "powout": output_path + '/4_aerials_power.csv',
})

for e in configs:
    met.get_estimation('fuzzymap', mobiles_sim, fprints_sim, **e, threshold=threshold)

fig.savefig(output_path + 'plot.png', bbox_inches='tight', dpi=150)

# plt.show()
