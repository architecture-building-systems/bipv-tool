import os
import numpy as np
import pandas as pd
import simplified_yield_calculation as syc
import versuch as vs


module_area = 0.6327  # m2
voltage_mp = 22  # Volts, this value is used for the division of power into voltage and current.
sensor_points_per_module = 88.0
module_efficiency = 0.12

string_arrangement = np.array([[45,44,42,43,41,40],[38,39,37,36,34,35,33,32],[30,31,29,28,26,27,25,24],
                               [23,20,17,14,11,8,5,2],[21,22,19,18,15,12,9],[16,13,10,6,3,0,47],[7,4,1,46,49,50,53,52],
                               [48,51,54,56,57,60,63,66],[55,58,59,62,61,64,65,67],[68,70,69,71,72,74,73,75]])
# cabling_length = [12,12,13,14,15,16,12,14,13,15]


current_directory = os.path.dirname(__file__)
sen_dir_ill_path = os.path.join(current_directory, "data\sen_dir.ill")
sen_dir_csv_path = os.path.join(current_directory, "data\sen_dir.csv")
sen_dir_ill = pd.read_csv(sen_dir_ill_path, sep=' ', header=None)
sensor_points_df = pd.read_csv(sen_dir_csv_path, sep=',', usecols=['sen_x', 'sen_y', 'sen_z'])
print "loaded"

 # find module center points
sensor_points_np = sensor_points_df.as_matrix()
module_center_points_np = np.empty((len(sensor_points_df)/int(sensor_points_per_module),3))  # 3 for x,y and z
print len(sensor_points_df)/int(sensor_points_per_module)

for module in range(len(sensor_points_df)/int(sensor_points_per_module)):
    rows_from = int(module*sensor_points_per_module)
    rows_to =  int((module+1)*sensor_points_per_module-1)  # -1

    module_center_points_np[module,:] = sensor_points_np[rows_from:rows_to,:].mean(axis=0)

module_irradiation_np = syc.cell2module_irradiance(sen_dir_ill=sen_dir_ill, sensor_points_per_module=sensor_points_per_module)

cabling_lengths = syc.calculate_cable_length(string_arrangement=string_arrangement, module_coordinates=module_center_points_np)

print cabling_lengths

total_energy_yield = syc.simple_yield_calculation(string_arrangement=string_arrangement,
                                                 module_irradiation_np=module_irradiation_np,
                                                 module_area=module_area, module_efficiency=module_efficiency,
                                                 cabling_length=cabling_lengths, voltage_mp=voltage_mp)


print total_energy_yield