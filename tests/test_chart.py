"""Tests for `chart` module."""

import unittest

import pandas as pd
from geemap import chart


class ChartTest(unittest.TestCase):
    """Tests for `chart` module."""

    def test_data_table_dict(self):
        """Test DataTable with a dictionary."""
        data = {"col1": [1, 2], "col2": [3, 4], "date": ["2022-01-01", "2022-01-02"]}
        dt = chart.DataTable(data, date_column="date")
        self.assertIsInstance(dt, chart.DataTable)
        self.assertEqual(dt.shape, (2, 3))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(dt["date"]))

    def test_data_table_df(self):
        """Test DataTable with a pandas DataFrame."""
        data = {"col1": [1, 2], "col2": [3, 4], "date": ["2022-01-01", "2022-01-02"]}
        df = pd.DataFrame(data)
        dt = chart.DataTable(df, date_column="date")
        self.assertIsInstance(dt, chart.DataTable)
        self.assertEqual(dt.shape, (2, 3))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(dt["date"]))

    def test_transpose_df(self):
        """Test transpose_df function."""
        data = {"label": ["A", "B"], "val1": [1, 2], "val2": [3, 4]}
        df = pd.DataFrame(data)

        # Test basic transpose
        transposed = chart.transpose_df(df, "label")
        self.assertEqual(transposed.shape, (2, 2))
        self.assertEqual(list(transposed.columns), ["A", "B"])
        self.assertEqual(list(transposed.index), ["val1", "val2"])
        self.assertEqual(transposed["A"]["val1"], 1)

        # Test with index_name
        transposed_with_index_name = chart.transpose_df(
            df, "label", index_name="Metrics"
        )
        self.assertEqual(transposed_with_index_name.columns.name, "Metrics")

        # Test with custom indexes
        transposed_with_indexes = chart.transpose_df(
            df, "label", indexes=["Value 1", "Value 2"]
        )
        self.assertEqual(list(transposed_with_indexes.index), ["Value 1", "Value 2"])

        # Test invalid label_col
        with self.assertRaises(ValueError):
            chart.transpose_df(df, "invalid_col")

        # Test invalid indexes length
        with self.assertRaises(ValueError):
            chart.transpose_df(df, "label", indexes=["Only one"])

    def test_pivot_df(self):
        """Test pivot_df function."""
        data = {
            "date": ["2022-01-01", "2022-01-01", "2022-01-02", "2022-01-02"],
            "variable": ["temp", "prec", "temp", "prec"],
            "value": [25, 5, 26, 3],
        }
        df = pd.DataFrame(data)

        pivoted = chart.pivot_df(df, index="date", columns="variable", values="value")

        self.assertEqual(pivoted.shape, (2, 3))
        self.assertEqual(list(pivoted.columns), ["date", "prec", "temp"])
        self.assertEqual(pivoted["temp"][0], 25)
        self.assertEqual(pivoted["prec"][1], 3)

    def test_array_to_df(self):
        """Test array_to_df function."""
        y_values = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        df = chart.array_to_df(y_values)
        self.assertEqual(df.shape, (3, 3))
        self.assertEqual(list(df.columns), ["x", "y1", "y2"])
        self.assertEqual(list(df["x"]), [1, 2, 3])
        self.assertEqual(list(df["y1"]), [1.0, 2.0, 3.0])
        self.assertEqual(list(df["y2"]), [4.0, 5.0, 6.0])

        x_values = [10, 20, 30]
        y_labels = ["a", "b"]
        df = chart.array_to_df(
            y_values, x_values=x_values, y_labels=y_labels, x_label="time"
        )
        self.assertEqual(df.shape, (3, 3))
        self.assertEqual(list(df.columns), ["time", "a", "b"])
        self.assertEqual(list(df["time"]), [10, 20, 30])
        self.assertEqual(list(df["a"]), [1.0, 2.0, 3.0])
        self.assertEqual(list(df["b"]), [4.0, 5.0, 6.0])


if __name__ == "__main__":
    unittest.main()
