import os

import localizationpy.mapping as mp
import localizationpy.file_manager as fm

points_number = 100
x_min = 0.1
x_max = 20.5
y_min = 0.1
y_max = 7.8
z_min = 1.5
z_max = 1.5

cube = mp.VectorShape(x_min, x_max, y_min, y_max, z_min, z_max)

gen_rand_points = mp.get_random_points(points_number, cube)

file_path = os.path.abspath("output/100_rand_points.dat")
fm.create_points_file(file_path, gen_rand_points)
