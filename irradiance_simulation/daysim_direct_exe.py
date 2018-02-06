import os
import pandas as pd
import math
import multiprocessing
import shutil
import time
import csv
import ntpath

from OCC import BRepGProp, GProp, TopoDS, BRep
from OCC.StlAPI import StlAPI_Reader
from OCCUtils import Topology

from pyliburo import gml3dmodel
from interface2py3d import pyptlist_frm_occface
import pyliburo
from pyliburo import py2radiance



def make_unique(original_list):
    unique_list = []
    [unique_list.append(obj) for obj in original_list if obj not in unique_list]
    return unique_list


def points_from_face(face):
    point_list = []
    pnt_coord = []
    wire_list = Topology.Topo(face).wires()
    for wire in wire_list:
        edges_list = Topology.Topo(wire).edges()
        for edge in edges_list:
            vertice_list = Topology.Topo(edge).vertices()
            for vertex in vertice_list:
                pnt_coord.append(
                    [BRep.BRep_Tool().Pnt(vertex).X(),
                     BRep.BRep_Tool().Pnt(vertex).Y(), BRep.BRep_Tool().Pnt(vertex).Z()])
    pnt_coord = make_unique(pnt_coord)
    for point in pnt_coord:
        point_list.append(point)
    return point_list


def add_rad_mat(aresults_path, abui, ageometry_table):

    file_path = os.path.join(aresults_path, abui + '\\rad\\' + abui +
                             "_material")
    file_name_rad = file_path + ".rad"
    file_name_txt = file_path + ".txt"
    os.rename(file_name_rad, file_name_rad.replace(".rad", ".txt"))
    with open(file_name_txt, 'a') as write_file:
        name_int = 0
        for geo in ageometry_table.index.values:
            mat_name = ageometry_table['mat_name'][geo]
            mat_value_R = round(ageometry_table['mat_value_R'][geo],4)
            mat_value_G = round(ageometry_table['mat_value_G'][geo],4)
            mat_value_B = round(ageometry_table['mat_value_B'][geo],4)
            specularity = round(ageometry_table['specularity'][geo],4)
            roughness = round(ageometry_table['roughness'][geo],4)
            mat_type = ageometry_table['mat_type'][geo]
            mat_nr  = ageometry_table['mat_nr'][geo]

            string = "void" + " " +str(mat_type)+ " " + mat_name + " 0 0" + " " + str(mat_nr) + " " + str(mat_value_R) + " " + str(mat_value_G) + " " + str(mat_value_B) \
                     + " " + str(specularity) + " " + str(roughness)
            write_file.writelines('\n' + string + '\n')
            name_int += 1
        write_file.close()
    os.rename(file_name_txt, file_name_rad.replace(".txt", ".rad"))


def percentage(task, now, total):
    percent = round((float(now)/float(total))*100, 0)
    division = 5
    number = int(round(percent/division, 0))

    bar = number * ">" + (100 / division - number) * "_"
    if now == total:
        print "\r", str(task), bar, percent, "%",
    else:
        print "\r", str(task),bar, percent, "%",


def geometry2radiance(arad, ageometry_table, ainput_path):
    # parameters for the radiance

    # loop over all builings
    bcnt = 0
    for geo in ageometry_table.index.values:

        filepath = os.path.join(ainput_path, geo + ".stl")
        geo_solid = TopoDS.TopoDS_Solid()
        StlAPI_Reader().Read(geo_solid, str(filepath))


        face_list = pyliburo.py3dmodel.fetch.faces_frm_solid(geo_solid)

        bf_cnt = 0
        for face in face_list:
            bface_pts = pyptlist_frm_occface(face)
            srfname = "building_srf" + str(bcnt) + str(bf_cnt)

            srfmat = ageometry_table['mat_name'][geo]
            py2radiance.RadSurface(srfname, bface_pts, srfmat, arad)
            bf_cnt += 1
        bcnt += 1
        print 'building done'

def calc_sensors(aresults_path, abui, ainput_path, axdim, aydim):

    print abui

    sen_df = []
    fps_df = []
    # import stl file
    filepath = os.path.join(ainput_path, abui + ".stl")
    geo_solid = TopoDS.TopoDS_Solid()
    StlAPI_Reader().Read(geo_solid, str(filepath))

    # calculate geometries properties
    props = GProp.GProp_GProps()
    BRepGProp.brepgprop_VolumeProperties(geo_solid, props)

    # reverse geometry if volume is negative
    if props.Mass() < 0:
        bui_vol = (-props.Mass())
        geo_solid.Reverse()
    else:
        bui_vol = (props.Mass())

    # get all faces from geometry
    face_list = pyliburo.py3dmodel.fetch.faces_frm_solid(geo_solid)

    fac_int = 0
    for face in face_list:


        normal = pyliburo.py3dmodel.calculate.face_normal(face)
        # calculate pts of each face
        fps = points_from_face(face)
        fps_df.append([val for sublist in fps for val in sublist])

        # calculate sensor points of each face
        sensor_srfs, sensor_pts, sensor_dirs = \
            gml3dmodel.generate_sensor_surfaces(face, axdim, aydim)
        fac_area = pyliburo.py3dmodel.calculate.face_area(face)
        # generate dataframe with building, face and sensor ID
        sen_int = 0

        for sen_dir in sensor_dirs:
            orientation = math.copysign(math.acos(normal[1]), normal[0]) * 180 / math.pi
            tilt = math.acos(normal[2]) * 180 / math.pi

            sen_df.append((fac_int, sen_int, fac_area, fac_area / len(sensor_dirs), sensor_pts[sen_int][0], sensor_pts[sen_int][1],
                 sensor_pts[sen_int][2], normal[0], normal[1], normal[2], orientation, tilt))
            sen_int += 1
        fac_int += 1

    sen_df = pd.DataFrame(sen_df, columns=['fac_int', 'sen_int', 'fac_area','sen_area', 'sen_x', 'sen_y',
                                       'sen_z', 'sen_dir_x', 'sen_dir_y', 'sen_dir_z', 'orientation', 'tilt'])
    sen_df.to_csv(os.path.join(aresults_path, abui + '_' + 'sen_df' + '.csv'), index=None, float_format="%.2f")

    fps_df = pd.DataFrame(fps_df, columns=['fp_0_0', 'fp_0_1', 'fp_0_2', 'fp_1_0', 'fp_1_1', 'fp_1_2', 'fp_2_0', 'fp_2_1', 'fp_2_2', ])
    fps_df.to_csv(os.path.join(aresults_path, abui + '_' + 'fps_df' + '.csv'), index=None, float_format="%.2f")


def execute_daysim(name, aresults_path, arad, aweatherfile_path, rad_params, ageometry_table, aground_reflectance, atime_step, astart_time, aend_time, acsv_path):

    sen_df = pd.read_csv(os.path.join(aresults_path, name + '_' + 'sen_df' + '.csv'))
    #sen_df = pd.read_csv(os.path.join(aresults_path, name +'.csv'))

    sen = sen_df[['sen_x', 'sen_y', 'sen_z']].values.tolist()
    sen_dir = sen_df[['sen_dir_x', 'sen_dir_y', 'sen_dir_z']].values.tolist()
    arad.set_sensor_points(sensor_normals=sen_dir, sensor_positions=sen)

    arad.create_sensor_input_file()


    # generate daysim result folders for all an_cores
    daysim_dir = os.path.join(aresults_path, name)
    arad.initialise_daysim(daysim_dir)

    # transform weather file
    arad.execute_epw2wea(aweatherfile_path, aground_reflectance)
    print 'wea complete'

    #further transform weather file from hourly to minute ds_shortterm
    if(atime_step != 60):
        execute_ds_shortterm(aweatherfile_path,arad.hea_file,atime_step)

    if (acsv_path!=None):

        head_epw, tail_epw = ntpath.split(aweatherfile_path)
        wfilename_no_extension = tail_epw.replace(".epw", "")
        wea_name_time_step = wfilename_no_extension + "_" + str(atime_step) + "min.wea"

        measured_data2wea(astart_time, aend_time, os.path.join(arad.daysimdir_wea,wea_name_time_step ), acsv_path, atime_step)

    arad.execute_radfiles2daysim()
    print 'radfiles2daysim complete'

    add_rad_mat(aresults_path, name, ageometry_table)

    arad.write_radiance_parameters(rad_params['rad_ab'], rad_params['rad_ad'], rad_params['rad_as'],rad_params['rad_ar'],
                                   rad_params['rad_aa'], rad_params['rad_lr'],rad_params['rad_st'],rad_params['rad_sj'],
                                   rad_params['rad_lw'],rad_params['rad_dj'],rad_params['rad_ds'],rad_params['rad_dr'],
                                   rad_params['rad_dp'])


    #os.rename(os.path.join(arad.data_folder_path, abui + ".pts"), os.path.join(daysim_dir, 'pts', "sensor_points.pts"))

    arad.execute_gen_dc("w/m2")
    print 'gen_dc complete'
    arad.execute_ds_illum()
    print 'ds_illum complete'
    print name, 'done'


def execute_sum(results_path, bui):

    res = pd.read_csv(os.path.join(results_path, bui, 'res', bui+'.ill'), sep=' ', header=None)
    sum = res.ix[:, 4:].sum(axis=1)
    print[bui]
    sum.columns = [bui]

    sum.to_csv(os.path.join(results_path, bui, 'res', bui+'.csv'), index=None)


def calc_radiation(project_path, geometry_table_name, weatherfile_path, sen_list=None, sensor_geometries_name=None, ground_reflectance=0.2, time_resolution=60, measurement_start=None, measurement_end=None, measurement_path=None):
    print 'Daysim direct mode'
    # =============================== parameters =============================== #
    input_path = os.path.join(project_path, 'input')
    results_path = os.path.join(project_path, 'output')

    #params
    rad_params = {
        'rad_n': 2,
        'rad_af': 'file',
        'rad_ab': 0, #Because in this case only diret-direct irradiation is used
        'rad_ad': 512,
        'rad_as': 256,
        'rad_ar': 128,
        'rad_aa': 0.15,
        'rad_lr': 8,
        'rad_st': 0.15,
        'rad_sj': 0.75,
        'rad_lw': 0.002,
        'rad_dj': 0.7,
        'rad_ds': 0.15,
        'rad_dr': 3,
        'rad_dp': 512,
        }

    # =============================== Preface =============================== #
    rad = py2radiance.Rad(os.path.join(input_path, 'base.rad'), os.path.join(input_path, 'py2radiance_data'))

    # =============================== Import =============================== #
    geometry_table = pd.read_csv(os.path.join(input_path, geometry_table_name+".csv"), index_col='name')


    # =============================== Simulation =============================== #
    geometry2radiance(rad, geometry_table, input_path)
    print 'geometry2radiance complete'
    rad.create_rad_input_file()

    # calculate sensor points
    if sen_list == None:
        xdim = 1.0
        ydim = 1.0

        sensor_geometries = pd.read_csv(os.path.join(input_path, sensor_geometries_name + '.csv'), index_col='name')
        batch_names = sensor_geometries.index.values
        pool = multiprocessing.Pool()  # use all available cores, otherwise specify the number you want as an argument
        for bui in batch_names:
            pool.apply_async(calc_sensors, args=(results_path, bui, input_path, xdim, ydim,))
        pool.close()
        pool.join()

    # load existing sensor points
    if sensor_geometries_name == None:
        batch_names = [sen_list]
        sensor_file_path = os.path.join(input_path, sen_list + '.csv')
        sensor_file_path_output = os.path.join(results_path, sen_list + '_sen_df.csv')
        shutil.copyfile(sensor_file_path, sensor_file_path_output)

    # execute daysim
    for bui in batch_names:
        execute_daysim(bui, results_path, rad, weatherfile_path, rad_params, geometry_table, ground_reflectance, time_resolution, measurement_start, measurement_end, measurement_path)
    #     process.start()
    # processes = []
    # for bui in batch_names:
    #     process = multiprocessing.Process(target=execute_daysim, args=(bui, results_path, rad, weatherfile_path, rad_params, geometry_table, ground_reflectance, time_resolution, measurement_start, measurement_end, measurement_path))
    #     process.start()
    #     processes.append(process)
    # for process in processes:
    #     process.join()

    # calculate sums of each stl file
    # pool = multiprocessing.Pool()
    # print batch_names
    # for bui in batch_names:
    #     pool.apply_async(execute_sum, args=(results_path, bui,))
    # pool.close()
    # pool.join()


def one_hour_one_point(HOY,aoutput_path, afile_name, sensor_point=0):

    res = pd.read_csv(os.path.join(aoutput_path, afile_name), sep=' ', header=None)
    value = res.ix[HOY-1, sensor_point+4]
    return value

def append_result(csv_path, value):
    with open(csv_path, 'ab') as results_saved:
        writer = csv.writer(results_saved)
        writer.writerow([str(value)])





def execute_ds_shortterm(epw_filepath, hea_filepath, time_step):

    head_epw, tail_epw = ntpath.split(epw_filepath)
    wfilename_no_extension = tail_epw.replace(".epw", "")
    wea_name_60 = wfilename_no_extension + "_60min.wea"
    wea_name_time_step = wfilename_no_extension + "_" + str(time_step) + "min.wea"

    head_hea, tail_hea = ntpath.split(hea_filepath)

    with open(hea_filepath, "r") as hea_file_read:
        lines = hea_file_read.read()
        lines = lines.replace('time_step 60', 'time_step ' + str(time_step))
        lines = lines.replace('wea_data_file' + ' ' + os.path.join(head_epw,wea_name_60), 'wea_data_file' + ' ' +os.path.join(os.path.join(head_hea,"wea"),wea_name_60 ))
        lines = lines.replace('wea_data_short_file wea\\' + str(wea_name_60),
                              'wea_data_short_file wea\\' + str(wea_name_time_step))
        print 'wea_data_short_file wea\\'

    with open(hea_filepath, "w") as hea_file_write:
        hea_file_write.write(lines)
        hea_file_write.close()


    command1 = "ds_shortterm" + " " + hea_filepath
    os.system(command1)

def wea_line(start, btime_step):
    cumDaysmonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
    hours = 0
    hours = cumDaysmonth[start['month']-1]*24
    hours = hours + 24*(start['day']-1) #-1 because the day hasnt finished yet
    hours = hours + start['hour'] #here the given hour is already over
    minutes = hours*60+start['minute']
    return minutes/btime_step-1 #python starts with row 0


def measured_data2wea(start_time, end_time, wea_path, csv_path, time_step):
    #pay attention with summer time!
    #wea file only uses standard time which is winter time
    #set summer_time to 1 for data in summertime
    summertime = 1
    start_time['hour']=start_time['hour']-summertime
    line_start = wea_line(start_time, time_step)
    line_end = wea_line(end_time, time_step)


    with open(wea_path, 'r+') as weatherfile:
        with open(csv_path, 'r') as data_file:
            data = pd.read_csv(data_file, header=1, names = ['Time', 'Diffuse_horizontal','direct_normal'] )
            weatherfile_content = pd.read_csv(weatherfile, header = 5, sep=" ", names=['month', 'day', 'hour','direct irrad', 'indirect irrad'])

            line = line_start
            # the value is set at line+1 because when the minute x is averaged in the measurement data, this means all
            # seconds of hh:x:ss. In a weather file however, if we choose the minute x, this is the data of the xth
            # minute, which is one minute earlier
            # This allows to use start_time with the normal format (e.g. 17:34 for the minute between 34:00 and 35:00
            for rad in data.direct_normal:
                weatherfile_content.set_value(line+1 , 'direct irrad', round(rad,0))
                line +=1

            for rad in data.Diffuse_horizontal:
                weatherfile_content.set_value(line+1 , 'indirect irrad', round(0,0)) #here zero because we want to work only with direct radiation
                line +=1

    with open(wea_path, 'r') as weatherfile:
        weatherfile_all = weatherfile.readlines()

    with open(wea_path, 'w' ) as weathernew:
        for i in range(0,6):
            weathernew.write(weatherfile_all[i])

    with open(wea_path, 'a' ) as weathernew:
        weatherfile_content.to_csv(wea_path, mode='a', sep=" ", header=False, index=False)

