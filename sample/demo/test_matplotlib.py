import matplotlib.pyplot as plt
import os
import numpy as np

from localizationpy import simulation as sm

static_points_path = os.path.abspath("../data/simulation_5/resul_4antenas_huellas_cada05m")
static_points_sim = sm.Simulation(static_points_path)
static_points_x = [coord.x for coord in static_points_sim.points]
static_points_y = [coord.y for coord in static_points_sim.points]

rand_points_path = os.path.abspath("../data/simulation_5/resul_4antenas_puntos_aleatorios")
rand_points_sim = sm.Simulation(rand_points_path)
rand_points_x = [coord.x for coord in rand_points_sim.points]
rand_points_y = [coord.y for coord in rand_points_sim.points]


fig, axs = plt.subplots(squeeze=False)
fig.suptitle('100 Random points position estimations')
# axs[0, 0].set_title('Estimation 1')
# axs[0, 0].set_xlim(0, 21)
# axs[0, 0].set_ylim(0, 8)
#
# major_ticks = np.arange(0, 21, 5)
# minor_ticks = np.arange(0, 21, 0.5)
# axs[0, 0].set_xticks(major_ticks)
# axs[0, 0].set_xticks(minor_ticks, minor=True)
#
# major_ticks = np.arange(0, 8, 1)
# minor_ticks = np.arange(0, 8, 0.5)
# axs[0, 0].set_yticks(major_ticks)
# axs[0, 0].set_yticks(minor_ticks, minor=True)
# axs[0, 0].grid(which='minor', alpha=0.2)
# axs[0, 0].grid(which='major', alpha=0.5)
#
# axs[0, 0].scatter(static_points_x, static_points_y, s=10, c='black', marker='x')
# axs[0, 0].scatter(rand_points_x, rand_points_y, s=10, c='green', marker='o')

# Connect markers
for i in range(0, len(rand_points_x)):
    v_x = list()
    v_y = list()
    v_x.append(rand_points_x[i])
    v_x.append(static_points_x[i])
    v_y.append(rand_points_y[i])
    v_y.append(static_points_y[i])
    plt.plot(v_x, v_y, color='purple', linewidth=0.2, alpha=0.5)

# # Add point ids
# for idx, (x, y) in enumerate(zip(rand_points_x, rand_points_y)):
#     label = "{}".format(idx + 1)
#     plt.annotate(label,  # this is the text
#                  (x, y),  # this is the point to label
#                  textcoords="offset points",  # how to position the text
#                  xytext=(0, 3),  # distance from text to points (x,y)
#                  ha='center',
#                  size=7)  # horizontal alignment can be left, right or center

plt.show()
