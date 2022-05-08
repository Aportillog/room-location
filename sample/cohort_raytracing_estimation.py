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

output_path = 'output/simulation_5/4points_position_estimation/'

# Plot configure
fig = plt.figure(figsize=(19.20, 10.80))
fig.suptitle('Smallest power EDs to 4 random points')
plt.tight_layout()
lplot.add_estimation_legend(fig)


# mpoint_idx = [rd.randint(0, len(rand_points_sim.points)) for i in range(4)]
mpoint_idx = [90, 52, 41, 39]

mobiles_sim.cohort_points(mpoint_idx)

configs = list()

# Estimation 1
configs.append({
    "aerials": ['1'],
    "subplot_name": 'Aerials: 1, points: {}'.format(len(mpoint_idx)),
    "output": output_path + '1_aerials.csv',
    "power_output": output_path + '1_aerials_powers.csv',
    "fprints_used": 4
})

# Estimation 4
configs.append({
    "aerials": ['1', '2', '3', '4'],
    "subplot_name": 'Aerials: 4, points: {}'.format(len(mpoint_idx)),
    "output": output_path + '4_aerials.csv',
    "power_output": output_path + '4_aerials_powers.csv',
    "fprints_used": 4
})

for cfg in configs:
    estimations = met.get_raytracing_estimation(mobiles_sim, fprints_sim, cfg["aerials"], fprints_used=cfg["fprints_used"])
    fm.create_power_estimation_file(cfg['power_output'], estimations)

    sel_fpoints = list()
    for est in estimations:
        sel_fpoints.extend([fpoint for fpoint in est.fpoints])

    fm.create_estimation_file(cfg['output'], estimations)
    lplot.plot_position_estimation(cfg['subplot_name'], fig, sel_fpoints, estimations,
                                   escolor="blue", plot_ids=True, plot_polygons=True)


fig.savefig(output_path + 'plot.png', bbox_inches='tight', dpi=150)
# plt.show()
