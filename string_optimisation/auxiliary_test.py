import unittest
import numpy.testing as npt
import numpy as np
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

    # def test_random_generator_for_only_having_each_module_once_per_string_arrangement(self):
    #
    #     number_of_modules = np.random.randint(0,50)
    #
    #     for i in range(150):
    #         aux.random_generator(number_of_modules)

if __name__ == "__main__":
    unittest.main()
