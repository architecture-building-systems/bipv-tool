import auxiliary as aux
import itertools
import os
import pandas as pd


import numpy as np
import random
import deap
from deap import tools


string_layout = [[50, 52, 53, 54, 55, 56, 57, 60],
                 [0, 1, 3, 26, 28, 44, 45, 47],
                 [30, 32, 34, 36, 37, 39, 41, 43],
                 [17, 19, 21, 23, 25, 27, 29, 31],
                 [33, 35, 38, 40, 42, 62, 65, 67],
                 [2, 4, 5, 8, 11, 46, 49],
                 [68, 69, 70, 71, 72, 73, 74],
                 [48, 51, 58, 59, 61, 64, 66],
                 [6, 9, 18, 20, 22, 24, 63],
                 [7, 10, 12, 13, 14, 15, 16]]


sensor_points_per_module = 40
current_directory = os.path.dirname(__file__)
sen_dir_csv_path = os.path.join(current_directory, "data\sen_dir.csv")
sensor_points_df = pd.read_csv(sen_dir_csv_path, sep=',', usecols=['sen_x', 'sen_y', 'sen_z'])
sensor_points_np = sensor_points_df.as_matrix()

module_center_points_np = np.empty((len(sensor_points_df) / int(sensor_points_per_module), 3))  # 3 for x,y and z
for module in range(len(sensor_points_df) / int(sensor_points_per_module)):
    rows_from = int(module * sensor_points_per_module)
    rows_to = int((module + 1) * sensor_points_per_module - 1)  # -1

    module_center_points_np[module, :] = sensor_points_np[rows_from:rows_to, :].mean(axis=0)

print module_center_points_np

cabling_lengths = np.array(aux.calculate_cable_length_greedy(string_layout, module_center_points_np))

print cabling_lengths*2+10