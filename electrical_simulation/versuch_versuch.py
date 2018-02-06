import pandas as pd
import numpy as np
import json
import datetime
import miasole_module_two as ps
import pvlib.pvsystem as pvsyst
#import shaded_miasole as ps
import interconnection as connect
import matplotlib.pyplot as plt


def get_irradiation_value(path, time, sensor_name):
    time = time.replace(second=0)
    irrad_data_df = pd.read_excel(path)
    irrad_data_df['Time'] = pd.to_datetime(irrad_data_df['Time'])
    irrad_data_df.set_index('Time', inplace=True)
    irrad = irrad_data_df.iloc[irrad_data_df.index.get_loc(time, method='nearest')][sensor_name]
    return int(round(irrad,0))

def get_temperature(path, time, sensor_name):
    time = time.replace(second=0)
    irrad_data_df = pd.read_excel(path)
    irrad_data_df['Time'] = pd.to_datetime(irrad_data_df['Time'])
    irrad_data_df.set_index('Time', inplace=True)
    temp = irrad_data_df.iloc[irrad_data_df.index.get_loc(time, method='nearest')][sensor_name]
    return round(temp,0)


def align_yaxis(ax1, v1, ax2, v2):
    """adjust ax2 ylimit so that v2 in ax2 is aligned to v1 in ax1"""
    _, y1 = ax1.transData.transform((0, v1))
    _, y2 = ax2.transData.transform((0, v2))
    inv = ax2.transData.inverted()
    _, dy = inv.transform((0, 0)) - inv.transform((0, y1-y2))
    miny, maxy = ax2.get_ylim()
    ax2.set_ylim(miny+dy, maxy+dy)


def create_irradiation_list(irradiation, shade_pattern, partially_shaded_irrad):
    irradiation_on_cells = []
    for i in range(len(shade_pattern)):
        if shade_pattern[i] ==1:
            irradiation_on_cells.append(irradiation)
        elif shade_pattern[i] == 0:
            irradiation_on_cells.append(1) #not zero because the IV-curve simulator cannot handle 0
        elif shade_pattern[i] == 2:
            irradiation_on_cells.append(partially_shaded_irrad)
        else:
            print "The shading pattern hasn't been defined correctly"
    return irradiation_on_cells

def get_measured_iv_curves_from_excel(filepath):
        iv_df = pd.read_excel(filepath, header=17)
        v_data = np.array(iv_df['U in V'].tolist())
        i_data = np.array(iv_df['I in A'].tolist())
        return i_data, v_data


def get_shading_pattern(filepath):
    with open(filepath, 'r')as jfile:
        return json.load(jfile)



def rearrange_shading_pattern(irradiation_pattern, number_of_subcells):
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

#This function finds the MPP for the measured data using the lists of I and V of the object
def get_mpp(self):
    mpp =0
    for counter in range(len(self.v_data)):
        if self.v_data[counter] * self.i_data[counter] > mpp:
            mpp = self.v_data[counter] * self.i_data[counter]
            self.mpp_voltage = self.v_data[counter]
            self.mpp_current = self.i_data[counter]
        else:
            pass
    self.mpp = mpp



if __name__ == "__main__":





    module_lookup_table_path = 'C:\Users\walkerl\Documents\MA_Local\Electrical_simulation\lookup\MIA_lookup.pkl'
    lookup_table = pd.read_pickle(module_lookup_table_path)
    lookup_table = lookup_table.astype('object')
    number_of_subcells = 5

    shading_string = 'completely shaded'  #This variable does not change calculations but will app
    irradiation_path = 'C:\Users\walkerl\Documents\MA_Local\Versuche\Messungen_17_08_15\meas_irrad.xlsx'
    time = datetime.datetime(2017,8,15,11,40,16)
    temp_sensor_name = 'RTD3'

    ambient_temperature = get_temperature(irradiation_path, time, temp_sensor_name)


    if time.minute < 10:
        measurement_path = r'C:\Users\walkerl\Documents\MA_Local\Versuche\Messungen_17_08_15\15-08-2017  ' + \
                           str(time.hour)+ '_0' + str(time.minute) + '_' + str(time.second)
        measurement_data_path = measurement_path + '.XLS'
        shading_pattern_path = measurement_path + "_shading.json"
    elif time.second < 10:
        measurement_path = r'C:\Users\walkerl\Documents\MA_Local\Versuche\Messungen_17_08_15\15-08-2017  ' + \
                           str(time.hour) + '_' + str(time.minute) + '_0' + str(time.second)
        measurement_data_path = measurement_path + '.XLS'
        shading_pattern_path = measurement_path + "_shading.json"

    elif time.second < 10 and time.minute < 10:
        measurement_path = r'C:\Users\walkerl\Documents\MA_Local\Versuche\Messungen_17_08_15\15-08-2017  ' + \
                           str(time.hour) + '_0' + str(time.minute) + '_0' + str(time.second)
        measurement_data_path = measurement_path + '.XLS'
        shading_pattern_path = measurement_path + "_shading.json"

    else:
        measurement_path = r'C:\Users\walkerl\Documents\MA_Local\Versuche\Messungen_17_08_15\15-08-2017  ' + \
                           str(time.hour)+ '_' + str(time.minute) + '_' + str(time.second)
        measurement_data_path = measurement_path + '.XLS'
        shading_pattern_path = measurement_path + "_shading.json"


    shading_pattern1 = get_shading_pattern(shading_pattern_path)

    sensor_name1 = "Pyranometer 2 (W/m2)"
    # sensor_name1 = "DNI (W/m2)"
    database_path = r'C:\Users\walkerl\Documents\BIPV-planning-tool\BIPV-planning-tool\electrical_simulation\data\sam-library-cec-modules-2015-6-30.csv'
    module_df = pvsyst.retrieve_sam(path=database_path)

    irrad_value1 = get_irradiation_value(irradiation_path, time, sensor_name1)
    irrad1 = create_irradiation_list(irrad_value1, shading_pattern1, partially_shaded_irrad=None)
    irrad_on_sub_cells_ordered1 =  rearrange_shading_pattern(irrad1,number_of_subcells)
    i_module_sim1, v_module_sim1, lookup_table = ps.partial_shading(irrad_on_sub_cells_ordered1, temperature=ambient_temperature,
                                                                  irrad_temp_lookup_df=lookup_table, module_df=module_df)


    i_module_meas, v_module_meas = get_measured_iv_curves_from_excel(measurement_data_path)

    mpp_measured = max(i_module_meas * v_module_meas)
    mpp_simulated = max(i_module_sim1 * v_module_sim1)

    print mpp_measured
    print mpp_simulated

    plt.plot(v_module_sim1, i_module_sim1, color='blue', linestyle='--')
    plt.plot(v_module_meas, i_module_meas, color='blue' )
    ax = plt.gca()
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels=['simulated IV ' , 'measured IV'],loc='upper left')
    ax.set_title('Irradiation: ' + str(int(irrad_value1)) + ", T = " + str(ambient_temperature)+ u"\u00b0" + "C" + '\n Shaded cells: ' + shading_string)
    ax.set_ylabel('Current I [A]')
    ax.set_xlabel('Voltage V [V]')
    ax.set_ylim(0,4)
    ax.set_xlim(0,105)
    ax2 = ax.twinx()
    ax2.set_ylim(0, 50)
    ax2.set_xlim(0,40)
    ax2.set_ylabel("Power P [W]")
    ax2.plot(v_module_sim1, v_module_sim1 * i_module_sim1, color='green', label='PV simulated', linestyle='--')
    ax2.plot(v_module_meas, i_module_meas*v_module_meas, color='green', label='PV measured' )
    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(handles, labels=['simulated PV ', 'measured PV'])
    align_yaxis(ax, 0, ax2, 0)

    # plt.savefig("F:\Validation_final\Plots_MIA\single_module/" + shading_string + str(int(irrad_value1)) + '.png')
    plt.show()





