import os
import shutil
import daysim_exe
import daysim_direct_exe
import AOI_mod as aoi


if __name__ == '__main__':

    current_directory = os.path.dirname(__file__)
    project_path = os.path.join(current_directory, r'project_folder')
    project_input_path = project_path + '\input'
    direct_project_path = os.path.join(current_directory, r'direct_project_folder')
    direct_project_input_path = direct_project_path + '\input'
    sensor_points = os.path.join(project_path, "output\sen_dir\pts\sensor_points.pts" )
    sen_dir_ill_total = os.path.join(project_path, r"output\sen_dir\res\sen_dir.ill" )
    sen_dir_ill_direct = os.path.join(direct_project_path, r"output\sen_dir\res\sen_dir.ill")
    result_path = os.path.join(project_path, r'results\sen_dir.ill')
    geometry_table_name = 'background_geometries'
    sensor_geometries_name = 'sensor_geometries'
    sen_list = 'sen_dir'

    if os.path.isdir(direct_project_path):
        shutil.rmtree(direct_project_path)

    shutil.copytree(project_path,direct_project_path)



    ### ================== SET PARAMETERS HERE ===================== ###
    
    weatherfile_path = os.path.join(project_path, 'input', 'Zuerich_Kloten_2013.epw')
    albedo_ground = 0.2
    latitude = 47.36700
    longitude = 8.55000
    a_r = 0.17  # is a module parameter that has to be set to calculate K
    time_zone_meridian = 15  # 15deg for CET, adapt for different time zones

    # =============================== call daysim in normal mode =============================== #

    daysim_exe.calc_radiation(project_path=project_path, geometry_table_name=geometry_table_name, weatherfile_path=weatherfile_path, sen_list=sen_list, ground_reflectance=albedo_ground,)

    # =============================== call daysim in direct-direct mode =============================== #

    daysim_direct_exe.calc_radiation(project_path=direct_project_path, geometry_table_name=geometry_table_name, weatherfile_path=weatherfile_path, sen_list=sen_list, ground_reflectance=0.0, )

    # =============================== apply angle of incidence correction =============================== #

    aoi.aoi_modifier(latitude=latitude, longitude=longitude, sensor_points=sensor_points, sen_dir_ill_total=sen_dir_ill_total, sen_dir_ill_direct=sen_dir_ill_direct, result_path=result_path, a_r=a_r, time_zone_meridian=time_zone_meridian)