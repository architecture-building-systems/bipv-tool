import numpy as np
import itertools
import matplotlib.pyplot as plt
import random
import pandas as pd




def simple_yield_calculation(string_arrangement, module_irradiation_np, module_area, module_efficiency, cabling_length,
                             hour_from=0, hour_to=8759, voltage_mp=None, roh=0.027, cabling_cross_section_area=4):
    """
    :param string_arrangement: np.array of modules in strings [[0 3 4 5] [1 2 6 7]] modules 0 3 4 and 5 are in string 1
    :param module_irradiation_np: one irradiance value per module [1000 1000 600 455 345 200 670 800]
    :param module_area: module aperture area in m2
    :param module_efficiency: e.g., STC module efficiency
    :param cabling_length: list of cable lengths for each string [34, 45]
    :param hour_from: int, start time of optimization in hour_of_year
    :param hour_to: int, start time of optimization in hour_of_year
    :param voltage_mp: float, maximum power point voltage from datasheet in [V]. 
    :param roh: float, specific cable resistivity in [Ohm mm2 /m]
    :param cabling_cross_section_area: float, in [mm2]
    :return: float, total array yield for the given parameters
    """

    # here you could add a temperature correction
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
    """
    This function is used, when more than one irradiance value is available per module. It does not necessarily have
    to be on the cell level. This is however especially important for curved or partially shaded modules
    :param sen_dir_ill: pandas dataframe, can be a direct import from a daysim .ill file via pandas read_csv the first
                        4 columns are used for date and time
    :param sensor_points_per_module: int, e.g. an irradiance value is simulated for all 72 cells of the module. -->72
    :return: np array of an average irradiance value for all given timesteps
    """

    number_of_modules = int((len(sen_dir_ill.columns)-4.0)/sensor_points_per_module)
    module_irradiation_np = np.empty((len(sen_dir_ill.index),number_of_modules)) # rows=hours

    for module in range(number_of_modules):
        columns_from = module*sensor_points_per_module + 4
        columns_to = ((module+1)*sensor_points_per_module + 4) -1
        module_irradiation_np[:,module] = sen_dir_ill.loc[:, columns_from:columns_to].mean(axis=1)

    return module_irradiation_np

def get_distance(point_a, point_b):
    """
    calcualtes disatance between two points
    :param point_a: list or numpy array, [x, y, z]
    :param point_b: list or numpy array, [x, y, z]
    :return: float, distance in respective coordinate scale 
    """
    return np.sqrt((point_a[0]-point_b[0])**2 + (point_a[1]-point_b[1])**2 + (point_a[2]-point_b[2])**2)


def calculate_cable_length_greedy(string_arrangement, module_coordinates):
    """
    This function calculates the shortest path between several points with the greedy approach. It will most probably 
    not find the shortest path but an approximation of it. This fast heuristic is used because the function is 
    evaluated repeatedly for many options in the genetic optimization and is therefore strongly influencing the 
    optimization time.
    :param string_arrangement: np.array or list, modules in strings e.g. [[0 3 4 5] [1 2 6 7]]
    :param module_coordinates: np.array or list, center coordinates for all modules 
    :return: list, cable length for each string
    """

    string_cabling_length_list = []
    for modules_in_string in string_arrangement:
        if len(modules_in_string)<=1:
            string_cable_length = 3
        else:
            string_cable_length = greedy(module_coordinates[modules_in_string])
        string_cabling_length_list.append(string_cable_length)
    return string_cabling_length_list


def greedy(point_list):
    """
    This function gets a list of points and finds a path to connect them all with a short distance
    :param point_list: list, list of all coordinates looked at [[x,y,z],[x,y,z]
    :return: float, distance value
    """
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
    """
    This function decodes the random generated chromosome into a string arrangement of strings with preferably equal 
    length.
    :param chromosome: list, shuffled list of all module numbers
    :param number_of_strings: int, chosen number of strings in which the modules will be distributed
    :return: np.array of string layout e.g. [0 1 2 3] [4 5 6]] for 7 modules with module 0,1,2,3 in string 1
    """
    individual_np = np.array(chromosome)
    string_layout = np.array_split(individual_np, number_of_strings)
    return string_layout

def random_generator(number_of_modules):
    """
    randomly generatec chromosomes according to the number of modules
    :param number_of_modules: int
    :return: list, shuffled array with all numbers between 0 and number_of_modules including each one only once.
    """
    chromosome = np.arange(number_of_modules)
    np.random.shuffle(chromosome)
    return chromosome.tolist()


