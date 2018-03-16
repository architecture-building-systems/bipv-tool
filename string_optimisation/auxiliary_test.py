import unittest
import numpy.testing as npt
import numpy as np
import pandas as pd
import numpy.random as npr

import auxiliary as aux


class TestModuleSimulation(unittest.TestCase):

    def test_get_distance_between_two_points_numpy(self):

        point_a = np.array([0., 0., 0.])
        point_b = np.array([0., 0., 1.])

        distance = np.array(1.0)

        self.assertAlmostEqual(aux.get_distance(point_a, point_b), distance, 6, msg="Distance between two points failed at (0,0,0), (0,0,1)")

    def test_get_distance_between_two_points_list(self):

        point_a =[0., 0., 0.]
        point_b =[0., 0., 1.]

        distance = np.array(1.0)

        self.assertAlmostEqual(aux.get_distance(point_a, point_b), distance, 6, msg="Distance between two points failed at (0,0,0), (0,0,1)")

    def test_random_generator_for_only_having_each_module_once_per_string_arrangement(self):

        number_of_modules = np.random.randint(0,50)
        result_history = []
        for i in range(20):
            generated_version = aux.random_generator(number_of_modules)
            result_history.append(np.bincount(generated_version).max())

        self.assertEqual(max(result_history),1,"The random string generator allows for string arrangements where one PV module used twice")


    def test_simple_yield_calculation_with_one_example(self):

        string_arrangement =[[0,3,2],[1,4]]
        module_irradiation_np = np.array([[1000,500,600,800,950], [1000, 1000, 1000, 1000, 1000]])
        module_area = 1
        module_efficiency = 0.2
        cabling_length = [25, 15]
        hour_from = 0
        hour_to = 1
        voltage_mp = 30
        roh = 0.027
        cabling_cross_section_area = 4


        expected_yield = 556.175
        calculated_yield = aux.simple_yield_calculation(string_arrangement,module_irradiation_np, module_area,
                                                        module_efficiency, cabling_length, hour_from, hour_to,
                                                        voltage_mp, roh, cabling_cross_section_area)
        self.assertEqual(calculated_yield, expected_yield, "simple yield calculation failed for one hour")


        hour_from = 0
        hour_to = 8759
        expected_yield = 1544.175
        calculated_yield = aux.simple_yield_calculation(string_arrangement, module_irradiation_np, module_area,
                                                       module_efficiency, cabling_length, hour_from, hour_to,
                                                       voltage_mp, roh, cabling_cross_section_area)
        self.assertEqual(calculated_yield, expected_yield, "simple yield calculation failed")

        hour_from = 0
        hour_to = 0
        expected_yield = 0
        calculated_yield = aux.simple_yield_calculation(string_arrangement, module_irradiation_np, module_area,
                                                        module_efficiency, cabling_length, hour_from, hour_to,
                                                        voltage_mp, roh, cabling_cross_section_area)
        self.assertEqual(calculated_yield, expected_yield, "yield of hour_from=hour_to does not result in 0")


    def test_cell2module_irradiance(self):

        sen_dir_ill = pd.DataFrame([[2018, 03, 16, 8, 1000, 500, 1000, 500],
                                   [2018, 03, 16, 9, 900, 500, 900, 500]])
        sensor_points_per_module = 4

        expected_result = np.array([[750.],[700.]])

        calculated_result = aux.cell2module_irradiance(sen_dir_ill, sensor_points_per_module)

        npt.assert_almost_equal(calculated_result, expected_result,7,"Averaging irradiance values over the module fails")

    def test_calculate_cable_length_greedy(self):

        point_coordinates = np.array([[0,0,0],[1,15,1],[0,2,0]])
        string_arrangement = [[0,1,2]]
        expected_result = np.array([15.07669683])

        calculated_result = np.array(aux.calculate_cable_length_greedy(string_arrangement, point_coordinates))

        npt.assert_almost_equal(calculated_result,expected_result, 5, err_msg= "cable length calculation fails at simple example")


if __name__ == "__main__":
    unittest.main()
