import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import os

from localizationpy import simulation as sm
import plotter


fprints_path = os.path.abspath("/home/aitor/localizationpy/input/simulation_6/project_ord_tot_6ant_huellas")
fprints_sim = sm.Simulation(fprints_path)

mobiles_path = os.path.abspath("/home/aitor/localizationpy/input/simulation_6/project_ord_tot_6ant_aleatorios")
mobiles_sim = sm.Simulation(mobiles_path)

# mpoint_idx = [65, 95, 22, 32]
mpoint_idx = [32]
mobiles_sim.cohort_points(mpoint_idx)

# Plot configure
fig = plt.figure()
fig.suptitle('Power scatters')

legend_elements = [Line2D([0], [0], marker='o', color='w', label='Fingerprint',
                          mec='black', mfc='black', markersize=10, alpha=0.6),
                   Line2D([0], [0], marker='o', color='w', label='Mobile',
                          mec='green', mfc='green', markersize=10, alpha=0.6)]
fig.legend(handles=legend_elements, loc="upper left")

aerials = ['1', '2', '3', '4', '5', '6']

for aerial in aerials:
    fprints_powers = []
    for pt in fprints_sim.points:
        fprints_powers.append(list((pt, fprints_sim.get_field_value(aerial, id=pt.id).power())))
    mobile_powers = []
    for pt in mobiles_sim.points:
        mobile_powers.append(list((pt, mobiles_sim.get_field_value(aerial, id=pt.id).power())))

    plotter.plot_aerial_powers('Aerial ' + aerial, fprints_powers, mobile_powers, fig)

plt.show()
