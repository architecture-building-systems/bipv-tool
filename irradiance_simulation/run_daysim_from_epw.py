#from iteration import *
import os
import daysim_exe
import daysim_direct_exe
import pandas as pd
import AOI_mod as aoi


if __name__ == '__main__':

    project_path = r'C:\daysim_first\final_miasole_03_optimisation'
    project_input_path = project_path + '\input'

    direct_project_path = r'C:\daysim_first\final_miasole_03_optimisation_direct'
    direct_project_input_path = direct_project_path + '\input'

    weatherfile_path = os.path.join(project_path, 'input', 'Zuerich_Kloten_2013.epw')


    geometry_table_name = 'background_geometries'
    sensor_geometries_name = 'sensor_geometries'
    sen_list = 'sen_dir'
    albedo_ground = 0.2

    # pregenerated_sensor_points_location = r'C:\Users\walkerl\Documents\MA_Local\Case_Study2\Sensor_points\MIA'
    # module_number_from = 0
    # module_number_to = 63


    latitude = 47.36700
    longitude = 8.55000
    sensor_points = r'C:\daysim_first\final_miasole_03_optimisation\output\sen_dir\pts\sensor_points.pts'
    sen_dir_ill_total = r'C:\daysim_first\final_miasole_03_optimisation\output\sen_dir\res\sen_dir.ill'
    sen_dir_ill_direct = r'C:\daysim_first\final_miasole_03_optimisation_direct\output\sen_dir\res\sen_dir.ill'
    result_path = r'C:\daysim_first\final_miasole_03_optimisation\results\sen_dir.ill'
    a_r = 0.17  # is a module parameter that has to be set to calculate K
    time_zone_meridian = 15  # 15deg for CET, adapt for different time zones




    # =============================== import the generated sensor points =============================== #

    # module_number = module_number_from
    # sensor_file_path = pregenerated_sensor_points_location + "\module" + str(module_number) + ".xlsx"
    # sensor_points_df = pd.read_excel(sensor_file_path, header=None, names=('sen_x', 'sen_y', 'sen_z', 'sen_dir_x',
    #                                                                        'sen_dir_y', 'sen_dir_z'))
    #
    # while(module_number < module_number_to):
    #     module_number +=1
    #     sensor_file_path = pregenerated_sensor_points_location + "\module" + str(module_number) + ".xlsx"
    #     temporary_sensor_points_df = pd.read_excel(sensor_file_path, header=None, names=('sen_x', 'sen_y', 'sen_z', 'sen_dir_x',
    #                                                                            'sen_dir_y', 'sen_dir_z'))
    #     sensor_points_df = pd.concat((sensor_points_df, temporary_sensor_points_df), join='outer')
    #
    # sensor_points_df.to_csv(os.path.join(project_input_path,sen_list) + '.csv', sep=',', index=False )


    # =============================== call daysim in normal mode =============================== #

    daysim_exe.calc_radiation(project_path=project_path, geometry_table_name=geometry_table_name, weatherfile_path=weatherfile_path, sen_list=sen_list, ground_reflectance=albedo_ground,)  # Use this one only when sensor points are already calculated and stored in the input data folder
    #
    # daysim_exe.calc_radiation(project_path, geometry_table_name, weatherfile_path, sensor_geometries_name=sensor_geometries_name, ground_reflectance=albedo_ground)
    #
    # =============================== call daysim in direct-direct mode =============================== #

    daysim_direct_exe.calc_radiation(project_path=direct_project_path, geometry_table_name=geometry_table_name, weatherfile_path=weatherfile_path, sen_list=sen_list, ground_reflectance=0.0, )  # Use this one only when sensor points are already calculated and stored in the py2radiance data folder

    # daysim_direct_exe.calc_radiation(project_path, geometry_table_name, weatherfile_path, sensor_geometries_name=sensor_geometries_name, ground_reflectance=albedo_ground)

    # =============================== apply angle of incidence correction =============================== #



    aoi.aoi_modifier(latitude=latitude, longitude=longitude, sensor_points=sensor_points, sen_dir_ill_total=sen_dir_ill_total, sen_dir_ill_direct=sen_dir_ill_direct, result_path=result_path, a_r=a_r, time_zone_meridian=time_zone_meridian)