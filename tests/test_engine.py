import unittest
from src.engine import (
    parse_dimension, 
    float_to_fraction, 
    round_to_32nd,
    calculate_drawer_box,
    generate_csv_cutlist,
    generate_txt_summary
)

class TestEngineDimensionParsing(unittest.TestCase):
    def test_round_to_32nd(self):
        self.assertEqual(round_to_32nd(19.625), 19.625)
        self.assertEqual(round_to_32nd(19.65625), 19.65625)  # 21/32
        self.assertEqual(round_to_32nd(19.6560), 19.65625)
        self.assertEqual(round_to_32nd(0.03125), 0.03125)

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

    def test_export_generators(self):
        res = calculate_drawer_box(20.0, 6.0, 21.0)
        csv_out = generate_csv_cutlist(res)
        self.assertIn("Cabinet Opening", csv_out)
        self.assertIn("19.6250", csv_out)
        self.assertIn("19 5/8\"", csv_out)

        txt_out = generate_txt_summary(res)
        self.assertIn("DRAWER CALCULATOR - CUT LIST & WORKSTATION SUMMARY", txt_out)
        self.assertIn("Side Panels (Qty: 2)", txt_out)

if __name__ == '__main__':
    unittest.main()
