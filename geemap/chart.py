"""Module for creating charts for Earth Engine data.
"""

import ee
import pandas as pd
import numpy as np
from bqplot import Tooltip
from bqplot import pyplot as plt

from .common import ee_to_df

from typing import Union


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
        self.colors = "black"
        self.df = ee_to_df(features)
        self.name = name

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
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)

        if self.width:
            fig.layout.width = self.width
        if self.height:
            fig.layout.height = self.height

        self.bar_chart.colors = self.colors
        self.bar_chart.type = self.type

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
    # TODO
    pass


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
