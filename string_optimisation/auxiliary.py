import numpy as np
import itertools
import matplotlib.pyplot as plt
import random
import pandas as pd

from matplotlib.patches import Rectangle

import time



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

def calculate_cable_length_tsp(string_arragnement, module_coordinates):

    string_cabling_length_list = []
    for index, modules_in_string in np.ndenumerate(string_arragnement):
        if len(modules_in_string)<=1:
            string_cable_length = 3
        else:
            string_cable_length = tsp(module_coordinates[modules_in_string])[0]
        string_cabling_length_list.append(string_cable_length)
    return string_cabling_length_list


def calculate_cable_length_greedy(string_arrangement, module_coordinates):


    string_cabling_length_list = []

    for modules_in_string in string_arrangement:

        if len(modules_in_string)<=1:
            string_cable_length = 3
        else:
            string_cable_length = greedy(module_coordinates[modules_in_string])

        string_cabling_length_list.append(string_cable_length)

    # string_cabling_length_list = []
    # print string_arrangement
    # print type(string_arrangement)
    # for index, modules_in_string in np.ndenumerate(string_arrangement):
    #     print type(modules_in_string)
    #     print modules_in_string
    #     if len(modules_in_string)<=1:
    #         string_cable_length = 3
    #     else:
    #         string_cable_length = greedy(module_coordinates[modules_in_string])
    #     string_cabling_length_list.append(string_cable_length)

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




 # Solution to travelling salesman problem implemented by mlalevic from the follwing GitHub repository:
 # https://gist.github.com/mlalevic/6222750
def tsp(point_list):
    all_distances = [[get_distance(a, b) for a in point_list] for b in point_list]
    A = {(frozenset([0, idx + 1]), idx + 1): (dist, [0, idx + 1]) for idx, dist in enumerate(all_distances[0][1:])}
    cnt = len(point_list)
    for m in range(2, cnt):
        B = {}
        for S in [frozenset(C) | {0} for C in itertools.combinations(range(1, cnt), m)]:
            for j in S - {0}:
                B[(S, j)] = min([(A[(S - {j}, k)][0] + all_distances[k][j], A[(S - {j}, k)][1] + [j]) for k in S if
                                 k != 0 and k != j])  # this will use 0th index of tuple for ordering, the same as if key=itemgetter(0) used
        A = B

    res = min([(A[d][0] + all_distances[0][d[1]], A[d][1]) for d in iter(A)])

    total_distance = 0
    for point_nr in range(len(res[1][:-1])):
        total_distance = total_distance + get_distance(point_list[res[1][point_nr]],point_list[res[1][point_nr+1]])

    # This closes the circle
    total_distance = total_distance + get_distance(point_list[res[1][len(res[1])-1]],point_list[res[1][0]])
    return res[0], res[1]


def decoding(chromosome, number_of_strings):
    individual_np = np.array(chromosome)
    string_layout = np.array_split(individual_np, number_of_strings)
    return string_layout

def random_generator(number_of_modules):
    chromosome = np.arange(number_of_modules)
    np.random.shuffle(chromosome)
    return chromosome.tolist()



def module_spacing(string_layout, distance_matrix_df):
    module_spacing_length = 0
    for index, modules_in_string in np.ndenumerate(string_layout):
        loop_passes = len(modules_in_string[:-1])
        for module_counter in range(loop_passes):
            module_spacing_length += distance_matrix_df[modules_in_string[module_counter]][modules_in_string[module_counter+1]]
    return module_spacing_length



def create_adjacency_matrix(module_center_points, distance_threshold):
    # So far only works with 3D coordinates!
    all_distances = np.array([[get_distance(a, b) for a in module_center_points] for b in module_center_points])
    adjacency_matrix = all_distances<distance_threshold
    return adjacency_matrix





class Result_Plot(object):
    "The class Result_Plot is used, so that plots can be updated faster"

    def __init__(self, module_centers, string_arrangement):
        self.module_centers = module_centers
        self.string_arrangement = string_arrangement
        self.generation_history = []
        self.cabling_history = []
        self.data = None

    def add_to_gen_history(self, new_value):
        self.generation_history.append(new_value)

    def add_to_cabling_history(self, new_value):
        self.cabling_history.append(new_value)

    def plot(self,filename=None, save_mode=False, save_csv=False):
        # plt.ion()
        plt.clf()
        cmap = plt.get_cmap('tab20')
        colors = [cmap(i) for i in np.linspace(0, 1, len(self.string_arrangement))]
        axes_a = plt.gca()
        axes_a.set_xlim(118,136)
        axes_a.set_ylim(-18,-3)
        axes_a.set_title("Generation")
        color_nr = 0
        color_list = np.empty(len(self.module_centers))
        for string in self.string_arrangement:
            for module in string:
                axes_a.add_patch(Rectangle((self.module_centers[module][0], self.module_centers[module][1]), 1.6, 0.3, angle=70, facecolor=colors[color_nr]))
            color_nr+=1

            # plt.pause(0.0001)
        if save_mode==True:
            plt.savefig(r"C:\Users\walkerl\Desktop\temp_stuff\Images\%s.png" % str(filename))
        if save_csv == True:
            display_color = np.empty(len(self.module_centers))
            string_count = 0
            for string in self.string_arrangement:
                display_color[string] = string_count
                string_count += 1

            colors_df = pd.DataFrame(display_color, columns=["colour"])
            colors_df.to_csv(r"C:\Users\walkerl\Desktop\temp_stuff\Images\data.csv", index=False)


        # plot2 = plt.plot(self.generation_history)

    def data_plot(self, hour_from, hour_to):
        cmap = plt.get_cmap('gnuplot')
        data_max = self.data[hour_from:hour_to,:].sum(axis=0).max()
        data_min = self.data[hour_from:hour_to,:].sum(axis=0).min()
        print data_min
        print data_max
        axes_a = plt.gca()
        axes_a.set_ylim(-18, -3)
        axes_a.set_xlim(118, 136)
        axes_a.set_title("Irradiance")

        # print self.data[hour_from:hour_to,:]
        for module in range(len(self.module_centers)):
            # print module
            # print self.data[hour_from:hour_to, module].sum()
            # print self.data[hour_from:hour_to, module]
            # print (self.data[hour_from:hour_to,module].sum()-data_min)/(data_max-data_min)
            axes_a.add_patch(Rectangle((self.module_centers[module][0], self.module_centers[module][1]), 1.6, 0.3, angle=70, facecolor=cmap((self.data[hour_from:hour_to,module].sum()-data_min)/(data_max-data_min))))
        # plt.show()
        plt.savefig(r"C:\Users\walkerl\Desktop\temp_stuff\Images\irradiation.png")

