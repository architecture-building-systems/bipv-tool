# coding=utf-8
import datetime
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

"""
This script will allow to consider the angle of incidence correction for modules.

Idea:   The direct-direct sunlight on a sensor point has a certain incidence angle. This angle shall
        be calculated from the time and the sensor point normal vector. To correctly get the sun angles
        the longitude and latitude as well as the elevation are needed.

        With the angle a correction according to the module properties are carried out for diffuse and direct
        irradiation. In the end the two components are added and then represent the irradiation on the 
        cells after the glass or module TCO

@author: Linus Walker
"""


# This function uses a simplified approach in the calculation of angles and can be off value by some degrees
def calc_sun_position(latitude_deg, longitude_deg, date, time_zone_meridian):
    # find hour of year
    hoy = hoy_from_date(date.month, date.day, date.hour, date.minute, date.second)
    # find day of year
    doy = doy_from_date(date.month, date.day)

    # calculate solar declination (according to class solar cells, ETHZ
    declination_deg = 23.45 * math.sin(math.radians((doy + 284) * 360 / 365.25))
    declination_rad = declination_deg / 180 * math.pi

    # Convert location to to Radians
    latitude_rad = math.radians(latitude_deg)
    longitude_rad = math.radians(longitude_deg)

    # Calculate True Solar Time: Solar time = Standard Time + (long-longitude standard)/15deg
    solar_time = hoy + (longitude_deg - time_zone_meridian) / 15  # Time_zone_meridian is a globally defined variable!

    # Calculate Hourly angle
    hourly_angle_deg = (solar_time - 12) * 15
    hourly_angle_rad = hourly_angle_deg / 180 * math.pi

    # Calculate Solar altitude with sin(hs) = sin(phi)sin(delta)+cos(phi)cos(delta)cos(omega_s)
    solar_altitude_rad = math.asin(math.sin(latitude_rad) * math.sin(declination_rad) + math.cos(latitude_rad) *
                                   math.cos(declination_rad) * math.cos(hourly_angle_rad))
    solar_altitude_deg = solar_altitude_rad / math.pi * 180

    # Calculate Solar azimuth (pay attention with conventions The formula gives results for south convetion.
    # The values are adapted to the north convention

    azimuth_rad_south = math.asin(math.cos(declination_rad) * math.sin(hourly_angle_rad) / math.cos(solar_altitude_rad))
    azimuth_rad_north = azimuth_rad_south + math.pi
    azimuth_deg_north = azimuth_rad_north / math.pi * 180

    return solar_altitude_deg, azimuth_deg_north


def hoy_from_date(month, day, hour, minute, second):  # will not return integers only
    cumDaysmonth = [0.0, 31.0, 59.0, 90.0, 120.0, 151.0, 181.0, 212.0, 243.0, 273.0, 304.0, 334.0, 365.0]
    hours = cumDaysmonth[month - 1] * 24
    hours = hours + 24.0 * (day - 1)  # -1 because the day hasnt finished yet
    hours = hours + hour  # here the given hour is already over
    hours = hours + minute / 60.0  # the minute has also finished
    hours = hours + second / 3600.0  # second has finished when counted
    return hours  # returns hours of year


def doy_from_date(month, day):
    cumDaysmonth = [0.0, 31.0, 59.0, 90.0, 120.0, 151.0, 181.0, 212.0, 243.0, 273.0, 304.0, 334.0, 365.0]
    days = cumDaysmonth[month - 1]
    days = days + day
    return days


def hhmmss_from_decimal_hour(hour):
    hh = int(hour)
    hour = hour - hh
    mm = int(hour * 60)
    hour = hour * 60 - mm
    ss = int(round(hour * 60, 0))
    return [hh, mm, ss]


# Loads daysim/Radiance sensor points from a file.
# input filepath, outpout
def load_sensor_points(sensor_file):
    return pd.read_csv(sensor_file, sep=' ', header=None, names=['x', 'y', 'z', 'xdir', 'ydir', 'zdir'])


# Loads the daysim irradiation results. Since two simulations are run for global and direct-direct irrad
# two filepaths are given
def load_irrad_data(irrad_complete_path, irrad_direct_path):
    irrad_complete = pd.read_csv(irrad_complete_path, sep=' ', header=None)
    irrad_dir_dir = pd.read_csv(irrad_direct_path, sep=' ', header=None)
    return irrad_complete, irrad_dir_dir


def safe_from_dataframe(df, df_path):
    df.to_csv(df_path, mode='w', sep=" ", header=False, index=False)


def angle_between_vectors(vector1, vector2):
    arcos_argument = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))

    arcos_argument = arcos_argument - 10 ** (-9)  # This is to fix a bug. Somehow although arcos should take 1.0 as an
    # argument it fails, when arcos_argument = 1.0. With that fix, it works.

    angle = np.pi / 2 - (np.arccos(arcos_argument))
    return angle


# Azimuth = zero at North clockwise positive
def vector_to_tilt_and_azimuth(avector):
    if avector[0] == 0 and avector[1] == 0:
        tilt = 0
        azimuth = 0  # technically this is wrong
    else:
        horizontal = np.array([avector[0], avector[1], 0])
        tilt = angle_between_vectors(avector, horizontal)

        if avector[0] >= 0 and avector[1] > 0:
            azimuth = np.arctan(avector[0] / avector[1])
        elif (avector[0] >= 0) and (avector[1] < 0):
            azimuth = np.pi - (np.arctan(avector[0] / (-avector[1])))
        elif avector[0] < 0 and avector[1] < 0:
            azimuth = np.pi + (np.arctan(-avector[0] / (-avector[1])))
        elif avector[1] == 0:
            if avector[0] > 0:
                azimuth = np.pi / 2
            else:
                azimuth = np.pi * 3 / 2
        else:
            azimuth = 2 * np.pi - (np.arctan(-avector[0] / avector[1]))
    return azimuth, tilt


# inputs in radians
def calculate_angle_of_incidence(asolar_azimuth, solar_zenith, sensor_azimuth, sensor_tilt):
    aoi = np.arccos(np.cos(solar_zenith) * np.cos(sensor_tilt) +
                    np.sin(solar_zenith) * np.sin(sensor_tilt) * np.cos(asolar_azimuth - sensor_azimuth))
    return aoi


# be sure to give theta_m in rad!!!
def k_martin_ruiz(theta_m, aa_r):
    if theta_m > np.pi / 2:
        return 0
    else:
        k = np.exp(1 / aa_r) * (1 - np.exp(-np.cos(theta_m) / aa_r)) / (np.exp(1 / aa_r) - 1)
        return k


k_list_global = []


def e_effective(e_dir, e_diff, theta, aa_r):
    k1 = k_martin_ruiz(theta, aa_r)
    # k2 =  k_martin_ruiz(np.pi/3, aa_r)
    k2 = 0.94984480313119235  # This value stays constant and does not need to be recalculated each time
    k_list_global.append(k1)
    e_eff = e_dir * k1 + e_diff * k2  # pi/3 is assumed for diffuse irrad
    if e_eff <0:
        print "flag"
        print "e_dir"
        print e_dir
        print "e_diff"
        print e_diff
        print "e_eff"
        print e_eff
        print "k1"
        print k1
    return e_eff


def aoi_modifier(latitude, longitude, sensor_points, sen_dir_ill_total, sen_dir_ill_direct, result_path,
                 a_r=0.17, time_zone_meridian=15):
    """

    :param latitude: input in degrees (ZRH 47.367)
    :param longitude: input in degrees (ZRH 8.55)
    :param sensor_points: path of sensor points which are stored in a csv file according to daysim_exe
    :param sen_dir_ill_total: resultpath from daysim_exe (.ill file)
    :param sen_dir_ill_direct: resultpath from daysim_direc exe (.ill file)
    :param result_path: path, where the new file shall be saved
    :param a_r: coefficient of the martin ruiz model. Best if curve fitted or from literature. Default 0.17
    :param time_zone_meridian: the meridian of the time zone, being 15deg for CET.
    :return: No return. A file with the results is saved at the given filepath
    """

    sensors_df = load_sensor_points(sensor_points)

    irrad_global_df, irrad_direct_direct_df = load_irrad_data(sen_dir_ill_total, sen_dir_ill_direct)

    irrad_direct_direct_np = irrad_direct_direct_df.as_matrix()
    irrad_global_bla_np = irrad_global_df.as_matrix()
    irrad_diffuse_np = irrad_global_bla_np-irrad_direct_direct_np

    if np.nanmin(irrad_diffuse_np)<0:

        print "Do flattening"
        max_sensor_number = len(irrad_diffuse_np[0])
        for hour in range(len(irrad_diffuse_np)):
            for sensor_number in range(max_sensor_number):
                if ((irrad_diffuse_np[hour][sensor_number]<0) and (sensor_number<max_sensor_number)):
                    irrad_diffuse_np[hour][sensor_number] = (irrad_diffuse_np[hour][sensor_number-1]+irrad_diffuse_np[hour][sensor_number+1])/2
                elif (irrad_diffuse_np[hour][sensor_number]<0):
                    irrad_diffuse_np[hour][sensor_number] = irrad_diffuse_np[hour][sensor_number - 1]
                else:
                    pass

        irrad_global_np = irrad_diffuse_np+irrad_direct_direct_np

        print "flattening done"

    print np.nanmin(irrad_diffuse_np)
    # plt.plot(irrad_direct_direct_np[8410], label="direct")
    # plt.plot(irrad_global_np[8410], label="global")
    # plt.plot(irrad_diffuse_np[8410], label="diffuse")
    # plt.show()
    print np.where(irrad_diffuse_np==np.nanmin(irrad_diffuse_np))


    solar_altitude_np = np.empty(len(irrad_global_df))
    solar_azimuth_np = np.empty(len(irrad_global_df))

    # a list with the solar angles for each time step is created.
    # the time input for calc_sun_position is always UTC time
    for timestep in range(len(irrad_global_df)):
        date = datetime.datetime(2017, irrad_global_df[0][timestep], irrad_global_df[1][timestep],
                                 hhmmss_from_decimal_hour(irrad_global_df[2][timestep])[0],
                                 hhmmss_from_decimal_hour(irrad_global_df[2][timestep])[1],
                                 hhmmss_from_decimal_hour(irrad_global_df[2][timestep])[2])
        sol_alti, sol_azi = calc_sun_position(latitude, longitude, date, time_zone_meridian)
        # Attention, here the angles are given in degrees

        solar_altitude_np[timestep] = sol_alti
        solar_azimuth_np[timestep] = sol_azi



    incident_angles_ = []
    incident_angles_np = np.empty((len(sensors_df), len(irrad_global_df)))
    # incident_angles is a list consisting of sublists [[incidence angles over time for sensor 1],
    # [incidence angles over time for sensor 2], etc.]

    for point_count in range(len(sensors_df)):
        vector = np.array([sensors_df.at[point_count, 'xdir'], sensors_df.at[point_count, 'ydir'],
                           sensors_df.at[point_count, 'zdir']])
        sensor_azimuth, sensor_tilt = vector_to_tilt_and_azimuth(vector)


        incident_angles_np[point_count] = calculate_angle_of_incidence(solar_azimuth_np/180 * np.pi,
                                                              np.pi / 2 - solar_altitude_np/180 * np.pi,
                                                              sensor_azimuth, sensor_tilt)




    irrad_ef_df = irrad_global_df.copy()


    for time_count in range(len(irrad_ef_df)):

        print time_count
        for point_count in range(len(irrad_ef_df.columns) - 4):
            irrad_ef_df.at[time_count, point_count + 4] = e_effective(
                irrad_direct_direct_np[time_count][point_count + 4],
                (irrad_global_np[time_count][point_count + 4] -irrad_direct_direct_np[time_count][point_count + 4]),
                incident_angles_np[point_count][time_count], a_r)

            # irrad_ef_df.at[time_count, point_count + 4] = e_effective(
            #     irrad_direct_direct_np[time_count][point_count + 4],
            #     (irrad_global_np[time_count][point_count + 4] -
            #      irrad_direct_direct_np[time_count][point_count + 4]),
            #     incident_angles_np[point_count][time_count], a_r)


    # for time_count in range(len(irrad_ef_df)):
    #     print 'length 2'
    #     print len(irrad_ef_df.columns)
    #     for point_count in range(len(irrad_ef_df.columns) - 4):
    #         print time_count
    #         print point_count + 4
    #         irrad_ef_df.at[time_count, point_count + 4] = e_effective(
                # irrad_direct_direct_df.at[time_count, point_count + 4],
    #             (irrad_global_df.at[time_count, point_count + 4] -
    #              irrad_direct_direct_df.at[time_count, point_count + 4]),
    #             incident_angles_np[point_count][time_count], a_r)

    safe_from_dataframe(irrad_ef_df, result_path)


    # 22.06.2017 First version of script that gives realistic results of the angles. Literature comparison and validation pending
    # 21.08.2017 Validation is difficult, since it is not possible to irradiate the module from different angles with the same irradiation

