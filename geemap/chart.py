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

from typing import List, Optional, Union, Dict


class DataTable:
    """
    A class to create and display various types of charts from data.

    Attributes:
        df (pd.DataFrame): The data to be displayed in the charts.
        chart: The bqplot Figure object for the chart.
    """

    def __init__(self, data: Union[Dict, pd.DataFrame], **kwargs):
        """
        Initializes the DataTable with data.

        Args:
            data (dict or pd.DataFrame): The input data. If it's a dictionary, it will be converted to a DataFrame.
            **kwargs: Additional keyword arguments to pass to the pd.DataFrame constructor.
        """
        if isinstance(data, pd.DataFrame):
            self.df = data
        else:
            self.df = pd.DataFrame(data, **kwargs)
        self.chart = None

    def setChartType(
        self,
        chart_type: str,
        x_cols: Optional[List[str]] = None,
        y_cols: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        title: Optional[str] = None,
        **kwargs,
    ) -> "DataTable":
        """
        Sets the chart type and other chart properties.

        Args:
            chart_type (str): The type of chart to create. Supported types are 'ScatterChart', 'LineChart', 'ColumnChart', 'BarChart', 'PieChart', 'AreaChart', and 'Table'.
            x_cols (list of str, optional): The columns to use for the x-axis. Defaults to the first column.
            y_cols (list of str, optional): The columns to use for the y-axis. Defaults to the second column.
            colors (list of str, optional): The colors to use for the chart. Defaults to a predefined list of colors.
            x_label (str, optional): The label for the x-axis. Defaults to None.
            y_label (str, optional): The label for the y-axis. Defaults to None.
            title (str, optional): The title of the chart. Defaults to the chart type.
            **kwargs: Additional keyword arguments to pass to the bqplot Figure or mark objects.

        Returns:
            DataTable: The DataTable instance with the chart set.
        """
        if x_cols is None:
            x_cols = [self.df.columns[0]]
        if y_cols is None:
            y_cols = [self.df.columns[1]]
        if title is None:
            title = chart_type

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
                marks.append(
                    bq.Bars(
                        x=self.df[x_col],
                        y=self.df[y_col],
                        scales={"x": x_sc, "y": y_sc},
                        orientation="horizontal",
                        colors=[color],
                        **kwargs,
                    )
                )
            elif chart_type == "AreaChart":
                marks.append(
                    bq.Lines(
                        x=self.df[x_col],
                        y=self.df[y_col],
                        scales={"x": x_sc, "y": y_sc},
                        fill="bottom",
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

        self.chart = bq.Figure(marks=marks, title=title, **kwargs)
        x_axis = bq.Axis(scale=x_sc, label=x_label)
        y_axis = bq.Axis(scale=y_sc, orientation="vertical", label=y_label)
        self.chart.axes = [x_axis, y_axis]

        return self

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
    image, classBand, region, reducer, scale, classLabels, xLabels, **kwargs
):
    # TODO
    pass


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
    # TODO
    pass


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
    # TODO
    pass


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
    # TODO
    pass


def image_histogram(
    image, region, scale, maxBuckets, minBucketWidth, maxRaw, maxPixels, **kwargs
):
    # TODO
    pass


def image_regions(image, regions, reducer, scale, seriesProperty, xLabels, **kwargs):
    # TODO
    pass


def image_series(imageCollection, region, reducer, scale, xProperty, **kwargs):
    # TODO
    pass


def image_seriesByRegion(
    imageCollection, regions, reducer, band, scale, xProperty, seriesProperty, **kwargs
):
    # TODO
    pass
