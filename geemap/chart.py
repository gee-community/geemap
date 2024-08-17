"""Module for creating charts from Earth Engine data.
"""

# *******************************************************************************#
# This module contains core features of the geemap package.                      #
# The Earth Engine team and the geemap community will maintain the core features.#
# *******************************************************************************#

import ee
import pandas as pd
import numpy as np
import bqplot as bq
import ipywidgets as widgets
from bqplot import Tooltip
from bqplot import pyplot as plt
from IPython.display import display
from .common import ee_to_df, zonal_stats, image_dates, hex_to_rgba

from typing import List, Optional, Union, Dict, Any, Tuple


class DataTable(pd.DataFrame):

    def __init__(
        self,
        data: Union[Dict[str, List[Any]], pd.DataFrame, None] = None,
        date_column: Optional[str] = None,
        date_format: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the DataTable with data.

        Args:
            data (Union[Dict[str, List[Any]], pd.DataFrame, None]): The input
                data. If it's a dictionary, it will be converted to a DataFrame.
            date_column (Optional[str]): The date column to convert to a DataFrame.
            date_format (Optional[str]): The format of the date column.
            **kwargs: Additional keyword arguments to pass to the pd.DataFrame
                constructor.
        """
        if isinstance(data, ee.FeatureCollection):
            data = ee_to_df(data)
        elif isinstance(data, ee.List):
            data = data.getInfo()
            kwargs["columns"] = data[0]
            data = data[1:]

        super().__init__(data, **kwargs)

        if date_column is not None:
            self[date_column] = pd.to_datetime(
                self[date_column], format=date_format, errors="coerce"
            )


def transpose_df(
    df: pd.DataFrame,
    label_col: str,
    index_name: str = None,
    indexes: list = None,
) -> pd.DataFrame:
    """
    Transposes a pandas DataFrame and optionally sets a new index name and
        custom indexes.

    Args:
        df (pd.DataFrame): The DataFrame to transpose.
        label_col (str): The column to set as the index before transposing.
        index_name (str, optional): The name to set for the index after
            transposing. Defaults to None.
        indexes (list, optional): A list of custom indexes to set after
            transposing. The length of this list must match the number of rows
            in the transposed DataFrame. Defaults to None.

    Returns:
        pd.DataFrame: The transposed DataFrame.

    Raises:
        ValueError: If `label_col` is not a column in the DataFrame.
        ValueError: If the length of `indexes` does not match the number of
            rows in the transposed DataFrame.
    """
    # Check if the specified column exists in the DataFrame
    if label_col not in df.columns:
        raise ValueError(f"Column '{label_col}' not found in DataFrame")

    # Set the specified column as the index
    transposed_df = df.set_index(label_col).transpose()

    # Set the index name if provided
    if index_name:
        transposed_df.columns.name = index_name

    # Set custom indexes if provided
    if indexes:
        if len(indexes) != len(transposed_df.index):
            raise ValueError(
                "Length of custom indexes must match the number of rows in the transposed DataFrame"
            )
        transposed_df.index = indexes

    return transposed_df


def pivot_df(df: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame:
    """
    Pivots a DataFrame using the specified index, columns, and values.

    Args:
        df (pd.DataFrame): The DataFrame to pivot.
        index (str): The column to use for the index.
        columns (str): The column to use for the columns.
        values (str): The column to use for the values.

    Returns:
        pd.DataFrame: The pivoted DataFrame.
    """
    df_pivot = df.pivot(index=index, columns=columns, values=values).reset_index()
    df_pivot.columns = [index] + [f"{col}" for col in df_pivot.columns[1:]]
    return df_pivot


def array_to_df(
    y_values: Union[ee.Array, ee.List, List[List[float]]],
    x_values: Optional[Union[ee.Array, ee.List, List[float]]] = None,
    y_labels: Optional[List[str]] = None,
    x_label: str = "x",
    axis: int = 1,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Converts arrays or lists of y-values and optional x-values into a pandas DataFrame.

    Args:
        y_values (Union[ee.Array, ee.List, List[List[float]]]): The y-values to convert.
        x_values (Optional[Union[ee.Array, ee.List, List[float]]]): The x-values to convert.
            Defaults to None.
        y_labels (Optional[List[str]]): The labels for the y-values. Defaults to None.
        x_label (str): The label for the x-values. Defaults to "x".
        axis (int): The axis along which to transpose the y-values if needed. Defaults to 1.
        **kwargs: Additional keyword arguments to pass to the pandas DataFrame constructor.

    Returns:
        pd.DataFrame: The resulting DataFrame.
    """

    if isinstance(y_values, ee.Array) or isinstance(y_values, ee.List):
        y_values = y_values.getInfo()

    if isinstance(x_values, ee.Array) or isinstance(x_values, ee.List):
        x_values = x_values.getInfo()

    if axis == 0:
        y_values = np.transpose(y_values)

    if x_values is None:
        x_values = list(range(1, len(y_values[0]) + 1))

    data = {x_label: x_values}

    if not isinstance(y_values[0], list):
        y_values = [y_values]

    if y_labels is None:
        y_labels = [
            f"y{str(i+1).zfill(len(str(len(y_values))))}" for i in range(len(y_values))
        ]

    if len(y_labels) != len(y_values):
        raise ValueError("The length of y_labels must match the length of y_values.")

    for i, series in enumerate(y_labels):
        data[series] = y_values[i]

    df = pd.DataFrame(data, **kwargs)
    return df


class Chart:
    """
    A class to create and display various types of charts from a data table.

    Attributes:
        data_table (pd.DataFrame): The data to be displayed in the charts.
        chart_type (str): The type of chart to create. Supported types are
            'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart', 'PieChart',
            'AreaChart', and 'Table'.
        chart: The bqplot Figure object for the chart.
    """

    def __init__(
        self,
        data_table: Union[Dict[str, List[Any]], pd.DataFrame],
        chart_type: str = "LineChart",
        x_cols: Optional[List[str]] = None,
        y_cols: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the Chart with data.

        Args:
            data_table (Union[Dict[str, List[Any]], pd.DataFrame]): A 2-D array of data.
                If it's a dictionary, it will be converted to a DataFrame.
            chart_type (str): The type of chart to create. Supported types are
                'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart',
                'PieChart', 'AreaChart', and 'Table'.
            x_cols (Optional[List[str]]): The columns to use for the x-axis.
                Defaults to the first column.
            y_cols (Optional[List[str]]): The columns to use for the y-axis.
                Defaults to the second column.
            colors (Optional[List[str]]): The colors to use for the chart.
                Defaults to a predefined list of colors.
            title (Optional[str]): The title of the chart. Defaults to the
                chart type.
            x_label (Optional[str]): The label for the x-axis. Defaults to an
                empty string.
            y_label (Optional[str]): The label for the y-axis. Defaults to an
                empty string.
            **kwargs: Additional keyword arguments to pass to the bqplot Figure
                or mark objects. For axes_options, see
                https://bqplot.github.io/bqplot/api/axes
        """
        self.data_table = DataTable(data_table)
        self.chart_type = chart_type
        self.chart = None
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.x_cols = x_cols
        self.y_cols = y_cols
        self.colors = colors
        self.xlim = kwargs.pop("xlim", None)
        self.ylim = kwargs.pop("ylim", None)

        if title is not None:
            kwargs["title"] = title
        self.figure = plt.figure(**kwargs)

        if chart_type is not None:
            self.set_chart_type(chart_type, **kwargs)

    def display(self) -> None:
        """
        Display the chart without toolbar.
        """
        self._set_plt_options()
        display(self.figure)

    def save_png(self, filepath: str = "chart.png", scale: float = 1.0) -> None:
        """
        Save the chart as a PNG image.

        Args:
            filepath (str): The path to save the PNG image. Defaults to 'chart.png'.
            scale (float): The scale factor for the image. Defaults to 1.0.
        """
        self.figure.save_png(filepath, scale=scale)

    def _ipython_display_(self) -> None:
        """
        Display the chart with toolbar.
        """
        self._set_plt_options()
        plt.show()

    def _set_plt_options(self) -> None:
        """
        Set the title and labels for the chart.
        """
        if self.title is not None:
            self.figure.title = self.title
        if self.x_label is not None:
            plt.xlabel(self.x_label)
        if self.y_label is not None:
            plt.ylabel(self.y_label)
        if self.xlim is not None:
            plt.xlim(self.xlim[0], self.xlim[1])
        if self.ylim is not None:
            plt.ylim(self.ylim[0], self.ylim[1])

    def set_chart_type(
        self,
        chart_type: str,
        clear: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Sets the chart type and other chart properties.

        Args:
            chart_type (str): The type of chart to create. Supported types are
                'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart',
                'PieChart', 'AreaChart', and 'Table'.
            clear (bool): Whether to clear the current chart before setting a new one.
                Defaults to True.
            **kwargs: Additional keyword arguments to pass to the bqplot Figure
                or mark objects.

        Returns:
            Chart: The Chart instance with the chart set.
        """
        if clear:
            plt.clear()
        self.chart_type = chart_type
        x_cols = self.x_cols
        y_cols = self.y_cols
        colors = self.colors

        if x_cols is None:
            x_cols = [self.data_table.columns[0]]
        if y_cols is None:
            y_cols = [self.data_table.columns[1]]

        if isinstance(x_cols, str):
            x_cols = [x_cols]

        if isinstance(y_cols, str):
            y_cols = [y_cols]

        if len(x_cols) == 1 and len(y_cols) > 1:
            x_cols = x_cols * len(y_cols)

        if "axes_options" not in kwargs:
            kwargs["axes_options"] = {
                "x": {"label_offset": "30px"},
                "y": {"label_offset": "40px"},
            }

        if chart_type == "PieChart":
            if colors is None:
                colors = [
                    "#1f77b4",
                    "#ff7f0e",
                    "#2ca02c",
                    "#d62728",
                    "#9467bd",
                    "#8c564b",
                    "#e377c2",
                    "#7f7f7f",
                    "#bcbd22",
                    "#17becf",
                ]  # Default pie chart colors
        else:
            if colors is None:
                colors = [
                    "blue",
                    "orange",
                    "green",
                    "red",
                    "purple",
                    "brown",
                ]  # Default colors

        if chart_type == "IntervalChart":

            x = self.data_table[x_cols[0]]
            y = [self.data_table[y_col] for y_col in y_cols]
            if "fill" not in kwargs:
                kwargs["fill"] = "between"

            self.chart = plt.plot(
                x,
                y,
                colors=colors,
                **kwargs,
            )
        else:
            for i, (x_col, y_col) in enumerate(zip(x_cols, y_cols)):
                color = colors[i % len(colors)]
                if "display_legend" not in kwargs and len(y_cols) > 1:
                    kwargs["display_legend"] = True
                    kwargs["labels"] = [y_col]
                else:
                    kwargs["labels"] = [y_col]

                x = self.data_table[x_col]
                y = self.data_table[y_col]

                if isinstance(x, pd.Series) and (
                    not pd.api.types.is_datetime64_any_dtype(x)
                ):
                    x = x.tolist()
                if isinstance(y, pd.Series) and (
                    not pd.api.types.is_datetime64_any_dtype(y)
                ):
                    y = y.tolist()

                if chart_type == "ScatterChart":
                    self.chart = plt.scatter(
                        x,
                        y,
                        colors=[color],
                        **kwargs,
                    )
                elif chart_type == "LineChart":
                    self.chart = plt.plot(
                        x,
                        y,
                        colors=[color],
                        **kwargs,
                    )
                elif chart_type == "AreaChart":
                    if "fill" not in kwargs:
                        kwargs["fill"] = "bottom"
                    self.chart = plt.plot(
                        x,
                        y,
                        colors=[color],
                        **kwargs,
                    )
                elif chart_type == "ColumnChart":
                    self.chart = plt.bar(
                        x,
                        y,
                        colors=[color],
                        **kwargs,
                    )
                elif chart_type == "BarChart":
                    if "orientation" not in kwargs:
                        kwargs["orientation"] = "horizontal"
                    self.chart = plt.bar(
                        x,
                        y,
                        colors=[color],
                        **kwargs,
                    )
                elif chart_type == "AreaChart":
                    if "fill" not in kwargs:
                        kwargs["fill"] = "bottom"
                    self.chart = plt.plot(
                        x,
                        y,
                        colors=[color],
                        **kwargs,
                    )
                elif chart_type == "PieChart":
                    kwargs.pop("labels", None)
                    self.chart = plt.pie(
                        sizes=y,
                        labels=x,
                        colors=colors[: len(x)],
                        **kwargs,
                    )
                elif chart_type == "Table":
                    output = widgets.Output(**kwargs)
                    with output:
                        display(self.data_table)
                    output.layout = widgets.Layout(width="50%")
                    display(output)
                else:
                    self.chart = plt.plot(
                        x,
                        y,
                        colors=[color],
                        **kwargs,
                    )

        self._set_plt_options()

    def get_chart_type(self) -> Optional[str]:
        """
        Get the current chart type.

        Returns:
            Optional[str]: The current chart type, or None if no chart type is set.
        """
        return self.chart_type

    def get_data_table(self) -> DataTable:
        """
        Get the DataTable used by the chart.

        Returns:
            DataTable: The DataTable instance containing the chart data.
        """
        return self.data_table

    def set_data_table(self, data: Union[Dict[str, List[Any]], pd.DataFrame]) -> None:
        """
        Set a new DataTable for the chart.

        Args:
            data (Union[Dict[str, List[Any]], pd.DataFrame]): The new data to be
            used for the chart.
        """
        self.data_table = DataTable(data)

    def set_options(self, **options: Any) -> None:
        """
        Set additional options for the chart.

        Args:
            **options: Additional options to set for the chart.
        """
        for key, value in options.items():
            setattr(self.figure, key, value)


class BaseChartClass:
    """This should include everything a chart module requires to plot figures."""

    def __init__(
        self,
        features: Union[ee.FeatureCollection, pd.DataFrame],
        default_labels: List[str],
        name: str,
        **kwargs: Any,
    ):
        """
        Initializes the BaseChartClass with the given features, labels, and name.

        Args:
            features (ee.FeatureCollection | pd.DataFrame): The features to plot.
            default_labels (List[str]): The default labels for the chart.
            name (str): The name of the chart.
            **kwargs: Additional keyword arguments to set as attributes.
        """
        self.ylim = None
        self.xlim = None
        self.title = ""
        self.legend_location = "top-left"
        self.layout_width = None
        self.layout_height = None
        self.display_legend = True
        self.x_label = None
        self.y_label = None
        self.labels = default_labels
        self.width = None
        self.height = None
        self.name = name

        if isinstance(self.labels, list) and (len(self.labels) > 1):
            self.colors = [
                "#604791",
                "#1d6b99",
                "#39a8a7",
                "#0f8755",
                "#76b349",
                "#f0af07",
                "#e37d05",
                "#cf513e",
                "#96356f",
                "#724173",
                "#9c4f97",
                "#696969",
            ]
        else:
            self.colors = "black"

        if isinstance(features, ee.FeatureCollection):
            self.df = ee_to_df(features)
        elif isinstance(features, pd.DataFrame):
            self.df = features

        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def get_data(cls) -> None:
        """
        Placeholder method to get data for the chart.
        """
        pass

    @classmethod
    def plot_chart(cls) -> None:
        """
        Placeholder method to plot the chart.
        """
        pass

    def __repr__(self) -> str:
        """
        Returns the string representation of the chart.

        Returns:
            str: The name of the chart.
        """
        return self.name


class BarChart(BaseChartClass):
    """Create Bar Chart. All histogram/bar charts can use this object."""

    def __init__(
        self,
        features: Union[ee.FeatureCollection, pd.DataFrame],
        default_labels: List[str],
        name: str,
        type: str = "grouped",
        **kwargs: Any,
    ):
        """
        Initializes the BarChart with the given features, labels, name, and type.

        Args:
            features (ee.FeatureCollection | pd.DataFrame): The features to plot.
            default_labels (List[str]): The default labels for the chart.
            name (str): The name of the chart.
            type (str, optional): The type of bar chart ('grouped' or 'stacked').
                Defaults to 'grouped'.
            **kwargs: Additional keyword arguments to set as attributes.
        """
        super().__init__(features, default_labels, name, **kwargs)
        self.type: str = type

    def generate_tooltip(self) -> None:
        """
        Generates a tooltip for the bar chart.
        """
        if (self.x_label is not None) and (self.y_label is not None):
            self.bar_chart.tooltip = Tooltip(
                fields=["x", "y"], labels=[self.x_label, self.y_label]
            )
        else:
            self.bar_chart.tooltip = Tooltip(fields=["x", "y"])

    def get_ylim(self) -> Tuple[float, float]:
        """
        Gets the y-axis limits for the bar chart.

        Returns:
            Tuple[float, float]: The minimum and maximum y-axis limits.
        """
        if self.ylim:
            ylim_min, ylim_max = self.ylim[0], self.ylim[1]
        else:
            if self.name in ["feature.byFeature", "feature.byProperty"]:
                ylim_min = np.min(self.y_data)
                ylim_max = np.max(self.y_data) + 0.2 * (
                    np.max(self.y_data) - np.min(self.y_data)
                )
            if self.name in ["feature.groups"]:
                ylim_min = np.min(self.df[self.yProperty])
                ylim_max = np.max(self.df[self.yProperty])
                ylim_max = ylim_max + 0.2 * (ylim_max - ylim_min)
        return (ylim_min, ylim_max)

    def plot_chart(self) -> None:
        """
        Plots the bar chart.
        """
        fig = plt.figure(
            title=self.title,
            legend_location=self.legend_location,
        )

        self.bar_chart = plt.bar(
            self.x_data,
            self.y_data,
            labels=self.labels,
            display_legend=self.display_legend,
        )

        self.generate_tooltip()
        plt.ylim(*self.get_ylim())
        if self.x_label:
            plt.xlabel(self.x_label)
        if self.y_label:
            plt.ylabel(self.y_label)

        if self.width:
            fig.layout.width = self.width
        if self.height:
            fig.layout.height = self.height

        self.bar_chart.colors = self.colors
        self.bar_chart.type = self.type

        plt.show()


class LineChart(BarChart):
    """A class to define variables and get_data method for a line chart."""

    def __init__(
        self,
        features: Union[ee.FeatureCollection, pd.DataFrame],
        labels: List[str],
        name: str = "line.chart",
        **kwargs: Any,
    ):
        """
        Initializes the LineChart with the given features, labels, and name.

        Args:
            features (ee.FeatureCollection | pd.DataFrame): The features to plot.
            labels (List[str]): The labels for the chart.
            name (str, optional): The name of the chart. Defaults to 'line.chart'.
            **kwargs: Additional keyword arguments to set as attributes.
        """
        super().__init__(features, labels, name, **kwargs)

    def plot_chart(self) -> None:
        """
        Plots the line chart.
        """
        fig = plt.figure(
            title=self.title,
            legend_location=self.legend_location,
        )

        self.line_chart = plt.plot(
            self.x_data,
            self.y_data,
            label=self.labels,
        )

        self.generate_tooltip()
        plt.ylim(*self.get_ylim())
        if self.x_label:
            plt.xlabel(self.x_label)
        if self.y_label:
            plt.ylabel(self.y_label)

        if self.width:
            fig.layout.width = self.width
        if self.height:
            fig.layout.height = self.height

        plt.show()


class Feature_ByFeature(BarChart):
    """An object to define variables and get_data method for features by feature."""

    def __init__(
        self,
        features: Union[ee.FeatureCollection, pd.DataFrame],
        x_property: str,
        y_properties: List[str],
        name: str = "feature.byFeature",
        **kwargs: Any,
    ):
        """
        Initializes the Feature_ByFeature with the given features, x_property,
        y_properties, and name.

        Args:
            features (ee.FeatureCollection | pd.DataFrame): The features to plot.
            x_property (str): The property to use for the x-axis.
            y_properties (List[str]): The properties to use for the y-axis.
            name (str, optional): The name of the chart. Defaults to
                'feature.byFeature'.
            **kwargs: Additional keyword arguments to set as attributes.
        """
        default_labels = y_properties
        super().__init__(features, default_labels, name, **kwargs)
        self.x_data, self.y_data = self.get_data(x_property, y_properties)

    def get_data(
        self, x_property: str, y_properties: List[str]
    ) -> Tuple[List[Any], List[Any]]:
        """
        Gets the data for the chart.

        Args:
            x_property (str): The property to use for the x-axis.
            y_properties (List[str]): The properties to use for the y-axis.

        Returns:
            Tuple[List[Any], List[Any]]: The x and y data for the chart.
        """
        x_data = list(self.df[x_property])
        y_data = list(self.df[y_properties].values.T)
        return x_data, y_data


class Feature_ByProperty(BarChart):
    """An object to define variables and get_data method for features by property."""

    def __init__(
        self,
        features: Union[ee.FeatureCollection, pd.DataFrame],
        x_properties: Union[List[str], Dict[str, str]],
        series_property: str,
        name: str = "feature.byProperty",
        **kwargs: Any,
    ):
        """
        Initializes the Feature_ByProperty with the given features, x_properties,
        series_property, and name.

        Args:
            features (ee.FeatureCollection | pd.DataFrame): The features to plot.
            x_properties (List[str] | Dict[str, str]): The properties to use for
                the x-axis.
            series_property (str): The property to use for labeling the series.
            name (str, optional): The name of the chart. Defaults to
                'feature.byProperty'.
            **kwargs: Additional keyword arguments to set as attributes.

        Raises:
            Exception: If 'labels' is in kwargs.
        """
        default_labels = None
        super().__init__(features, default_labels, name, **kwargs)
        if "labels" in kwargs:
            raise Exception("Please remove labels in kwargs and try again.")

        self.labels = list(self.df[series_property])
        self.x_data, self.y_data = self.get_data(x_properties)

    def get_data(
        self, x_properties: Union[List[str], Dict[str, str]]
    ) -> Tuple[List[Any], List[Any]]:
        """
        Gets the data for the chart.

        Args:
            x_properties (List[str] | Dict[str, str]): The properties to use for
                the x-axis.

        Returns:
            Tuple[List[Any], List[Any]]: The x and y data for the chart.

        Raises:
            Exception: If x_properties is not a list or dictionary.
        """
        if isinstance(x_properties, list):
            x_data = x_properties
            y_data = self.df[x_properties].values
        elif isinstance(x_properties, dict):
            x_data = list(x_properties.values())
            y_data = self.df[list(x_properties.keys())].values
        else:
            raise Exception("x_properties must be a list or dictionary.")

        return x_data, y_data


class Feature_Groups(BarChart):
    """An object to define variables and get_data method for feature groups."""

    def __init__(
        self,
        features: Union[ee.FeatureCollection, pd.DataFrame],
        x_property: str,
        y_property: str,
        series_property: str,
        name: str = "feature.groups",
        type: str = "stacked",
        **kwargs: Any,
    ):
        """
        Initializes the Feature_Groups with the given features, x_property,
        y_property, series_property, name, and type.

        Args:
            features (ee.FeatureCollection | pd.DataFrame): The features to plot.
            x_property (str): The property to use for the x-axis.
            y_property (str): The property to use for the y-axis.
            series_property (str): The property to use for labeling the series.
            name (str, optional): The name of the chart. Defaults to 'feature.groups'.
            type (str, optional): The type of bar chart ('grouped' or 'stacked').
                Defaults to 'stacked'.
            **kwargs: Additional keyword arguments to set as attributes.
        """
        df = ee_to_df(features)
        self.unique_series_values = df[series_property].unique().tolist()
        default_labels = [str(x) for x in self.unique_series_values]
        self.yProperty = y_property
        super().__init__(features, default_labels, name, type, **kwargs)

        self.new_column_names = self.get_column_names(series_property, y_property)
        self.x_data, self.y_data = self.get_data(x_property, self.new_column_names)

    def get_column_names(self, series_property: str, y_property: str) -> List[str]:
        """
        Gets the new column names for the DataFrame.

        Args:
            series_property (str): The property to use for labeling the series.
            y_property (str): The property to use for the y-axis.

        Returns:
            List[str]: The new column names.
        """
        new_column_names = []

        for value in self.unique_series_values:
            sample_filter = (self.df[series_property] == value).map({True: 1, False: 0})
            column_name = str(y_property) + "_" + str(value)
            self.df[column_name] = self.df[y_property] * sample_filter
            new_column_names.append(column_name)

        return new_column_names

    def get_data(
        self, x_property: str, new_column_names: List[str]
    ) -> Tuple[List[Any], List[Any]]:
        """
        Gets the data for the chart.

        Args:
            x_property (str): The property to use for the x-axis.
            new_column_names (List[str]): The new column names for the y-axis.

        Returns:
            Tuple[List[Any], List[Any]]: The x and y data for the chart.
        """
        x_data = list(self.df[x_property])
        y_data = [self.df[x] for x in new_column_names]

        return x_data, y_data


def feature_by_feature(
    features: ee.FeatureCollection,
    x_property: str,
    y_properties: List[str],
    **kwargs: Any,
) -> None:
    """
    Generates a Chart from a set of features. Plots the value of one or more
    properties for each feature.
    Reference: https://developers.google.com/earth-engine/guides/charts_feature#uichartfeaturebyfeature

    Args:
        features (ee.FeatureCollection): The feature collection to generate a chart from.
        x_property (str): Features labeled by x_property.
        y_properties (List[str]): Values of y_properties.
        **kwargs: Additional keyword arguments to set as attributes.

    Raises:
        Exception: Errors when creating the chart.
    """
    bar = Feature_ByFeature(
        features=features, x_property=x_property, y_properties=y_properties, **kwargs
    )

    try:
        bar.plot_chart()
    except Exception as e:
        raise Exception(e)


def feature_by_property(
    features: ee.FeatureCollection,
    x_properties: Union[list, dict],
    series_property: str,
    **kwargs,
):
    """Generates a Chart from a set of features. Plots property values of one or
     more features.
    Reference: https://developers.google.com/earth-engine/guides/charts_feature#uichartfeaturebyproperty

    Args:
        features (ee.FeatureCollection): The features to include in the chart.
        x_properties (list | dict): One of (1) a list of properties to be
            plotted on the x-axis; or (2) a (property, label) dictionary
            specifying labels for properties to be used as values on the x-axis.
        series_property (str): The name of the property used to label each
            feature in the legend.

    Raises:
        Exception: If the provided xProperties is not a list or dict.
        Exception: If the chart fails to create.
    """
    bar = Feature_ByProperty(
        features=features,
        x_properties=x_properties,
        series_property=series_property,
        **kwargs,
    )

    try:
        bar.plot_chart()

    except Exception as e:
        raise Exception(e)


def feature_groups(
    features: ee.FeatureCollection,
    x_property: str,
    y_property: str,
    series_property: str,
    **kwargs: Any,
) -> None:
    """
    Generates a Chart from a set of features.
    Plots the value of one property for each feature.

    Reference:
    https://developers.google.com/earth-engine/guides/charts_feature#uichartfeaturegroups

    Args:
        features (ee.FeatureCollection): The feature collection to make a chart from.
        x_property (str): Features labeled by xProperty.
        y_property (str): Features labeled by yProperty.
        series_property (str): The property used to label each feature in the legend.
        **kwargs: Additional keyword arguments to set as attributes.

    Raises:
        Exception: Errors when creating the chart.
    """

    bar = Feature_Groups(
        features=features,
        x_property=x_property,
        y_property=y_property,
        series_property=series_property,
        **kwargs,
    )

    try:
        bar.plot_chart()

    except Exception as e:
        raise Exception(e)


def feature_histogram(
    features: ee.FeatureCollection,
    property: str,
    max_buckets: Optional[int] = None,
    min_bucket_width: Optional[float] = None,
    show: bool = True,
    **kwargs: Any,
) -> Optional[Any]:
    """
    Generates a Chart from a set of features.
    Computes and plots a histogram of the given property.
    - X-axis = Histogram buckets (of property value).
    - Y-axis = Frequency

    Reference:
    https://developers.google.com/earth-engine/guides/charts_feature#uichartfeaturehistogram

    Args:
        features (ee.FeatureCollection): The features to include in the chart.
        property (str): The name of the property to generate the histogram for.
        max_buckets (int, optional): The maximum number of buckets (bins) to use
            when building a histogram; will be rounded up to a power of 2.
        min_bucket_width (float, optional): The minimum histogram bucket width,
            or null to allow any power of 2.
        show (bool, optional): Whether to show the chart. If not, it will return
            the bqplot chart object, which can be used to retrieve data for the
            chart. Defaults to True.
        **kwargs: Additional keyword arguments to set as attributes.

    Raises:
        Exception: If the provided xProperties is not a list or dict.
        Exception: If the chart fails to create.

    Returns:
        Optional[Any]: The bqplot chart object if show is False, otherwise None.
    """
    import math

    if not isinstance(features, ee.FeatureCollection):
        raise Exception("features must be an ee.FeatureCollection")

    first = features.first()
    props = first.propertyNames().getInfo()
    if property not in props:
        raise Exception(
            f"property {property} not found. Available properties: {', '.join(props)}"
        )

    def nextPowerOf2(n):
        return pow(2, math.ceil(math.log2(n)))

    def grow_bin(bin_size, ref):
        while bin_size < ref:
            bin_size *= 2
        return bin_size

    try:
        raw_data = pd.to_numeric(
            pd.Series(features.aggregate_array(property).getInfo())
        )
        y_data = raw_data.tolist()

        if "ylim" in kwargs:
            min_value = kwargs["ylim"][0]
            max_value = kwargs["ylim"][1]
        else:
            min_value = raw_data.min()
            max_value = raw_data.max()

        data_range = max_value - min_value

        if not max_buckets:
            initial_bin_size = nextPowerOf2(data_range / pow(2, 8))
            if min_bucket_width:
                if min_bucket_width < initial_bin_size:
                    bin_size = grow_bin(min_bucket_width, initial_bin_size)
                else:
                    bin_size = min_bucket_width
            else:
                bin_size = initial_bin_size
        else:
            initial_bin_size = math.ceil(data_range / nextPowerOf2(max_buckets))
            if min_bucket_width:
                if min_bucket_width < initial_bin_size:
                    bin_size = grow_bin(min_bucket_width, initial_bin_size)
                else:
                    bin_size = min_bucket_width
            else:
                bin_size = initial_bin_size

        start_bins = (math.floor(min_value / bin_size) * bin_size) - (bin_size / 2)
        end_bins = (math.ceil(max_value / bin_size) * bin_size) + (bin_size / 2)

        if start_bins < min_value:
            y_data.append(start_bins)
        else:
            y_data[y_data.index(min_value)] = start_bins
        if end_bins > max_value:
            y_data.append(end_bins)
        else:
            y_data[y_data.index(max_value)] = end_bins

        num_bins = math.floor((end_bins - start_bins) / bin_size)

        if "title" not in kwargs:
            title = ""
        else:
            title = kwargs["title"]

        fig = plt.figure(title=title)

        if "width" in kwargs:
            fig.layout.width = kwargs["width"]
        if "height" in kwargs:
            fig.layout.height = kwargs["height"]

        if "x_label" not in kwargs:
            x_label = ""
        else:
            x_label = kwargs["x_label"]

        if "y_label" not in kwargs:
            y_label = ""
        else:
            y_label = kwargs["y_label"]

        histogram = plt.hist(
            sample=y_data,
            bins=num_bins,
            axes_options={"count": {"label": y_label}, "sample": {"label": x_label}},
        )

        if "colors" in kwargs:
            histogram.colors = kwargs["colors"]
        if "stroke" in kwargs:
            histogram.stroke = kwargs["stroke"]
        else:
            histogram.stroke = "#ffffff00"
        if "stroke_width" in kwargs:
            histogram.stroke_width = kwargs["stroke_width"]
        else:
            histogram.stroke_width = 0

        if ("x_label" in kwargs) and ("y_label" in kwargs):
            histogram.tooltip = Tooltip(
                fields=["midpoint", "count"],
                labels=[kwargs["x_label"], kwargs["y_label"]],
            )
        else:
            histogram.tooltip = Tooltip(fields=["midpoint", "count"])

        if show:
            plt.show()
        else:
            return histogram

    except Exception as e:
        raise Exception(e)


def image_by_class(
    image: ee.Image,
    class_band: str,
    region: Union[ee.Geometry, ee.FeatureCollection],
    reducer: Union[str, ee.Reducer] = "MEAN",
    scale: Optional[int] = None,
    class_labels: Optional[List[str]] = None,
    x_labels: Optional[List[str]] = None,
    chart_type: str = "LineChart",
    **kwargs: Any,
) -> Any:
    """
    Generates a Chart from an image by class. Extracts and plots band values by class.

    Args:
        image (ee.Image): Image to extract band values from.
        class_band (str): The band name to use as class labels.
        region (ee.Geometry | ee.FeatureCollection): The region(s) to reduce.
        reducer (str | ee.Reducer, optional): The reducer type for zonal statistics. Can
            be one of 'mean', 'median', 'sum', 'min', 'max', etc. Defaults to 'MEAN'.
        scale (int, optional): The scale in meters at which to perform the analysis.
        class_labels (List[str], optional): List of class labels.
        x_labels (List[str], optional): List of x-axis labels.
        chart_type (str, optional): The type of chart to create. Supported types are
            'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart', 'PieChart',
            'AreaChart', and 'Table'. Defaults to 'LineChart'.
        **kwargs: Additional keyword arguments.

    Returns:
        Any: The generated chart.
    """
    fc = zonal_stats(
        image, region, stat_type=reducer, scale=scale, verbose=False, return_fc=True
    )
    bands = image.bandNames().getInfo()
    df = ee_to_df(fc)[bands + [class_band]]

    df_transposed = df.set_index(class_band).T

    if x_labels is not None:
        df_transposed["label"] = x_labels
    else:
        df_transposed["label"] = df_transposed.index

    if class_labels is None:
        y_cols = df_transposed.columns.tolist()
        y_cols.remove("label")
    else:
        y_cols = class_labels

    fig = Chart(
        df_transposed, chart_type=chart_type, x_cols="label", y_cols=y_cols, **kwargs
    )
    return fig


def image_by_region(
    image: ee.Image,
    regions: Union[ee.FeatureCollection, ee.Geometry],
    reducer: Union[str, ee.Reducer],
    scale: int,
    x_property: str,
    **kwargs: Any,
) -> None:
    """
    Generates a Chart from an image. Extracts and plots band values in one or more
    regions in the image, with each band in a separate series.

    Args:
        image (ee.Image): Image to extract band values from.
        regions (ee.FeatureCollection | ee.Geometry): Regions to reduce.
            Defaults to the image's footprint.
        reducer (str | ee.Reducer): The reducer type for zonal statistics. Can
            be one of 'mean', 'median', 'sum', 'min', 'max', etc.
        scale (int): The scale in meters at which to perform the analysis.
        x_property (str): The name of the property in the feature collection to
            use as the x-axis values.
        **kwargs: Additional keyword arguments to be passed to the
            `feature_by_feature` function.

    Returns:
        None
    """

    fc = zonal_stats(
        image, regions, stat_type=reducer, scale=scale, verbose=False, return_fc=True
    )
    bands = image.bandNames().getInfo()
    df = ee_to_df(fc)[bands + [x_property]]
    feature_by_feature(df, x_property, bands, **kwargs)


def image_doy_series(
    image_collection: ee.ImageCollection,
    region: Optional[Union[ee.Geometry, ee.FeatureCollection]] = None,
    region_reducer: Optional[Union[str, ee.Reducer]] = None,
    scale: Optional[int] = None,
    year_reducer: Optional[Union[str, ee.Reducer]] = None,
    start_day: int = 1,
    end_day: int = 366,
    chart_type: str = "LineChart",
    colors: Optional[List[str]] = None,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    **kwargs: Any,
) -> Chart:
    """
    Generates a time series chart of an image collection for a specific region
        over a range of days of the year.

    Args:
        image_collection (ee.ImageCollection): The image collection to analyze.
        region (Optional[Union[ee.Geometry, ee.FeatureCollection]]): The region
            to reduce.
        region_reducer (Optional[Union[str, ee.Reducer]]): The reducer type for
            zonal statistics.Can be one of 'mean', 'median', 'sum', 'min', 'max', etc.
        scale (Optional[int]): The scale in meters at which to perform the analysis.
        year_reducer (Optional[Union[str, ee.Reducer]]): The reducer type for
            yearly statistics.
        start_day (int): The start day of the year.
        end_day (int): The end day of the year.
        chart_type (str): The type of chart to create. Supported types are
            'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart',
            'PieChart', 'AreaChart', and 'Table'.
        colors (Optional[List[str]]): The colors to use for the chart.
            Defaults to a predefined list of colors.
        title (Optional[str]): The title of the chart. Defaults to the
            chart type.
        x_label (Optional[str]): The label for the x-axis. Defaults to an
            empty string.
        y_label (Optional[str]): The label for the y-axis. Defaults to an
            empty string.
        **kwargs: Additional keyword arguments to pass to the bqplot Figure
            or mark objects. For axes_options, see
            https://bqplot.github.io/bqplot/api/axes

    Returns:
        Chart: The generated chart.
    """

    # Function to add day-of-year ('doy') and year properties to each image.
    def set_doys(collection):
        def add_doy(img):
            date = img.date()
            year = date.get("year")
            doy = date.getRelative("day", "year").floor().add(1)
            return img.set({"doy": doy, "year": year})

        return collection.map(add_doy)

    # Reduces images with the same day of year.
    def group_by_doy(collection, start, end, reducer):
        collection = set_doys(collection)

        doys = ee.FeatureCollection(
            [ee.Feature(None, {"doy": i}) for i in range(start, end + 1)]
        )

        # Group images by their day of year.
        filter = ee.Filter(ee.Filter.equals(leftField="doy", rightField="doy"))
        joined = ee.Join.saveAll("matches").apply(
            primary=doys, secondary=collection, condition=filter
        )

        # For each DoY, reduce images across years.
        def reduce_images(doy):
            images = ee.ImageCollection.fromImages(doy.get("matches"))
            image = images.reduce(reducer)
            return image.set(
                {
                    "doy": doy.get("doy"),
                    "geo": images.geometry(),  # // Retain geometry for future reduceRegion.
                }
            )

        return ee.ImageCollection(joined.map(reduce_images))

    # Set default values and filters if parameters are not provided.
    region_reducer = region_reducer or ee.Reducer.mean()
    year_reducer = year_reducer or ee.Reducer.mean()

    # Optionally filter the image collection by region.
    filtered_collection = image_collection
    if region:
        filtered_collection = filtered_collection.filterBounds(region)
    filtered_collection = set_doys(filtered_collection)

    doy_images = group_by_doy(filtered_collection, start_day, end_day, year_reducer)

    # For each DoY, reduce images across years within the region.
    def reduce_doy_images(image):
        region_for_image = region if region else image.get("geo")
        dictionary = image.reduceRegion(
            reducer=region_reducer, geometry=region_for_image, scale=scale
        )

        return ee.Feature(None, {"doy": image.get("doy")}).set(dictionary)

    reduced = ee.FeatureCollection(doy_images.map(reduce_doy_images))

    df = ee_to_df(reduced)
    df.columns = df.columns.str.replace(r"_.*", "", regex=True)

    x_cols = "doy"
    y_cols = df.columns.tolist()
    y_cols.remove("doy")

    fig = Chart(
        df,
        chart_type,
        x_cols,
        y_cols,
        colors,
        title,
        x_label,
        y_label,
        **kwargs,
    )
    return fig


def image_doy_series_by_region(
    image_collection: ee.ImageCollection,
    band_name: str,
    regions: ee.FeatureCollection,
    region_reducer: Optional[Union[str, ee.Reducer]] = None,
    scale: Optional[int] = None,
    year_reducer: Optional[Union[str, ee.Reducer]] = None,
    series_property: Optional[str] = None,
    start_day: int = 1,
    end_day: int = 366,
    chart_type: str = "LineChart",
    colors: Optional[List[str]] = None,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    **kwargs: Any,
) -> Chart:
    """
    Generates a time series chart of an image collection for multiple regions
    over a range of days of the year.

    Args:
        image_collection (ee.ImageCollection): The image collection to analyze.
        band_name (str): The name of the band to analyze.
        regions (ee.FeatureCollection): The regions to analyze.
        region_reducer (Optional[Union[str, ee.Reducer]]): The reducer type for
            zonal statistics.
        scale (Optional[int]): The scale in meters at which to perform the analysis.
        year_reducer (Optional[Union[str, ee.Reducer]]): The reducer type for
            yearly statistics.
        series_property (Optional[str]): The property to use for labeling the series.
        start_day (int): The start day of the year.
        end_day (int): The end day of the year.
        chart_type (str): The type of chart to create. Supported types are
            'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart',
            'PieChart', 'AreaChart', and 'Table'.
        colors (Optional[List[str]]): The colors to use for the chart.
            Defaults to a predefined list of colors.
        title (Optional[str]): The title of the chart. Defaults to the
            chart type.
        x_label (Optional[str]): The label for the x-axis. Defaults to an
            empty string.
        y_label (Optional[str]): The label for the y-axis. Defaults to an
            empty string.
        **kwargs: Additional keyword arguments to pass to the bqplot Figure
            or mark objects. For axes_options, see
            https://bqplot.github.io/bqplot/api/axes

    Returns:
        Chart: The generated chart.
    """

    image_collection = image_collection.select(band_name)

    # Function to add day-of-year ('doy') and year properties to each image.
    def set_doys(collection):
        def add_doy(img):
            date = img.date()
            year = date.get("year")
            doy = date.getRelative("day", "year").floor().add(1)
            return img.set({"doy": doy, "year": year})

        return collection.map(add_doy)

    # Reduces images with the same day of year.
    def group_by_doy(collection, start, end, reducer):
        collection = set_doys(collection)

        doys = ee.FeatureCollection(
            [ee.Feature(None, {"doy": i}) for i in range(start, end + 1)]
        )

        # Group images by their day of year.
        filter = ee.Filter(ee.Filter.equals(leftField="doy", rightField="doy"))
        joined = ee.Join.saveAll("matches").apply(
            primary=doys, secondary=collection, condition=filter
        )

        # For each DoY, reduce images across years.
        def reduce_images(doy):
            images = ee.ImageCollection.fromImages(doy.get("matches"))
            image = images.reduce(reducer)
            return image.set(
                {
                    "doy": doy.get("doy"),
                    "geo": images.geometry(),  # // Retain geometry for future reduceRegion.
                }
            )

        return ee.ImageCollection(joined.map(reduce_images))

    if year_reducer is None:
        year_reducer = ee.Reducer.mean()
    if region_reducer is None:
        region_reducer = ee.Reducer.mean()

    doy_images = group_by_doy(image_collection, start_day, end_day, year_reducer)

    if series_property is None:
        series_property = "system:index"
    regions = regions.select([series_property])
    fc = zonal_stats(
        doy_images.toBands(),
        regions,
        stat_type=region_reducer,
        scale=scale,
        verbose=False,
        return_fc=True,
    )
    df = ee_to_df(fc)
    df = transpose_df(df, label_col=series_property, index_name="doy")
    df["doy"] = df.index.str.split("_").str[0].astype(int)
    df.sort_values("doy", inplace=True)
    y_cols = df.columns.tolist()
    y_cols.remove("doy")

    fig = Chart(
        df,
        chart_type,
        "doy",
        y_cols,
        colors,
        title,
        x_label,
        y_label,
        **kwargs,
    )
    return fig


def doy_series_by_year(
    image_collection: ee.ImageCollection,
    band_name: str,
    region: Optional[Union[ee.Geometry, ee.FeatureCollection]] = None,
    region_reducer: Optional[Union[str, ee.Reducer]] = None,
    scale: Optional[int] = None,
    same_day_reducer: Optional[Union[str, ee.Reducer]] = None,
    start_day: int = 1,
    end_day: int = 366,
    chart_type: str = "LineChart",
    colors: Optional[List[str]] = None,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    **kwargs: Any,
) -> Chart:
    """
    Generates a time series chart of an image collection for a specific region
    over multiple years.

    Args:
        image_collection (ee.ImageCollection): The image collection to analyze.
        band_name (str): The name of the band to analyze.
        region (Optional[Union[ee.Geometry, ee.FeatureCollection]]): The region
            to analyze.
        region_reducer (Optional[Union[str, ee.Reducer]]): The reducer type for
            zonal statistics.
        scale (Optional[int]): The scale in meters at which to perform the analysis.
        same_day_reducer (Optional[Union[str, ee.Reducer]]): The reducer type
            for daily statistics.
        start_day (int): The start day of the year.
        end_day (int): The end day of the year.
        chart_type (str): The type of chart to create. Supported types are
            'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart',
            'PieChart', 'AreaChart', and 'Table'.
        colors (Optional[List[str]]): The colors to use for the chart.
            Defaults to a predefined list of colors.
        title (Optional[str]): The title of the chart. Defaults to the
            chart type.
        x_label (Optional[str]): The label for the x-axis. Defaults to an
            empty string.
        y_label (Optional[str]): The label for the y-axis. Defaults to an
            empty string.
        **kwargs: Additional keyword arguments to pass to the bqplot Figure
            or mark objects. For axes_options, see
            https://bqplot.github.io/bqplot/api/axes

    Returns:
        Chart: The generated chart.
    """

    # Function to add day-of-year ('doy') and year properties to each image.
    def set_doys(collection):
        def add_doy(img):
            date = img.date()
            year = date.get("year")
            doy = date.getRelative("day", "year").floor().add(1)
            return img.set({"doy": doy, "year": year})

        return collection.map(add_doy)

    # Set default values and filters if parameters are not provided.
    region_reducer = region_reducer or ee.Reducer.mean()
    same_day_reducer = same_day_reducer or ee.Reducer.mean()

    # Optionally filter the image collection by region.
    filtered_collection = image_collection
    if region:
        filtered_collection = filtered_collection.filterBounds(region)
    filtered_collection = set_doys(filtered_collection)

    # Filter image collection by day of year.
    filtered_collection = filtered_collection.filter(
        ee.Filter.calendarRange(start_day, end_day, "day_of_year")
    )

    # Generate a feature for each (doy, value, year) combination.
    def create_feature(image):
        value = (
            image.select(band_name)
            .reduceRegion(reducer=region_reducer, geometry=region, scale=scale)
            .get(band_name)
        )  # Get the reduced value for the given band.
        return ee.Feature(
            None, {"doy": image.get("doy"), "year": image.get("year"), "value": value}
        )

    tuples = filtered_collection.map(create_feature)

    # Group by unique (doy, year) pairs.
    distinct_doy_year = tuples.distinct(["doy", "year"])

    # Join the original tuples with the distinct (doy, year) pairs.
    filter = ee.Filter.And(
        ee.Filter.equals(leftField="doy", rightField="doy"),
        ee.Filter.equals(leftField="year", rightField="year"),
    )
    joined = ee.Join.saveAll("matches").apply(
        primary=distinct_doy_year, secondary=tuples, condition=filter
    )

    # For each (doy, year), reduce the values of the joined features.
    def reduce_features(doy_year):
        features = ee.FeatureCollection(ee.List(doy_year.get("matches")))
        value = features.aggregate_array("value").reduce(same_day_reducer)
        return doy_year.set("value", value)

    reduced = joined.map(reduce_features)

    df = ee_to_df(reduced, columns=["doy", "year", "value"])
    df = pivot_df(df, index="doy", columns="year", values="value")
    y_cols = df.columns.tolist()[1:]
    x_cols = "doy"

    fig = Chart(
        df,
        chart_type,
        x_cols,
        y_cols,
        colors,
        title,
        x_label,
        y_label,
        **kwargs,
    )
    return fig


def image_histogram(
    image: ee.Image,
    region: ee.Geometry,
    scale: int,
    max_buckets: int,
    min_bucket_width: float,
    max_raw: int,
    max_pixels: int,
    reducer_args: Dict[str, Any] = {},
    **kwargs: Dict[str, Any],
) -> bq.Figure:
    """
    Creates a histogram for each band of the specified image within the given
    region using bqplot.

    Args:
        image (ee.Image): The Earth Engine image for which to create histograms.
        region (ee.Geometry): The region over which to calculate the histograms.
        scale (int): The scale in meters of the calculation.
        max_buckets (int): The maximum number of buckets in the histogram.
        min_bucket_width (float): The minimum width of the buckets in the histogram.
        max_raw (int): The maximum number of pixels to include in the histogram.
        max_pixels (int): The maximum number of pixels to reduce.
        reducer_args (Dict[str, Any]): Additional arguments to pass to the image.reduceRegion.

    Keyword Args:
        colors (List[str]): Colors for the histograms of each band.
        labels (List[str]): Labels for the histograms of each band.
        title (str): Title of the combined histogram plot.
        legend_location (str): Location of the legend in the plot.

    Returns:
        bq.Figure: The bqplot figure containing the histograms.
    """
    # Calculate the histogram data.
    histogram = image.reduceRegion(
        reducer=ee.Reducer.histogram(
            maxBuckets=max_buckets, minBucketWidth=min_bucket_width, maxRaw=max_raw
        ),
        geometry=region,
        scale=scale,
        maxPixels=max_pixels,
        **reducer_args,
    )

    histograms = {
        band: histogram.get(band).getInfo() for band in image.bandNames().getInfo()
    }

    # Create bqplot histograms for each band.
    def create_histogram(
        hist_data: Dict[str, Any], color: str, label: str
    ) -> bq.Figure:
        """
        Creates a bqplot histogram for the given histogram data.

        Args:
            hist_data (dict): The histogram data.
            color (str): The color of the histogram.
            label (str): The label of the histogram.

        Returns:
            bq.Figure: The bqplot figure for the histogram.
        """
        x_data = np.array(hist_data["bucketMeans"])
        y_data = np.array(hist_data["histogram"])

        x_sc = bq.LinearScale()
        y_sc = bq.LinearScale()

        bar = bq.Bars(
            x=x_data,
            y=y_data,
            scales={"x": x_sc, "y": y_sc},
            colors=[color],
            display_legend=True,
            labels=[label],
        )

        ax_x = bq.Axis(scale=x_sc, label="Reflectance (x1e4)", tick_format="0.0f")
        ax_y = bq.Axis(
            scale=y_sc, orientation="vertical", label="Count", tick_format="0.0f"
        )

        return bq.Figure(marks=[bar], axes=[ax_x, ax_y])

    # Define colors and labels for the bands.
    band_colors = kwargs.get("colors", ["#cf513e", "#1d6b99", "#f0af07"])
    band_labels = kwargs.get("labels", image.bandNames().getInfo())

    # Create and combine histograms for each band.
    histograms_fig = []
    for band, color, label in zip(histograms.keys(), band_colors, band_labels):
        histograms_fig.append(create_histogram(histograms[band], color, label))

    combined_fig = bq.Figure(
        marks=[fig.marks[0] for fig in histograms_fig],
        axes=histograms_fig[0].axes,
        **kwargs,
    )

    for fig, label in zip(histograms_fig, band_labels):
        fig.marks[0].labels = [label]

    combined_fig.legend_location = kwargs.get("legend_location", "top-right")

    return combined_fig


def image_regions(
    image: ee.Image,
    regions: Union[ee.FeatureCollection, ee.Geometry],
    reducer: Union[str, ee.Reducer],
    scale: int,
    series_property: str,
    x_labels: List[str],
    **kwargs: Any,
) -> None:
    """
    Generates a Chart from an image by regions. Extracts and plots band values
    in multiple regions.

    Args:
        image (ee.Image): Image to extract band values from.
        regions (Union[ee.FeatureCollection, ee.Geometry]): Regions to reduce.
            Defaults to the image's footprint.
        reducer (Union[str, ee.Reducer]): The reducer type for zonal statistics.
            Can be one of 'mean', 'median', 'sum', 'min', 'max', etc.
        scale (int): The scale in meters at which to perform the analysis.
        series_property (str): The property to use for labeling the series.
        x_labels (List[str]): List of x-axis labels.
        **kwargs: Additional keyword arguments.

    Returns:
        bq.Figure: The bqplot figure.
    """
    fc = zonal_stats(
        image, regions, stat_type=reducer, scale=scale, verbose=False, return_fc=True
    )
    bands = image.bandNames().getInfo()
    fc = fc.select(bands + [series_property])
    return feature_by_property(fc, x_labels, series_property, **kwargs)


def image_series(
    image_collection: ee.ImageCollection,
    region: Union[ee.Geometry, ee.FeatureCollection],
    reducer: Optional[Union[str, ee.Reducer]] = None,
    scale: Optional[int] = None,
    x_property: str = "system:time_start",
    chart_type: str = "LineChart",
    x_cols: Optional[List[str]] = None,
    y_cols: Optional[List[str]] = None,
    colors: Optional[List[str]] = None,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    **kwargs: Any,
) -> Chart:
    """
    Generates a time series chart of an image collection for a specific region.

    Args:
        image_collection (ee.ImageCollection): The image collection to analyze.
        region (Union[ee.Geometry, ee.FeatureCollection]): The region to reduce.
        reducer (Optional[Union[str, ee.Reducer]]): The reducer to use.
        scale (Optional[int]): The scale in meters at which to perform the analysis.
        x_property (str): The name of the property to use as the x-axis values.
        chart_type (str): The type of chart to create. Supported types are
            'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart',
            'PieChart', 'AreaChart', and 'Table'.
        x_cols (Optional[List[str]]): The columns to use for the x-axis.
            Defaults to the first column.
        y_cols (Optional[List[str]]): The columns to use for the y-axis.
            Defaults to the second column.
        colors (Optional[List[str]]): The colors to use for the chart.
            Defaults to a predefined list of colors.
        title (Optional[str]): The title of the chart. Defaults to the
            chart type.
        x_label (Optional[str]): The label for the x-axis. Defaults to an
            empty string.
        y_label (Optional[str]): The label for the y-axis. Defaults to an
            empty string.
        **kwargs: Additional keyword arguments to pass to the bqplot Figure
            or mark objects. For axes_options, see
            https://bqplot.github.io/bqplot/api/axes

    Returns:
        Chart: The chart object.
    """

    if reducer is None:
        reducer = ee.Reducer.mean()

    band_names = image_collection.first().bandNames().getInfo()

    # Function to reduce the region and get the mean for each image.
    def get_stats(image):
        stats = image.reduceRegion(reducer=reducer, geometry=region, scale=scale)

        results = {}
        for band in band_names:
            results[band] = stats.get(band)

        if x_property == "system:time_start" or x_property == "system:time_end":
            results["date"] = image.date().format("YYYY-MM-dd")
        else:
            results[x_property] = image.get(x_property).getInfo()

        return ee.Feature(None, results)

    # Apply the function over the image collection.
    fc = ee.FeatureCollection(
        image_collection.map(get_stats).filter(ee.Filter.notNull(band_names))
    )
    df = ee_to_df(fc)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

    fig = Chart(
        df,
        chart_type,
        x_cols,
        y_cols,
        colors,
        title,
        x_label,
        y_label,
        **kwargs,
    )
    return fig


def image_series_by_region(
    image_collection: ee.ImageCollection,
    regions: Union[ee.FeatureCollection, ee.Geometry],
    reducer: Optional[Union[str, ee.Reducer]] = None,
    band: Optional[str] = None,
    scale: Optional[int] = None,
    x_property: str = "system:time_start",
    series_property: str = "system:index",
    chart_type: str = "LineChart",
    x_cols: Optional[List[str]] = None,
    y_cols: Optional[List[str]] = None,
    colors: Optional[List[str]] = None,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    **kwargs: Any,
) -> Chart:
    """
    Generates a time series chart of an image collection for multiple regions.

    Args:
        image_collection (ee.ImageCollection): The image collection to analyze.
        regions (ee.FeatureCollection | ee.Geometry): The regions to reduce.
        reducer (str | ee.Reducer): The reducer type for zonal statistics.
        band (str): The name of the band to analyze.
        scale (int): The scale in meters at which to perform the analysis.
        x_property (str): The name of the property to use as the x-axis values.
        series_property (str): The property to use for labeling the series.
        chart_type (str): The type of chart to create. Supported types are
            'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart',
            'PieChart', 'AreaChart', and 'Table'.
        x_cols (Optional[List[str]]): The columns to use for the x-axis.
            Defaults to the first column.
        y_cols (Optional[List[str]]): The columns to use for the y-axis.
            Defaults to the second column.
        colors (Optional[List[str]]): The colors to use for the chart.
            Defaults to a predefined list of colors.
        title (Optional[str]): The title of the chart. Defaults to the
            chart type.
        x_label (Optional[str]): The label for the x-axis. Defaults to an
            empty string.
        y_label (Optional[str]): The label for the y-axis. Defaults to an
            empty string.
        **kwargs: Additional keyword arguments to pass to the bqplot Figure
            or mark objects. For axes_options, see
            https://bqplot.github.io/bqplot/api/axes

    Returns:
        Chart: The chart object.
    """
    if reducer is None:
        reducer = ee.Reducer.mean()

    if band is None:
        band = image_collection.first().bandNames().get(0).getInfo()

    image = image_collection.select(band).toBands()

    fc = zonal_stats(
        image, regions, stat_type=reducer, scale=scale, verbose=False, return_fc=True
    )
    columns = image.bandNames().getInfo() + [series_property]
    df = ee_to_df(fc, columns=columns)

    headers = df[series_property].tolist()
    df = df.drop(columns=[series_property]).T
    df.columns = headers

    if x_property == "system:time_start" or x_property == "system:time_end":
        indexes = image_dates(image_collection).getInfo()
        df["index"] = pd.to_datetime(indexes)

    else:
        indexes = image_collection.aggregate_array(x_property).getInfo()
        df["index"] = indexes

    fig = Chart(
        df,
        chart_type,
        x_cols,
        y_cols,
        colors,
        title,
        x_label,
        y_label,
        **kwargs,
    )
    return fig


def array_values(
    array: Union[ee.Array, ee.List, List[List[float]]],
    x_labels: Optional[Union[ee.Array, ee.List, List[float]]] = None,
    axis: int = 1,
    series_names: Optional[List[str]] = None,
    chart_type: str = "LineChart",
    colors: Optional[List[str]] = None,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    **kwargs: Any,
) -> Chart:
    """
    Converts an array to a DataFrame and generates a chart.

    Args:
        array (Union[ee.Array, ee.List, List[List[float]]]): The array to convert.
        x_labels (Optional[Union[ee.Array, ee.List, List[float]]]): The labels
            for the x-axis. Defaults to None.
        axis (int): The axis along which to transpose the array if needed. Defaults to 1.
        series_names (Optional[List[str]]): The names of the series. Defaults to None.
        chart_type (str): The type of chart to create. Defaults to "LineChart".
        colors (Optional[List[str]]): The colors to use for the chart. Defaults to None.
        title (Optional[str]): The title of the chart. Defaults to None.
        x_label (Optional[str]): The label for the x-axis. Defaults to None.
        y_label (Optional[str]): The label for the y-axis. Defaults to None.
        **kwargs: Additional keyword arguments to pass to the Chart constructor.

    Returns:
        Chart: The generated chart.
    """

    df = array_to_df(array, x_values=x_labels, y_labels=series_names, axis=axis)
    fig = Chart(
        df,
        x_cols=["x"],
        y_cols=df.columns.tolist()[1:],
        chart_type=chart_type,
        colors=colors,
        title=title,
        x_label=x_label,
        y_label=y_label,
        **kwargs,
    )
    return fig
