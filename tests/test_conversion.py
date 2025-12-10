"""Tests for conversion module."""

import unittest

from geemap import conversion


class TestConversion(unittest.TestCase):
    """Tests for conversion."""

    def test_find_matching_bracket_single_line(self):
        lines = ['{ "key": "value" }']
        line_index, char_index = conversion.find_matching_bracket(lines, 0, 0)
        self.assertEqual(line_index, 0)
        self.assertEqual(char_index, 17)

    def test_find_matching_bracket_multi_line(self):
        lines = ["{", '  "key": "value"', "}"]
        line_index, char_index = conversion.find_matching_bracket(lines, 0, 0)
        self.assertEqual(line_index, 2)
        self.assertEqual(char_index, 0)

    def test_find_matching_bracket_nested(self):
        lines = ["{", '  "key": { "nested_key": "nested_value" }', "}"]
        line_index, char_index = conversion.find_matching_bracket(lines, 0, 0)
        self.assertEqual(line_index, 2)
        self.assertEqual(char_index, 0)

    def test_find_matching_bracket_parentheses(self):
        lines = ["(", '  "key": "value"', ")"]
        line_index, char_index = conversion.find_matching_bracket(
            lines, 0, 0, matching_char="("
        )
        self.assertEqual(line_index, 2)
        self.assertEqual(char_index, 0)

    def test_find_matching_bracket_square_brackets(self):
        lines = ["[", '  "item1",', '  "item2"', "]"]
        line_index, char_index = conversion.find_matching_bracket(
            lines, 0, 0, matching_char="["
        )
        self.assertEqual(line_index, 3)
        self.assertEqual(char_index, 0)

    def test_find_matching_bracket_no_match(self):
        lines = ["{", '  "key": "value"']
        line_index, char_index = conversion.find_matching_bracket(lines, 0, 0)
        self.assertEqual(line_index, -1)
        self.assertEqual(char_index, -1)

    def test_format_params_simple(self):
        line = "min: 0"
        self.assertEqual(conversion.format_params(line), "'min': 0")

    def test_format_params_multiple(self):
        line = "min: 0, max: 10"
        self.assertEqual(conversion.format_params(line), "'min': 0, 'max': 10")

    def test_format_params_braces(self):
        line = "{min: 0, max: 10}"
        self.assertEqual(conversion.format_params(line), "{'min': 0, 'max': 10}")

    def test_format_params_quoted(self):
        line = "{'min': 0, max: 10}"
        self.assertEqual(conversion.format_params(line), "{'min': 0, 'max': 10}")

    def test_format_params_palette(self):
        line = "palette: ['#440154', '#404387', '#29788E']"
        self.assertEqual(
            conversion.format_params(line),
            "'palette': ['#440154', '#404387', '#29788E']",
        )

    def test_format_params_string_value(self):
        line = "description: 'hello'"
        self.assertEqual(conversion.format_params(line), "'description': 'hello'")

    def test_use_math_true(self):
        lines = ["var pi = Math.PI;", "print(pi);"]
        self.assertTrue(conversion.use_math(lines))

    def test_use_math_false(self):
        lines = ["var pi = 3.14;", "print(pi);"]
        self.assertFalse(conversion.use_math(lines))

    def test_convert_for_loop_i_plus_plus(self):
        line = "for (var i = 0; i < 10; i++) {"
        self.assertEqual(
            conversion.convert_for_loop(line), "for i in range(0, 10, 1): {"
        )

    def test_convert_for_loop_i_minus_minus(self):
        line = "for (var i = 10; i > 0; i--) {"
        self.assertEqual(
            conversion.convert_for_loop(line), "for i in range(10, 0, -1): {"
        )

    def test_convert_for_loop_in(self):
        line = "for (var i in myList) {"
        self.assertEqual(conversion.convert_for_loop(line), "for i in myList: {")

    def test_convert_for_loop_no_var(self):
        line = "for (i = 0; i < 10; i++) {"
        self.assertEqual(
            conversion.convert_for_loop(line), "for i in range(0, 10, 1): {"
        )

    def test_remove_all_indentation(self):
        lines = ["  line1", "\tline2", "line3", "", "  \t line4"]
        expected = ["line1", "line2", "line3", "", "line4"]
        self.assertEqual(conversion.remove_all_indentation(lines), expected)


if __name__ == "__main__":
    unittest.main()
