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




def evaluation_function(individual, amodule_irradiation_np, amodule_area, amodule_efficiency,
                        center_points, voltage_mp, number_of_strings, hour_from=0, hour_to=8759, roh=0.027, cabling_cross_section_area=4 ):


    string_layout = aux.decoding(individual, number_of_strings)


    # cabling_lengths = aux.calculate_cable_length_simple(string_layout, center_points)
    cabling_lengths = aux.calculate_cable_length_greedy(string_layout, center_points)

    # total_cabling_length = sum(cabling_lengths)
    # total_module_spacing = aux.module_spacing(string_layout, distance_matrix_np)
    total_energy_yield = syc.simple_yield_calculation(string_arrangement=string_layout,
                                                      module_irradiation_np=amodule_irradiation_np,
                                                      module_area=amodule_area, module_efficiency=amodule_efficiency,
                                                      cabling_length=cabling_lengths, hour_from=hour_from,
                                                      hour_to=hour_to, voltage_mp=voltage_mp, roh=roh,
                                                      cabling_cross_section_area=cabling_cross_section_area)


    # total_goodness = total_energy_yield*energy_price-total_cabling_length*cabling_price

    # return total_cabling_length,
    return total_energy_yield/1000.0,
    # return total_module_spacing,
    # return total_energy_yield, total_cabling_length




def main(plot_obj, cxpb=0.9, mutpb=0.5, number_of_strings=None):

    random.seed(64)
    CXPB = cxpb
    MUTPB = mutpb

    # pop will be a list of 300 individuals
    pop = toolbox.population(n=500)
    print "start of evolution"

    #Evaluate the entire population
    fitnesses = list(toolbox.map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    generation = 0
    generation_history =[]

    #begin evolution
    while generation < 1000:
        generation+=1
        print ("Generation %i" % generation)

        #select the next generation individuals
        offspring = toolbox.select(pop, len(pop))

        #clone the selected individuals
        offspring = list(toolbox.map(toolbox.clone, offspring))

        # Here crossover and mutation takes place on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
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


        if generation%1==0:
            # Gather all the fitnesses in one list and print the stats
            generation_fits = [ind.fitness.values[0] for ind in pop]
            # cabling_fits = [ind.fitness.values[1] for ind in pop]

            length = len(pop)
            generation_mean = sum(generation_fits) / length
            # cabling_mean = sum(cabling_fits)/length
            generation_max = max(generation_fits)
            # generation_min = min(generation_fits)
            # cabling_min = min(cabling_fits)
            generation_history.append(generation_max)
            # cabling_history.append(cabling_min)
            # sum2 = sum(x * x for x in generation_fits)
            # std = abs(sum2 / length - generation_mean ** 2) ** 0.5

            # print("  Min %s and %s" % (min(generation_fits), cabling_min))
            # print("  Max %s and %s" % (generation_max, max(cabling_fits)))
            # print("  Avg %s and %s" % (generation_mean, cabling_mean))
            # print("  Min %s" % min(generation_fits))
            # print("  Max %s" % generation_max)
            # print("  Avg %s" % generation_mean)
            # print("  Std %s" % std)

            # print aux.decoding(pop[generation_fits.index(max(generation_fits))]).tolist()


            # plot_obj.string_arrangement = aux.decoding(pop[generation_fits.index(max(generation_fits))]).tolist()
            # plot_obj.plot(filename="distance" + str(generation),save_mode=False)

            if generation==1000:
                layout = plt.figure(1)
                plot_obj.string_arrangement = aux.decoding(pop[generation_fits.index(max(generation_fits))],number_of_strings)#.tolist()
                plot_obj.plot(filename="layout" + str(int(100*cxpb)) + str(int(100*mutpb)), save_mode=True, save_csv=True)


            # plt.ion()


            if generation==1000:
                history = plt.figure(2)
                history.clf()
                plt.plot(generation_history)
                plt.ylabel("Output [kWh]")
                plt.xlabel("Generations [n]")
                plt.title("Evolution with cxpb = %s and mutpb = %s" %(cxpb,mutpb))
                plt.ylim(7100,8700)
                plt.savefig(r"C:\Users\walkerl\Desktop\temp_stuff\Images\history%s" % str(generation)+str(int(100*cxpb)) +str(int(100*mutpb)))
                plt.show()
                # plt.pause(0.001)

        # visualize_result







creator.create("FitnessMax", base.Fitness, weights=(1,))

# An individual will be a list of strings for each module, i.e. one chromosome
creator.create("Individual", list, fitness=creator.FitnessMax)

if __name__ == "__main__":


    # Definitions of numbers
    maximum_string_number = 10
    # string_length = 8
    module_area = 0.90  # m2
    sensor_points_per_module = 40
    module_efficiency = 0.133
    number_of_modules = 75
    hoy_from = 0
    hoy_to = 8759
    specific_cable_resistivity = 0.017
    module_mpp_voltage = 29.5
    cable_cross_section = 4  # mm2

    cxpb = 0.5
    mutpb=0.4


    # Definitions of filepaths and import of data
    current_directory = os.path.dirname(__file__)
    sen_dir_ill_path = os.path.join(current_directory, "data\sen_dir.ill")
    sen_dir_csv_path = os.path.join(current_directory, "data\sen_dir.csv")
    # spacing_list_path = os.path.join(current_directory, "data\spacing_list.csv")
    sen_dir_ill = pd.read_csv(sen_dir_ill_path, sep=' ', header=None)
    sensor_points_df = pd.read_csv(sen_dir_csv_path, sep=',', usecols=['sen_x', 'sen_y', 'sen_z'])

    # spacing_list = pd.read_csv(spacing_list_path, sep=",", header=None, squeeze=True)
    # spacing_matrix_np = spacing_list.values.reshape(number_of_modules,number_of_modules)

    module_irradiation_np = syc.cell2module_irradiance(sen_dir_ill=sen_dir_ill,
                                                       sensor_points_per_module=sensor_points_per_module)
    print module_irradiation_np.sum()

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
    irradiance_plot.data = module_irradiation_np
    irradiance_plot.data_plot(hour_from=hoy_from, hour_to=hoy_to)


    toolbox = base.Toolbox()

    pool = multiprocessing.Pool(processes=6)
    toolbox.register("map", pool.map)

    #Register the chromosome generator here:
    toolbox.register("generator", aux.random_generator, number_of_modules)

    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generator)

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluation_function, amodule_irradiation_np=module_irradiation_np,
                     amodule_area=module_area, amodule_efficiency=module_efficiency,
                     center_points= module_center_points_np, voltage_mp=module_mpp_voltage,
                     number_of_strings=maximum_string_number,  hour_from=hoy_from, hour_to=hoy_to,
                     roh=specific_cable_resistivity, cabling_cross_section_area=cable_cross_section)


    # I do not really know what these registries do... but they always seem to be the same
    toolbox.register("mate", tools.cxPartialyMatched)

    #up is the maximum number of strings -1
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.04)
    toolbox.register("select", tools.selTournament, tournsize=3)



    # cxpb = [0.01,0.2,0.4,0.6,0.8,0.99]
    # mutpb = [0.01,0.2,0.4,0.6,0.8,0.99]

    # for crossover_prob in cxpb:
    #     for mutation_pb in mutpb:
    #         main(visual, cxpb=crossover_prob, mutpb=mutation_pb, number_of_strings=maximum_string_number)
    #
    main(visual, cxpb=cxpb, mutpb=mutpb, number_of_strings=maximum_string_number)