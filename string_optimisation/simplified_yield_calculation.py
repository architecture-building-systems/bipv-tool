import pandas as pd
import numpy as np


def cell2module_irradiance(sen_dir_ill, sensor_points_per_module):

    number_of_modules = int((len(sen_dir_ill.columns)-4.0)/sensor_points_per_module)
    module_irradiation_np = np.empty((len(sen_dir_ill.index),number_of_modules)) # rows=hours

    for module in range(number_of_modules):
        columns_from = module*sensor_points_per_module + 4
        columns_to = ((module+1)*sensor_points_per_module + 4) -1
        module_irradiation_np[:,module] = sen_dir_ill.loc[:, columns_from:columns_to].mean(axis=1)

    return module_irradiation_np


def simple_yield_calculation(string_arrangement, module_irradiation_np, module_area, module_efficiency, cabling_length,
                             hour_from=0, hour_to=8759, voltage_mp=None, roh=0.027, cabling_cross_section_area=4):
    """
    :param string_arrangement: 
    :param module_irradiation_np: 
    :param module_area: 
    :param module_efficiency: 
    :param cabling_length: 
    :param hour_from: 
    :param hour_to: 
    :param voltage_mp: 
    :param roh: 
    :param cabling_cross_section_area: 
    :return: 
    """
    # zuerst eine Optimierung auf Einstrahlung machen.
    # hier kommt spaeter die Temperaturkorrekture

    module_output_np = module_irradiation_np[hour_from:hour_to, :] * module_efficiency * module_area
    array_yield = 0
    count_index = 0
    # all_currents =[] # wieder wegnehmen
    for modules_in_string in string_arrangement:
        minimum_module_output = module_output_np[:, modules_in_string].min(axis=1) * len(modules_in_string)
        current_of_min_module = minimum_module_output/len(modules_in_string) / voltage_mp
        # all_currents.append(current_of_min_module) # Wieder wegnehmen
        losses_of_strings = np.square(current_of_min_module) * roh / cabling_cross_section_area * cabling_length[
            count_index]
        final_yield = minimum_module_output - losses_of_strings
        array_yield += final_yield.sum()
        count_index+=1




    # total_current = np.empty(current_of_min_module.shape)# Wieder wegnehmen

    # for string_current in all_currents:# Wieder wegnehmen
    #     total_current = np.add(total_current, string_current)# Wieder wegnehmen

    # additional_losses = np.square(total_current) * roh / 40 * 10
    # total_add_losses = additional_losses.sum()
    # array_yield =array_yield - total_add_losses


    return array_yield


def get_distance(point_a, point_b):

    return np.sqrt((point_a[0]-point_b[0])**2 + (point_a[1]-point_b[1])**2 + (point_a[2]-point_b[2])**2)


def calculate_cable_length(string_arrangement, module_coordinates):

    string_cabling_length_list = []
    for index, modules_in_string in np.ndenumerate(string_arrangement):
        string_cabling_length = 0
        for module in modules_in_string[:-1]:
            string_cabling_length += get_distance(module_coordinates[module], module_coordinates[module+1])
        string_cabling_length_list.append(string_cabling_length * 2)  # because cabling goes both ways)
    return string_cabling_length_list