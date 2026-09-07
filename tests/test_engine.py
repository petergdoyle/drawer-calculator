import unittest
from src.engine import (
    parse_dimension, 
    float_to_fraction, 
    round_to_32nd,
    inches_to_mm,
    mm_to_inches,
    format_dimension_pair,
    calculate_drawer_box,
    validate_inputs,
    generate_csv_cutlist,
    generate_txt_summary
)

class TestEngineDimensionParsing(unittest.TestCase):
    def test_round_to_32nd(self):
        self.assertEqual(round_to_32nd(19.625), 19.625)
        self.assertEqual(round_to_32nd(19.65625), 19.65625)  # 21/32
        self.assertEqual(round_to_32nd(19.6560), 19.65625)
        self.assertEqual(round_to_32nd(0.03125), 0.03125)

    def test_unit_conversions(self):
        self.assertAlmostEqual(inches_to_mm(20.0), 508.0, places=1)
        self.assertAlmostEqual(mm_to_inches(508.0), 20.0, places=3)
        
        p_imp, s_imp = format_dimension_pair(20.0, "Fractional Inches (\")")
        self.assertEqual(p_imp, '20"')
        self.assertEqual(s_imp, '(508.0 mm)')

        p_met, s_met = format_dimension_pair(20.0, "Metric (mm)")
        self.assertEqual(p_met, '508.0 mm')
        self.assertEqual(s_met, '(20")')

    def test_parse_dimension_decimals(self):
        val, err = parse_dimension("19.625")
        self.assertIsNone(err)
        self.assertEqual(val, 19.625)

        val, err = parse_dimension(20.5)
        self.assertIsNone(err)
        self.assertEqual(val, 20.5)

        val, err = parse_dimension('19.625"')
        self.assertIsNone(err)
        self.assertEqual(val, 19.625)

    def test_parse_dimension_metric(self):
        # 508 mm = 20 inches
        val, err = parse_dimension("508 mm", unit_system="Metric (mm)")
        self.assertIsNone(err)
        self.assertEqual(val, 20.0)

        val, err = parse_dimension("508", unit_system="Metric (mm)")
        self.assertIsNone(err)
        self.assertEqual(val, 20.0)

    def test_parse_dimension_fractions(self):
        # Mixed fractions
        val, err = parse_dimension("19 5/8")
        self.assertIsNone(err)
        self.assertEqual(val, 19.625)

        val, err = parse_dimension("19-5/8")
        self.assertIsNone(err)
        self.assertEqual(val, 19.625)

        val, err = parse_dimension('19 5/8"')
        self.assertIsNone(err)
        self.assertEqual(val, 19.625)

        # 32nd precision
        val, err = parse_dimension("19 21/32")
        self.assertIsNone(err)
        self.assertEqual(val, 19.65625)

        val, err = parse_dimension("21/32")
        self.assertIsNone(err)
        self.assertEqual(val, 0.65625)

        val, err = parse_dimension('5/8"')
        self.assertIsNone(err)
        self.assertEqual(val, 0.625)

    def test_parse_dimension_invalid(self):
        val, err = parse_dimension("abc")
        self.assertIsNotNone(err)
        self.assertIsNone(val)

        val, err = parse_dimension("5/0")
        self.assertIsNotNone(err)
        self.assertIsNone(val)

    def test_float_to_fraction_32nd(self):
        self.assertEqual(float_to_fraction(19.625), '19 5/8"')
        self.assertEqual(float_to_fraction(19.65625), '19 21/32"')
        self.assertEqual(float_to_fraction(0.03125), '1/32"')
        self.assertEqual(float_to_fraction(20.0), '20"')

    def test_joinery_cut_widths(self):
        # Butt Joint
        res_butt = calculate_drawer_box(20.0, 6.0, 21.0, material_thickness=0.625, joint_type="Butt Joint (Dominos / Dowels)")
        self.assertEqual(res_butt["drawer_width"], 19.625)
        # Front/Back cut width = 19.625 - 2*(0.625) = 18.375
        self.assertEqual(res_butt["front_back_cut_width"], 18.375)

        # Miter Joint
        res_miter = calculate_drawer_box(20.0, 6.0, 21.0, material_thickness=0.625, joint_type="Miter Joint")
        self.assertEqual(res_miter["front_back_cut_width"], 19.625)

        # Dovetail Joint
        res_dove = calculate_drawer_box(20.0, 6.0, 21.0, material_thickness=0.75, joint_type="Dovetail Joint")
        self.assertEqual(res_dove["front_back_cut_width"], 19.625)

        # Dado Butt Joint
        res_dado = calculate_drawer_box(20.0, 6.0, 21.0, material_thickness=0.625, joint_type="Dado Butt Joint")
        # 19.625 - 2*(0.625 - 0.25) = 19.625 - 0.75 = 18.875
        self.assertEqual(res_dado["front_back_cut_width"], 18.875)

    def test_slide_thickness_validation(self):
        slide_58 = {"name": "Blum 563H", "width_tolerance": 0.375, "height_tolerance": 1.0, "min_cab_width": 6.0, "min_cab_height": 3.5, "max_material_thickness": 0.625}
        
        # Valid 5/8" thickness
        warns_ok = validate_inputs(20.0, 6.0, 21.0, slide_cfg=slide_58, material_thickness=0.625)
        self.assertEqual(len(warns_ok), 0)

    def test_custom_dado_depth_and_bottom_thickness(self):
        # Default 3/8" dado depth, 1/4" bottom thickness
        res_def = calculate_drawer_box(20.0, 6.0, 21.0, material_thickness=0.625, dado_depth=0.375, bottom_thickness=0.25)
        # Inside width = 20.0 - 0.375 - 2*(0.625) = 19.625 - 1.25 = 18.375
        # Bottom width = 18.375 + 2*(0.375) = 19.125
        self.assertEqual(res_def["inside_width"], 18.375)
        self.assertEqual(res_def["bottom_width"], 19.125)
        self.assertEqual(res_def["bottom_thickness"], 0.25)
        self.assertEqual(res_def["dado_depth"], 0.375)

        # 1/2" dado depth
        res_half = calculate_drawer_box(20.0, 6.0, 21.0, material_thickness=0.625, dado_depth=0.500, bottom_thickness=0.375)
        # Bottom width = 18.375 + 2*(0.500) = 19.375
        self.assertEqual(res_half["bottom_width"], 19.375)
        self.assertEqual(res_half["bottom_thickness"], 0.375)
        self.assertEqual(res_half["dado_depth"], 0.500)

    def test_custom_front_thickness_and_setback(self):
        # Default 3/4" front thickness, 0" additional setback -> total setback 0.75"
        res_def = calculate_drawer_box(20.0, 6.0, 21.0, drawer_front_thickness=0.75, additional_setback=0.0)
        # min_depth_overlay = 21.0 + 0.65625 = 21.65625
        # min_depth_inset = 21.65625 + 0.75 = 22.40625
        self.assertEqual(res_def["total_inset_setback"], 0.75)
        self.assertEqual(res_def["min_depth_inset"], 22.40625)

        # Custom 7/8" front thickness (0.875") + 1/4" additional setback (0.25") -> total setback 1.125"
        res_custom = calculate_drawer_box(20.0, 6.0, 21.0, drawer_front_thickness=0.875, additional_setback=0.25)
        self.assertEqual(res_custom["total_inset_setback"], 1.125)
        self.assertEqual(res_custom["min_depth_inset"], 21.65625 + 1.125)

if __name__ == '__main__':
    unittest.main()
