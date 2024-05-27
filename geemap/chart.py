"""Module for creating charts for Earth Engine data.
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
from .common import ee_to_df, zonal_stats

from typing import List, Optional, Union, Dict, Any


class DataTable(pd.DataFrame):

    def __init__(
        self,
        data: Union[Dict[str, List[Any]], pd.DataFrame, None] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the DataTable with data.

        Args:
            data (Union[Dict[str, List[Any]], pd.DataFrame, None]): The input
                data. If it's a dictionary, it will be converted to a DataFrame.
            **kwargs: Additional keyword arguments to pass to the pd.DataFrame
                constructor.
        """
        if isinstance(data, ee.FeatureCollection):
            data = ee_to_df(data)

        super().__init__(data, **kwargs)


class Chart:
    """
    A class to create and display various types of charts from data.

    Attributes:
        df (pd.DataFrame): The data to be displayed in the charts.
        chart: The bqplot Figure object for the chart.
    """

    def __init__(
        self,
        data: Union[Dict[str, List[Any]], pd.DataFrame],
        chart_type: str = "LineChart",
        x_cols: Optional[List[str]] = None,
        y_cols: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the Chart with data.

        Args:
            data (Union[Dict[str, List[Any]], pd.DataFrame]): The input data.
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
            xlabel (Optional[str]): The label for the x-axis. Defaults to an
                empty string.
            ylabel (Optional[str]): The label for the y-axis. Defaults to an
                empty string.
            options (Optional[Dict[str, Any]]): Additional options for the chart.
            **kwargs: Additional keyword arguments to pass to the bqplot Figure
                or mark objects.
        """
        self.df = DataTable(data)
        self.chart_type = chart_type
        self.chart = None
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.x_cols = x_cols
        self.y_cols = y_cols
        self.colors = colors
        self.options = options

        if title is not None:
            kwargs["title"] = title
        self.figure = plt.figure(**kwargs)

        if chart_type is not None:
            self.set_chart_type(chart_type, **kwargs)

    def display(self) -> None:
        """
        Display the chart without toolbar.
        """
        self._set_title_and_labels()
        display(self.figure)

    def _ipython_display_(self) -> None:
        """
        Display the chart with toolbar.
        """
        self._set_title_and_labels()
        plt.show()

    def _set_title_and_labels(self) -> None:
        """
        Set the title and labels for the chart.
        """
        if self.title is not None:
            self.figure.title = self.title
        if self.xlabel is not None:
            plt.xlabel(self.xlabel)
        if self.ylabel is not None:
            plt.ylabel(self.ylabel)

    def set_chart_type(
        self,
        chart_type: str,
        clear: bool = True,
        **kwargs: Any,
    ):
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
            x_cols = [self.df.columns[0]]
        if y_cols is None:
            y_cols = [self.df.columns[1]]

        if isinstance(x_cols, str):
            x_cols = [x_cols]

        if isinstance(y_cols, str):
            y_cols = [y_cols]

        if len(x_cols) == 1 and len(y_cols) > 1:
            x_cols = x_cols * len(y_cols)

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

        for i, (x_col, y_col) in enumerate(zip(x_cols, y_cols)):
            color = colors[i % len(colors)]
            if "display_legend" not in kwargs and len(y_cols) > 1:
                kwargs["display_legend"] = True
                kwargs["labels"] = [y_col]
            else:
                kwargs["labels"] = [y_col]

            if chart_type == "ScatterChart":
                self.chart = plt.scatter(
                    self.df[x_col].tolist(),
                    self.df[y_col].tolist(),
                    colors=[color],
                    **kwargs,
                )
            elif chart_type == "LineChart":
                self.chart = plt.plot(
                    self.df[x_col].tolist(),
                    self.df[y_col].tolist(),
                    colors=[color],
                    **kwargs,
                )
            elif chart_type == "ColumnChart":
                self.chart = plt.bar(
                    self.df[x_col].tolist(),
                    self.df[y_col].tolist(),
                    colors=[color],
                    **kwargs,
                )
            elif chart_type == "BarChart":
                if "orientation" not in kwargs:
                    kwargs["orientation"] = "horizontal"
                self.chart = plt.bar(
                    self.df[x_col].tolist(),
                    self.df[y_col].tolist(),
                    colors=[color],
                    **kwargs,
                )
            elif chart_type == "AreaChart":
                if "fill" not in kwargs:
                    kwargs["fill"] = "bottom"
                self.chart = plt.plot(
                    self.df[x_col].tolist(),
                    self.df[y_col].tolist(),
                    colors=[color],
                    **kwargs,
                )
            elif chart_type == "PieChart":
                kwargs.pop("labels", None)
                self.chart = plt.pie(
                    sizes=self.df[y_col].tolist(),
                    labels=self.df[x_col].tolist(),
                    colors=colors[: len(self.df[x_col])],
                    **kwargs,
                )
            elif chart_type == "Table":
                output = widgets.Output(**kwargs)
                with output:
                    display(self.df)
                output.layout = widgets.Layout(width="50%")
                display(output)
            else:
                raise ValueError("Unsupported chart type")

        self._set_title_and_labels()

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
        return self.df

    def set_data_table(self, data: Union[Dict[str, List[Any]], pd.DataFrame]) -> None:
        """
        Set a new DataTable for the chart.

        Args:
            data (Union[Dict[str, List[Any]], pd.DataFrame]): The new data to be used for the chart.
        """
        self.df = DataTable(data)

    def set_options(self, **options: Any) -> None:
        """
        Set additional options for the chart.

        Args:
            **options: Additional options to set for the chart.
        """
        for key, value in options.items():
            setattr(self.figure, key, value)


class BaseChart:
    """
    A class to create and display various types of charts from data.

    Attributes:
        df (pd.DataFrame): The data to be displayed in the charts.
        chart: The bqplot Figure object for the chart.
    """

    def __init__(self, data: Union[Dict, pd.DataFrame], **kwargs: Any) -> None:
        """
        Initializes the BaseChart with data.

        Args:
            data (dict or pd.DataFrame): The input data. If it's a dictionary,
                it will be converted to a DataFrame.
            **kwargs: Additional keyword arguments to pass to the pd.DataFrame
                constructor.
        """
        self.df = DataTable(data)
        self.chart = None
        self.chart_type = None

    def setChartType(
        self,
        chart_type: str,
        x_cols: Optional[List[str]] = None,
        y_cols: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        x_label: Optional[str] = "",
        y_label: Optional[str] = "",
        title: Optional[str] = None,
        **kwargs: Any,
    ) -> "BaseChart":
        """
        Sets the chart type and other chart properties.

        Args:
            chart_type (str): The type of chart to create. Supported types are
                'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart',
                'PieChart', 'AreaChart', and 'Table'.
            x_cols (list of str, optional): The columns to use for the x-axis.
                Defaults to the first column.
            y_cols (list of str, optional): The columns to use for the y-axis.
                Defaults to the second column.
            colors (list of str, optional): The colors to use for the chart.
                Defaults to a predefined list of colors.
            x_label (str, optional): The label for the x-axis. Defaults to an
                empty string.
            y_label (str, optional): The label for the y-axis. Defaults to an
                empty string.
            title (str, optional): The title of the chart. Defaults to the
                chart type.
            **kwargs: Additional keyword arguments to pass to the bqplot Figure
                or mark objects.

        Returns:
            BaseChart: The BaseChart instance with the chart set.
        """
        self.chart_type = chart_type

        if x_cols is None:
            x_cols = [self.df.columns[0]]
        if y_cols is None:
            y_cols = [self.df.columns[1]]

        if isinstance(x_cols, str):
            x_cols = [x_cols]

        if isinstance(y_cols, str):
            y_cols = [y_cols]

        if len(x_cols) == 1 and len(y_cols) > 1:
            x_cols = x_cols * len(y_cols)

        if title is not None:
            kwargs["title"] = title

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

        x_sc = bq.OrdinalScale()
        y_sc = bq.LinearScale()

        marks = []
        for i, (x_col, y_col) in enumerate(zip(x_cols, y_cols)):
            color = colors[
                i % len(colors)
            ]  # Cycle through colors if not enough are provided
            if "display_legend" not in kwargs and len(y_cols) > 1:
                kwargs["display_legend"] = True
                kwargs["labels"] = [y_col]
            else:
                kwargs["labels"] = [y_col]

            if chart_type == "ScatterChart":
                marks.append(
                    bq.Scatter(
                        x=self.df[x_col],
                        y=self.df[y_col],
                        scales={"x": x_sc, "y": y_sc},
                        colors=[color],
                        **kwargs,
                    )
                )
            elif chart_type == "LineChart":
                marks.append(
                    bq.Lines(
                        x=self.df[x_col],
                        y=self.df[y_col],
                        scales={"x": x_sc, "y": y_sc},
                        colors=[color],
                        **kwargs,
                    )
                )
            elif chart_type == "ColumnChart":
                marks.append(
                    bq.Bars(
                        x=self.df[x_col],
                        y=self.df[y_col],
                        scales={"x": x_sc, "y": y_sc},
                        colors=[color],
                        **kwargs,
                    )
                )
            elif chart_type == "BarChart":
                if "orientation" not in kwargs:
                    kwargs["orientation"] = "horizontal"
                marks.append(
                    bq.Bars(
                        x=self.df[x_col],
                        y=self.df[y_col],
                        scales={"x": x_sc, "y": y_sc},
                        colors=[color],
                        **kwargs,
                    )
                )
            elif chart_type == "AreaChart":
                if "fill" not in kwargs:
                    kwargs["fill"] = "bottom"
                marks.append(
                    bq.Lines(
                        x=self.df[x_col],
                        y=self.df[y_col],
                        scales={"x": x_sc, "y": y_sc},
                        colors=[color],
                        **kwargs,
                    )
                )
            elif chart_type == "PieChart":
                # Pie chart does not support multiple series in the same way; use only the first pair of x_col and y_col
                self.chart = bq.Figure(title=title, **kwargs)
                pie = bq.Pie(
                    sizes=self.df[y_cols[0]].tolist(),
                    labels=self.df[x_cols[0]].tolist(),
                    colors=colors[: len(self.df[x_cols[0]])],
                    **kwargs,
                )
                self.chart.marks = [pie]
                return self
            elif chart_type == "Table":
                self.chart = widgets.Output(**kwargs)
                with self.chart:
                    display(self.df)
                self.chart.layout = widgets.Layout(width="50%")
                return self
            else:
                raise ValueError("Unsupported chart type")

        x_axis = bq.Axis(scale=x_sc, label=x_label)
        y_axis = bq.Axis(scale=y_sc, orientation="vertical", label=y_label)
        self.chart = bq.Figure(marks=marks, axes=[x_axis, y_axis], **kwargs)

        return self

    def getChartType(self) -> Optional[str]:
        """
        Get the current chart type.

        Returns:
            Optional[str]: The current chart type, or None if no chart type is set.
        """
        return self.chart_type

    def getDataTable(self) -> DataTable:
        """
        Get the DataTable used by the chart.

        Returns:
            DataTable: The DataTable instance containing the chart data.
        """
        return self.df

    def setDataTable(self, data: Union[Dict[str, List[Any]], pd.DataFrame]) -> None:
        """
        Set a new DataTable for the chart.

        Args:
            data (Union[Dict[str, List[Any]], pd.DataFrame]): The new data to be used for the chart.
        """
        self.df = DataTable(data)

    def setOptions(self, **options: Any) -> None:
        """
        Set additional options for the chart.

        Args:
            **options: Additional options to set for the chart.
        """
        for key, value in options.items():
            setattr(self.chart, key, value)

    def display(self) -> None:
        """
        Displays the chart.
        """
        display(self.chart)


class BaseChartClass:
    """This should include everything a chart module requires to plot figures."""

    def __init__(self, features, default_labels, name, **kwargs):
        self.ylim = None
        self.xlim = None
        self.title = ""
        self.legend_location = "top-left"
        self.layout_width = None
        self.layout_height = None
        self.display_legend = True
        self.xlabel = None
        self.ylabel = None
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
    def get_data(self):
        pass

    @classmethod
    def plot_chart(self):
        pass

    def __repr__(self):
        return self.name


class BarChart(BaseChartClass):
    """Create Bar Chart. All histogram/bar charts can use this object."""

    def __init__(self, features, default_labels, name, type="grouped", **kwargs):
        super().__init__(features, default_labels, name, **kwargs)
        self.type = type

    def generate_tooltip(self):
        if (self.xlabel is not None) and (self.ylabel is not None):
            self.bar_chart.tooltip = Tooltip(
                fields=["x", "y"], labels=[self.xlabel, self.ylabel]
            )
        else:
            self.bar_chart.tooltip = Tooltip(fields=["x", "y"])

    def get_ylim(self):
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

    def plot_chart(self):
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
        if self.xlabel:
            plt.xlabel(self.xlabel)
        if self.ylabel:
            plt.ylabel(self.ylabel)

        if self.width:
            fig.layout.width = self.width
        if self.height:
            fig.layout.height = self.height

        self.bar_chart.colors = self.colors
        self.bar_chart.type = self.type

        plt.show()


class LineChart(BarChart):
    """A class to define variables and get_data method for a line chart."""

    def __init__(self, features, labels, name="line.chart", **kwargs):
        super().__init__(features, labels, name, **kwargs)

    def plot_chart(self):
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
        if self.xlabel:
            plt.xlabel(self.xlabel)
        if self.ylabel:
            plt.ylabel(self.ylabel)

        if self.width:
            fig.layout.width = self.width
        if self.height:
            fig.layout.height = self.height

        plt.show()


class Feature_ByFeature(BarChart):
    """A object to define variables and get_data method."""

    def __init__(
        self, features, xProperty, yProperties, name="feature.byFeature", **kwargs
    ):
        default_labels = yProperties
        super().__init__(features, default_labels, name, **kwargs)
        self.x_data, self.y_data = self.get_data(xProperty, yProperties)

    def get_data(self, xProperty, yProperties):
        x_data = list(self.df[xProperty])
        y_data = list(self.df[yProperties].values.T)
        return x_data, y_data


class Feature_ByProperty(BarChart):
    """A object to define variables and get_data method."""

    def __init__(
        self, features, xProperties, seriesProperty, name="feature.byProperty", **kwargs
    ):
        default_labels = None
        super().__init__(features, default_labels, name, **kwargs)
        if "labels" in kwargs:
            raise Exception("Please remove labels in kwargs and try again.")

        self.labels = list(self.df[seriesProperty])
        self.x_data, self.y_data = self.get_data(xProperties)

    def get_data(self, xProperties):
        if isinstance(xProperties, list):
            x_data = xProperties
            y_data = self.df[xProperties].values
        elif isinstance(xProperties, dict):
            x_data = list(xProperties.values())
            y_data = self.df[list(xProperties.keys())].values
        else:
            raise Exception("xProperties must be a list or dictionary.")

        return x_data, y_data


class Feature_Groups(BarChart):
    """A object to define variables and get_data method."""

    def __init__(
        self,
        features,
        xProperty,
        yProperty,
        seriesProperty,
        name="feature.groups",
        type="stacked",
        **kwargs,
    ):
        df = ee_to_df(features)
        self.unique_series_values = df[seriesProperty].unique().tolist()
        default_labels = [str(x) for x in self.unique_series_values]
        self.yProperty = yProperty
        super().__init__(features, default_labels, name, type, **kwargs)

        self.new_column_names = self.get_column_names(seriesProperty, yProperty)
        self.x_data, self.y_data = self.get_data(xProperty, self.new_column_names)

    def get_column_names(self, seriesProperty, yProperty):
        new_column_names = []

        for value in self.unique_series_values:
            sample_filter = (self.df[seriesProperty] == value).map({True: 1, False: 0})
            column_name = str(yProperty) + "_" + str(value)
            self.df[column_name] = self.df[yProperty] * sample_filter
            new_column_names.append(column_name)

        return new_column_names

    def get_data(self, xProperty, new_column_names):
        x_data = list(self.df[xProperty])
        y_data = [self.df[x] for x in new_column_names]

        return x_data, y_data


class Image_byClass(LineChart):
    """A object to define variables and get_data method."""

    def __init__(
        self,
        image,
        region,
        reducer,
        scale,
        classLabels,
        xLabels,
        xProperty,
        name="image.byClass",
        **kwargs,
    ):
        self.classLabels = classLabels
        self.xLabels = xLabels
        super().__init__(image, classLabels, name, **kwargs)
        self.x_data, self.y_data = self.get_data(
            image, region, xProperty, reducer, scale
        )

    def get_data(self, image, region, xProperty, reducer, scale):
        fc = zonal_stats(
            image, region, stat_type=reducer, scale=scale, verbose=False, return_fc=True
        )
        bands = image.bandNames().getInfo()
        df = ee_to_df(fc)[bands + [xProperty]]
        columns = df.columns.tolist()
        columns.remove(xProperty)
        x_data = columns
        y_data = df.drop([xProperty], axis=1).to_numpy()

        return x_data, y_data


def feature_byFeature(
    features: ee.FeatureCollection, xProperty: str, yProperties: list, **kwargs
):
    """Generates a Chart from a set of features. Plots the value of one or more properties for each feature.
    Reference: https://developers.google.com/earth-engine/guides/charts_feature#uichartfeaturebyfeature

    Args:
        features (ee.FeatureCollection): The feature collection to generate a chart from.
        xProperty (str): Features labeled by xProperty.
        yProperties (list): Values of yProperties.

    Raises:
        Exception: Errors when creating the chart.
    """
    bar = Feature_ByFeature(
        features=features, xProperty=xProperty, yProperties=yProperties, **kwargs
    )

    try:
        bar.plot_chart()

    except Exception as e:
        raise Exception(e)


def feature_byProperty(
    features: ee.FeatureCollection,
    xProperties: Union[list, dict],
    seriesProperty: str,
    **kwargs,
):
    """Generates a Chart from a set of features. Plots property values of one or more features.
    Reference: https://developers.google.com/earth-engine/guides/charts_feature#uichartfeaturebyproperty

    Args:
        features (ee.FeatureCollection): The features to include in the chart.
        xProperties (list | dict): One of (1) a list of properties to be plotted on the x-axis; or
            (2) a (property, label) dictionary specifying labels for properties to be used as values on the x-axis.
        seriesProperty (str): The name of the property used to label each feature in the legend.

    Raises:
        Exception: If the provided xProperties is not a list or dict.
        Exception: If the chart fails to create.
    """
    bar = Feature_ByProperty(
        features=features,
        xProperties=xProperties,
        seriesProperty=seriesProperty,
        **kwargs,
    )

    try:
        bar.plot_chart()

    except Exception as e:
        raise Exception(e)


def feature_groups(features, xProperty, yProperty, seriesProperty, **kwargs):
    """Generates a Chart from a set of features.
    Plots the value of one property for each feature.
    Reference:
    https://developers.google.com/earth-engine/guides/charts_feature#uichartfeaturegroups
    Args:
        features (ee.FeatureCollection): The feature collection to make a chart from.
        xProperty (str): Features labeled by xProperty.
        yProperty (str): Features labeled by yProperty.
        seriesProperty (str): The property used to label each feature in the legend.
    Raises:
        Exception: Errors when creating the chart.
    """

    bar = Feature_Groups(
        features=features,
        xProperty=xProperty,
        yProperty=yProperty,
        seriesProperty=seriesProperty,
        **kwargs,
    )

    try:
        bar.plot_chart()

    except Exception as e:
        raise Exception(e)


def feature_histogram(
    features, property, maxBuckets=None, minBucketWidth=None, show=True, **kwargs
):
    """
    Generates a Chart from a set of features.
    Computes and plots a histogram of the given property.
    - X-axis = Histogram buckets (of property value).
    - Y-axis = Frequency

    Reference:
    https://developers.google.com/earth-engine/guides/charts_feature#uichartfeaturehistogram

    Args:
        features  (ee.FeatureCollection): The features to include in the chart.
        property                   (str): The name of the property to generate the histogram for.
        maxBuckets       (int, optional): The maximum number of buckets (bins) to use when building a histogram;
                                          will be rounded up to a power of 2.
        minBucketWidth (float, optional): The minimum histogram bucket width, or null to allow any power of 2.
        show (bool, optional): Whether to show the chart. If not, it will return the bqplot chart object, which can be used to retrieve data for the chart. Defaults to True.

    Raises:
        Exception: If the provided xProperties is not a list or dict.
        Exception: If the chart fails to create.
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

        if not maxBuckets:
            initial_bin_size = nextPowerOf2(data_range / pow(2, 8))
            if minBucketWidth:
                if minBucketWidth < initial_bin_size:
                    bin_size = grow_bin(minBucketWidth, initial_bin_size)
                else:
                    bin_size = minBucketWidth
            else:
                bin_size = initial_bin_size
        else:
            initial_bin_size = math.ceil(data_range / nextPowerOf2(maxBuckets))
            if minBucketWidth:
                if minBucketWidth < initial_bin_size:
                    bin_size = grow_bin(minBucketWidth, initial_bin_size)
                else:
                    bin_size = minBucketWidth
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

        if "xlabel" not in kwargs:
            xlabel = ""
        else:
            xlabel = kwargs["xlabel"]

        if "ylabel" not in kwargs:
            ylabel = ""
        else:
            ylabel = kwargs["ylabel"]

        histogram = plt.hist(
            sample=y_data,
            bins=num_bins,
            axes_options={"count": {"label": ylabel}, "sample": {"label": xlabel}},
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

        if ("xlabel" in kwargs) and ("ylabel" in kwargs):
            histogram.tooltip = Tooltip(
                fields=["midpoint", "count"],
                labels=[kwargs["xlabel"], kwargs["ylabel"]],
            )
        else:
            histogram.tooltip = Tooltip(fields=["midpoint", "count"])

        if show:
            plt.show()
        else:
            return histogram

    except Exception as e:
        raise Exception(e)


def image_byClass(
    image,
    classBand,
    region,
    reducer="MEAN",
    scale=None,
    classLabels=None,
    xLabels=None,
    chart_type="LineChart",
    **kwargs,
):
    """
    Generates a Chart from an image by class. Extracts and plots band values by
        class.

    Args:
        image (ee.Image): Image to extract band values from.
        classBand (str): The band name to use as class labels.
        region (ee.Geometry | ee.FeatureCollection): The region(s) to reduce.
        reducer (str | ee.Reducer): The reducer type for zonal statistics. Can
            be one of 'mean', 'median', 'sum', 'min', 'max', etc.
        scale (int): The scale in meters at which to perform the analysis.
        classLabels (list): List of class labels.
        xLabels (list): List of x-axis labels.
        chart_type (str): The type of chart to create. Supported types are
            'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart', 'PieChart',
                'AreaChart', and 'Table'.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    fc = zonal_stats(
        image, region, stat_type=reducer, scale=scale, verbose=False, return_fc=True
    )
    bands = image.bandNames().getInfo()
    df = ee_to_df(fc)[bands + [classBand]]

    df_transposed = df.set_index(classBand).T

    if xLabels is not None:
        df_transposed["label"] = xLabels
    else:
        df_transposed["label"] = df_transposed.index

    if classLabels is None:
        y_cols = df_transposed.columns.tolist()
        y_cols.remove("label")
    else:
        y_cols = classLabels

    fig = BaseChart(df_transposed)
    fig.setChartType(
        chart_type,
        x_cols="label",
        y_cols=y_cols,
        **kwargs,
    )

    return fig.chart


def image_byRegion(image, regions, reducer, scale, xProperty, **kwargs):
    """
    Generates a Chart from an image. Extracts and plots band values in one or more regions in the image, with each band in a separate series.

    Args:
        image (ee.Image): Image to extract band values from.
        regions (ee.FeatureCollection | ee.Geometry): Regions to reduce. Defaults to the image's footprint.
        reducer (str | ee.Reducer): The reducer type for zonal statistics. Can be one of 'mean', 'median', 'sum', 'min', 'max', etc.
        scale (int): The scale in meters at which to perform the analysis.
        xProperty (str): The name of the property in the feature collection to use as the x-axis values.
        **kwargs: Additional keyword arguments to be passed to the `feature_byFeature` function.

    Returns:
        None
    """

    fc = zonal_stats(
        image, regions, stat_type=reducer, scale=scale, verbose=False, return_fc=True
    )
    bands = image.bandNames().getInfo()
    df = ee_to_df(fc)[bands + [xProperty]]
    feature_byFeature(df, xProperty, bands, **kwargs)


def image_doySeries(
    imageCollection,
    region,
    regionReducer,
    scale,
    yearReducer,
    startDay,
    endDay,
    **kwargs,
):
    """
    Generates a time series chart of an image collection for a specific region over a range of days of the year.

    Args:
        imageCollection (ee.ImageCollection): The image collection to analyze.
        region (ee.Geometry | ee.FeatureCollection): The region to reduce.
        regionReducer (str | ee.Reducer): The reducer type for zonal statistics. Can be one of 'mean', 'median', 'sum', 'min', 'max', etc.
        scale (int): The scale in meters at which to perform the analysis.
        yearReducer (str | ee.Reducer): The reducer type for yearly statistics.
        startDay (int): The start day of the year.
        endDay (int): The end day of the year.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    series = imageCollection.filter(
        ee.Filter.calendarRange(startDay, endDay, "day_of_year")
    )
    fc = zonal_stats(
        series,
        region,
        stat_type=regionReducer,
        scale=scale,
        verbose=False,
        return_fc=True,
    )
    df = ee_to_df(fc)
    years = df["year"].unique()
    values = {
        year: df[df["year"] == year].drop(columns=["year"]).mean() for year in years
    }

    # Creating a dataframe to hold the results
    result_df = pd.DataFrame(values).T

    # Plotting the results
    line_chart = LineChart(result_df, years.tolist(), **kwargs)
    line_chart.plot_chart()


def image_doySeriesByRegion(
    imageCollection,
    bandName,
    regions,
    regionReducer,
    scale,
    yearReducer,
    seriesProperty,
    startDay,
    endDay,
    **kwargs,
):
    """
    Generates a time series chart of an image collection for multiple regions over a range of days of the year.

    Args:
        imageCollection (ee.ImageCollection): The image collection to analyze.
        bandName (str): The name of the band to analyze.
        regions (ee.FeatureCollection): The regions to analyze.
        regionReducer (str | ee.Reducer): The reducer type for zonal statistics.
        scale (int): The scale in meters at which to perform the analysis.
        yearReducer (str | ee.Reducer): The reducer type for yearly statistics.
        seriesProperty (str): The property to use for labeling the series.
        startDay (int): The start day of the year.
        endDay (int): The end day of the year.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    series = imageCollection.filter(
        ee.Filter.calendarRange(startDay, endDay, "day_of_year")
    )
    fc = zonal_stats(
        series,
        regions,
        stat_type=regionReducer,
        scale=scale,
        verbose=False,
        return_fc=True,
    )
    bands = [bandName] + [seriesProperty]
    df = ee_to_df(fc)[bands]
    line_chart = Feature_ByProperty(df, [bandName], seriesProperty, **kwargs)
    line_chart.plot_chart()


def image_doySeriesByYear(
    imageCollection,
    bandName,
    region,
    regionReducer,
    scale,
    sameDayReducer,
    startDay,
    endDay,
    **kwargs,
):
    """
    Generates a time series chart of an image collection for a specific region over multiple years.

    Args:
        imageCollection (ee.ImageCollection): The image collection to analyze.
        bandName (str): The name of the band to analyze.
        region (ee.Geometry | ee.FeatureCollection): The region to analyze.
        regionReducer (str | ee.Reducer): The reducer type for zonal statistics.
        scale (int): The scale in meters at which to perform the analysis.
        sameDayReducer (str | ee.Reducer): The reducer type for daily statistics.
        startDay (int): The start day of the year.
        endDay (int): The end day of the year.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    series = imageCollection.filter(
        ee.Filter.calendarRange(startDay, endDay, "day_of_year")
    )
    fc = zonal_stats(
        series,
        region,
        stat_type=regionReducer,
        scale=scale,
        verbose=False,
        return_fc=True,
    )
    bands = [bandName, "year"]
    df = ee_to_df(fc)[bands]
    line_chart = Feature_ByProperty(df, [bandName], "year", **kwargs)
    line_chart.plot_chart()


def image_histogram(
    image: ee.Image,
    region: ee.Geometry,
    scale: int,
    maxBuckets: int,
    minBucketWidth: float,
    maxRaw: int,
    maxPixels: int,
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
        maxBuckets (int): The maximum number of buckets in the histogram.
        minBucketWidth (float): The minimum width of the buckets in the histogram.
        maxRaw (int): The maximum number of pixels to include in the histogram.
        maxPixels (int): The maximum number of pixels to reduce.
        reducer_args (dict): Additional arguments to pass to the image.reduceRegion.

    Keyword Args:
        colors (list[str]): Colors for the histograms of each band.
        labels (list[str]): Labels for the histograms of each band.
        title (str): Title of the combined histogram plot.
        legend_location (str): Location of the legend in the plot.

    Returns:
        bq.Figure: The bqplot figure containing the histograms.
    """
    # Calculate the histogram data.
    histogram = image.reduceRegion(
        reducer=ee.Reducer.histogram(
            maxBuckets=maxBuckets, minBucketWidth=minBucketWidth, maxRaw=maxRaw
        ),
        geometry=region,
        scale=scale,
        maxPixels=maxPixels,
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


def image_regions(image, regions, reducer, scale, seriesProperty, xLabels, **kwargs):
    """
    Generates a Chart from an image by regions. Extracts and plots band values in multiple regions.

    Args:
        image (ee.Image): Image to extract band values from.
        regions (ee.FeatureCollection | ee.Geometry): Regions to reduce. Defaults to the image's footprint.
        reducer (str | ee.Reducer): The reducer type for zonal statistics. Can be one of 'mean', 'median', 'sum', 'min', 'max', etc.
        scale (int): The scale in meters at which to perform the analysis.
        seriesProperty (str): The property to use for labeling the series.
        xLabels (list): List of x-axis labels.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    fc = zonal_stats(
        image, regions, stat_type=reducer, scale=scale, verbose=False, return_fc=True
    )
    bands = image.bandNames().getInfo()
    df = ee_to_df(fc)[bands + [seriesProperty]]
    feature_groups(df, seriesProperty, bands, seriesProperty, **kwargs)


def image_series(imageCollection, region, reducer, scale, xProperty, **kwargs):
    """
    Generates a time series chart of an image collection for a specific region.

    Args:
        imageCollection (ee.ImageCollection): The image collection to analyze.
        region (ee.Geometry | ee.FeatureCollection): The region to reduce.
        reducer (str | ee.Reducer): The reducer type for zonal statistics. Can be one of 'mean', 'median', 'sum', 'min', 'max', etc.
        scale (int): The scale in meters at which to perform the analysis.
        xProperty (str): The name of the property to use as the x-axis values.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    fc = zonal_stats(
        imageCollection,
        region,
        stat_type=reducer,
        scale=scale,
        verbose=False,
        return_fc=True,
    )
    bands = imageCollection.first().bandNames().getInfo()
    df = ee_to_df(fc)[bands + [xProperty]]
    feature_byFeature(df, xProperty, bands, **kwargs)


def image_seriesByRegion(
    imageCollection, regions, reducer, band, scale, xProperty, seriesProperty, **kwargs
):
    """
    Generates a time series chart of an image collection for multiple regions.

    Args:
        imageCollection (ee.ImageCollection): The image collection to analyze.
        regions (ee.FeatureCollection | ee.Geometry): The regions to reduce.
        reducer (str | ee.Reducer): The reducer type for zonal statistics.
        band (str): The name of the band to analyze.
        scale (int): The scale in meters at which to perform the analysis.
        xProperty (str): The name of the property to use as the x-axis values.
        seriesProperty (str): The property to use for labeling the series.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    fc = zonal_stats(
        imageCollection,
        regions,
        stat_type=reducer,
        scale=scale,
        verbose=False,
        return_fc=True,
    )
    df = ee_to_df(fc)[[band, xProperty, seriesProperty]]
    feature_groups(df, xProperty, band, seriesProperty, **kwargs)
