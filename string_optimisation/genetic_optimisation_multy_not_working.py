import os
import random
import auxiliary as aux
import simplified_yield_calculation as syc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


from deap import base
from deap import creator
from deap import tools
import multiprocessing

import time


def init_individual():

    return  np.array([7., 6., 8., 8., 7., 6., 8., 8., 5., 7., 6., 8., 5., 7., 6.,
              8., 5., 7., 6., 8., 5., 7., 6., 4., 5., 7., 6., 4., 5., 3.,
              6., 4., 5., 3., 3., 4., 5., 2., 3., 4., 2., 3., 4., 2., 3.,
              4., 2., 3., 4., 2., 3., 1., 2., 2., 1., 0., 2., 1., 0., 1.,
              1., 0., 1., 1., 0., 0., 1., 0., 0., 0., 9., 9., 10.,10.,9.,
              9., 10.,10.,9., 9., 10.,10.,9., 9., 10.,10.,11.,12.,12.,12.,
              11.,12.,12.,12.,11.,12.,13.,13.,11.,12.,13.,13.,11.,13.,13.,
              11.,11.,13.,14.,14.,14.,14.,14.,14.,14.])


def evaluation_function(individual, amodule_irradiation_np, amodule_area, amodule_efficiency, distance_matrix_np,
                        center_points, voltage_mp, hour_from=0, hour_to=8759, roh=0.027, cabling_cross_section_area=4 ):
    start = time.time()

    #Individual is a list of numbers, a chromosome
    string_layout = aux.decoding(np.array(individual))

    cabling_lengths = aux.length_calculation(string_layout, center_points)
    # total_module_spacing = aux.module_spacing(string_layout, distance_matrix_np)
    total_energy_yield = syc.simple_yield_calculation(string_arrangement=string_layout,
                                                      module_irradiation_np=amodule_irradiation_np,
                                                      module_area=amodule_area, module_efficiency=amodule_efficiency,
                                                      cabling_length=cabling_lengths, hour_from=hour_from,
                                                      hour_to=hour_to, voltage_mp=voltage_mp, roh=roh,
                                                      cabling_cross_section_area=cabling_cross_section_area)



    # total_goodness = total_energy_yield*energy_price-total_cabling_length*cabling_price

    return total_energy_yield,
    # return total_energy_yield, total_cabling_length




def main(plot_obj):

    random.seed(64)
    CXRB = 0.92
    MUTPB = 0.03

    # pop will be a list of 300 individuals
    pop = toolbox.population(n=500)
    print "start of evolution"

    #Evaluate the entire population
    fitnesses = list(toolbox.map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    fits = [ind.fitness.values[0] for ind in pop]

    generation = 0

    generation_history =[]
    cabling_history = []

    #begin evolution
    while generation < 2000:
        generation+=1
        print ("Generation %i" % generation)

        #select the next generation individuals
        offspring = toolbox.select(pop, len(pop))

        #clone the selected individuals
        offspring = list(toolbox.map(toolbox.clone, offspring))

        # Here crossover and mutation takes place on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXRB:
                toolbox.mate(child1,child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
                if random.random() < MUTPB:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values


        # Evaluate the individuals with an invaldi fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]

        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
        pop[:] = offspring

        start = time.time()

        if generation%15==0:
            # Gather all the fitnesses in one list and print the stats
            generation_fits = [ind.fitness.values[0] for ind in pop]
            cabling_fits = [ind.fitness.values[1] for ind in pop]

            length = len(pop)
            generation_mean = sum(generation_fits) / length
            cabling_mean = sum(cabling_fits)/length
            generation_max = max(generation_fits)
            cabling_min = min(cabling_fits)
            generation_history.append(generation_max)
            cabling_history.append(cabling_min)
            # sum2 = sum(x * x for x in generation_fits)
            # std = abs(sum2 / length - generation_mean ** 2) ** 0.5

            print("  Min %s and %s" % (min(generation_fits), cabling_min))
            print("  Max %s and %s" % (generation_max, max(cabling_fits)))
            print("  Avg %s and %s" % (generation_mean, cabling_mean))
            # print("  Std %s" % std)

            print aux.decoding(pop[cabling_fits.index(min(cabling_fits))]).tolist()

            layout = plt.figure(1)
            plot_obj.string_arrangement = aux.decoding(pop[generation_fits.index(max(generation_fits))]).tolist()
            plot_obj.plot(filename="distance" + str(generation))

            plt.ion()
            history = plt.figure(2)
            history.clf()
            plt.plot(generation_history)
            plt.pause(0.001)


        print "Time"
        print time.time()-start
        # visualize_result







creator.create("FitnessMax", base.Fitness, weights=(1,))

# An individual will be a list of strings for each module, i.e. one chromosome
creator.create("Individual", list, fitness=creator.FitnessMax)

if __name__ == "__main__":


    # Definitions of numbers
    maximum_string_number = 8
    string_length = 8
    module_area = 0.943  # m2
    sensor_points_per_module = 230
    module_efficiency = 0.12
    number_of_modules = 76
    hoy_from = 4123
    hoy_to = 4124
    specific_cable_resistivity = 0.017
    module_mpp_voltage = 22
    cable_cross_section = 4  # mm2


    # Definitions of filepaths and import of data
    current_directory = os.path.dirname(__file__)
    sen_dir_ill_path = os.path.join(current_directory, "data\sen_dir.ill")
    sen_dir_csv_path = os.path.join(current_directory, "data\sen_dir.csv")
    spacing_list_path = os.path.join(current_directory, "data\spacing_list.csv")
    sen_dir_ill = pd.read_csv(sen_dir_ill_path, sep=' ', header=None)
    sensor_points_df = pd.read_csv(sen_dir_csv_path, sep=',', usecols=['sen_x', 'sen_y', 'sen_z'])

    spacing_list = pd.read_csv(spacing_list_path, sep=",", header=None, squeeze=True)
    spacing_matrix_np = spacing_list.values.reshape(number_of_modules,number_of_modules)

    module_irradiation_np = syc.cell2module_irradiance(sen_dir_ill=sen_dir_ill,
                                                       sensor_points_per_module=sensor_points_per_module)

    sensor_points_np = sensor_points_df.as_matrix()

    # Calculation of module coordinates
    module_center_points_np = np.empty((len(sensor_points_df) / int(sensor_points_per_module), 3))  # 3 for x,y and z
    for module in range(len(sensor_points_df) / int(sensor_points_per_module)):
        rows_from = int(module * sensor_points_per_module)
        rows_to = int((module + 1) * sensor_points_per_module - 1)  # -1

        module_center_points_np[module, :] = sensor_points_np[rows_from:rows_to, :].mean(axis=0)



    # initialising plot object for live plot of GA results
    visual = aux.Result_Plot(module_center_points_np, None)

    # plotting of irradiance data in the chosen timeframe
    irradiance_plot = aux.Result_Plot(module_center_points_np, None)
    irradiance_plot.data=module_irradiation_np
    irradiance_plot.data_plot(hour_from=hoy_from, hour_to=hoy_to)


    toolbox = base.Toolbox()

    pool = multiprocessing.Pool(processes=6)
    toolbox.register("map", pool.map)

    #Register the chromosome generator here:
    toolbox.register("generator", random.randint, 0,maximum_string_number-1)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.generator, number_of_modules)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluation_function, amodule_irradiation_np=module_irradiation_np,
                     amodule_area=module_area, amodule_efficiency=module_efficiency,
                     distance_matrix_np=spacing_matrix_np, center_points= module_center_points_np,
                     voltage_mp=module_mpp_voltage, hour_from=hoy_from, hour_to=hoy_to, roh=specific_cable_resistivity,
                     cabling_cross_section_area=cable_cross_section)


    # I do not really know what these registries do... but they always seem to be the same
    toolbox.register("mate", tools.cxTwoPoint)
    # toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
    #up is the maximum number of strings -1
    toolbox.register("mutate", tools.mutUniformInt, low=0,up=(maximum_string_number-1), indpb=0.25)
    toolbox.register("select", tools.selTournament, tournsize=3)

    main(visual)