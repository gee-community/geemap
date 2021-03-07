"""Module for creating charts for Earth Engine data.
"""

import ee
import pandas as pd
from bqplot import pyplot as plt
from bqplot import Tooltip


def feature_byFeature(features, xProperty, yProperties, **kwargs):
    """Generates a Chart from a set of features. Plots the value of one or more properties for each feature.
    Reference: https://developers.google.com/earth-engine/guides/charts_feature#column_chart

    Args:
        features (ee.FeatureCollection): The feature collection to generate a chart from.
        xProperty (str): Features labeled by xProperty.
        yProperties (list): Values of yProperties.

    Raises:
        Exception: Errors when creating the chart.
    """

    try:

        data = features.map(lambda f: ee.Feature(None, f.toDictionary()))
        data = [x["properties"] for x in data.getInfo()["features"]]
        df = pd.DataFrame(data)

        x_data = list(df[xProperty])
        y_data = df[yProperties].values.T.tolist()

        # fig = plt.figure()
        plt.bar(x_data, y_data)

        fig = plt.figure(
            title=kwargs["title"],
            fig_margin={"top": 30, "bottom": 30, "left": 30, "right": 30},
            legend_location="right",
        )

        labels = kwargs["labels"]

        bar_chart = plt.bar(x_data, y_data, labels=labels, display_legend=True)

        bar_chart.type = "grouped"

        bar_chart.colors = kwargs["colors"]

        bar_chart.tooltip = Tooltip(fields=["y"])

        plt.xlabel(kwargs["xlabel"])
        plt.ylabel(kwargs["ylabel"])
        plt.ylim(-5, 30)

        plt.show()

    except Exception as e:
        raise Exception(e)


def feature_byProperty(features, xProperties, seriesProperty, **kwargs):
    # TODO
    pass


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
