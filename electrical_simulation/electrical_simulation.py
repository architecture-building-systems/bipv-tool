import pandas as pd
import os
import numpy as np
import miasole_module_two as ps
import pickle
import pvlib.pvsystem as pvsyst
import time
import multiprocessing
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

def simulation_multiprocessing(module, num_irrad_per_module, irradiation_complete_df, module_result_path,
                               temperature_series, module_lookuptable_np, cell_breakdown_voltage,
                               evaluated_module_voltages, simulation_parameters, module_params):

    columns_from = module * num_irrad_per_module + 4  # The module data starts at column 4
    columns_to = columns_from + num_irrad_per_module - 1  # -1 because the column from already counts to the module
    module_df_temp = irradiation_complete_df.loc[:, columns_from:columns_to]

    hourly_iv_curves = []
    for row in range(len(module_df_temp.index)):
        irradiation_on_module = module_df_temp.loc[row, :].tolist()
        i_module_sim, v_module_sim, lookup_table = simulate_one_hour(irradiation_on_module=irradiation_on_module,
                                                                     hour_temperature=temperature_series[row],
                                                                     lookup_table=module_lookuptable_np,
                                                                     breakdown_voltage=cell_breakdown_voltage,
                                                                     evaluated_module_voltages=evaluated_module_voltages,
                                                                     simulation_parameters=simulation_parameters,
                                                                     module_params=module_params)

        hourly_iv_curves.append([i_module_sim, v_module_sim])
        # print "hour = " + str(row)

    module_path = module_result_path + "\module" + str(module) + ".pkl"
    with open(module_path, 'w') as f:
        pickle.dump(hourly_iv_curves, f)

    print "module done = " + str(module)



def simulate_one_hour(irradiation_on_module, hour_temperature, lookup_table, breakdown_voltage,
                      evaluated_module_voltages, simulation_parameters, module_params):

    if max(irradiation_on_module) == 0:  # Filter out the hours without irradiation

        i_module_sim = np.asarray(0)
        v_module_sim = np.asarray(0)

    else:
        i_module_sim, v_module_sim, lookup_table = ps.partial_shading(irradiation_on_module,
                                                                      temperature=hour_temperature,
                                                                      irrad_temp_lookup_np=lookup_table,
                                                                      breakdown_voltage=breakdown_voltage,
                                                                      evaluated_module_voltages=evaluated_module_voltages,
                                                                      simulation_parameters=simulation_parameters,
                                                                      module_params=module_params)

    return i_module_sim, v_module_sim, lookup_table


if __name__ == '__main__':


    ### ============= DEFINITION OF THE SYSTEM ====================== ###

    # ------ Module Parameters ------ #
    bypass_diodes = 28
    module_name = 'MiaSole_Flex_03_120N'  # make sure the name is stated as in the database
    number_of_subcells = 4
    cell_breakdown_voltage = -6.10  # [V] This value is usually not found in documentations.

    # ------ Simulation Parameters ------ #

    # Check out which of these parameters can be taken directly from the database
    start_module = 0
    end_module = 13
    analysis_resolution_module = 0.56  #
    interpolation_resolution_module = 0.12  # [A]
    interpolation_resolution_submodules = 0.03  # [A] could be chosen as interpolatiom_res_module/numcell
    final_module_iv_resolution=0.2  # [A] or [V] counts for both dimensions, this is for the final "curve cleaning"

    round_irradiance_to_ten = True # If this is set to True, the irradiance values will be rounded to the nearest ten
                                    # value which saves memory and speeds up the calculation

    # -------- Filepaths --------- #
    current_directory = os.path.dirname(__file__)
    irradiation_results_path = os.path.join(current_directory, r'data\sen_dir.ill')
    module_lookup_table_path = os.path.join(current_directory, r'data\lookup_mia.npy')
    epw_path = os.path.join(current_directory, r'data\Zuerich_Kloten_2013.epw')
    module_result_path = os.path.join(current_directory, 'results')
    database_path = os.path.join(current_directory, r'data\CEC_Modules.csv')


    ### =============================================================== ###








    ### ===== Fixed Parameters ====== ###
    # This value decides, in the interconnection of cells to submodules or submodules to modules, how far negative
    # currents shall maximally be considered. A slightly negative value is chosen to make sure, the IV curve
    # crosses the voltage axes.
    min_module_current = -0.5  #[A]
    ### ============================= ###



    simulation_parameters = {"start_module":start_module,
                             "end_module":end_module,
                             "cell_bd_voltage":cell_breakdown_voltage,
                             "analysis_resolution":analysis_resolution_module,
                             "interpolation_resolution_module":interpolation_resolution_module,
                             "interpolation_resolution_submodules":interpolation_resolution_module,
                             "final_module_iv_resolution":final_module_iv_resolution,
                             "round_irradiance_to_ten":round_irradiance_to_ten}


    # Data is looked up in CEC module database
    module_df = pvsyst.retrieve_sam(path=database_path)
    module_params = {'a_ref': module_df[module_name]['a_ref'],
                     'I_L_ref': module_df[module_name]['I_L_ref'],
                     'I_o_ref': module_df[module_name]['I_o_ref'],
                     'R_sh_ref': module_df[module_name]['R_sh_ref'],
                     'R_s': module_df[module_name]['R_s'],
                     'number_of_cells': module_df[module_name]['N_s'],
                     'number_of_subcells': number_of_subcells,
                     'alpha_short_current': module_df[module_name]['alpha_sc'],
                     't_noct': module_df[module_name]['T_NOCT'],
                     'number_of_bypass_diodes': bypass_diodes,
                     'max_module_current': 1.2*module_df[module_name]['I_sc_ref'],
                     "min_module_current": min_module_current,
                     'max_module_voltage': 1.35*module_df[module_name]['V_oc_ref']}

    # a_ref = modified diode ideality factor at STC
    # I_L_ref = photocurrent at STC [A]
    # I_o_ref = diode reverse saturation current [A]
    # R_sh_ref = Shunt resistance at STC [Ohm]
    # R_s = Series resistance at STC [Ohm]



    # Import of data
    irradiation_complete_df = pd.read_csv(irradiation_results_path, sep=' ', header=None, dtype=np.float16)

    weatherfile = pd.read_csv(epw_path, skiprows=8, header=None)
    temperature_series = weatherfile[6].tolist()

    if round_irradiance_to_ten == True:
        irradiation_complete_df = irradiation_complete_df.round(-1)
    else:
        pass




    vmin_module= 0.99*cell_breakdown_voltage*module_params['number_of_cells']


    evaluated_module_voltages = np.arange(vmin_module, module_params['max_module_voltage'], analysis_resolution_module)
    # evaluated_module_voltages = np.arange(-338.8, 200, 0.1)

    ### Create lookup table
    if round_irradiance_to_ten == True:
        module_lookuptable_np = np.empty((75, 120, 2, len(evaluated_module_voltages)))
        module_lookuptable_np[:] = np.nan

    else:
        # Ambient Temperature -25 to 49 Celsius and Irrad vrom 0 to 1199 W/m2
        module_lookuptable_np = np.empty((75,1200,2,len(evaluated_module_voltages)))
        module_lookuptable_np[:] = np.nan

    print "Lookup table has been created"

    start_time = time.time()

    # Calculation of all module IV-curves
    if database_path==None:
        print "Please add the module database path"




    num_irrad_per_module = module_params['number_of_cells'] * module_params['number_of_subcells']

    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count()-1)

    for module in range(start_module, end_module + 1, 1):

        # simulation_multiprocessing(module, num_irrad_per_module, irradiation_complete_df, module_result_path,
        #                            temperature_series, module_lookuptable_np, cell_breakdown_voltage,
        #                            evaluated_module_voltages, simulation_parameters, module_params)
        #
        pool.apply_async(simulation_multiprocessing,args=(module, num_irrad_per_module, irradiation_complete_df,
                                                            module_result_path, temperature_series,
                                                            module_lookuptable_np, cell_breakdown_voltage,
                                                            evaluated_module_voltages, simulation_parameters,
                                                            module_params))

    pool.close()
    pool.join()





    print "finishing time"
    print time.time()-start_time







