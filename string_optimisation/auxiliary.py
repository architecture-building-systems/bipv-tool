import numpy as np
import itertools
import matplotlib.pyplot as plt
import random
import pandas as pd




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

    return array_yield

def cell2module_irradiance(sen_dir_ill, sensor_points_per_module):

    number_of_modules = int((len(sen_dir_ill.columns)-4.0)/sensor_points_per_module)
    module_irradiation_np = np.empty((len(sen_dir_ill.index),number_of_modules)) # rows=hours

    for module in range(number_of_modules):
        columns_from = module*sensor_points_per_module + 4
        columns_to = ((module+1)*sensor_points_per_module + 4) -1
        module_irradiation_np[:,module] = sen_dir_ill.loc[:, columns_from:columns_to].mean(axis=1)

    return module_irradiation_np

def get_distance(point_a, point_b):

    return np.sqrt((point_a[0]-point_b[0])**2 + (point_a[1]-point_b[1])**2 + (point_a[2]-point_b[2])**2)



def calculate_cable_length_simple(string_arrangement, module_coordinates):

    string_cabling_length_list = []
    for index, modules_in_string in np.ndenumerate(string_arrangement):
        string_cabling_length = 0
        for module in modules_in_string[:-1]:
            string_cabling_length += get_distance(module_coordinates[module], module_coordinates[module+1])
        string_cabling_length_list.append(string_cabling_length * 2)  # because cabling goes both ways)
    return string_cabling_length_list


def calculate_cable_length_greedy(string_arrangement, module_coordinates):

    string_cabling_length_list = []
    for modules_in_string in string_arrangement:
        if len(modules_in_string)<=1:
            string_cable_length = 3
        else:
            string_cable_length = greedy(module_coordinates[modules_in_string])
        string_cabling_length_list.append(string_cable_length)
    return string_cabling_length_list



def greedy(point_list):
    available_points = np.ones(len(point_list), dtype=bool)
    all_distances = np.array([[get_distance(a, b) for a in point_list] for b in point_list])
    start_point = 0
    distance = 0

    # The for loop only runs len(ptlist)-1 times because from the last point there is no continuation
    for point in range(len(point_list) - 1):
        available_points[start_point] = False
        minimum_distance = all_distances[start_point, available_points].min()
        next_point = np.where(all_distances[start_point, :] == minimum_distance)[0]
        distance += minimum_distance
        start_point = next_point[0]  # [0] is required because np.where returns an array

    return distance


def decoding(chromosome, number_of_strings):
    individual_np = np.array(chromosome)
    string_layout = np.array_split(individual_np, number_of_strings)
    return string_layout

def random_generator(number_of_modules):
    chromosome = np.arange(number_of_modules)
    np.random.shuffle(chromosome)
    return chromosome.tolist()


