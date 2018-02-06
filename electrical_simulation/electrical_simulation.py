import pandas as pd
import os
import numpy as np
import miasole_module_two as ps
import pickle
import pvlib.pvsystem as pvsyst
"""
In the dataframe always 72 consecutive columns are representative for one module. Thereof these 72 irradiation
values are in the following order on the module:
        1,  2,  3,   4,  5,  6,  7,  8,  9, 10, 11, 12,
        13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
        25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36,
        37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48,
        49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60,
        61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72

For the miasole module it looks as follows:
        1,  2,  3,  4,  5,  6,  7,  8,  9,  10, 11, 12, 13, 14, 15, 16, 17, 18, 19, ..., 44,
        45, 46, 47, ..                                                                 , 88,
        ...                                                                              ...
        ...                                                                              ...
        177,....                                                                        ,220

So the resolution for the miasole is higher than for the HIT module. It has further be to be considered, that
in the miasole module the subcells have to be connected to cells first. So a new list with the input 
[1,45,99,..,177,2,46,...] has to be generated
Always take into account that in a list the value 1 will be stored at 0.
 """


def run_simulation(input_dataframe, num_cells_per_module, temperature_series, lookup_table, mod_temp_path,
                   module_start, module_end, database_path, module_name, bypass_diodes, subcells, num_irrad_per_module):
    """
    :param input_dataframe: irradiation on every cell/subcell
    :param num_cells_per_module: cells_per_module 
    :param temperature_series: 
    :param lookup_table: 
    :return: 
    """

    modules_in_df = (len(input_dataframe.columns) - 4) / num_irrad_per_module

    if database_path==None:
        print "Please add the module database path"

    # Data is looked up in CEC module database
    module_df = pvsyst.retrieve_sam(path=database_path)
    # e.g. [module0[hour0[i[],v[]]], module1[hour1[i[],v[]]], ..., modulen[hour8759[i[],v[]]]
    # basically for every module there is a sublist for hourly values, for each hour there is a sublist with i and v
    # a specific i or v list can be called as follows: modules_iv[module][hour][i/v]

    # for module in range(modules_in_df):
    for module in range(module_start, module_end + 1, 1):
        columns_from = module * num_irrad_per_module + 4  # The module data starts at column 4
        columns_to = columns_from + num_irrad_per_module - 1  # -1 because the column from already counts to the module
        module_df_temp = input_dataframe.loc[:, columns_from:columns_to]

        hourly_iv_curves = []
        for row in range(len(module_df_temp.index)):
            irradiation_on_module = module_df_temp.loc[row, :].tolist()
            # print irradiation_on_module
            if max(irradiation_on_module) == 0:  # Filter out the hours without irradiation

                i_module_sim = np.asarray(0)
                v_module_sim = np.asarray(0)
                hourly_iv_curves.append([i_module_sim, v_module_sim])
                print "hour = " + str(row)
            else:
                i_module_sim, v_module_sim, lookup_table = ps.partial_shading(irradiation_on_module,
                                                                              temperature=temperature_series[row],
                                                                              irrad_temp_lookup_df=lookup_table,
                                                                              module_df=module_df,
                                                                              module_name=module_name,
                                                                              numcells=num_cells_per_module,
                                                                              n_bypass_diodes=bypass_diodes,
                                                                              num_subcells=subcells)
                hourly_iv_curves.append([i_module_sim, v_module_sim])

                print "hour = " + str(row)

        # The results for each module are saved in a file. This is required to lower the memory consumption
        # of the program when a high amount of modules is considered
        module_path = mod_temp_path + "\module" + str(module) + ".pkl"

        with open(module_path, 'w') as f:
            pickle.dump(hourly_iv_curves, f)

        print "module done = " + str(module)

    return lookup_table


def results_to_csv(module_list, path):
    """

    :param module_list: 
    :param path: 
    :return: 
    """
    df = pd.DataFrame(module_list)
    df = df.transpose()
    df.to_csv(path, index_label='Hours')


if __name__ == '__main__':
    # Set the following parameters according to the problem.
    n_cells = 56
    bypass_diodes = 28
    module_name = 'MiaSole_Flex_03_120N'  # make sure the name is stated as in the database
    number_of_subcells = 23
    start_module = 13
    end_module = 14

    num_irrad_per_module = n_cells * number_of_subcells
    current_directory = os.path.dirname(__file__)
    irradiation_results_path = os.path.join(current_directory, r'data\sen_dir.ill')
    module_lookup_table_path = os.path.join(current_directory, r'data\lookup_mia.pkl')
    epw_path = os.path.join(current_directory, r'data\Zuerich_Kloten_2013.epw')
    module_temp_results = os.path.join(current_directory, 'results')
    database_path = os.path.join(current_directory, r'data\CEC_Modules.csv')

    # Import of data
    irradiation_complete_df = pd.read_csv(irradiation_results_path, sep=' ', header=None)
    module_lookuptable = pd.read_pickle(module_lookup_table_path)
    module_lookuptable = module_lookuptable.astype('object')
    weatherfile = pd.read_csv(epw_path, skiprows=8, header=None)
    temperature = weatherfile[6].tolist()

    # Calculation of all module IV-curves
    module_lookuptable = run_simulation(irradiation_complete_df, n_cells, temperature,
                                                        module_lookuptable, module_temp_results, start_module,
                                                        end_module, database_path, module_name, bypass_diodes,
                                                        number_of_subcells, num_irrad_per_module)

    with open(module_lookup_table_path, 'w') as f:
        pickle.dump(module_lookuptable, f)







