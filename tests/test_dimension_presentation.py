import unittest

from bowl_index.presentation import format_dimensions, format_fact_value, language_name


class DimensionPresentationTests(unittest.TestCase):
    def test_catalogue_language_doubt_survives_the_reader_heading(self):
        self.assertEqual(language_name([{"field": "inscription_language", "value_text":
            "Possibly Aramaic (museum description)", "certainty": "uncertain"}]),
            "Possibly Aramaic (unspecified)")

    def test_nli_label_is_english_without_inferred_diameter(self):
        value = format_dimensions("Height 72 mm; source field ‘הקף’ 164 mm")
        self.assertEqual(value, "Height 7.2 cm · Circumference 16.4 cm")
        self.assertNotIn("diameter", value.lower())

    def test_repeated_source_labels_are_removed_without_losing_uncertainty(self):
        for original, display in (
            ("Incomplete; 11 fragments (museum description)", "Incomplete; 11 fragments"),
            ("Demon (museum classification)", "Demon"),
            ("Nippur, Iraq (museum-reported provenience)", "Nippur, Iraq"),
            ("Possibly Aramaic (museum description)", "Possibly Aramaic"),
            ("Height 7 cm (approximately)", "Height 7 cm (approximately)"),
            ("Jewish Historical Museum (Belgrade)", "Jewish Historical Museum (Belgrade)"),
        ):
            self.assertEqual(format_fact_value(original), display)

    def test_qualifiers_and_units_retain_their_measurement_roles(self):
        self.assertEqual(format_dimensions("height 75 mm; outside diameter 183 mm"),
                         "Outside diameter 18.3 cm · Height 7.5 cm")
        self.assertEqual(format_dimensions("3 inches diameter"), "Diameter 7.62 cm")
        self.assertEqual(format_dimensions("Opening diameter 15 cm; depth 5.6 cm"),
                         "Opening diameter 15 cm · Depth 5.6 cm")

    def test_unlabelled_dimensions_do_not_acquire_invented_axes(self):
        self.assertEqual(format_dimensions("180x60 mm."),
                         "Measurements (axes unspecified) 18 × 6 cm")
        self.assertEqual(format_dimensions("163.2 mm"), "Measurement (axis unspecified) 16.32 cm")

    def test_partial_parsing_cannot_drop_uncertainty_or_other_measurements(self):
        for value in ("approximately 3 in diameter", "Diameter 15–16 cm; height 5 cm",
                      "Diameter 15 cm; height 5 cm; base 8 cm", "height 5 cm; height 6 cm",
                      "Group components reportedly 175–200 mm × 50–75 mm; individual assignment unavailable"):
            self.assertEqual(format_dimensions(value), value)


if __name__ == "__main__":
    unittest.main()
