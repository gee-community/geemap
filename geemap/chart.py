"""Module for creating charts for Earth Engine data.
"""

import ee
import pandas as pd
from bqplot import Tooltip
from bqplot import pyplot as plt

from .common import ee_to_df


def feature_byFeature(features, xProperty, yProperties, **kwargs):
    """Generates a Chart from a set of features. Plots the value of one or more properties for each feature.
    Reference: https://developers.google.com/earth-engine/guides/charts_feature#uichartfeaturebyfeature

    Args:
        features (ee.FeatureCollection): The feature collection to generate a chart from.
        xProperty (str): Features labeled by xProperty.
        yProperties (list): Values of yProperties.

    Raises:
        Exception: Errors when creating the chart.
    """

    try:

        df = ee_to_df(features)
        if "ylim" in kwargs:
            min_value = kwargs["ylim"][0]
            max_value = kwargs["ylim"][1]
        else:
            min_value = df[yProperties].to_numpy().min()
            max_value = df[yProperties].to_numpy().max()
            max_value = max_value + 0.2 * (max_value - min_value)

        if "title" not in kwargs:
            title = ""
        else:
            title = kwargs["title"]
        if "legend_location" not in kwargs:
            legend_location = "top-left"
        else:
            legend_location = kwargs["legend_location"]

        x_data = list(df[xProperty])
        y_data = df[yProperties].values.T.tolist()

        plt.bar(x_data, y_data)
        fig = plt.figure(
            title=title,
            legend_location=legend_location,
        )

        if "width" in kwargs:
            fig.layout.width = kwargs["width"]
        if "height" in kwargs:
            fig.layout.height = kwargs["height"]

        if "labels" in kwargs:
            labels = kwargs["labels"]
        else:
            labels = yProperties

        if "display_legend" not in kwargs:
            display_legend = True
        else:
            display_legend = kwargs["display_legend"]

        bar_chart = plt.bar(
            x_data, y_data, labels=labels, display_legend=display_legend
        )

        bar_chart.type = "grouped"

        if "colors" in kwargs:
            bar_chart.colors = kwargs["colors"]

        if "xlabel" in kwargs:
            plt.xlabel(kwargs["xlabel"])
        if "ylabel" in kwargs:
            plt.ylabel(kwargs["ylabel"])
        plt.ylim(min_value, max_value)

        if "xlabel" in kwargs and ("ylabel" in kwargs):
            bar_chart.tooltip = Tooltip(
                fields=["x", "y"], labels=[kwargs["xlabel"], kwargs["ylabel"]]
            )
        else:
            bar_chart.tooltip = Tooltip(fields=["x", "y"])

        plt.show()

    except Exception as e:
        raise Exception(e)


def feature_byProperty(features, xProperties, seriesProperty, **kwargs):
    """Generates a Chart from a set of features. Plots property values of one or more features.
    Reference: https://developers.google.com/earth-engine/guides/charts_feature#uichartfeaturebyproperty

    Args:
        features (ee.FeatureCollection): The features to include in the chart.
        xProperties (list | dict): One of (1) a list of properties to be plotted on the x-axis; or (2) a (property, label) dictionary specifying labels for properties to be used as values on the x-axis.
        seriesProperty (str): The name of the property used to label each feature in the legend.

    Raises:
        Exception: If the provided xProperties is not a list or dict.
        Exception: If the chart fails to create.
    """
    try:
        df = ee_to_df(features)

        if isinstance(xProperties, list):
            x_data = xProperties
            y_data = df[xProperties].values
        elif isinstance(xProperties, dict):
            x_data = list(xProperties.values())
            y_data = df[list(xProperties.keys())].values
        else:
            raise Exception("xProperties must be a list or dictionary.")

        labels = list(df[seriesProperty])

        if "ylim" in kwargs:
            min_value = kwargs["ylim"][0]
            max_value = kwargs["ylim"][1]
        else:
            min_value = y_data.min()
            max_value = y_data.max()
            max_value = max_value + 0.2 * (max_value - min_value)

        if "title" not in kwargs:
            title = ""
        else:
            title = kwargs["title"]
        if "legend_location" not in kwargs:
            legend_location = "top-left"
        else:
            legend_location = kwargs["legend_location"]

        if "display_legend" not in kwargs:
            display_legend = True
        else:
            display_legend = kwargs["display_legend"]

        fig = plt.figure(
            title=title,
            legend_location=legend_location,
        )

        if "width" in kwargs:
            fig.layout.width = kwargs["width"]
        if "height" in kwargs:
            fig.layout.height = kwargs["height"]

        bar_chart = plt.bar(
            x=x_data, y=y_data, labels=labels, display_legend=display_legend
        )

        bar_chart.type = "grouped"

        if "colors" in kwargs:
            bar_chart.colors = kwargs["colors"]

        if "xlabel" in kwargs:
            plt.xlabel(kwargs["xlabel"])
        if "ylabel" in kwargs:
            plt.ylabel(kwargs["ylabel"])
        plt.ylim(min_value, max_value)

        if "xlabel" in kwargs and ("ylabel" in kwargs):
            bar_chart.tooltip = Tooltip(
                fields=["x", "y"], labels=[kwargs["xlabel"], kwargs["ylabel"]]
            )
        else:
            bar_chart.tooltip = Tooltip(fields=["x", "y"])

        plt.show()

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

    try:
        df = ee_to_df(features)
        df[yProperty] = pd.to_numeric(df[yProperty])
        unique_series_values = df[seriesProperty].unique().tolist()
        new_column_names = []

        for value in unique_series_values:
            sample_filter = (df[seriesProperty] == value).map({True: 1, False: 0})
            column_name = str(yProperty) + "_" + str(value)
            df[column_name] = df[yProperty] * sample_filter
            new_column_names.append(column_name)

        if "labels" in kwargs:
            labels = kwargs["labels"]
        else:
            labels = [str(x) for x in unique_series_values]

        if "ylim" in kwargs:
            min_value = kwargs["ylim"][0]
            max_value = kwargs["ylim"][1]
        else:
            min_value = df[yProperty].to_numpy().min()
            max_value = df[yProperty].to_numpy().max()
            max_value = max_value + 0.2 * (max_value - min_value)

        if "title" not in kwargs:
            title = ""
        else:
            title = kwargs["title"]
        if "legend_location" not in kwargs:
            legend_location = "top-left"
        else:
            legend_location = kwargs["legend_location"]

        x_data = list(df[xProperty])
        y_data = [df[x] for x in new_column_names]

        plt.bar(x_data, y_data)
        fig = plt.figure(
            title=title,
            legend_location=legend_location,
        )

        if "width" in kwargs:
            fig.layout.width = kwargs["width"]
        if "height" in kwargs:
            fig.layout.height = kwargs["height"]

        if "display_legend" not in kwargs:
            display_legend = True
        else:
            display_legend = kwargs["display_legend"]

        bar_chart = plt.bar(
            x_data, y_data, labels=labels, display_legend=display_legend
        )

        if "colors" in kwargs:
            bar_chart.colors = kwargs["colors"]

        if "xlabel" in kwargs:
            plt.xlabel(kwargs["xlabel"])
        if "ylabel" in kwargs:
            plt.ylabel(kwargs["ylabel"])
        plt.ylim(min_value, max_value)

        if "xlabel" in kwargs and ("ylabel" in kwargs):
            bar_chart.tooltip = Tooltip(
                fields=["x", "y"], labels=[kwargs["xlabel"], kwargs["ylabel"]]
            )
        else:
            bar_chart.tooltip = Tooltip(fields=["x", "y"])

        plt.show()

    except Exception as e:
        raise Exception(e)


def feature_histogram(
    features, property, maxBuckets=None, minBucketWidth=None, **kwargs
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
        plt.show()

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
