import os
import random
import auxiliary as aux
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing

from deap import base
from deap import creator
from deap import tools



def evaluation_function(individual, amodule_irradiation_np, amodule_area, amodule_efficiency,
                        center_points, voltage_mp, number_of_strings, hour_from=0, hour_to=8759,
                        roh=0.027, cabling_cross_section_area=4 ):


    string_layout = aux.decoding(individual, number_of_strings)

    cabling_lengths = aux.calculate_cable_length_greedy(string_layout, center_points)

    total_energy_yield = aux.simple_yield_calculation(string_arrangement=string_layout,
                                                      module_irradiation_np=amodule_irradiation_np,
                                                      module_area=amodule_area, module_efficiency=amodule_efficiency,
                                                      cabling_length=cabling_lengths, hour_from=hour_from,
                                                      hour_to=hour_to, voltage_mp=voltage_mp, roh=roh,
                                                      cabling_cross_section_area=cabling_cross_section_area)

    return total_energy_yield/1000.0,


def run_optimisation(cxpb=0.9, mutpb=0.5, number_of_generations=1000, population_size=500, number_of_strings=None):

    random.seed(64)
    pop = toolbox.population(n=population_size)
    print "start of evolution"

    #Evaluate the entire population
    fitnesses = list(toolbox.map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    generation = 0
    generation_history =[]

    #begin evolution
    while generation < number_of_generations:
        generation+=1
        print ("Generation %i" % generation)

        #select the next generation individuals
        offspring = toolbox.select(pop, len(pop))

        #clone the selected individuals
        offspring = list(toolbox.map(toolbox.clone, offspring))

        # Here crossover and mutation takes place on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < cxpb:
                toolbox.mate(child1,child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
                if random.random() < mutpb:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)

        for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
        pop[:] = offspring

        # Gather all the fitnesses in one list and print the stats
        generation_fits = [ind.fitness.values[0] for ind in pop]
        generation_max = max(generation_fits)
        generation_history.append(generation_max)



        if generation==number_of_generations:

            print aux.decoding(pop[generation_fits.index(generation_max)], number_of_strings)
            plt.plot(generation_history)
            result_path = os.path.join(os.path.dirname(__file__), r"data\history.csv")
            pd.DataFrame(generation_history).to_csv(result_path)
            plt.ylabel("Output [kWh]")
            plt.xlabel("Generations [n]")
            plt.title("Evolution with cxpb = %s and mutpb = %s" %(cxpb, mutpb))
            # plt.savefig(r"C:\Users\walkerl\Desktop\temp_stuff\Images\history%s" % (str(int(100*cxpb)) + "_" +str(int(100*mutpb))))
            plt.show()







#  Creation of a specific individual's class
creator.create("FitnessMax", base.Fitness, weights=(1,))
creator.create("Individual", list, fitness=creator.FitnessMax)

if __name__ == "__main__":


    ### ========= Definition of parameters =========== ###
    maximum_string_number = 10
    module_area = 0.90  # m2
    sensor_points_per_module = 40
    module_efficiency = 0.133
    number_of_modules = 75
    hoy_from = 0
    hoy_to = 8759
    specific_cable_resistivity = 0.017
    module_mpp_voltage = 29.5
    cable_cross_section = 4  # mm2

    # GA Parameters
    cxpb = 0.5
    mutpb=0.4
    number_of_generations = 1000
    population_size = 500



    # Definitions of filepaths and import of data
    current_directory = os.path.dirname(__file__)
    sen_dir_ill_path = os.path.join(current_directory, "data\sen_dir.ill")
    sen_dir_csv_path = os.path.join(current_directory, "data\sen_dir.csv")

    #  Read data
    sen_dir_ill = pd.read_csv(sen_dir_ill_path, sep=' ', header=None)
    sensor_points_df = pd.read_csv(sen_dir_csv_path, sep=',', usecols=['sen_x', 'sen_y', 'sen_z'])


    module_irradiation_np = aux.cell2module_irradiance(sen_dir_ill=sen_dir_ill,
                                                       sensor_points_per_module=sensor_points_per_module)
    sensor_points_np = sensor_points_df.as_matrix()

    # Calculation of module coordinates
    module_center_points_np = np.empty((len(sensor_points_df) / int(sensor_points_per_module), 3))  # 3 for x,y and z
    for module in range(len(sensor_points_df) / int(sensor_points_per_module)):
        rows_from = int(module * sensor_points_per_module)
        rows_to = int((module + 1) * sensor_points_per_module - 1)  # -1
        module_center_points_np[module, :] = sensor_points_np[rows_from:rows_to, :].mean(axis=0)


    # Prepare Genetic Algorithm Tools and register functions
    toolbox = base.Toolbox()

    #  Allow for multiprocessing
    pool = multiprocessing.Pool(processes=6)
    toolbox.register("map", pool.map)

    #  Register the chromosome generator here:
    toolbox.register("generator", aux.random_generator, number_of_modules)


    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generator)

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    #  Register the evaluation function here:
    toolbox.register("evaluate", evaluation_function, amodule_irradiation_np=module_irradiation_np,
                     amodule_area=module_area, amodule_efficiency=module_efficiency,
                     center_points= module_center_points_np, voltage_mp=module_mpp_voltage,
                     number_of_strings=maximum_string_number,  hour_from=hoy_from, hour_to=hoy_to,
                     roh=specific_cable_resistivity, cabling_cross_section_area=cable_cross_section)


    #  Choose type of crossover
    toolbox.register("mate", tools.cxPartialyMatched)

    #  Choose type of mutation
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.04)

    #  Choose type of selection algorithm
    toolbox.register("select", tools.selTournament, tournsize=3)

    run_optimisation(cxpb=cxpb, mutpb=mutpb, number_of_generations=number_of_generations,
                     population_size=population_size, number_of_strings=maximum_string_number)


