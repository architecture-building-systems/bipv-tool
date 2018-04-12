import numpy as np
import pvlib.pvsystem as pvsyst
import interconnection as connect
import matplotlib.pyplot as plt


def calculate_reverse_scaling_factor(voltages, breakdown_voltage, miller_exponent):
    """
    :param voltages: numpy array of voltages
    :param breakdown_voltage: the minimum voltage before the avelanche breakdown happens
    :param miller_exponent: --> google
    :return: numpy array of according factors
    """
    reverse_scaling_factor = np.reciprocal(1. - np.power((np.absolute(voltages) / -breakdown_voltage), miller_exponent))
    return reverse_scaling_factor


def calculate_sub_cell_characteristics(irrad_on_subcells, evaluated_cell_voltages, num_subcells,
                                       reverse_scaling_factor, irrad_temp_lookup_np, t_ambient, irrad_noct, t_noct,
                                       t_a_noct, alpha_short_current, module_params, egap_ev):
    """

    :param irrad_on_subcells: 
    :param evaluated_voltages: 
    :param numcells: 
    :param irrad_temp_lookup_df: 
    :param irrad_noct: 
    :param t_noct: 
    :param t_a_noct: 
    :param alpha_short_current: 
    :param module_params: 
    :param egap_ev: 
    :return:    subcell_v_values: List of np arrays where a list of v-values is stored for every cell
                subcell_i_values,:List of np arrays where a list of v-values is stored for every cell
    """

    subcell_i_values = np.empty((len(irrad_on_subcells), len(
        evaluated_cell_voltages)))  # List of lists where a list of i-values is stored for every subcell
    subcell_v_values = np.empty((len(irrad_on_subcells), len(
        evaluated_cell_voltages)))  # List of lists where a list of v-values is stored for every cell, basically the same as for cells

    irrad_on_subcells_np = np.array(irrad_on_subcells)  # Take this out of the function
    sub_cell_irrad_np = np.rint(irrad_on_subcells_np).astype(int)  # Take this out of the function
    t_ambient = int(t_ambient)  # Take this out of the function

    temperature_row = irrad_temp_lookup_np[t_ambient + 25]  # +25 because row on is at -25Celsius

    for position, irradiance_value in np.ndenumerate(sub_cell_irrad_np):

        if not (temperature_row[irradiance_value,0,0] != temperature_row[irradiance_value,0,0]):  # Checks for NaNs
            subcell_i_values[position] = temperature_row[irradiance_value][0]  # should collect a numpy array
            subcell_v_values[position] = temperature_row[irradiance_value][1]  # should collect a numpy array

        else:
            if irradiance_value == 0:
                irradiance_value = 1

            t_cell = float(t_ambient) + float(irradiance_value) / irrad_noct * (t_noct - t_a_noct)  # t_cell in deg C
            desoto_values = pvsyst.calcparams_desoto(irradiance_value, t_cell, alpha_short_current, module_params,
                                                     egap_ev, 0.0001, 1, 1000, 25)
            # calcparams_desoto takes the temperature in degrees Celsius!
            photocurrent = desoto_values[0]  # [A]
            sat_current = desoto_values[1]  # [A]
            series_resistance = desoto_values[2]  # [Ohm]
            shunt_resistance = desoto_values[3]  # [Ohm]
            nnsvth = desoto_values[4]

            # Basic assumption here: Module IV-curve can be converted to a cell IV-curve by dividing the module voltage
            # by the number of cells further the subcell current is calculated by dividing currents by the number of
            # subcells.
            evaluated_subcell_currents = pvsyst.i_from_v(shunt_resistance, series_resistance, nnsvth,
                                                         evaluated_cell_voltages, sat_current, photocurrent)


            subcell_v_values[position] = evaluated_cell_voltages  # Save for later use

            # calculate the subcell forward and reverse characteristc
            subcell_current = np.multiply(evaluated_subcell_currents, reverse_scaling_factor) / num_subcells  # Numpy array

            subcell_i_values[position] = subcell_current  # Save for later use
            irrad_temp_lookup_np[t_ambient + 25][irradiance_value] = [subcell_current, evaluated_cell_voltages]

    return subcell_i_values, subcell_v_values


def sub_cells_2_cells(subcell_i_values, num_subcells):
    """
    :param subcell_i_values:  numpy array
    :param num_subcells: 
    :return: cell_i_values, numpy array
    simple reshaping can be used, because the subcell v values all have the same basis
    """
    cell_i_values = subcell_i_values.reshape((-1, num_subcells, len(subcell_i_values[0]))).sum(axis=1)
    return cell_i_values


def cells2substrings(cell_v_values_np, cell_i_values_np, cells_per_substring, number_of_substrings, max_i_module,
                     min_i_module, interpolation_resolution_submodules):
    """
    :param cell_v_values_np: numpy array of cell voltage values [[cell1values][cell2values] etc]
    :param cell_i_values_np: numpy array of cell current values [[cell1values][cell2values] etc]
    :param cells_per_substring: int, this value represents how many cells are in a substring = number of cells per 
            bypass diode
    :param number_of_substrings: int, here equal to number of bypass diodes 
    :param max_i_module: this is the maximum expected current in the module. Setting a value close above Isc prevents
            having huge unnecessary interpolations when connecting the cells.
    :param min_i_module: zero can be used as long as cells are not connected in parallel to other cells
    :return: returns numpy dtype object array with i and v values for each substring/submodule
    """
    i_connected_np = np.empty(number_of_substrings, dtype=object)
    v_connected_np = np.empty(number_of_substrings, dtype=object)

    for substring in range(number_of_substrings):  # iterate through all the substrings by number

        substring_v_values_np = cell_v_values_np[substring * cells_per_substring:(substring + 1) * cells_per_substring]
        substring_i_values_np = cell_i_values_np[substring * cells_per_substring:(substring + 1) * cells_per_substring]
        i_connected_np[substring], v_connected_np[substring] = connect.series_connect_multiple(substring_i_values_np,
                                                                                       substring_v_values_np,
                                                                                       max_i_module, min_i_module,
                                                                                    interpolation_resolution_submodules)
    return i_connected_np, v_connected_np


def bypass_diodes_on_substrings(substring_i_values_np, substring_v_values_np, number_of_substrings,
                                diode_saturation_current=1.0e-7, n_x_Vt=1.7e-2, numerical_diode_threshold=-1):
    """
    :param substring_i_values: numpy array dtype object
    :param substring_v_values: numpy array dtype object
    :param number_of_substrings: int, here equal to number of bypass diodes 
    :param diode_saturation_current: float, the saturation current of the modelled diode
    :param n_x_Vt: float, thermal voltage multiplied by the diode ideality factor
    :param numerical_diode_threshold: this is a value to speed up the calculation by not taking any values into account
            below this voltage and thereby not causing any overflow errors.
    :return: returns the parallel addition of the bypass diodes and the substring currents
    """

    diode_current = np.empty(number_of_substrings, dtype=object)  # List of np ndarrays for the current of each diode

    for substring in range(number_of_substrings):
        # Do diode calculations diode_current = 1.e-7*np.exp(-voltage_selected/1.7e-2) Where from??
        # diode_steps = np.empty(len(substring_v_values[substring]))

        substring_v_values_np[substring][substring_v_values_np[substring] < numerical_diode_threshold] = numerical_diode_threshold
        diode_steps = diode_saturation_current * np.exp(-substring_v_values_np[substring] / n_x_Vt)
        diode_current[substring]=diode_steps

    for substring in range(number_of_substrings):
        substring_i_values_np[substring] = np.add(substring_i_values_np[substring], diode_current[substring])

    return substring_i_values_np


def partial_shading(irrad_on_subcells, temperature=25, irrad_temp_lookup_np=None,
                    breakdown_voltage=-6.10, evaluated_module_voltages=None, simulation_parameters=None,
                    module_params=None):
    """
    This function returns the module IV curve of a module under any partial shading conditions or unequal irradiance.
    :param irrad_on_subcells: list, list of all irradiance values on the specific module (for one specific hour) make
                                sure that the dimensions of this list equals the number of cells or subcells that are
                                used for the module. E.G number of cells = 56, num_subcells=4 --> list length = 274
    :param temperature: float, Ambient temperature value for the given hour
    :param irrad_temp_lookup_df: 
    :param module_df: 
    :param module_name: 
    :param numcells: 
    :param n_bypass_diodes: 
    :param num_subcells: 
    :param vmax: 
    :param v_threshold: 
    :param breakdown_voltage: 
    :return: 
    """

    # Definition of constants, these are defined in hardcode because they are fixed:
    t_a_noct = 20  # [a,NOCT]
    irrad_noct = 800  # [W/m2]
    egap_ev = 1.12  # Band gap energy [eV]
    miller_exponent = 3  # This is set


    #For now here, change to parameters:
    max_i_module = module_params["max_module_current"]  # [A]
    min_i_module = module_params["min_module_current"] # [A], min value of interpolation in series connect
    n_bypass_diodes = module_params["number_of_bypass_diodes"]
    numcells = module_params["number_of_cells"]
    num_subcells = module_params["number_of_subcells"]

    interpolation_resolution_submodules = simulation_parameters["interpolation_resolution_submodules"]  # [A]
    interpolation_resolution_module = simulation_parameters["interpolation_resolution_module"]  # [A]
    final_module_iv_resolution = simulation_parameters["final_module_iv_resolution"]  # [A] or [V] counts for both dimensions



    if n_bypass_diodes > 0:
        cells_per_substring = numcells / n_bypass_diodes
    else:
        cells_per_substring = numcells

    if cells_per_substring % 1 != 0:
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

    alpha_short_current = module_params['alpha_short_current']
    t_noct = module_params['t_noct']

    evaluated_cell_voltages = evaluated_module_voltages / numcells  # Only divide by the number of cells

    reverse_scaling_factor = calculate_reverse_scaling_factor(evaluated_cell_voltages, breakdown_voltage, miller_exponent)

    t_ambient = temperature  # degC, if measured, use data here

    # Calculate sub_cell characteristic
    subcell_i_values, subcell_v_values = calculate_sub_cell_characteristics(irrad_on_subcells=irrad_on_subcells,
                                                                            evaluated_cell_voltages=evaluated_cell_voltages,
                                                                            num_subcells=num_subcells,
                                                                            reverse_scaling_factor=reverse_scaling_factor,
                                                                            irrad_temp_lookup_np=irrad_temp_lookup_np,
                                                                            t_ambient=t_ambient,
                                                                            irrad_noct=irrad_noct,
                                                                            t_noct=t_noct, t_a_noct=t_a_noct,
                                                                            alpha_short_current=alpha_short_current,
                                                                            module_params=module_params,
                                                                            egap_ev=egap_ev)

    # Calculate cell characteristics
    cell_i_values_np = sub_cells_2_cells(subcell_i_values, num_subcells)
    cell_v_values_np = np.tile(evaluated_cell_voltages, (numcells, 1))


    # Calculate basic substring characteristics
    i_connected_np, v_connected_np = cells2substrings(cell_v_values_np, cell_i_values_np, cells_per_substring,
                                                      n_bypass_diodes, max_i_module, min_i_module,
                                                      interpolation_resolution_submodules)

    # add bypass diode to sub_strings

    i_connected_np = bypass_diodes_on_substrings(substring_i_values_np=i_connected_np,
                                                 substring_v_values_np=v_connected_np,
                                                 number_of_substrings=n_bypass_diodes)

    # add sub_module voltages:

    i_module, v_module = connect.series_connect_multiple(i_connected_np, v_connected_np, max_i_module, min_i_module,
                                                         interpolation_resolution_module)

    i_module, v_module = connect.clean_curve([i_module, v_module], final_module_iv_resolution)

    print len(i_module)
    print len(v_module)
    plt.plot(v_module, i_module)
    plt.show()

    return i_module, v_module, irrad_temp_lookup_np



