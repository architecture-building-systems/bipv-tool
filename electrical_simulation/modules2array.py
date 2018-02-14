import numpy as np
import pickle
import os
import interconnection as connect


def read_module(module_folder, module_num):
    module_name = "module" + str(module_num) + ".pkl"
    module_path = os.path.join(module_folder, module_name)
    print module_path
    with open(module_path) as datafile:
        module_iv = pickle.load(datafile)
    return module_iv


def read_string(string_folder, string_num):
    string_name = "string" + str(string_num) + ".pkl"
    string_path = os.path.join(string_folder, string_name)
    print string_path
    with open(string_path) as datafile:
        string_iv = pickle.load(datafile)

    return string_iv


def read_parallel_tie(iv_folder, par_tie_num):
    par_tie_name = "parallel_tie" + str(par_tie_num) + ".pkl"
    par_tie_path = os.path.join(iv_folder, par_tie_name)
    print par_tie_path
    with open(par_tie_path) as datafile:
        par_tie_iv = pickle.load(datafile)
    return par_tie_iv


def data2pickle(data, filepath):
    with open(filepath, 'w') as f:  # This will take some time but on the same time speed up the calculation process
        pickle.dump(data, f)


def modules2strings(string_configuration, module_iv_folder):
    string_number = 0
    for string in string_configuration:
        count = 0
        for module_nr in string:  # do modules for each hour to prevent having to load the files over and over again.
            print "module" + str(module_nr)
            if count == 0:
                iv_string = read_module(module_iv_folder, string[0])
            else:
                module_iv = read_module(module_iv_folder, module_nr)
                for hour in range(len(iv_string)):
                    # print iv_string[hour][0]
                    if iv_string[hour][0].max() == 0:
                        pass  # A pass will leave the iv_string[hour] at zero
                    elif module_iv[hour][
                        0].max() == 0:  # This is required in cases where one module gets sun and the next not
                        iv_string[hour] = np.array([0, 0])
                    else:
                        # print hour
                        iv_string[hour] = connect.series_connect_string(iv_string[hour][0], iv_string[hour][1],
                                                                        module_iv[hour][0], module_iv[hour][1])
            count += 1
        # strings_in_array.append(iv_string)  # If this take too much memory. Save it in pickle format.
        string_path = module_iv_folder + "\string" + str(string_number) + ".pkl"
        string_number += 1
        data2pickle(iv_string, string_path)


def strings_connect_parallel(parallel_connection, module_iv_folder):


    for counter in range(len(parallel_connection)):
        string_nr = parallel_connection[counter]
        if counter == 0:
            parallel_iv = read_string(module_iv_folder, string_nr)
        else:
            string_iv = read_string(module_iv_folder, string_nr)
            for hour in range(len(parallel_iv)):
                if parallel_iv[hour][0].max() == 0:
                    # print hour
                    pass
                elif string_iv[hour][0].max() == 0:  # This is required in cases where one module gets sun and the next not
                    parallel_iv[hour] = np.array([0, 0])
                else:
                    # print hour
                    parallel_iv[hour] = connect.parallel_connect_string(parallel_iv[hour][0], parallel_iv[hour][1],
                                                                     string_iv[hour][0], string_iv[hour][1])
    # array_path = module_iv_folder + r"\parallel_string" + ".pkl"
    # data2pickle(parallel_iv, array_path)
    return parallel_iv


def calculate_yield(mpp_series, timestep=1, hoy_from=0, hoy_to=8759):
    """
    :param mpp_series: numpy array
    :param timestep: 
    :return: returns the cumulative energy yield of the considered time period.
    """
    energy_yield = np.sum(mpp_series[hoy_from:hoy_to+1] * timestep)
    return energy_yield


def calculate_losses(impp_series, cable_length, cable_cross_section=4, hoy_from=0, hoy_to=8759):
    specific_resistance = 0.017  # Ohm/mm2/m (Copper)
    losses = np.empty(len(impp_series))
    for timestep in range(len(impp_series)):
        losses[timestep] = specific_resistance * cable_length * cable_cross_section * impp_series[timestep] ** 2

    dc_losses = np.sum(losses[hoy_from:hoy_to+1])
    return dc_losses


def modules2parallel_tie(parallel_tie_arrangement, module_iv_folder):
    parallel_tie_number = 0
    for par_connection in parallel_tie_arrangement:

        count = 0
        for module_nr in par_connection:
            # do modules for each hour to prevent having to load the files over and over again.

            print "module" + str(module_nr)

            if count == 0:
                iv_connection = read_module(module_iv_folder, par_connection[0])

            else:

                module_iv = read_module(module_iv_folder, module_nr)

                for hour in range(len(iv_connection)):
                    if iv_connection[hour][0].max() == 0:
                        # print hour
                        pass  # A pass will leave the iv_string[hour] at zero
                    elif module_iv[hour][
                        0].max() == 0:  # This is required in cases where one module gets sun and the next not
                        iv_connection[hour] = np.array([0, 0])
                    else:
                        # print hour
                        iv_connection[hour] = connect.parallel_connect_string(iv_connection[hour][0],
                                                                              iv_connection[hour][1],
                                                                              module_iv[hour][0], module_iv[hour][1])
            count += 1

        # strings_in_array.append(iv_string)  # If this take too much memory. Save it in pickle format.
        parallel_tie_path = module_iv_folder + "\parallel_tie" + str(parallel_tie_number) + ".pkl"
        parallel_tie_number += 1
        data2pickle(iv_connection, parallel_tie_path)


def parallel_ties2array(parallel_tie_arrangement, module_iv_folder):
    for par_tie_nr in range(len(parallel_tie_arrangement)):
        if par_tie_nr == 0:
            iv_array = read_parallel_tie(module_iv_folder, par_tie_nr)
        else:
            string_iv = read_parallel_tie(module_iv_folder, par_tie_nr)

            for hour in range(len(iv_array)):
                if iv_array[hour][0].max() == 0:
                    # print hour
                    pass
                elif string_iv[hour][
                    0].max() == 0:  # This is required in cases where one module gets sun and the next not
                    iv_array[hour] = np.array([0, 0])

                else:
                    # print hour
                    iv_array[hour] = connect.series_connect_string(iv_array[hour][0], iv_array[hour][1],
                                                                   string_iv[hour][0], string_iv[hour][1])

    array_path = module_iv_folder + r"\array_TCT" + ".pkl"
    data2pickle(iv_array, array_path)
    return iv_array


def calculate_mpp(iv_data):
    """
    :param iv_data: 
    :return: 
    """
    dimension = len(iv_data)
    mpp_total = np.empty(dimension)
    i_mpp_total = np.empty(dimension)
    v_mpp_total = np.empty(dimension)
    for timestep in range(dimension):
        power = np.multiply(iv_data[timestep][0], iv_data[timestep][1])
        mpp = power.max()
        if mpp == 0:
            impp = 0
            vmpp = 0
        else:

            index = np.where(power == mpp)

            impp = iv_data[timestep][0][index]
            vmpp = iv_data[timestep][1][index]

        mpp_total[timestep] = mpp
        i_mpp_total[timestep] = impp
        v_mpp_total[timestep] = vmpp

    return mpp_total, i_mpp_total, v_mpp_total


def series_parallel(string_arrangement, module_iv_folder, recalculate=False, hoy_from=0, hoy_to=8759):
    if recalculate == True:
        modules2strings(string_arrangement, module_iv_folder)
    strings2array(string_arrangement, module_iv_folder)
    return calculate_yield(calculate_mpp(strings2array(string_arrangement, module_iv_folder))[0], hoy_from=hoy_from,
                           hoy_to=hoy_to)


# def series_parallel_with_dc_losses(string_arrangement, module_iv_folder, cable_length, recalculate=False,
#                                    cable_cross_section=4, hoy_from=0, hoy_to=8759):
#     if recalculate == True:
#         modules2strings(string_arrangement, module_iv_folder)
#     array_iv = strings2array(string_arrangement, module_iv_folder)
#     mpp, impp, vmpp = calculate_mpp(array_iv)
#     energy_yield = calculate_yield(mpp, hoy_from=hoy_from, hoy_to=hoy_to)
#     dc_losses = calculate_losses(impp, cable_length, cable_cross_section=cable_cross_section, hoy_from=hoy_from,
#                                  hoy_to=hoy_to)
#
#     return energy_yield, dc_losses


def series_parallel_with_dc_losses(modules_in_strings, strings_in_parallel , module_iv_folder, string_cable_lengths,
                                   parallel_cable_lengths, recalculate=False, cable_cross_section = 4, hoy_from=0,
                                   hoy_to=8759):
    """
    This function connects IV-curves of modules to IV curves of a series parallel arrays. Modules are connected to 
    strings, then strings are connected in parallel. In case of several parallel connections each leading to an 
    inverter, make sure to indicate which strings shall be connected in parallel.
    
    :param modules_in_strings: list of lists where every sublist consists of the module's numbers of one string
    :param strings_in_parallel: list of lists where every sublist consists of the string numbers connected in parallel
    :param moduel_iv_folder: filepath to the datafolder where the modules are stored
    :param string_cable_lengths: list containing the cable length of each string. has same length as modules_in_strings
    :param recalculate: Boolean, use True when string arrangement changed or new modules are used,
                        use False when only cable lengths are changed
    :param parallel_cable_lengths: list of cable lengths after the strings are connected in parallel. Length of list 
                                    must be euqal to number of inverters
    :param cable_cross_section: cable_cross_section in [mm2]
    :param hoy_from: hour of year when the simulation starts, default 0
    :param hoy_to: hour of year when the simulation ends, default 8759
    :return: Energy yield of the system and DC losses
    """

    """To improve:
            -string iv-curves are loaded from a file twice due to restrictions with the memory, 1.make file sizes 
             smaller, 2.only load once and use twice
    """

    if recalculate == True:
        modules2strings(modules_in_strings, module_iv_folder)

    parallel_connection_loss = []
    #  e.g. strings_in_parallel = [[0,1,2],[3,4,5]]
    #  e.g. parallel_connection = [0,1,2]
    sub_system_counter = 0
    for parallel_connection in strings_in_parallel:
        #  parallel_connection equals string numbers of this part of the system
        parallel_iv = strings_connect_parallel(parallel_connection, module_iv_folder)

        #  These are the maximum power values for shunt connected modules
        mpp, impp, vmpp = calculate_mpp(parallel_iv)

        # Calculate dc losses from each individual string:
        string_loss = []
        for string in parallel_connection:
        #  e.g. string = 0
            string_iv = read_string(module_iv_folder, string)
            i_values = interpolate_i_from_v(string_iv, vmpp)
            string_loss.append(calculate_losses(i_values, string_cable_lengths[string], cable_cross_section,
                                                hoy_from, hoy_to))


        dc_loss_in_parallel_cable = calculate_losses(impp, parallel_cable_lengths[sub_system_counter],
                                                     cable_cross_section, hoy_from, hoy_to)

        parallel_connection_loss.append(sum(string_loss)+dc_loss_in_parallel_cable)


    dc_losses = sum(parallel_connection_loss)
        #vmpp of the parallel connected system is the voltage at which all the strings are operated

    energy_yield = calculate_yield(mpp, hoy_from=hoy_from, hoy_to=hoy_to)

    return energy_yield, dc_losses



def interpolate_i_from_v(list_of_iv_curves, v):
    """
    This function interpolates the i value for a v value from iv-data
    :param list_of_iv_curves: [[[i],[v]],[[i],[v]],...]
    :param v: list of v values [v,v,...] (same length as list of iv curves
    :return: list of i values [i,i,...]
    """
    i = np.empty(len(v))
    counter=0
    for iv_curve in list_of_iv_curves:
         #  iv_curve[1] muss aufsteigend sein

        if iv_curve[0].size == 1:
            i[counter] = 0
            counter +=1
        else:
            i[counter] = np.interp(v[counter],iv_curve[1], iv_curve[0])
            counter +=1
    return i




def string_inverter(string_arrangement, module_iv_folder, recalculate=False, string_from=None, string_to=None,
                    hoy_from=0, hoy_to=8759):
    if string_from != None:
        strings = range(string_from, string_to + 1, 1)
    else:
        # Here it is assumed, that the strings were newly generated and all the strings of the string arrangment
        # will be considered.
        strings = range(len(string_arrangement))
    if recalculate == True:
        modules2strings(string_arrangement, module_iv_folder)
    string_mpp = []
    string_yield = np.empty(len(strings))
    counter = 0
    for string in strings:
        string_iv = read_string(module_iv_folder, string)  # Module is an integer from the initial module's list
        mpp = calculate_mpp(string_iv)[0]
        string_mpp.append(mpp)
        string_yield[counter] = calculate_yield(mpp, hoy_from=hoy_from, hoy_to=hoy_to)
        counter += 1
    total_yield = np.sum(string_yield)

    return total_yield


def string_inverter_with_dc_losses(string_arrangement, module_iv_folder, cable_lengths, cable_cross_section=4,
                                   recalculate=False, string_from=None, string_to=None, hoy_from=0, hoy_to=8759):
    if string_from != None:
        strings = range(string_from, string_to + 1, 1)
    else:
        # Here it is assumed, that the strings were newly generated and all the
        # strings of the string arrangment will be considered.
        strings = range(len(string_arrangement))
    if recalculate == True:
        modules2strings(string_arrangement, module_iv_folder)

    string_mpp = []
    string_yield = np.empty(len(strings))
    string_losses = np.empty(len(strings))
    counter = 0
    for string in strings:
        string_iv = read_string(module_iv_folder, string)  # Module is an integer from the initial module's list
        mpp, impp, vmpp = calculate_mpp(string_iv)
        string_mpp.append(mpp)
        string_yield[counter] = calculate_yield(mpp, hoy_from=hoy_from, hoy_to=hoy_to)
        string_losses[counter] = calculate_losses(impp, cable_lengths[counter], cable_cross_section, hoy_from=hoy_from,
                                                  hoy_to=hoy_to)
        counter += 1
    total_yield = np.sum(string_yield)
    total_losses = np.sum(string_losses)
    return total_yield, total_losses


def total_crosstied(parallel_tie_arrangement, module_iv_folder, recalculate=False, hoy_from=0, hoy_to=8759):
    if recalculate == True:
        modules2parallel_tie(parallel_tie_arrangement, module_iv_folder)
    parallel_ties2array(parallel_tie_arrangement, module_iv_folder)

    return calculate_yield(calculate_mpp(parallel_ties2array(parallel_tie_arrangement, module_iv_folder))[0],
                           hoy_from=hoy_from, hoy_to=hoy_to)


def total_crosstied_with_dc_losses(parallel_tie_arrangement, module_iv_folder, cable_length, cable_cross_section=4,
                                   recalculate=False, hoy_from=0, hoy_to=8759):
    """
    This function is based on the simplified assumptions, that the dc cabling losses occur mostly in the cables serially
    connecting the ties. There is only need of one cable length and cross section. The function is not suited for 
    detailed loss analysis.

    :param parallel_tie_arrangement: 
    :param module_iv_folder: 
    :param cable_length: 
    :param cable_cross_section: 
    :param recalculate: 
    :return: 
    """

    if recalculate == True:
        modules2parallel_tie(parallel_tie_arrangement, module_iv_folder)
    mpp, impp, vmpp = calculate_mpp(parallel_ties2array(parallel_tie_arrangement, module_iv_folder))
    energy_yield = calculate_yield(mpp, hoy_from=hoy_from, hoy_to=hoy_to)
    dc_losses = calculate_losses(impp_series=impp, cable_length=cable_length, cable_cross_section=cable_cross_section,
                                 hoy_from=hoy_from, hoy_to=hoy_to)
    return energy_yield, dc_losses


def module_inverter(module_list, module_iv_folder, hoy_from=0, hoy_to=8759):
    modules = module_list.flatten()
    print modules
    module_mpp = []
    module_yield = np.empty(len(modules))
    counter = 0
    for module in modules:
        module_iv = read_module(module_iv_folder, module)  # Module is an integer from the initial module's list
        mpp, impp, vmpp = calculate_mpp(module_iv)
        module_mpp.append(mpp)
        module_yield[counter] = calculate_yield(mpp, hoy_from=hoy_from, hoy_to=hoy_to)
        counter += 1
    total_yield = np.sum(module_yield)

    return total_yield


if __name__ == '__main__':

    current_directory = os.path.dirname(__file__)
    # module_iv_folder = os.path.join(current_directory, 'results\standard')  # This is where the simulated IV curves are stored.

    module_iv_folder = r"F:\Paper\Module-simulations\longi\unbypassed"

    # The string layout shows, how the strings are connected. Every sublist is a string.
    # For now, all strings are connected in parallel

    string_arrangement = [[50, 52, 53, 54, 55, 56, 57, 60],
                     [0, 1, 3, 26, 28, 44, 45, 47],
                     [30, 32, 34, 36, 37, 39, 41, 43],
                     [17, 19, 21, 23, 25, 27, 29, 31],
                     [33, 35, 38, 40, 42, 62, 65, 67],
                     [2, 4, 5, 8, 11, 46, 49],
                     [68, 69, 70, 71, 72, 73, 74],
                     [48, 51, 58, 59, 61, 64, 66],
                     [6, 9, 18, 20, 22, 24, 63],
                     [7, 10, 12, 13, 14, 15, 16]]

    connected_strings = [[0,1,2,3,4],[5,6,7,8,9]]
    cable_lengths = [24.26966766, 35.80156587, 21.5220064, 16.25342756, 43.74859659, 23.09968771, 20.14244473, 23.02407104, 36.1392263, 21.12497824]
    parallel_cable_lengths = [10,10]
    # string_arrangement = np.array([74])

    # string_arrangement = np.arange(0,75)
    print string_arrangement

    # print string_inverter(string_arrangement=string_arrangement, module_iv_folder=module_iv_folder, recalculate=True,
    #                       hoy_from=0, hoy_to=8759)
    #
    # print string_inverter_with_dc_losses(string_arrangement=string_arrangement,  module_iv_folder=module_iv_folder,
    #                                      recalculate=True, cable_lengths=cable_lengths, hoy_from=0, hoy_to=8759)

    # print series_parallel(string_arrangement, module_iv_folder, recalculate=True, hoy_from=0, hoy_to=8759)
    print series_parallel_with_dc_losses(string_arrangement, strings_in_parallel=connected_strings,
                                         module_iv_folder=module_iv_folder, string_cable_lengths=cable_lengths,
                                         parallel_cable_lengths=parallel_cable_lengths,  recalculate=False, hoy_from=0,
                                         hoy_to=8759)


    # print total_crosstied(string_arrangement, module_iv_folder, recalculate=True, hoy_from=0, hoy_to=8759)
    # print total_crosstied_with_dc_losses(string_arrangement,module_iv_folder, 15, recalculate=True, hoy_from=0,
    #                                      hoy_to=8759)

    # print module_inverter(string_arrangement, module_iv_folder, hoy_from=0, hoy_to=8759)
