import unittest
import numpy.testing as npt
import numpy as np
import numpy.random as npr

from miasole_module_two import calculate_reverse_scaling_factor
import miasole_module_two as mod_calc


class TestModuleSimulation(unittest.TestCase):


    def test_reverse_scaling_factor(self):

        voltages = np.array([-5., -1., 0., 0.1, 1., 2.5, 6.])

        breakdown_voltage = -10
        miller_exponent = 3
        reference_result = np.array([1.142857143, 1.001001001, 1.000000000, 1.000001000, 1.001001001,
                                     1.015873016, 1.275510204])
        result = calculate_reverse_scaling_factor(voltages, breakdown_voltage=breakdown_voltage,
                                                  miller_exponent=miller_exponent )
        npt.assert_almost_equal(result,reference_result,5)




    def test_sub_cells_2_cells_example_values(self):

        subcell_current_values = np.array([[-1, -0.5, 0, 0.5, 1],[-1, -0.5, 0, 0.5, 1.0],[1, 1, 2, 2, 5],[1, 1, 2, 2, 5]])
        expected_result = np.array([[-2, -1, 0, 1, 2],[2, 2, 4, 4, 10]])

        result = mod_calc.sub_cells_2_cells(subcell_current_values, num_subcells=2)

        npt.assert_almost_equal(result, expected_result,7)

    def test_sub_cells_2_cells_input_length_eq_output_length(self):

        subcell_current_values = npr.rand(10,10)
        result = mod_calc.sub_cells_2_cells(subcell_current_values,10)

        self.assertEqual(len(result[0]), 10, "The dimension of the cell_i_values does not correspond to the dimension of the subcell_i values")

    def test_subcells_2_cells_also_runs_with_one_subcell(self):
        subcell_current_values = np.array([[1.0]])
        expected_result = np.array([[1.0]])
        result = mod_calc.sub_cells_2_cells(subcell_current_values, num_subcells=1)
        npt.assert_almost_equal(result, expected_result, 7)







if __name__ == "__main__":
    unittest.main()




