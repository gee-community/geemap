"""Tests for the plot module."""

from __future__ import annotations

import unittest
from unittest import mock

import pandas as pd

from geemap import plot


class MockFigure:

    def __init__(self) -> None:
        self.layout_updates: dict = {}

    def update_layout(self, **kwargs) -> MockFigure:
        self.layout_updates.update(kwargs)
        return self


def create_sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "category": ["A", "B", "C", "D", "E"],
            "value": [10, 20, 15, 25, 5],
            "count": [100, 200, 150, 250, 50],
        }
    )


class TestBarChart(unittest.TestCase):

    def setUp(self) -> None:
        self.df = create_sample_dataframe()

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_valid_dataframe(self, mock_bar: mock.Mock) -> None:
        mock_bar.return_value = MockFigure()
        result = plot.bar_chart(data=self.df, x="category", y="value")
        self.assertIsNotNone(result)
        mock_bar.assert_called_once()

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_descending_order(self, mock_bar: mock.Mock) -> None:
        mock_bar.return_value = MockFigure()
        df_copy = self.df.copy()
        plot.bar_chart(data=df_copy, x="category", y="value", descending=True)
        self.assertEqual(df_copy.iloc[0]["value"], 25)

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_ascending_order(self, mock_bar: mock.Mock) -> None:
        mock_bar.return_value = MockFigure()
        df_copy = self.df.copy()
        plot.bar_chart(data=df_copy, x="category", y="value", descending=False)
        self.assertEqual(df_copy.iloc[0]["value"], 5)

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_max_rows_limit(self, mock_bar: mock.Mock) -> None:
        mock_bar.return_value = MockFigure()
        plot.bar_chart(data=self.df, x="category", y="value", max_rows=3)
        call_args = mock_bar.call_args
        data_passed = call_args[0][0]
        self.assertEqual(len(data_passed), 3)

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_layout_args_applied(self, mock_bar: mock.Mock) -> None:
        mock_fig = MockFigure()
        mock_bar.return_value = mock_fig
        plot.bar_chart(
            data=self.df,
            x="category",
            y="value",
            layout_args={"title_x": 0.5, "showlegend": False},
        )
        self.assertEqual(mock_fig.layout_updates.get("title_x"), 0.5)
        self.assertEqual(mock_fig.layout_updates.get("showlegend"), False)

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_x_label_applied(self, mock_bar: mock.Mock) -> None:
        mock_bar.return_value = MockFigure()
        plot.bar_chart(data=self.df, x="category", y="value", x_label="Category Label")
        call_args = mock_bar.call_args
        labels = call_args[1].get("labels", {})
        self.assertEqual(labels.get("category"), "Category Label")

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_y_label_applied(self, mock_bar: mock.Mock) -> None:
        mock_bar.return_value = MockFigure()
        plot.bar_chart(data=self.df, x="category", y="value", y_label="Value Label")
        call_args = mock_bar.call_args
        labels = call_args[1].get("labels", {})
        self.assertEqual(labels.get("value"), "Value Label")

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_legend_title_applied(self, mock_bar: mock.Mock) -> None:
        mock_fig = MockFigure()
        mock_bar.return_value = mock_fig
        plot.bar_chart(data=self.df, x="category", y="value", legend_title="My Legend")
        legend = mock_fig.layout_updates.get("legend", {})
        self.assertEqual(legend.get("title"), "My Legend")

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_title_passed(self, mock_bar: mock.Mock) -> None:
        mock_bar.return_value = MockFigure()
        plot.bar_chart(data=self.df, x="category", y="value", title="My Chart")
        call_args = mock_bar.call_args
        self.assertEqual(call_args[1].get("title"), "My Chart")

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_height_passed(self, mock_bar: mock.Mock) -> None:
        mock_bar.return_value = MockFigure()
        plot.bar_chart(data=self.df, x="category", y="value", height=600)
        call_args = mock_bar.call_args
        self.assertEqual(call_args[1].get("height"), 600)

    def test_bar_chart_invalid_data_raises(self) -> None:
        with self.assertRaises(ValueError):
            plot.bar_chart(data=[1, 2, 3], x="x", y="y")

    def test_bar_chart_none_data_raises(self) -> None:
        with self.assertRaises(ValueError):
            plot.bar_chart(data=None, x="x", y="y")

    @mock.patch("geemap.plot.px.bar")
    def test_bar_chart_y_as_list(self, mock_bar: mock.Mock) -> None:
        mock_bar.return_value = MockFigure()
        df_copy = self.df.copy()
        plot.bar_chart(
            data=df_copy, x="category", y=["value", "count"], descending=True
        )
        self.assertEqual(df_copy.iloc[0]["value"], 25)


class TestLineChart(unittest.TestCase):

    def setUp(self) -> None:
        self.df = create_sample_dataframe()

    @mock.patch("geemap.plot.px.line")
    def test_line_chart_valid_dataframe(self, mock_line: mock.Mock) -> None:
        mock_line.return_value = MockFigure()
        result = plot.line_chart(data=self.df, x="category", y="value")
        self.assertIsNotNone(result)
        mock_line.assert_called_once()

    @mock.patch("geemap.plot.px.line")
    def test_line_chart_descending_order(self, mock_line: mock.Mock) -> None:
        mock_line.return_value = MockFigure()
        df_copy = self.df.copy()
        plot.line_chart(data=df_copy, x="category", y="value", descending=True)
        self.assertEqual(df_copy.iloc[0]["value"], 25)

    @mock.patch("geemap.plot.px.line")
    def test_line_chart_ascending_order(self, mock_line: mock.Mock) -> None:
        mock_line.return_value = MockFigure()
        df_copy = self.df.copy()
        plot.line_chart(data=df_copy, x="category", y="value", descending=False)
        self.assertEqual(df_copy.iloc[0]["value"], 5)

    @mock.patch("geemap.plot.px.line")
    def test_line_chart_no_sorting(self, mock_line: mock.Mock) -> None:
        mock_line.return_value = MockFigure()
        df_copy = self.df.copy()
        original_first = df_copy.iloc[0]["value"]
        plot.line_chart(data=df_copy, x="category", y="value", descending=None)
        self.assertEqual(df_copy.iloc[0]["value"], original_first)

    @mock.patch("geemap.plot.px.line")
    def test_line_chart_max_rows_limit(self, mock_line: mock.Mock) -> None:
        mock_line.return_value = MockFigure()
        plot.line_chart(data=self.df, x="category", y="value", max_rows=2)
        call_args = mock_line.call_args
        data_passed = call_args[0][0]
        self.assertEqual(len(data_passed), 2)

    @mock.patch("geemap.plot.px.line")
    def test_line_chart_layout_args_applied(self, mock_line: mock.Mock) -> None:
        mock_fig = MockFigure()
        mock_line.return_value = mock_fig
        plot.line_chart(
            data=self.df,
            x="category",
            y="value",
            layout_args={"title_x": 0.5},
        )
        self.assertEqual(mock_fig.layout_updates.get("title_x"), 0.5)

    @mock.patch("geemap.plot.px.line")
    def test_line_chart_labels_applied(self, mock_line: mock.Mock) -> None:
        mock_line.return_value = MockFigure()
        plot.line_chart(
            data=self.df,
            x="category",
            y="value",
            x_label="X Axis",
            y_label="Y Axis",
        )
        call_args = mock_line.call_args
        labels = call_args[1].get("labels", {})
        self.assertEqual(labels.get("category"), "X Axis")
        self.assertEqual(labels.get("value"), "Y Axis")

    @mock.patch("geemap.plot.px.line")
    def test_line_chart_legend_title_applied(self, mock_line: mock.Mock) -> None:
        mock_fig = MockFigure()
        mock_line.return_value = mock_fig
        plot.line_chart(data=self.df, x="category", y="value", legend_title="Legend")
        legend = mock_fig.layout_updates.get("legend", {})
        self.assertEqual(legend.get("title"), "Legend")

    def test_line_chart_invalid_data_raises(self) -> None:
        with self.assertRaises(ValueError):
            plot.line_chart(data={"a": 1}, x="x", y="y")

    def test_line_chart_none_data_raises(self) -> None:
        with self.assertRaises(ValueError):
            plot.line_chart(data=None, x="x", y="y")


class TestHistogram(unittest.TestCase):

    def setUp(self) -> None:
        self.df = create_sample_dataframe()

    @mock.patch("geemap.plot.px.histogram")
    def test_histogram_valid_dataframe(self, mock_hist: mock.Mock) -> None:
        mock_hist.return_value = MockFigure()
        result = plot.histogram(data=self.df, x="value")
        self.assertIsNotNone(result)
        mock_hist.assert_called_once()

    @mock.patch("geemap.plot.px.histogram")
    def test_histogram_descending_order(self, mock_hist: mock.Mock) -> None:
        mock_hist.return_value = MockFigure()
        df_copy = self.df.copy()
        plot.histogram(data=df_copy, x="category", y="value", descending=True)
        self.assertEqual(df_copy.iloc[0]["value"], 25)

    @mock.patch("geemap.plot.px.histogram")
    def test_histogram_no_sorting(self, mock_hist: mock.Mock) -> None:
        mock_hist.return_value = MockFigure()
        df_copy = self.df.copy()
        original_first = df_copy.iloc[0]["value"]
        plot.histogram(data=df_copy, x="value", descending=None)
        self.assertEqual(df_copy.iloc[0]["value"], original_first)

    @mock.patch("geemap.plot.px.histogram")
    def test_histogram_max_rows_limit(self, mock_hist: mock.Mock) -> None:
        mock_hist.return_value = MockFigure()
        plot.histogram(data=self.df, x="value", max_rows=3)
        call_args = mock_hist.call_args
        data_passed = call_args[0][0]
        self.assertEqual(len(data_passed), 3)

    @mock.patch("geemap.plot.px.histogram")
    def test_histogram_layout_args_applied(self, mock_hist: mock.Mock) -> None:
        mock_fig = MockFigure()
        mock_hist.return_value = mock_fig
        plot.histogram(
            data=self.df,
            x="value",
            layout_args={"bargap": 0.2},
        )
        self.assertEqual(mock_fig.layout_updates.get("bargap"), 0.2)

    @mock.patch("geemap.plot.px.histogram")
    def test_histogram_labels_applied(self, mock_hist: mock.Mock) -> None:
        mock_hist.return_value = MockFigure()
        plot.histogram(
            data=self.df,
            x="value",
            y="count",
            x_label="Values",
            y_label="Count",
        )
        call_args = mock_hist.call_args
        labels = call_args[1].get("labels", {})
        self.assertEqual(labels.get("value"), "Values")
        self.assertEqual(labels.get("count"), "Count")

    @mock.patch("geemap.plot.px.histogram")
    def test_histogram_title_passed(self, mock_hist: mock.Mock) -> None:
        mock_hist.return_value = MockFigure()
        plot.histogram(data=self.df, x="value", title="Histogram Title")
        call_args = mock_hist.call_args
        self.assertEqual(call_args[1].get("title"), "Histogram Title")

    def test_histogram_invalid_data_raises(self) -> None:
        with self.assertRaises(ValueError):
            plot.histogram(data=123, x="x")

    def test_histogram_none_data_raises(self) -> None:
        with self.assertRaises(ValueError):
            plot.histogram(data=None, x="x")


class TestPieChart(unittest.TestCase):

    def setUp(self) -> None:
        self.df = pd.DataFrame(
            {
                "fruit": ["Apple", "Banana", "Cherry", "Date", "Elderberry"],
                "quantity": [30, 20, 15, 25, 10],
            }
        )

    @mock.patch("geemap.plot.px.pie")
    def test_pie_chart_valid_dataframe(self, mock_pie: mock.Mock) -> None:
        mock_pie.return_value = MockFigure()
        result = plot.pie_chart(data=self.df, names="fruit", values="quantity")
        self.assertIsNotNone(result)
        mock_pie.assert_called_once()

    @mock.patch("geemap.plot.px.pie")
    def test_pie_chart_descending_order(self, mock_pie: mock.Mock) -> None:
        mock_pie.return_value = MockFigure()
        df_copy = self.df.copy()
        plot.pie_chart(data=df_copy, names="fruit", values="quantity", descending=True)
        self.assertEqual(df_copy.iloc[0]["quantity"], 30)

    @mock.patch("geemap.plot.px.pie")
    def test_pie_chart_ascending_order(self, mock_pie: mock.Mock) -> None:
        mock_pie.return_value = MockFigure()
        df_copy = self.df.copy()
        plot.pie_chart(data=df_copy, names="fruit", values="quantity", descending=False)
        self.assertEqual(df_copy.iloc[0]["quantity"], 10)

    @mock.patch("geemap.plot.px.pie")
    def test_pie_chart_max_rows_with_other(self, mock_pie: mock.Mock) -> None:
        mock_pie.return_value = MockFigure()
        df = pd.DataFrame(
            {
                "fruit": ["A", "B", "C", "D", "E", "F"],
                "quantity": [100, 80, 60, 40, 20, 10],
            }
        )
        plot.pie_chart(data=df, names="fruit", values="quantity", max_rows=4)
        call_args = mock_pie.call_args
        data_passed = call_args[1].get("data_frame")
        self.assertIn("Other", data_passed["fruit"].values)

    @mock.patch("geemap.plot.px.pie")
    def test_pie_chart_custom_other_label(self, mock_pie: mock.Mock) -> None:
        mock_pie.return_value = MockFigure()
        df = pd.DataFrame(
            {
                "fruit": ["A", "B", "C", "D", "E"],
                "quantity": [100, 80, 60, 40, 20],
            }
        )
        plot.pie_chart(
            data=df,
            names="fruit",
            values="quantity",
            max_rows=3,
            other_label="Rest",
        )
        call_args = mock_pie.call_args
        data_passed = call_args[1].get("data_frame")
        self.assertIn("Rest", data_passed["fruit"].values)

    @mock.patch("geemap.plot.px.pie")
    def test_pie_chart_donut_hole(self, mock_pie: mock.Mock) -> None:
        mock_pie.return_value = MockFigure()
        plot.pie_chart(data=self.df, names="fruit", values="quantity", hole=0.4)
        call_args = mock_pie.call_args
        self.assertEqual(call_args[1].get("hole"), 0.4)

    @mock.patch("geemap.plot.px.pie")
    def test_pie_chart_layout_args_applied(self, mock_pie: mock.Mock) -> None:
        mock_fig = MockFigure()
        mock_pie.return_value = mock_fig
        plot.pie_chart(
            data=self.df,
            names="fruit",
            values="quantity",
            layout_args={"showlegend": True},
        )
        self.assertEqual(mock_fig.layout_updates.get("showlegend"), True)

    @mock.patch("geemap.plot.px.pie")
    def test_pie_chart_legend_title_applied(self, mock_pie: mock.Mock) -> None:
        mock_fig = MockFigure()
        mock_pie.return_value = mock_fig
        plot.pie_chart(
            data=self.df,
            names="fruit",
            values="quantity",
            legend_title="Fruits",
        )
        legend = mock_fig.layout_updates.get("legend", {})
        self.assertEqual(legend.get("title"), "Fruits")

    @mock.patch("geemap.plot.px.pie")
    def test_pie_chart_title_passed(self, mock_pie: mock.Mock) -> None:
        mock_pie.return_value = MockFigure()
        plot.pie_chart(
            data=self.df, names="fruit", values="quantity", title="Pie Title"
        )
        call_args = mock_pie.call_args
        self.assertEqual(call_args[1].get("title"), "Pie Title")

    @mock.patch("geemap.plot.px.pie")
    def test_pie_chart_opacity_passed(self, mock_pie: mock.Mock) -> None:
        mock_pie.return_value = MockFigure()
        plot.pie_chart(data=self.df, names="fruit", values="quantity", opacity=0.8)
        call_args = mock_pie.call_args
        self.assertEqual(call_args[1].get("opacity"), 0.8)

    def test_pie_chart_invalid_data_raises(self) -> None:
        with self.assertRaises(ValueError):
            plot.pie_chart(data=[1, 2, 3], names="x", values="y")

    def test_pie_chart_none_data_raises(self) -> None:
        with self.assertRaises(ValueError):
            plot.pie_chart(data=None, names="x", values="y")


if __name__ == "__main__":
    unittest.main()
