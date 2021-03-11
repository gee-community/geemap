"""Module for creating charts for Earth Engine data.
"""

import ee
import pandas as pd
from bqplot import pyplot as plt
from bqplot import Tooltip
from .common import ee_to_pandas


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

        df = ee_to_pandas(features)
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
        df = ee_to_pandas(features)

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
    # TODO
    pass


def feature_histogram(features, property, maxBuckets, minBucketWidth, maxRaw, **kwargs):
    # TODO
    pass


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
    **kwargs
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
    **kwargs
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
    **kwargs
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
