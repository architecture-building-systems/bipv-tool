import numpy as np
import pandas as pd
import pvlib.pvsystem as pvsyst
import matplotlib.pyplot as plt
import interconnection as connect
import time



def partial_shading(irrad_on_subcells, temperature=25, irrad_temp_lookup_df=None, module_df=None,
                    module_name='MiaSole_Flex_03_120N', numcells=56, n_bypass_diodes=28, num_subcells=4):


    # Definition of constants:
    q = 1.60217662e-19  # Electron Charge[Coulombs]
    k_boltzmann = 1.38064852e-23  # [J/K]
    t_a_noct = 20  # [a,NOCT]
    irrad_noct = 800  # [W/m2]
    egap_ev = 1.12  # Band gap energy [eV]

    if n_bypass_diodes > 0:
        cells_per_substring = numcells/n_bypass_diodes
    else:
        cells_per_substring = numcells

    if cells_per_substring%1 != 0:
        print "WARNING: Number of bypass diodes or number of cells is wrong."
    else:
        pass


    # Rearrange irrad_on_subcells
    irrad_on_subcells = connect.rearrange_shading_pattern_miasole(irrad_on_subcells, num_subcells)



    # a_ref = modified diode ideality factor at STC
    # I_L_ref = photocurrent at STC [A]
    # I_o_ref = diode reverse saturation current [A]
    # R_sh_ref = Shunt resistance at STC [Ohm]
    # R_s = Series resistance at STC [Ohm]
    module_params = {'a_ref':module_df[module_name]['a_ref'], 'I_L_ref':module_df[module_name]['I_L_ref'],
                     'I_o_ref':module_df[module_name]['I_o_ref'], 'R_sh_ref':module_df[module_name]['R_sh_ref'],
                     'R_s':module_df[module_name]['R_s']}
    alpha_short_current = module_df[module_name]['alpha_sc']
    t_noct = module_df[module_name]['T_NOCT']


    vmin = -6.05*numcells  # [V] This value is very sensitive. Special attention has to be paid when working at
                            # low irradiation levels with low temperatures. A value which is too high will make the
                            # PVLIB i_from_v function to fail and will add NaNs into the array which will lead to
                            # problems in the connection of cells and modules
    vmax = 50.0  # [V]

    v_threshold = -1  # Volts, this threshold is used to delte datapaoints that will later on become unnecessary due to the bypass diode.

    evaluated_voltages = np.arange(vmin, vmax, 0.1)  # The step used here strongly influences the calculation time

    # reverse scaling factor for each voltage step is calculated.
    breakdown_voltage = -6.10  # Von der Zelle oder vom Modul?
    miller_exponent = 3  # This is set. Maybe put this part to the start of the code.
    subcell_voltage = evaluated_voltages/numcells  # Only divide by the number of cells

    reverse_scaling_factor = np.empty(len(subcell_voltage))
    for pos, v in np.ndenumerate(subcell_voltage):
        reverse_scaling_factor[pos] = (1. / (1. - (abs(v) / -breakdown_voltage) ** miller_exponent))

    subcell_i_values = []  # List of lists where a list of i-values is stored for every subcell
    subcell_v_values = []  # List of lists where a list of v-values is stored for every cell, basically the same as for cells

    t_ambient = temperature  # degC, if measured, use data here


    for sub_cell_irrad in irrad_on_subcells:

        # By making the irradiation an temperature to integers, the funcionality of the lookup table is ensured.
        # Daysim irradiation results should normally be given as integers anyway
        sub_cell_irrad = int(sub_cell_irrad)
        subcell_voltage = evaluated_voltages / numcells
        t_ambient = int(t_ambient)

        value_from_table = irrad_temp_lookup_df.loc[t_ambient,str(sub_cell_irrad)]

        if not(value_from_table!=value_from_table):  # Checks for NaNs
            sub_cell_current = value_from_table[0]  #should collect a numpy array
            sub_cell_voltage = value_from_table[1]  #should collect a numpy array

            subcell_i_values.append(sub_cell_current)
            subcell_v_values.append(sub_cell_voltage)

        else:
            #An irradiation of >0 is required to get an IV curve. Night hours are excluded earlier
            if sub_cell_irrad == 0:
                sub_cell_irrad_calc = 1
            else:
                sub_cell_irrad_calc = sub_cell_irrad

            t_cell = float(t_ambient) + float(sub_cell_irrad_calc)/irrad_noct*(t_noct - t_a_noct)  # t_cell in deg C
            desoto_values = pvsyst.calcparams_desoto(sub_cell_irrad_calc, t_cell, alpha_short_current, module_params,
                                                     egap_ev, 0.0001, 1,
                                                     1000, 25)  # delta Bandgap should be included as a variable
            # calcparams_desoto takes the temperature in degrees Celsius!
            photocurrent = desoto_values[0]  # [A]
            sat_current = desoto_values[1]  # [A]
            series_resistance = desoto_values[2]  # [Ohm]
            shunt_resistance = desoto_values[3]  # [Ohm]
            nnsvth = desoto_values[4]

            # Basic assumption here: Module IV-curve can be converted to a cell IV-curve by dividing the module voltage
            # by the number of cells further the subcell current is calculated by dividing currents by the number of
            # subcells.
            evaluated_currents = np.empty(len(evaluated_voltages))
            for pos, v in np.ndenumerate(evaluated_voltages):
                current_temp = pvsyst.i_from_v(shunt_resistance, series_resistance, nnsvth, v,
                                               sat_current, photocurrent)
                evaluated_currents[pos] = current_temp


            subcell_v_values.append(subcell_voltage)  # Save for later use

            # calculate the subcell forward and reverse characteristc

            subcell_current = np.multiply(evaluated_currents, reverse_scaling_factor)/num_subcells  # Numpy array


            subcell_i_values.append(subcell_current)  # Save for later use
            result = [subcell_current, subcell_voltage]
            irrad_temp_lookup_df.set_value(t_ambient, str(sub_cell_irrad), result)
            # Save values to lookup-table:  (the column is called by its name, which is a string)

    cell_v_values = []  # List of np arrays where a list of v-values is stored for every cell
    cell_i_values = []  # List of np arrays where a list of i-values is stored for every cell

    sub_cell_counter = 0
    # cell_v_values = subcell_v_values
    for cell in range(numcells):  # Since the voltage steps will remain the same for cell and subcell, all the currents of the subcells can simply be summed.
        i_sum_of_subcells = subcell_i_values[sub_cell_counter]  # numpy array from list
        sub_cell_counter+=1
        for subcell in range(num_subcells-1):  # -1, weil die erste sub_cell schon zuvor einbezogen wird

            i_sum_of_subcells = np.add(i_sum_of_subcells, subcell_i_values[sub_cell_counter])  # addition of two np arrays
            sub_cell_counter+=1


        cell_i_values.append(i_sum_of_subcells)
        cell_v_values.append(subcell_voltage) #Because currents were calculated from voltages and so far all the iv curves have the same voltage base.
    # Module calculations



    #without bypass diode:
    if n_bypass_diodes==0:
        i_connected = cell_i_values[0]
        v_connected = cell_v_values[0]
        for cell in range(numcells-1):
            i_connected, v_connected = connect.series_connect(i_connected, v_connected, cell_i_values[cell+1],
                                                               cell_v_values[cell+1])

    #with bypass diode:
    else:

        #calculate the iv curve for each substring. With bypass diode this will be a list of lists for each substring
        i_connected = []  # list of numpy arrays
        v_connected = []  # list of numpy arrays
        cell_counter = 0

        cell_v_values_np = np.array(cell_v_values)
        cell_i_values_np = np.array(cell_i_values)

        for substring in range(n_bypass_diodes):  # iterate through all the substrings by number

            substring_v_values_np = cell_v_values_np[substring*cells_per_substring:(substring+1)*cells_per_substring]
            substring_i_values_np = cell_i_values_np[substring*cells_per_substring:(substring+1)*cells_per_substring]
            i_connected_substring, v_connected_substring = connect.series_connect_multiple(substring_i_values_np, substring_v_values_np, v_threshold)

            i_connected.append(i_connected_substring)
            v_connected.append(v_connected_substring)


        #add bypass diode to sub_strings
        diode_current = [] #List of np arrays for the current of each diode
        for substring in range(n_bypass_diodes):

            #Do diode calculations diode_current = 1.e-7*np.exp(-voltage_selected/1.7e-2) Where from??
            diode_steps = np.empty(len(v_connected[substring]))

            for pos, v in np.ndenumerate(v_connected[substring]):
                # The if statement is case specific here to save time. Remove when use as flexible tool.
                if v <-1:
                    diode_steps[pos] = 100
                else:
                    diode_steps[pos] = (1.e-7*np.exp(-v/1.7e-2))
            diode_current.append(diode_steps)




        for substring in range(n_bypass_diodes):
            i_connected[substring] = np.add(i_connected[substring], diode_current[substring])

            # plt.plot(v_connected[substring],i_connected[substring])
            # plt.show()


        # add sub_module voltages:

        i_module, v_module = connect.series_connect_multiple(i_connected, v_connected, -7.5)

    i_module, v_module = connect.clean_curve([i_module,v_module], 0.2)
    # Returns tow np.arrays i_module and v_module as well as the lookup table of the cells

    print len(i_module)
    print len(v_module)

    return i_module, v_module, irrad_temp_lookup_df



