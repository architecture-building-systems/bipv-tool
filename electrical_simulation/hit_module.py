import numpy as np
import pandas as pd
import pvlib.pvsystem as pvsyst
import interconnection as connect



def partial_shading(irrad_on_cells, temperature=25, irrad_temp_lookup_df=None, module_database_path=None,
                    module_name='Sanyo_Electric_of_Panasonic_Group_VBHN240SA11', numcells=72, n_bypass_diodes=3,
                    num_subcells=0):
    # Definition of constants:
    q = 1.60217662e-19  # Electron Charge[Coulombs]
    k_boltzmann = 1.38064852e-23  # [J/K]
    t_a_noct = 20  # [a,NOCT]
    irrad_noct = 800  # [W/m2]
    egap_ev = 1.12  # Band gap energy [eV]

    if num_subcells!=1:
        print 'Do not use this script for subcell level'

    if n_bypass_diodes > 0:
        cells_per_substring = numcells/n_bypass_diodes
    else:
        cells_per_substring = numcells

    if cells_per_substring%1 != 0:
        print "WARNING: Number of bypass diodes or number of cells is wrong."
    else:
        pass

    if module_database_path==None:
        print "Please add the module database path"
    # Data is looked up in CEC module database
    module_df = pvsyst.retrieve_sam(path=module_database_path)
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


    vmin = -14.35*numcells  # [V] This value is very sensitive. Special attention has to be paid when working at
                            # low irradiation levels with low temperatures. A value which is too high will make the
                            # PVLIB i_from_v function to fail and will add NaNs into the array which will lead to
                            # problems in the connection of cells and modules
    vmax = 60  # [V]
    evaluated_voltages = np.arange(vmin, vmax, 0.1)  # The step chosen here is an initial step, it will be altered with

    # reverse scaling factor for each voltage step is calculated.
    breakdown_voltage = -14.5  # Von der Zelle oder vom Modul?
    miller_exponent = 3  # This is set. Maybe put this part to the start of the code.
    cell_voltage = evaluated_voltages/numcells

    reverse_scaling_factor = np.empty(len(cell_voltage))
    for pos, v in np.ndenumerate(cell_voltage):
        reverse_scaling_factor[pos] = (1. / (1. - (abs(v) / -breakdown_voltage) ** miller_exponent))

    cell_v_values = []  # List of lists where a list of v-values is stored for every cell
    cell_i_values = []  # List of lists where a list of i-values is stored for every cell
    t_ambient = temperature  # degC, if measured, use data here

    for cell_irrad in irrad_on_cells:

        # By making the irradiation an temperature to integers, the funcionality of the lookup table is ensured.
        # Daysim irradiation results should normally be given as integers anyway
        cell_irrad = int(cell_irrad)
        t_ambient = int(t_ambient)

        value_from_table = irrad_temp_lookup_df.loc[t_ambient,str(cell_irrad)]  # the column is called by its name, which is a string

        if not(value_from_table!=value_from_table):  # Checks for NaNs
            new_cell_current = value_from_table[0]  #should collect a numpy array
            new_cell_voltage = value_from_table[1]  #should collect a numpy array

            cell_i_values.append(new_cell_current)
            cell_v_values.append(new_cell_voltage)


        else:
            #An irradiation of >0 is required to get an IV curve. Night hours are excluded earlier
            if cell_irrad == 0:
                cell_irrad_calc = 1
            else:
                cell_irrad_calc = cell_irrad

            t_cell = float(t_ambient) + ((float(cell_irrad_calc)/irrad_noct)*(t_noct - t_a_noct))  # t_cell in deg C
            desoto_values = pvsyst.calcparams_desoto(cell_irrad_calc, t_cell, alpha_short_current, module_params,
                                                     egap_ev, 0.0001, 1,
                                                     1000, 25)  # delta Bandgap should be included as a variable
            # calcparams_desoto takes the temperature in degrees Celsius!
            photocurrent = desoto_values[0]  # [A]
            sat_current = desoto_values[1]  # [A]
            series_resistance = desoto_values[2]  # [Ohm]
            shunt_resistance = desoto_values[3]  # [Ohm]
            nnsvth = desoto_values[4]

            # Basic assumption here: Module IV-curve can be converted to a cell IV-curve by dividing the module voltage
            # by the number of cells
            evaluated_currents = np.empty(len(evaluated_voltages))  #should be a numpy array
            for pos, v in np.ndenumerate(evaluated_voltages):
                current_temp = pvsyst.i_from_v(shunt_resistance, series_resistance, nnsvth, v,
                                               sat_current, photocurrent)
                evaluated_currents[pos] = current_temp

            # calculate the cell forward and reverse characteristic

            cell_current = np.multiply(evaluated_currents, reverse_scaling_factor)


            # The clean_curve removes unnecessary values and helps saving space in the lookup table
            new_cell_current, new_cell_voltage = connect.clean_curve([cell_current,cell_voltage], 0.01)

            cell_v_values.append(new_cell_voltage)  # Save for later use
            cell_i_values.append(new_cell_current)  # Save for later use
            #Save values to lookup-table:  (the column is called by its name, which is a string)

            result = [new_cell_current, new_cell_voltage]
            irrad_temp_lookup_df.set_value(t_ambient, str(cell_irrad), result)




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

        for substring in range(n_bypass_diodes):  # iterate through all the substrings by number
            i_connected_substring = cell_i_values[cell_counter]  #np array
            v_connected_substring = cell_v_values[cell_counter]  #np array
            cell_counter+=1

            for cell in range(cells_per_substring-1):

                i_connected_substring, v_connected_substring = connect.series_connect_cell2substring(i_connected_substring,
                                                                                                     v_connected_substring,
                                                                                                     cell_i_values[cell_counter],
                                                                                                     cell_v_values[cell_counter])
                cell_counter+=1

            i_connected.append(i_connected_substring)
            v_connected.append(v_connected_substring)

        #add bypass diode to sub_strings
        diode_current = [] #List of np arrays for the current of each diode
        for substring in range(n_bypass_diodes):
            #Get rid of insignificant values and values that cause an overflow in the diode equation:
            iv_dataframe = pd.DataFrame({'i':i_connected[substring], 'v':v_connected[substring]})
            new_iv_dataframe = iv_dataframe[iv_dataframe['v']>-5.0] #Delete all values below -5Volts
            i_connected[substring] = new_iv_dataframe['i'].values
            v_connected[substring] = new_iv_dataframe['v'].values

            #Do diode calculations diode_current = 1.e-7*np.exp(-voltage_selected/1.7e-2) Where from??
            diode_steps = np.empty(len(v_connected[substring]))

            for pos, v in np.ndenumerate(v_connected[substring]):
                diode_steps[pos] = (10e-5*np.expm1(-v/(1.5*25e-3)))
            diode_current.append(diode_steps)


        for substring in range(n_bypass_diodes):
            i_connected[substring] = np.add(i_connected[substring], diode_current[substring])

        # add sub_module voltages:
        i_module = i_connected[0]
        v_module = v_connected[0]

        for substring in range(n_bypass_diodes-1):
            i_module, v_module = connect.series_connect(i_module, v_module, i_connected[substring+1],
                                                        v_connected[substring+1]) #This includes a clean curve

    # Returns tow np.arrays i_module and v_module as well as the lookup table of the cells
    return i_module, v_module, irrad_temp_lookup_df



