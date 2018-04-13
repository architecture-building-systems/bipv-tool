import numpy as np

"""
This file contains functions that are able to interconnect IV-characteristics in series and parallel

at the moment several functions do the same on a different scale (cell or array) this shall be simplified to only two 
functions, one for parallel and one for series.


"""


def series_connect_multiple(multiple_i_values_np, multiple_v_values_np, upper_i_interpolation_threshold,
                            lower_i_interpolation_threshold, interpolation_resolution_grid_i_values):
    """
    :param multiple_i_values_np: 
    :param multiple_v_values_np: 
    :param minimum_voltage_of_return:  
    :return: 
    """

    for index in range(len(multiple_i_values_np)):
        multiple_i_values_np[index] = np.flipud(multiple_i_values_np[index]) # The flip is required for the interpolation
        multiple_v_values_np[index] = np.flipud(multiple_v_values_np[index])
        minimum = maximum = 0
        sublist_min = multiple_i_values_np[index].min()
        sublist_max = multiple_i_values_np[index].max()

        if sublist_min < minimum:
            minimum = sublist_min
        else:
            pass
        if sublist_max > maximum:
            maximum = sublist_max
        else:
            pass

    if maximum >= upper_i_interpolation_threshold:
        maximum = upper_i_interpolation_threshold  # Ampere
    else:
        pass

    if minimum <= lower_i_interpolation_threshold:
        minimum = lower_i_interpolation_threshold
    else:
        pass


    i_lin_np = np.linspace(minimum, maximum, num= int((maximum-minimum)/interpolation_resolution_grid_i_values))
    multiple_interp_v_values = np.empty(len(multiple_v_values_np), dtype=object)



    for index in range(len(multiple_v_values_np)):
        # Each index stands for one cell/submodule that is connected
        multiple_interp_v_values[index] = np.interp(i_lin_np, multiple_i_values_np[index], multiple_v_values_np[index])
    v_joined_flipped =  multiple_interp_v_values.sum(axis=0)



    # This last interpolation helps to distribute the datapoints also for nearly horizontal curves.
    v_joined = np.flipud(v_joined_flipped)
    i_lin_flipped = np.flipud(i_lin_np)
    voltage_min = v_joined.min()
    voltage_max = v_joined.max()
    v_lin_np = np.linspace(voltage_min, voltage_max, (voltage_max-voltage_min)/interpolation_resolution_grid_i_values)
    i_joined = np.interp(v_lin_np, v_joined, i_lin_flipped)


    return i_joined, v_lin_np


def series_connect_string(i1, v1, i2, v2):
    """
    :param i1: np array of currents that is available from the first iv-curve [A]
    :param v1: np array of voltages that is available from the first iv-curve [V]
    :param i2: np array of currents that is available from the second iv-curve [A]
    :param v2: np array of voltages that is available from the second iv-curve [V]
    :return: 2 np arrays, one of currents and one of voltages from the new iv-curve in [A] and [V]
    """

    # The values have to be flipped for the interpolation process
    i1np = np.flipud(i1)
    v1np = np.flipud(v1)
    i2np = np.flipud(i2)
    v2np = np.flipud(v2)

    # This conditional statement helps to keep the values in a realistic scope and therefore minimising the
    # calculation time. if the threshold is increased, then the num value has to be increased drastically
    if max(i1np.max, i2np.max) <= 30:
        i_lin_np = np.linspace( min(i1np.min(), i2np.min()),max(i1np.max(), i2np.max()),num=2000)
    else:
        i_lin_np = np.linspace(min(i1np.min(), i2np.min()), 30, num=2000)

    # This interpolation is needed to bring the two curves to the same current basis where the voltages can be added.
    v1interp = np.interp(i_lin_np,i1np, v1np,)
    v2interp = np.interp(i_lin_np, i2np, v2np)

    v3 = np.add(v1interp,v2interp)

    # This last interpolation helps to distribute the datapoint also for nearly horizontal curves.
    v3_flipped = np.flipud(v3)
    i_lin_np_flipped = np.flipud(i_lin_np)
    v_lin_np = np.linspace(v3.min(), v3.max(),3000)
    i3interp = np.interp(v_lin_np, v3_flipped, i_lin_np_flipped)

    return i3interp, v_lin_np



def parallel_connect_string(i1, v1, i2, v2):
    """
        :param i1: np array of currents that is available from the first iv-curve [A]
        :param v1: np array of voltages that is available from the first iv-curve [V]
        :param i2: np array of currents that is available from the second iv-curve [A]
        :param v2: np array of voltages that is available from the second iv-curve [V]
        :return: 2 np arrays, one of currents and one of voltages from the new iv-curve in [A] and [V]
        """

    # For the parallel case, the input i-v curves do not have to be flipped, since the interpolation will be on the
    # basis of voltage. The voltage is already ordered form low to high values.

    # This conditional statement helps to keep the values in a realistic scope and therefore minimising the
    # calculation time. if the threshold is increased, then the num value has to be increased drastically

    if min(v1.min, v2.min) >= -50:  # For arrays with long series connections this value is maybe too low
        v_lin_np = np.linspace(min(v1.min(), v2.min()), max(v1.max(), v2.max()), num=3000)
    else:
        v_lin_np = np.linspace(-50, max(v1.max, v2.max), num=3000)

    # This interpolation is needed to bring the two curves to the same voltage basis where the currents can be added.
    i1interp = np.interp(v_lin_np, v1, i1)
    i2interp = np.interp(v_lin_np, v2, i2)

    # here the addition of the curve takes place
    i3 = np.add(i1interp, i2interp)
    v3 = v_lin_np

    return i3, v3



def clean_curve(iv_curve, tolerance):

    pos = 0
    while(pos < len(iv_curve[0])-1):
        if (abs(iv_curve[0][pos]-iv_curve[0][pos+1]) < tolerance) and (abs(iv_curve[1][pos]-iv_curve[1][pos+1]) < tolerance):
            iv_curve = np.delete(iv_curve,pos+1,axis=1)
            # here no pos+=1 because we compare to the same again
        else:
            pos+=1
    return iv_curve



def rearrange_shading_pattern_miasole(irradiation_pattern, number_of_subcells):
    # The irradiation pattern is given in a list from module left to right, up to down.
    # The Miasole module has subcells that are connected in parallel first which requires to rearrange the pattern
    # e.g: [1,2,3,4,                                                                                        [1,5,9,
    #       5,6,7,8,        as the irradiation on subcells needs to be transformed to the following list:    2,6,10,
    #       9,10,11,12]                                                                                      3,7,11,
    #                                                                                                        4,8,12]
    new_pattern = []
    for i in range(len(irradiation_pattern) / number_of_subcells):
        for y in range(number_of_subcells):
            new_pattern.append(irradiation_pattern[y * len(irradiation_pattern) / number_of_subcells + i])
    return new_pattern