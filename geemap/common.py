"""This module contains some common functions for both folium and ipyleaflet to interact with the Earth Engine Python API.
"""

# *******************************************************************************#
# This module contains core features and extra features of the geemap package.   #
# The Earth Engine team and the geemap community will maintain the core features.#
# The geemap community will maintain the extra features.                         #
# The core features include classes and functions below until the line # ******* #
# *******************************************************************************#

import csv
import datetime
import io
import json
import math
import os
import requests
import shutil
import tarfile
import urllib.request
import warnings
import zipfile

import ee
import ipywidgets as widgets
from ipytree import Node, Tree
from typing import Union, List, Dict, Optional, Any

from .coreutils import *

try:
    from IPython.display import display, IFrame, Javascript
except ImportError:
    pass


def ee_export_image(
    ee_object,
    filename,
    scale=None,
    crs=None,
    crs_transform=None,
    region=None,
    dimensions=None,
    file_per_band=False,
    format="ZIPPED_GEO_TIFF",
    unzip=True,
    unmask_value=None,
    timeout=300,
    proxies=None,
):
    """Exports an ee.Image as a GeoTIFF.

    Args:
        ee_object (object): The ee.Image to download.
        filename (str): Output filename for the exported image.
        scale (float, optional): A default scale to use for any bands that do not specify one; ignored if crs and crs_transform is specified. Defaults to None.
        crs (str, optional): A default CRS string to use for any bands that do not explicitly specify one. Defaults to None.
        crs_transform (list, optional): a default affine transform to use for any bands that do not specify one, of the same format as the crs_transform of bands. Defaults to None.
        region (object, optional): A polygon specifying a region to download; ignored if crs and crs_transform is specified. Defaults to None.
        dimensions (list, optional): An optional array of two integers defining the width and height to which the band is cropped. Defaults to None.
        file_per_band (bool, optional): Whether to produce a different GeoTIFF per band. Defaults to False.
        format (str, optional):  One of: "ZIPPED_GEO_TIFF" (GeoTIFF file(s) wrapped in a zip file, default), "GEO_TIFF" (GeoTIFF file), "NPY" (NumPy binary format). If "GEO_TIFF" or "NPY",
            filePerBand and all band-level transformations will be ignored. Loading a NumPy output results in a structured array.
        unzip (bool, optional): Whether to unzip the downloaded file. Defaults to True.
        unmask_value (float, optional): The value to use for pixels that are masked in the input image.
            If the exported image contains zero values, you should set the unmask value to a  non-zero value so that the zero values are not treated as missing data. Defaults to None.
        timeout (int, optional): The timeout in seconds for the request. Defaults to 300.
        proxies (dict, optional): A dictionary of proxy servers to use. Defaults to None.
    """

    if not isinstance(ee_object, ee.Image):
        print("The ee_object must be an ee.Image.")
        return

    if unmask_value is not None:
        ee_object = ee_object.selfMask().unmask(unmask_value)
        if isinstance(region, ee.Geometry):
            ee_object = ee_object.clip(region)
        elif isinstance(region, ee.FeatureCollection):
            ee_object = ee_object.clipToCollection(region)

    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()
    filename_zip = filename.replace(".tif", ".zip")

    if filetype != "tif":
        print("The filename must end with .tif")
        return

    try:
        print("Generating URL ...")
        params = {"name": name, "filePerBand": file_per_band}

        params["scale"] = scale
        if region is None:
            region = ee_object.geometry()
        if dimensions is not None:
            params["dimensions"] = dimensions
        if region is not None:
            params["region"] = region
        if crs is not None:
            params["crs"] = crs
        if crs_transform is not None:
            params["crs_transform"] = crs_transform
        if format != "ZIPPED_GEO_TIFF":
            params["format"] = format

        try:
            url = ee_object.getDownloadURL(params)
        except Exception as e:
            print("An error occurred while downloading.")
            print(e)
            return
        print(f"Downloading data from {url}\nPlease wait ...")
        # Need to initialize r to something because of how we currently handle errors
        # We should aim to refactor the code such that only one try block is needed
        r = None
        r = requests.get(url, stream=True, timeout=timeout, proxies=proxies)

        if r.status_code != 200:
            print("An error occurred while downloading.")
            return

        with open(filename_zip, "wb") as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)

    except Exception as e:
        print("An error occurred while downloading.")
        if r is not None:
            print(r.json()["error"]["message"])
        return

    try:
        if unzip:
            with zipfile.ZipFile(filename_zip) as z:
                z.extractall(os.path.dirname(filename))
            os.remove(filename_zip)

        if file_per_band:
            print(f"Data downloaded to {os.path.dirname(filename)}")
        else:
            print(f"Data downloaded to {filename}")
    except Exception as e:
        print(e)


def ee_export_image_collection(
    ee_object,
    out_dir,
    scale=None,
    crs=None,
    crs_transform=None,
    region=None,
    dimensions=None,
    file_per_band=False,
    format="ZIPPED_GEO_TIFF",
    unmask_value=None,
    filenames=None,
    timeout=300,
    proxies=None,
):
    """Exports an ImageCollection as GeoTIFFs.

    Args:
        ee_object (object): The ee.Image to download.
        out_dir (str): The output directory for the exported images.
        scale (float, optional): A default scale to use for any bands that do not specify one; ignored if crs and crs_transform is specified. Defaults to None.
        crs (str, optional): A default CRS string to use for any bands that do not explicitly specify one. Defaults to None.
        crs_transform (list, optional): a default affine transform to use for any bands that do not specify one, of the same format as the crs_transform of bands. Defaults to None.
        region (object, optional): A polygon specifying a region to download; ignored if crs and crs_transform is specified. Defaults to None.
        dimensions (list, optional): An optional array of two integers defining the width and height to which the band is cropped. Defaults to None.
        file_per_band (bool, optional): Whether to produce a different GeoTIFF per band. Defaults to False.
        format (str, optional):  One of: "ZIPPED_GEO_TIFF" (GeoTIFF file(s) wrapped in a zip file, default), "GEO_TIFF" (GeoTIFF file), "NPY" (NumPy binary format). If "GEO_TIFF" or "NPY",
            filePerBand and all band-level transformations will be ignored. Loading a NumPy output results in a structured array.
        unmask_value (float, optional): The value to use for pixels that are masked in the input image.
            If the exported image contains zero values, you should set the unmask value to a  non-zero value so that the zero values are not treated as missing data. Defaults to None.
        filenames (list | int, optional): A list of filenames to use for the exported images. Defaults to None.
        timeout (int, optional): The timeout in seconds for the request. Defaults to 300.
        proxies (dict, optional): A dictionary of proxy servers to use. Defaults to None.
    """

    if not isinstance(ee_object, ee.ImageCollection):
        print("The ee_object must be an ee.ImageCollection.")
        return

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        count = int(ee_object.size().getInfo())
        print(f"Total number of images: {count}\n")

        if filenames is None:
            filenames = ee_object.aggregate_array("system:index").getInfo()
        elif isinstance(filenames, int):
            filenames = [str(f + filenames) for f in range(0, count)]

        if len(filenames) != count:
            raise Exception(
                "The number of filenames must be equal to the number of images."
            )

        filenames = [str(f) + ".tif" for f in filenames if not str(f).endswith(".tif")]

        for i in range(0, count):
            image = ee.Image(ee_object.toList(count).get(i))
            filename = os.path.join(out_dir, filenames[i])
            print(f"Exporting {i + 1}/{count}: {filename}")
            ee_export_image(
                image,
                filename=filename,
                scale=scale,
                crs=crs,
                crs_transform=crs_transform,
                region=region,
                dimensions=dimensions,
                file_per_band=file_per_band,
                format=format,
                unmask_value=unmask_value,
                timeout=timeout,
                proxies=proxies,
            )
            print("\n")

    except Exception as e:
        print(e)


def ee_export_image_to_drive(
    image,
    description="myExportImageTask",
    folder=None,
    fileNamePrefix=None,
    dimensions=None,
    region=None,
    scale=None,
    crs=None,
    crsTransform=None,
    maxPixels=None,
    shardSize=None,
    fileDimensions=None,
    skipEmptyTiles=None,
    fileFormat=None,
    formatOptions=None,
    **kwargs,
):
    """Creates a batch task to export an Image as a raster to Google Drive.

    Args:
        image: The image to be exported.
        description: Human-readable name of the task.
        folder: The name of a unique folder in your Drive account to
            export into. Defaults to the root of the drive.
        fileNamePrefix: The Google Drive filename for the export.
            Defaults to the name of the task.
        dimensions: The dimensions of the exported image. Takes either a
            single positive integer as the maximum dimension or "WIDTHxHEIGHT"
            where WIDTH and HEIGHT are each positive integers.
        region: The lon,lat coordinates for a LinearRing or Polygon
            specifying the region to export. Can be specified as a nested
            lists of numbers or a serialized string. Defaults to the image's
            region.
        scale: The resolution in meters per pixel. Defaults to the
            native resolution of the image asset unless a crsTransform
            is specified.
        crs: The coordinate reference system of the exported image's
            projection. Defaults to the image's default projection.
        crsTransform: A comma-separated string of 6 numbers describing
            the affine transform of the coordinate reference system of the
            exported image's projection, in the order: xScale, xShearing,
            xTranslation, yShearing, yScale and yTranslation. Defaults to
            the image's native CRS transform.
        maxPixels: The maximum allowed number of pixels in the exported
            image. The task will fail if the exported region covers more
            pixels in the specified projection. Defaults to 100,000,000.
        shardSize: Size in pixels of the tiles in which this image will be
            computed. Defaults to 256.
        fileDimensions: The dimensions in pixels of each image file, if the
            image is too large to fit in a single file. May specify a
            single number to indicate a square shape, or a tuple of two
            dimensions to indicate (width,height). Note that the image will
            still be clipped to the overall image dimensions. Must be a
            multiple of shardSize.
        skipEmptyTiles: If true, skip writing empty (i.e. fully-masked)
            image tiles. Defaults to false.
        fileFormat: The string file format to which the image is exported.
            Currently only 'GeoTIFF' and 'TFRecord' are supported, defaults to
            'GeoTIFF'.
        formatOptions: A dictionary of string keys to format specific options.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'crs_transform', 'driveFolder', and 'driveFileNamePrefix'.
    """

    if not isinstance(image, ee.Image):
        raise ValueError("Input image must be an instance of ee.Image")

    task = ee.batch.Export.image.toDrive(
        image,
        description,
        folder,
        fileNamePrefix,
        dimensions,
        region,
        scale,
        crs,
        crsTransform,
        maxPixels,
        shardSize,
        fileDimensions,
        skipEmptyTiles,
        fileFormat,
        formatOptions,
        **kwargs,
    )
    task.start()


def ee_export_image_to_asset(
    image,
    description="myExportImageTask",
    assetId=None,
    pyramidingPolicy=None,
    dimensions=None,
    region=None,
    scale=None,
    crs=None,
    crsTransform=None,
    maxPixels=None,
    **kwargs,
):
    """Creates a task to export an EE Image to an EE Asset.

    Args:
        image: The image to be exported.
        description: Human-readable name of the task.
        assetId: The destination asset ID.
        pyramidingPolicy: The pyramiding policy to apply to each band in the
            image, a dictionary keyed by band name. Values must be
            one of: "mean", "sample", "min", "max", or "mode".
            Defaults to "mean". A special key, ".default", may be used to
            change the default for all bands.
        dimensions: The dimensions of the exported image. Takes either a
            single positive integer as the maximum dimension or "WIDTHxHEIGHT"
            where WIDTH and HEIGHT are each positive integers.
        region: The lon,lat coordinates for a LinearRing or Polygon
            specifying the region to export. Can be specified as a nested
            lists of numbers or a serialized string. Defaults to the image's
            region.
        scale: The resolution in meters per pixel. Defaults to the
            native resolution of the image asset unless a crsTransform
            is specified.
        crs: The coordinate reference system of the exported image's
            projection. Defaults to the image's default projection.
        crsTransform: A comma-separated string of 6 numbers describing
            the affine transform of the coordinate reference system of the
            exported image's projection, in the order: xScale, xShearing,
            xTranslation, yShearing, yScale and yTranslation. Defaults to
            the image's native CRS transform.
        maxPixels: The maximum allowed number of pixels in the exported
            image. The task will fail if the exported region covers more
            pixels in the specified projection. Defaults to 100,000,000.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'crs_transform'.
    """

    if isinstance(image, ee.Image) or isinstance(image, ee.image.Image):
        pass
    else:
        raise ValueError("Input image must be an instance of ee.Image")

    if isinstance(assetId, str):
        if assetId.startswith("users/") or assetId.startswith("projects/"):
            pass
        else:
            assetId = f"{ee_user_id()}/{assetId}"

    task = ee.batch.Export.image.toAsset(
        image,
        description,
        assetId,
        pyramidingPolicy,
        dimensions,
        region,
        scale,
        crs,
        crsTransform,
        maxPixels,
        **kwargs,
    )
    task.start()


def ee_export_image_to_cloud_storage(
    image,
    description="myExportImageTask",
    bucket=None,
    fileNamePrefix=None,
    dimensions=None,
    region=None,
    scale=None,
    crs=None,
    crsTransform=None,
    maxPixels=None,
    shardSize=None,
    fileDimensions=None,
    skipEmptyTiles=None,
    fileFormat=None,
    formatOptions=None,
    **kwargs,
):
    """Creates a task to export an EE Image to Google Cloud Storage.

    Args:
        image: The image to be exported.
        description: Human-readable name of the task.
        bucket: The name of a Cloud Storage bucket for the export.
        fileNamePrefix: Cloud Storage object name prefix for the export.
            Defaults to the name of the task.
        dimensions: The dimensions of the exported image. Takes either a
            single positive integer as the maximum dimension or "WIDTHxHEIGHT"
            where WIDTH and HEIGHT are each positive integers.
        region: The lon,lat coordinates for a LinearRing or Polygon
            specifying the region to export. Can be specified as a nested
            lists of numbers or a serialized string. Defaults to the image's
            region.
        scale: The resolution in meters per pixel. Defaults to the
            native resolution of the image asset unless a crsTransform
            is specified.
        crs: The coordinate reference system of the exported image's
            projection. Defaults to the image's default projection.
        crsTransform: A comma-separated string of 6 numbers describing
            the affine transform of the coordinate reference system of the
            exported image's projection, in the order: xScale, xShearing,
            xTranslation, yShearing, yScale and yTranslation. Defaults to
            the image's native CRS transform.
        maxPixels: The maximum allowed number of pixels in the exported
            image. The task will fail if the exported region covers more
            pixels in the specified projection. Defaults to 100,000,000.
        shardSize: Size in pixels of the tiles in which this image will be
            computed. Defaults to 256.
        fileDimensions: The dimensions in pixels of each image file, if the
            image is too large to fit in a single file. May specify a
            single number to indicate a square shape, or a tuple of two
            dimensions to indicate (width,height). Note that the image will
            still be clipped to the overall image dimensions. Must be a
            multiple of shardSize.
        skipEmptyTiles: If true, skip writing empty (i.e. fully-masked)
            image tiles. Defaults to false.
        fileFormat: The string file format to which the image is exported.
            Currently only 'GeoTIFF' and 'TFRecord' are supported, defaults to
            'GeoTIFF'.
        formatOptions: A dictionary of string keys to format specific options.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'crs_transform'.
    """

    if not isinstance(image, ee.Image):
        raise ValueError("Input image must be an instance of ee.Image")

    try:
        task = ee.batch.Export.image.toCloudStorage(
            image,
            description,
            bucket,
            fileNamePrefix,
            dimensions,
            region,
            scale,
            crs,
            crsTransform,
            maxPixels,
            shardSize,
            fileDimensions,
            skipEmptyTiles,
            fileFormat,
            formatOptions,
            **kwargs,
        )
        task.start()
    except Exception as e:
        print(e)


def ee_export_image_collection_to_drive(
    ee_object,
    descriptions=None,
    folder=None,
    fileNamePrefix=None,
    dimensions=None,
    region=None,
    scale=None,
    crs=None,
    crsTransform=None,
    maxPixels=None,
    shardSize=None,
    fileDimensions=None,
    skipEmptyTiles=None,
    fileFormat=None,
    formatOptions=None,
    **kwargs,
):
    """Creates a batch task to export an ImageCollection as raster images to Google Drive.

    Args:
        ee_object: The image collection to export.
        descriptions: A list of human-readable names of the tasks.
        folder: The name of a unique folder in your Drive account to
            export into. Defaults to the root of the drive.
        fileNamePrefix: The Google Drive filename for the export.
            Defaults to the name of the task.
        dimensions: The dimensions of the exported image. Takes either a
            single positive integer as the maximum dimension or "WIDTHxHEIGHT"
            where WIDTH and HEIGHT are each positive integers.
        region: The lon,lat coordinates for a LinearRing or Polygon
            specifying the region to export. Can be specified as a nested
            lists of numbers or a serialized string. Defaults to the image's
            region.
        scale: The resolution in meters per pixel. Defaults to the
            native resolution of the image asset unless a crsTransform
            is specified.
        crs: The coordinate reference system of the exported image's
            projection. Defaults to the image's default projection.
        crsTransform: A comma-separated string of 6 numbers describing
            the affine transform of the coordinate reference system of the
            exported image's projection, in the order: xScale, xShearing,
            xTranslation, yShearing, yScale and yTranslation. Defaults to
            the image's native CRS transform.
        maxPixels: The maximum allowed number of pixels in the exported
            image. The task will fail if the exported region covers more
            pixels in the specified projection. Defaults to 100,000,000.
        shardSize: Size in pixels of the tiles in which this image will be
            computed. Defaults to 256.
        fileDimensions: The dimensions in pixels of each image file, if the
            image is too large to fit in a single file. May specify a
            single number to indicate a square shape, or a tuple of two
            dimensions to indicate (width,height). Note that the image will
            still be clipped to the overall image dimensions. Must be a
            multiple of shardSize.
        skipEmptyTiles: If true, skip writing empty (i.e. fully-masked)
            image tiles. Defaults to false.
        fileFormat: The string file format to which the image is exported.
            Currently only 'GeoTIFF' and 'TFRecord' are supported, defaults to
            'GeoTIFF'.
        formatOptions: A dictionary of string keys to format specific options.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'crs_transform', 'driveFolder', and 'driveFileNamePrefix'.
    """

    if not isinstance(ee_object, ee.ImageCollection):
        raise ValueError("The ee_object must be an ee.ImageCollection.")

    try:
        count = int(ee_object.size().getInfo())
        print(f"Total number of images: {count}\n")

        if (descriptions is not None) and (len(descriptions) != count):
            raise ValueError(
                "The number of descriptions is not equal to the number of images."
            )

        if descriptions is None:
            descriptions = ee_object.aggregate_array("system:index").getInfo()

        images = ee_object.toList(count)

        if os.environ.get("USE_MKDOCS") is not None:  # skip if running GitHub CI.
            return

        for i in range(0, count):
            image = ee.Image(images.get(i))
            description = descriptions[i]
            ee_export_image_to_drive(
                image,
                description,
                folder,
                fileNamePrefix,
                dimensions,
                region,
                scale,
                crs,
                crsTransform,
                maxPixels,
                shardSize,
                fileDimensions,
                skipEmptyTiles,
                fileFormat,
                formatOptions,
                **kwargs,
            )

    except Exception as e:
        print(e)


def ee_export_image_collection_to_asset(
    ee_object,
    descriptions=None,
    assetIds=None,
    pyramidingPolicy=None,
    dimensions=None,
    region=None,
    scale=None,
    crs=None,
    crsTransform=None,
    maxPixels=None,
    **kwargs,
):
    """Creates a batch task to export an ImageCollection as raster images to Google Drive.

    Args:
        ee_object: The image collection to export.
        descriptions: A list of human-readable names of the tasks.
        assetIds: The destination asset ID.
        pyramidingPolicy: The pyramiding policy to apply to each band in the
            image, a dictionary keyed by band name. Values must be
            one of: "mean", "sample", "min", "max", or "mode".
            Defaults to "mean". A special key, ".default", may be used to
            change the default for all bands.
        dimensions: The dimensions of the exported image. Takes either a
            single positive integer as the maximum dimension or "WIDTHxHEIGHT"
            where WIDTH and HEIGHT are each positive integers.
        region: The lon,lat coordinates for a LinearRing or Polygon
            specifying the region to export. Can be specified as a nested
            lists of numbers or a serialized string. Defaults to the image's
            region.
        scale: The resolution in meters per pixel. Defaults to the
            native resolution of the image asset unless a crsTransform
            is specified.
        crs: The coordinate reference system of the exported image's
            projection. Defaults to the image's default projection.
        crsTransform: A comma-separated string of 6 numbers describing
            the affine transform of the coordinate reference system of the
            exported image's projection, in the order: xScale, xShearing,
            xTranslation, yShearing, yScale and yTranslation. Defaults to
            the image's native CRS transform.
        maxPixels: The maximum allowed number of pixels in the exported
            image. The task will fail if the exported region covers more
            pixels in the specified projection. Defaults to 100,000,000.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'crs_transform'.
    """

    if not isinstance(ee_object, ee.ImageCollection):
        raise ValueError("The ee_object must be an ee.ImageCollection.")

    try:
        count = int(ee_object.size().getInfo())
        print(f"Total number of images: {count}\n")

        if (descriptions is not None) and (len(descriptions) != count):
            print("The number of descriptions is not equal to the number of images.")
            return

        if descriptions is None:
            descriptions = ee_object.aggregate_array("system:index").getInfo()

        if assetIds is None:
            assetIds = descriptions

        images = ee_object.toList(count)

        if os.environ.get("USE_MKDOCS") is not None:  # skip if running GitHub CI.
            return

        for i in range(0, count):
            image = ee.Image(images.get(i))
            description = descriptions[i]
            assetId = assetIds[i]
            ee_export_image_to_asset(
                image,
                description,
                assetId,
                pyramidingPolicy,
                dimensions,
                region,
                scale,
                crs,
                crsTransform,
                maxPixels,
                **kwargs,
            )

    except Exception as e:
        print(e)


def ee_export_image_collection_to_cloud_storage(
    ee_object,
    descriptions=None,
    bucket=None,
    fileNamePrefix=None,
    dimensions=None,
    region=None,
    scale=None,
    crs=None,
    crsTransform=None,
    maxPixels=None,
    shardSize=None,
    fileDimensions=None,
    skipEmptyTiles=None,
    fileFormat=None,
    formatOptions=None,
    **kwargs,
):
    """Creates a batch task to export an ImageCollection as raster images to a Google Cloud bucket.

    Args:
        ee_object: The image collection to export.
        descriptions: A list of human-readable names of the tasks.
        bucket: The name of a Cloud Storage bucket for the export.
        fileNamePrefix: Cloud Storage object name prefix for the export.
            Defaults to the name of the task.
        dimensions: The dimensions of the exported image. Takes either a
            single positive integer as the maximum dimension or "WIDTHxHEIGHT"
            where WIDTH and HEIGHT are each positive integers.
        region: The lon,lat coordinates for a LinearRing or Polygon
            specifying the region to export. Can be specified as a nested
            lists of numbers or a serialized string. Defaults to the image's
            region.
        scale: The resolution in meters per pixel. Defaults to the
            native resolution of the image asset unless a crsTransform
            is specified.
        crs: The coordinate reference system of the exported image's
            projection. Defaults to the image's default projection.
        crsTransform: A comma-separated string of 6 numbers describing
            the affine transform of the coordinate reference system of the
            exported image's projection, in the order: xScale, xShearing,
            xTranslation, yShearing, yScale and yTranslation. Defaults to
            the image's native CRS transform.
        maxPixels: The maximum allowed number of pixels in the exported
            image. The task will fail if the exported region covers more
            pixels in the specified projection. Defaults to 100,000,000.
        shardSize: Size in pixels of the tiles in which this image will be
            computed. Defaults to 256.
        fileDimensions: The dimensions in pixels of each image file, if the
            image is too large to fit in a single file. May specify a
            single number to indicate a square shape, or a tuple of two
            dimensions to indicate (width,height). Note that the image will
            still be clipped to the overall image dimensions. Must be a
            multiple of shardSize.
        skipEmptyTiles: If true, skip writing empty (i.e. fully-masked)
            image tiles. Defaults to false.
        fileFormat: The string file format to which the image is exported.
            Currently only 'GeoTIFF' and 'TFRecord' are supported, defaults to
            'GeoTIFF'.
        formatOptions: A dictionary of string keys to format specific options.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'crs_transform'.
    """

    if not isinstance(ee_object, ee.ImageCollection):
        raise ValueError("The ee_object must be an ee.ImageCollection.")

    try:
        count = int(ee_object.size().getInfo())
        print(f"Total number of images: {count}\n")

        if (descriptions is not None) and (len(descriptions) != count):
            print("The number of descriptions is not equal to the number of images.")
            return

        if descriptions is None:
            descriptions = ee_object.aggregate_array("system:index").getInfo()

        images = ee_object.toList(count)

        if os.environ.get("USE_MKDOCS") is not None:  # skip if running GitHub CI.
            return

        for i in range(0, count):
            image = ee.Image(images.get(i))
            description = descriptions[i]
            ee_export_image_to_cloud_storage(
                image,
                description,
                bucket,
                fileNamePrefix,
                dimensions,
                region,
                scale,
                crs,
                crsTransform,
                maxPixels,
                shardSize,
                fileDimensions,
                skipEmptyTiles,
                fileFormat,
                formatOptions,
                **kwargs,
            )

    except Exception as e:
        print(e)


def ee_export_geojson(
    ee_object, filename=None, selectors=None, timeout=300, proxies=None
):
    """Exports Earth Engine FeatureCollection to geojson.

    Args:
        ee_object (object): ee.FeatureCollection to export.
        filename (str): Output file name. Defaults to None.
        selectors (list, optional): A list of attributes to export. Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 300 seconds.
        proxies (dict, optional): Proxy settings. Defaults to None.
    """

    if not isinstance(ee_object, ee.FeatureCollection):
        print("The ee_object must be an ee.FeatureCollection.")
        return

    if filename is None:
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = os.path.join(out_dir, random_string(6) + ".geojson")

    allowed_formats = ["geojson"]
    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()

    if not (filetype.lower() in allowed_formats):
        print("The output file type must be geojson.")
        return

    if selectors is None:
        selectors = ee_object.first().propertyNames().getInfo()
        selectors = [".geo"] + selectors

    elif not isinstance(selectors, list):
        print("selectors must be a list, such as ['attribute1', 'attribute2']")
        return
    else:
        allowed_attributes = ee_object.first().propertyNames().getInfo()
        for attribute in selectors:
            if not (attribute in allowed_attributes):
                print(
                    "Attributes must be one chosen from: {} ".format(
                        ", ".join(allowed_attributes)
                    )
                )
                return

    try:
        # print('Generating URL ...')
        url = ee_object.getDownloadURL(
            filetype=filetype, selectors=selectors, filename=name
        )
        # print('Downloading data from {}\nPlease wait ...'.format(url))
        r = None
        r = requests.get(url, stream=True, timeout=timeout, proxies=proxies)

        if r.status_code != 200:
            print("An error occurred while downloading. \n Retrying ...")
            try:
                new_ee_object = ee_object.map(filter_polygons)
                print("Generating URL ...")
                url = new_ee_object.getDownloadURL(
                    filetype=filetype, selectors=selectors, filename=name
                )
                print(f"Downloading data from {url}\nPlease wait ...")
                r = requests.get(url, stream=True, timeout=timeout, proxies=proxies)
            except Exception as e:
                print(e)

        with open(filename, "wb") as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)
    except Exception as e:
        print("An error occurred while downloading.")
        if r is not None:
            print(r.json()["error"]["message"])

        return

    with open(filename) as f:
        geojson = f.read()

    return geojson


def ee_export_vector(
    ee_object,
    filename,
    selectors=None,
    verbose=True,
    keep_zip=False,
    timeout=300,
    proxies=None,
):
    """Exports Earth Engine FeatureCollection to other formats, including shp, csv, json, kml, and kmz.

    Args:
        ee_object (object): ee.FeatureCollection to export.
        filename (str): Output file name.
        selectors (list, optional): A list of attributes to export. Defaults to None.
        verbose (bool, optional): Whether to print out descriptive text.
        keep_zip (bool, optional): Whether to keep the downloaded shapefile as a zip file.
        timeout (int, optional): Timeout in seconds. Defaults to 300 seconds.
        proxies (dict, optional): A dictionary of proxies to use. Defaults to None.
    """

    if not isinstance(ee_object, ee.FeatureCollection):
        raise ValueError("ee_object must be an ee.FeatureCollection")

    allowed_formats = ["csv", "geojson", "json", "kml", "kmz", "shp"]
    # allowed_formats = ['csv', 'kml', 'kmz']
    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()

    if filetype == "shp":
        filename = filename.replace(".shp", ".zip")

    if not (filetype.lower() in allowed_formats):
        raise ValueError(
            "The file type must be one of the following: {}".format(
                ", ".join(allowed_formats)
            )
        )

    if selectors is None:
        selectors = ee_object.first().propertyNames().getInfo()
        if filetype == "csv":
            # remove .geo coordinate field
            ee_object = ee_object.select([".*"], None, False)

    if filetype == "geojson":
        selectors = [".geo"] + selectors

    elif not isinstance(selectors, list):
        raise ValueError(
            "selectors must be a list, such as ['attribute1', 'attribute2']"
        )
    else:
        allowed_attributes = ee_object.first().propertyNames().getInfo()
        for attribute in selectors:
            if not (attribute in allowed_attributes):
                raise ValueError(
                    "Attributes must be one chosen from: {} ".format(
                        ", ".join(allowed_attributes)
                    )
                )

    try:
        if verbose:
            print("Generating URL ...")
        url = ee_object.getDownloadURL(
            filetype=filetype, selectors=selectors, filename=name
        )
        if verbose:
            print(f"Downloading data from {url}\nPlease wait ...")
        r = None
        r = requests.get(url, stream=True, timeout=timeout, proxies=proxies)

        if r.status_code != 200:
            print("An error occurred while downloading. \n Retrying ...")
            try:
                new_ee_object = ee_object.map(filter_polygons)
                print("Generating URL ...")
                url = new_ee_object.getDownloadURL(
                    filetype=filetype, selectors=selectors, filename=name
                )
                print(f"Downloading data from {url}\nPlease wait ...")
                r = requests.get(url, stream=True, timeout=timeout, proxies=proxies)
            except Exception as e:
                print(e)
                raise ValueError

        with open(filename, "wb") as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)
    except Exception as e:
        print("An error occurred while downloading.")
        if r is not None:
            print(r.json()["error"]["message"])
        raise ValueError(e)

    try:
        if filetype == "shp":
            with zipfile.ZipFile(filename) as z:
                z.extractall(os.path.dirname(filename))
            if not keep_zip:
                os.remove(filename)
            filename = filename.replace(".zip", ".shp")
        if verbose:
            print(f"Data downloaded to {filename}")
    except Exception as e:
        raise ValueError(e)


def ee_export_vector_to_drive(
    collection,
    description="myExportTableTask",
    folder=None,
    fileNamePrefix=None,
    fileFormat=None,
    selectors=None,
    maxVertices=None,
    **kwargs,
):
    """Creates a task to export a FeatureCollection to Drive.

    Args:
        collection: The feature collection to be exported.
        description: Human-readable name of the task.
        folder: The name of a unique folder in your Drive account to
            export into. Defaults to the root of the drive.
        fileNamePrefix: The Google Drive filename for the export.
            Defaults to the name of the task.
        fileFormat: The output format: "CSV" (default), "GeoJSON", "KML",
            "KMZ", "SHP", or "TFRecord".
        selectors: The list of properties to include in the output, as a list
            of strings or a comma-separated string. By default, all properties
            are included.
        maxVertices:
            Max number of uncut vertices per geometry; geometries with more
            vertices will be cut into pieces smaller than this size.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'driveFolder' and 'driveFileNamePrefix'.
    """
    if not isinstance(collection, ee.FeatureCollection):
        raise ValueError("The collection must be an ee.FeatureCollection.")

    allowed_formats = ["csv", "geojson", "kml", "kmz", "shp", "tfrecord"]
    if not (fileFormat.lower() in allowed_formats):
        raise ValueError(
            "The file type must be one of the following: {}".format(
                ", ".join(allowed_formats)
            )
        )

    if os.environ.get("USE_MKDOCS") is not None:  # skip if running GitHub CI.
        return

    print(
        f"Exporting {description}... Please check the Task Manager from the JavaScript Code Editor."
    )

    task = ee.batch.Export.table.toDrive(
        collection,
        description,
        folder,
        fileNamePrefix,
        fileFormat,
        selectors,
        maxVertices,
        **kwargs,
    )
    task.start()


def ee_export_vector_to_asset(
    collection,
    description="myExportTableTask",
    assetId=None,
    maxVertices=None,
    **kwargs,
):
    """Creates a task to export a FeatureCollection to Asset.

    Args:
        collection: The feature collection to be exported.
        description: Human-readable name of the task.
        assetId: The destination asset ID.
        maxVertices:
            Max number of uncut vertices per geometry; geometries with more
            vertices will be cut into pieces smaller than this size.
        **kwargs: Holds other keyword arguments that may have been deprecated.
    """
    if not isinstance(collection, ee.FeatureCollection):
        raise ValueError("The collection must be an ee.FeatureCollection.")

    if os.environ.get("USE_MKDOCS") is not None:  # skip if running GitHub CI.
        return

    if isinstance(assetId, str):
        if assetId.startswith("users/") or assetId.startswith("projects/"):
            pass
        else:
            assetId = f"{ee_user_id()}/{assetId}"

    print(assetId)
    print(
        f"Exporting {description}... Please check the Task Manager from the JavaScript Code Editor."
    )

    task = ee.batch.Export.table.toAsset(
        collection,
        description,
        assetId,
        maxVertices,
        **kwargs,
    )
    task.start()


def ee_export_vector_to_cloud_storage(
    collection,
    description="myExportTableTask",
    bucket=None,
    fileNamePrefix=None,
    fileFormat=None,
    selectors=None,
    maxVertices=None,
    **kwargs,
):
    """Creates a task to export a FeatureCollection to Google Cloud Storage.

    Args:
        collection: The feature collection to be exported.
        description: Human-readable name of the task.
        bucket: The name of a Cloud Storage bucket for the export.
        fileNamePrefix: Cloud Storage object name prefix for the export.
            Defaults to the name of the task.
        fileFormat: The output format: "CSV" (default), "GeoJSON", "KML", "KMZ",
            "SHP", or "TFRecord".
        selectors: The list of properties to include in the output, as a list
            of strings or a comma-separated string. By default, all properties
            are included.
        maxVertices:
            Max number of uncut vertices per geometry; geometries with more
            vertices will be cut into pieces smaller than this size.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'outputBucket'.
    """
    if not isinstance(collection, ee.FeatureCollection):
        raise ValueError("The collection must be an ee.FeatureCollection.")

    allowed_formats = ["csv", "geojson", "kml", "kmz", "shp", "tfrecord"]
    if not (fileFormat.lower() in allowed_formats):
        raise ValueError(
            "The file type must be one of the following: {}".format(
                ", ".join(allowed_formats)
            )
        )

    if os.environ.get("USE_MKDOCS") is not None:  # skip if running GitHub CI.
        return

    print(
        f"Exporting {description}... Please check the Task Manager from the JavaScript Code Editor."
    )

    task = ee.batch.Export.table.toCloudStorage(
        collection,
        description,
        bucket,
        fileNamePrefix,
        fileFormat,
        selectors,
        maxVertices,
        **kwargs,
    )
    task.start()


def ee_export_vector_to_feature_view(
    collection,
    description="myExportTableTask",
    assetId=None,
    ingestionTimeParameters=None,
    **kwargs,
):
    """Creates a task to export a FeatureCollection to a FeatureView.

    Args:
        collection: The feature collection to be exported.
        description: Human-readable name of the task.
        assetId: The destination asset ID.
        ingestionTimeParameters: The FeatureView ingestion time parameters.
        **kwargs: Holds other keyword arguments that may have been deprecated.
    """
    if not isinstance(collection, ee.FeatureCollection):
        raise ValueError("The collection must be an ee.FeatureCollection.")

    if os.environ.get("USE_MKDOCS") is not None:  # skip if running GitHub CI.
        return

    print(
        f"Exporting {description}... Please check the Task Manager from the JavaScript Code Editor."
    )

    task = ee.batch.Export.table.toFeatureView(
        collection,
        description,
        assetId,
        ingestionTimeParameters,
        **kwargs,
    )
    task.start()


def ee_export_video_to_drive(
    collection,
    description="myExportVideoTask",
    folder=None,
    fileNamePrefix=None,
    framesPerSecond=None,
    dimensions=None,
    region=None,
    scale=None,
    crs=None,
    crsTransform=None,
    maxPixels=None,
    maxFrames=None,
    **kwargs,
):
    """Creates a task to export an ImageCollection as a video to Drive.

    Args:
        collection: The image collection to be exported. The collection must
            only contain RGB images.
        description: Human-readable name of the task.
        folder: The name of a unique folder in your Drive account to
            export into. Defaults to the root of the drive.
        fileNamePrefix: The Google Drive filename for the export.
            Defaults to the name of the task.
        framesPerSecond: A number between .1 and 120 describing the
            framerate of the exported video.
        dimensions: The dimensions of the exported video. Takes either a
            single positive integer as the maximum dimension or "WIDTHxHEIGHT"
            where WIDTH and HEIGHT are each positive integers.
        region: The lon,lat coordinates for a LinearRing or Polygon
            specifying the region to export. Can be specified as a nested
            lists of numbers or a serialized string. Defaults to the first
            image's region.
        scale: The resolution in meters per pixel.
        crs: The coordinate reference system of the exported video's
            projection. Defaults to SR-ORG:6627.
        crsTransform: A comma-separated string of 6 numbers describing
            the affine transform of the coordinate reference system of the
            exported video's projection, in the order: xScale, xShearing,
            xTranslation, yShearing, yScale and yTranslation. Defaults to
            the image collection's native CRS transform.
        maxPixels: The maximum number of pixels per frame.
            Defaults to 1e8 pixels per frame. By setting this explicitly,
            you may raise or lower the limit.
        maxFrames: The maximum number of frames to export.
            Defaults to 1000 frames. By setting this explicitly, you may
            raise or lower the limit.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'crs_transform'.

    """
    if not isinstance(collection, ee.ImageCollection):
        raise TypeError("collection must be an ee.ImageCollection")

    if os.environ.get("USE_MKDOCS") is not None:  # skip if running GitHub CI.
        return

    print(
        f"Exporting {description}... Please check the Task Manager from the JavaScript Code Editor."
    )

    task = ee.batch.Export.video.toDrive(
        collection,
        description,
        folder,
        fileNamePrefix,
        framesPerSecond,
        dimensions,
        region,
        scale,
        crs,
        crsTransform,
        maxPixels,
        maxFrames,
        **kwargs,
    )
    task.start()


def ee_export_video_to_cloud_storage(
    collection,
    description="myExportVideoTask",
    bucket=None,
    fileNamePrefix=None,
    framesPerSecond=None,
    dimensions=None,
    region=None,
    scale=None,
    crs=None,
    crsTransform=None,
    maxPixels=None,
    maxFrames=None,
    **kwargs,
):
    """Creates a task to export an ImageCollection as a video to Cloud Storage.

    Args:
        collection: The image collection to be exported. The collection must
            only contain RGB images.
        description: Human-readable name of the task.
        bucket: The name of a Cloud Storage bucket for the export.
        fileNamePrefix: Cloud Storage object name prefix for the export.
            Defaults to the task's description.
        framesPerSecond: A number between .1 and 120 describing the
            framerate of the exported video.
        dimensions: The dimensions of the exported video. Takes either a
            single positive integer as the maximum dimension or "WIDTHxHEIGHT"
            where WIDTH and HEIGHT are each positive integers.
        region: The lon,lat coordinates for a LinearRing or Polygon
            specifying the region to export. Can be specified as a nested
            lists of numbers or a serialized string. Defaults to the first
            image's region.
        scale: The resolution in meters per pixel.
        crs: The coordinate reference system of the exported video's
            projection. Defaults to SR-ORG:6627.
        crsTransform: A comma-separated string of 6 numbers describing
            the affine transform of the coordinate reference system of the
            exported video's projection, in the order: xScale, xShearing,
            xTranslation, yShearing, yScale and yTranslation. Defaults to
            the image collection's native CRS transform.
        maxPixels: The maximum number of pixels per frame.
            Defaults to 1e8 pixels per frame. By setting this explicitly,
            you may raise or lower the limit.
        maxFrames: The maximum number of frames to export.
            Defaults to 1000 frames. By setting this explicitly, you may
            raise or lower the limit.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'crs_transform'.

    """
    if not isinstance(collection, ee.ImageCollection):
        raise TypeError("collection must be an ee.ImageCollection")

    if os.environ.get("USE_MKDOCS") is not None:  # skip if running GitHub CI.
        return

    print(
        f"Exporting {description}... Please check the Task Manager from the JavaScript Code Editor."
    )

    task = ee.batch.Export.video.toCloudStorage(
        collection,
        description,
        bucket,
        fileNamePrefix,
        framesPerSecond,
        dimensions,
        region,
        scale,
        crs,
        crsTransform,
        maxPixels,
        maxFrames,
        **kwargs,
    )
    task.start()


def ee_export_map_to_cloud_storage(
    image,
    description="myExportMapTask",
    bucket=None,
    fileFormat=None,
    path=None,
    writePublicTiles=None,
    maxZoom=None,
    scale=None,
    minZoom=None,
    region=None,
    skipEmptyTiles=None,
    mapsApiKey=None,
    **kwargs,
):
    """Creates a task to export an Image as a pyramid of map tiles.

    Exports a rectangular pyramid of map tiles for use with web map
    viewers. The map tiles will be accompanied by a reference
    index.html file that displays them using the Google Maps API,
    and an earth.html file for opening the map on Google Earth.

    Args:
        image: The image to export as tiles.
        description: Human-readable name of the task.
        bucket: The destination bucket to write to.
        fileFormat: The map tiles' file format, one of 'auto', 'png',
            or 'jpeg'. Defaults to 'auto', which means that opaque tiles
            will be encoded as 'jpg' and tiles with transparency will be
            encoded as 'png'.
        path: The string used as the output's path. A trailing '/'
            is optional. Defaults to the task's description.
        writePublicTiles: Whether to write public tiles instead of using the
            bucket's default object ACL. Defaults to True and requires the
            invoker to be an OWNER of bucket.
        maxZoom: The maximum zoom level of the map tiles to export.
        scale: The max image resolution in meters per pixel, as an alternative
            to 'maxZoom'. The scale will be converted to the most appropriate
            maximum zoom level at the equator.
        minZoom: The optional minimum zoom level of the map tiles to export.
        region: The lon,lat coordinates for a LinearRing or Polygon
            specifying the region to export. Can be specified as a nested
            lists of numbers or a serialized string. Map tiles will be
            produced in the rectangular region containing this geometry.
            Defaults to the image's region.
        skipEmptyTiles: If true, skip writing empty (i.e. fully-transparent)
            map tiles. Defaults to false.
        mapsApiKey: Used in index.html to initialize the Google Maps API. This
            removes the "development purposes only" message from the map.
        **kwargs: Holds other keyword arguments that may have been deprecated
            such as 'crs_transform'.

    """
    if not isinstance(image, ee.Image):
        raise TypeError("image must be an ee.Image")

    if os.environ.get("USE_MKDOCS") is not None:  # skip if running GitHub CI.
        return

    print(
        f"Exporting {description}... Please check the Task Manager from the JavaScript Code Editor."
    )

    task = ee.batch.Export.map.toCloudStorage(
        image,
        description,
        bucket,
        fileFormat,
        path,
        writePublicTiles,
        maxZoom,
        scale,
        minZoom,
        region,
        skipEmptyTiles,
        mapsApiKey,
        **kwargs,
    )
    task.start()


# ******************************************************************************#
# The classes and functions above are the core features of the geemap package.  #
# The Earth Engine team and the geemap community will maintain these features.  #
# ******************************************************************************#

# ******************************************************************************#
# The classes and functions below are the extra features of the geemap package. #
# The geemap community will maintain these features.                            #
# ******************************************************************************#


class TitilerEndpoint:
    """This class contains the methods for the titiler endpoint."""

    def __init__(
        self,
        endpoint="https://titiler.xyz",
        name="stac",
        TileMatrixSetId="WebMercatorQuad",
    ):
        """Initialize the TitilerEndpoint object.

        Args:
            endpoint (str, optional): The endpoint of the titiler server. Defaults to "https://titiler.xyz".
            name (str, optional): The name to be used in the file path. Defaults to "stac".
            TileMatrixSetId (str, optional): The TileMatrixSetId to be used in the file path. Defaults to "WebMercatorQuad".
        """
        self.endpoint = endpoint
        self.name = name
        self.TileMatrixSetId = TileMatrixSetId

    def url_for_stac_item(self):
        return f"{self.endpoint}/{self.name}/{self.TileMatrixSetId}/tilejson.json"

    def url_for_stac_assets(self):
        return f"{self.endpoint}/{self.name}/assets"

    def url_for_stac_bounds(self):
        return f"{self.endpoint}/{self.name}/bounds"

    def url_for_stac_info(self):
        return f"{self.endpoint}/{self.name}/info"

    def url_for_stac_info_geojson(self):
        return f"{self.endpoint}/{self.name}/info.geojson"

    def url_for_stac_statistics(self):
        return f"{self.endpoint}/{self.name}/statistics"

    def url_for_stac_pixel_value(self, lon, lat):
        return f"{self.endpoint}/{self.name}/point/{lon},{lat}"

    def url_for_stac_wmts(self):
        return (
            f"{self.endpoint}/{self.name}/{self.TileMatrixSetId}/WMTSCapabilities.xml"
        )


class PlanetaryComputerEndpoint(TitilerEndpoint):
    """This class contains the methods for the Microsoft Planetary Computer endpoint."""

    def __init__(
        self,
        endpoint="https://planetarycomputer.microsoft.com/api/data/v1",
        name="item",
        TileMatrixSetId="WebMercatorQuad",
    ):
        """Initialize the PlanetaryComputerEndpoint object.

        Args:
            endpoint (str, optional): The endpoint of the titiler server. Defaults to "https://planetarycomputer.microsoft.com/api/data/v1".
            name (str, optional): The name to be used in the file path. Defaults to "item".
            TileMatrixSetId (str, optional): The TileMatrixSetId to be used in the file path. Defaults to "WebMercatorQuad".
        """
        super().__init__(endpoint, name, TileMatrixSetId)

    def url_for_stac_collection(self):
        return f"{self.endpoint}/collection/{self.TileMatrixSetId}/tilejson.json"

    def url_for_collection_assets(self):
        return f"{self.endpoint}/collection/assets"

    def url_for_collection_bounds(self):
        return f"{self.endpoint}/collection/bounds"

    def url_for_collection_info(self):
        return f"{self.endpoint}/collection/info"

    def url_for_collection_info_geojson(self):
        return f"{self.endpoint}/collection/info.geojson"

    def url_for_collection_pixel_value(self, lon, lat):
        return f"{self.endpoint}/collection/point/{lon},{lat}"

    def url_for_collection_wmts(self):
        return f"{self.endpoint}/collection/{self.TileMatrixSetId}/WMTSCapabilities.xml"

    def url_for_collection_lat_lon_assets(self, lng, lat):
        return f"{self.endpoint}/collection/{lng},{lat}/assets"

    def url_for_collection_bbox_assets(self, minx, miny, maxx, maxy):
        return f"{self.endpoint}/collection/{minx},{miny},{maxx},{maxy}/assets"

    def url_for_stac_mosaic(self, searchid):
        return f"{self.endpoint}/mosaic/{searchid}/{self.TileMatrixSetId}/tilejson.json"

    def url_for_mosaic_info(self, searchid):
        return f"{self.endpoint}/mosaic/{searchid}/info"

    def url_for_mosaic_lat_lon_assets(self, searchid, lon, lat):
        return f"{self.endpoint}/mosaic/{searchid}/{lon},{lat}/assets"


def check_titiler_endpoint(titiler_endpoint=None):
    """Returns the default titiler endpoint.

    Returns:
        object: A titiler endpoint.
    """
    if titiler_endpoint is None:
        if os.environ.get("TITILER_ENDPOINT") is not None:
            titiler_endpoint = os.environ.get("TITILER_ENDPOINT")

            if titiler_endpoint == "planetary-computer":
                titiler_endpoint = PlanetaryComputerEndpoint()
        else:
            titiler_endpoint = "https://titiler.xyz"
    elif titiler_endpoint in ["planetary-computer", "pc"]:
        titiler_endpoint = PlanetaryComputerEndpoint()

    return titiler_endpoint


def set_proxy(port=1080, ip="http://127.0.0.1", timeout=300):
    """Sets proxy if needed. This is only needed for countries where Google services are not available.

    Args:
        port (int, optional): The proxy port number. Defaults to 1080.
        ip (str, optional): The IP address. Defaults to 'http://127.0.0.1'.
        timeout (int, optional): The timeout in seconds. Defaults to 300.
    """
    try:
        if not ip.startswith("http"):
            ip = "http://" + ip
        proxy = "{}:{}".format(ip, port)

        os.environ["HTTP_PROXY"] = proxy
        os.environ["HTTPS_PROXY"] = proxy

        a = requests.get("https://earthengine.google.com/", timeout=timeout)

        if a.status_code != 200:
            print(
                "Failed to connect to Earth Engine. Please double check the port number and ip address."
            )

    except Exception as e:
        print(e)


def is_drive_mounted():
    """Checks whether Google Drive is mounted in Google Colab.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    drive_path = "/content/drive/My Drive"
    if os.path.exists(drive_path):
        return True
    else:
        return False


def credentials_in_drive():
    """Checks if the ee credentials file exists in Google Drive.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    credentials_path = "/content/drive/My Drive/.config/earthengine/credentials"
    if os.path.exists(credentials_path):
        return True
    else:
        return False


def credentials_in_colab():
    """Checks if the ee credentials file exists in Google Colab.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    credentials_path = "/root/.config/earthengine/credentials"
    if os.path.exists(credentials_path):
        return True
    else:
        return False


def copy_credentials_to_drive():
    """Copies ee credentials from Google Colab to Google Drive."""
    src = "/root/.config/earthengine/credentials"
    dst = "/content/drive/My Drive/.config/earthengine/credentials"

    wd = os.path.dirname(dst)
    if not os.path.exists(wd):
        os.makedirs(wd)

    shutil.copyfile(src, dst)


def copy_credentials_to_colab():
    """Copies ee credentials from Google Drive to Google Colab."""
    src = "/content/drive/My Drive/.config/earthengine/credentials"
    dst = "/root/.config/earthengine/credentials"

    wd = os.path.dirname(dst)
    if not os.path.exists(wd):
        os.makedirs(wd)

    shutil.copyfile(src, dst)


########################################
#         Package Installation         #
########################################


def check_install(package):
    """Checks whether a package is installed. If not, it will install the package.

    Args:
        package (str): The name of the package to check.
    """
    import subprocess

    try:
        __import__(package)
        # print('{} is already installed.'.format(package))
    except ImportError:
        print(f"{package} is not installed. Installing ...")
        try:
            subprocess.check_call(["python", "-m", "pip", "install", package])
        except Exception as e:
            print(f"Failed to install {package}")
            print(e)
        print(f"{package} has been installed successfully.")


def update_package():
    """Updates the geemap package from the geemap GitHub repository without the need to use pip or conda.
    In this way, I don't have to keep updating pypi and conda-forge with every minor update of the package.

    """

    try:
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        clone_repo(out_dir=download_dir)

        pkg_dir = os.path.join(download_dir, "geemap-master")
        work_dir = os.getcwd()
        os.chdir(pkg_dir)

        if shutil.which("pip") is None:
            cmd = "pip3 install ."
        else:
            cmd = "pip install ."

        os.system(cmd)
        os.chdir(work_dir)

        print(
            "\nPlease comment out 'geemap.update_package()' and restart the kernel to take effect:\nJupyter menu -> Kernel -> Restart & Clear Output"
        )

    except Exception as e:
        raise Exception(e)


def check_package(name, URL=""):
    try:
        __import__(name.lower())
    except Exception:
        raise ImportError(
            f"{name} is not installed. Please install it before proceeding. {URL}"
        )


def install_package(package):
    """Install a Python package.

    Args:
        package (str | list): The package name or a GitHub URL or a list of package names or GitHub URLs.
    """
    import subprocess

    if isinstance(package, str):
        packages = [package]

    for package in packages:
        if package.startswith("https"):
            package = f"git+{package}"

        # Execute pip install command and show output in real-time
        command = f"pip install {package}"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)

        # Print output in real-time
        while True:
            output = process.stdout.readline()
            if output == b"" and process.poll() is not None:
                break
            if output:
                print(output.decode("utf-8").strip())

        # Wait for process to complete
        process.wait()


def clone_repo(out_dir=".", unzip=True):
    """Clones the geemap GitHub repository.

    Args:
        out_dir (str, optional): Output folder for the repo. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the repository. Defaults to True.
    """
    url = "https://github.com/gee-community/geemap/archive/master.zip"
    filename = "geemap-master.zip"
    download_from_url(url, out_file_name=filename, out_dir=out_dir, unzip=unzip)


def install_from_github(url):
    """Install a package from a GitHub repository.

    Args:
        url (str): The URL of the GitHub repository.
    """

    try:
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        repo_name = os.path.basename(url)
        zip_url = os.path.join(url, "archive/master.zip")
        filename = repo_name + "-master.zip"
        download_from_url(
            url=zip_url, out_file_name=filename, out_dir=download_dir, unzip=True
        )

        pkg_dir = os.path.join(download_dir, repo_name + "-master")
        pkg_name = os.path.basename(url)
        work_dir = os.getcwd()
        os.chdir(pkg_dir)
        print(f"Installing {pkg_name}...")
        cmd = "pip install ."
        os.system(cmd)
        os.chdir(work_dir)
        print(f"{pkg_name} has been installed successfully.")
        # print("\nPlease comment out 'install_from_github()' and restart the kernel to take effect:\nJupyter menu -> Kernel -> Restart & Clear Output")

    except Exception as e:
        print(e)


def check_git_install():
    """Checks if Git is installed.

    Returns:
        bool: Returns True if Git is installed, otherwise returns False.
    """
    import webbrowser

    cmd = "git --version"
    output = os.popen(cmd).read()

    if "git version" in output:
        return True
    else:
        url = "https://git-scm.com/downloads"
        print(f"Git is not installed. Please download Git from {url} and install it.")
        webbrowser.open_new_tab(url)
        return False


def clone_github_repo(url, out_dir):
    """Clones a GitHub repository.

    Args:
        url (str): The link to the GitHub repository
        out_dir (str): The output directory for the cloned repository.
    """

    repo_name = os.path.basename(url)
    # url_zip = os.path.join(url, 'archive/master.zip')
    url_zip = url + "/archive/master.zip"

    if os.path.exists(out_dir):
        print(
            "The specified output directory already exists. Please choose a new directory."
        )
        return

    parent_dir = os.path.dirname(out_dir)
    out_file_path = os.path.join(parent_dir, repo_name + ".zip")

    try:
        urllib.request.urlretrieve(url_zip, out_file_path)
    except Exception:
        print("The provided URL is invalid. Please double check the URL.")
        return

    with zipfile.ZipFile(out_file_path, "r") as zip_ref:
        zip_ref.extractall(parent_dir)

    src = out_file_path.replace(".zip", "-master")
    os.rename(src, out_dir)
    os.remove(out_file_path)


def clone_google_repo(url, out_dir=None):
    """Clones an Earth Engine repository from https://earthengine.googlesource.com, such as https://earthengine.googlesource.com/users/google/datasets

    Args:
        url (str): The link to the Earth Engine repository
        out_dir (str, optional): The output directory for the cloned repository. Defaults to None.
    """
    repo_name = os.path.basename(url)

    if out_dir is None:
        out_dir = os.path.join(os.getcwd(), repo_name)

    if not os.path.exists(os.path.dirname(out_dir)):
        os.makedirs(os.path.dirname(out_dir))

    if os.path.exists(out_dir):
        print(
            "The specified output directory already exists. Please choose a new directory."
        )
        return

    if check_git_install():
        cmd = f'git clone "{url}" "{out_dir}"'
        os.popen(cmd).read()


def open_github(subdir=None):
    """Opens the GitHub repository for this package.

    Args:
        subdir (str, optional): Sub-directory of the repository. Defaults to None.
    """
    import webbrowser

    url = "https://github.com/gee-community/geemap"

    if subdir == "source":
        url += "/tree/master/geemap/"
    elif subdir == "examples":
        url += "/tree/master/examples"
    elif subdir == "tutorials":
        url += "/tree/master/tutorials"

    webbrowser.open_new_tab(url)


def open_youtube():
    """Opens the YouTube tutorials for geemap."""
    import webbrowser

    url = "https://www.youtube.com/playlist?list=PLAxJ4-o7ZoPccOFv1dCwvGI6TYnirRTg3"
    webbrowser.open_new_tab(url)


########################################
#           Python Utilities           #
########################################


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    # from shutil import which

    return shutil.which(name) is not None


def open_image_from_url(url, timeout=300, proxies=None):
    """Loads an image from the specified URL.

    Args:
        url (str): URL of the image.
        timeout (int, optional): Timeout in seconds. Defaults to 300.
        proxies (dict, optional): Dictionary of proxies. Defaults to None.

    Returns:
        object: Image object.
    """
    from PIL import Image

    # from io import BytesIO
    # from urllib.parse import urlparse

    try:
        url = get_direct_url(url)
        response = requests.get(url, timeout=timeout, proxies=proxies)
        img = Image.open(io.BytesIO(response.content))
        return img
    except Exception as e:
        print(e)


def show_image(img_path, width=None, height=None):
    """Shows an image within Jupyter notebook.

    Args:
        img_path (str): The image file path.
        width (int, optional): Width of the image in pixels. Defaults to None.
        height (int, optional): Height of the image in pixels. Defaults to None.

    """
    from IPython.display import display

    try:
        out = widgets.Output()
        # layout={'border': '1px solid black'})
        # layout={'border': '1px solid black', 'width': str(width + 20) + 'px', 'height': str(height + 10) + 'px'},)
        out.outputs = ()
        display(out)
        with out:
            if isinstance(img_path, str) and img_path.startswith("http"):
                file_path = download_file(img_path)
            else:
                file_path = img_path
            file = open(file_path, "rb")
            image = file.read()
            if (width is None) and (height is None):
                display(widgets.Image(value=image))
            elif (width is not None) and (height is not None):
                display(widgets.Image(value=image, width=width, height=height))
            else:
                print("You need set both width and height.")
                return
    except Exception as e:
        print(e)


def show_html(html):
    """Shows HTML within Jupyter notebook.

    Args:
        html (str): File path or HTML string.

    Raises:
        FileNotFoundError: If the file does not exist.

    Returns:
        ipywidgets.HTML: HTML widget.
    """
    if os.path.exists(html):
        with open(html, "r") as f:
            content = f.read()

        widget = widgets.HTML(value=content)
        return widget
    else:
        try:
            widget = widgets.HTML(value=html)
            return widget
        except Exception as e:
            raise Exception(e)


def has_transparency(img):
    """Checks whether an image has transparency.

    Args:
        img (object):  a PIL Image object.

    Returns:
        bool: True if it has transparency, False otherwise.
    """

    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True

    return False


def upload_to_imgur(in_gif):
    """Uploads an image to imgur.com

    Args:
        in_gif (str): The file path to the image.
    """
    import subprocess

    pkg_name = "imgur-uploader"
    if not is_tool(pkg_name):
        check_install(pkg_name)

    try:
        IMGUR_API_ID = os.environ.get("IMGUR_API_ID", None)
        IMGUR_API_SECRET = os.environ.get("IMGUR_API_SECRET", None)
        credentials_path = os.path.join(
            os.path.expanduser("~"), ".config/imgur_uploader/uploader.cfg"
        )

        if (
            (IMGUR_API_ID is not None) and (IMGUR_API_SECRET is not None)
        ) or os.path.exists(credentials_path):
            proc = subprocess.Popen(["imgur-uploader", in_gif], stdout=subprocess.PIPE)
            for _ in range(0, 2):
                line = proc.stdout.readline()
                print(line.rstrip().decode("utf-8"))
            # while True:
            #     line = proc.stdout.readline()
            #     if not line:
            #         break
            #     print(line.rstrip().decode("utf-8"))
        else:
            print(
                "Imgur API credentials could not be found. Please check https://pypi.org/project/imgur-uploader/ for instructions on how to get Imgur API credentials"
            )
            return

    except Exception as e:
        print(e)


########################################
#           Color and Fonts            #
########################################


def system_fonts(show_full_path=False):
    """Gets a list of system fonts

        # Common font locations:
        # Linux: /usr/share/fonts/TTF/
        # Windows: C:/Windows/Fonts
        # macOS:  System > Library > Fonts

    Args:
        show_full_path (bool, optional): Whether to show the full path of each system font. Defaults to False.

    Returns:
        list: A list of system fonts.
    """
    try:
        import matplotlib.font_manager

        font_list = matplotlib.font_manager.findSystemFonts(
            fontpaths=None, fontext="ttf"
        )
        font_list.sort()

        font_names = [os.path.basename(f) for f in font_list]
        font_names.sort()

        if show_full_path:
            return font_list
        else:
            return font_names

    except Exception as e:
        print(e)


########################################
#           Data Download              #
########################################


def download_from_url(url, out_file_name=None, out_dir=".", unzip=True, verbose=True):
    """Download a file from a URL (e.g., https://github.com/giswqs/whitebox/raw/master/examples/testdata.zip)

    Args:
        url (str): The HTTP URL to download.
        out_file_name (str, optional): The output file name to use. Defaults to None.
        out_dir (str, optional): The output directory to use. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the downloaded file if it is a zip file. Defaults to True.
        verbose (bool, optional): Whether to display or not the output of the function
    """
    in_file_name = os.path.basename(url)

    if out_file_name is None:
        out_file_name = in_file_name
    out_file_path = os.path.join(os.path.abspath(out_dir), out_file_name)

    if verbose:
        print(f"Downloading {url} ...")

    try:
        urllib.request.urlretrieve(url, out_file_path)
    except Exception:
        raise Exception("The URL is invalid. Please double check the URL.")

    final_path = out_file_path

    if unzip:
        # if it is a zip file
        if ".zip" in out_file_name:
            if verbose:
                print(f"Unzipping {out_file_name} ...")
            with zipfile.ZipFile(out_file_path, "r") as zip_ref:
                zip_ref.extractall(out_dir)
            final_path = os.path.join(
                os.path.abspath(out_dir), out_file_name.replace(".zip", "")
            )

        # if it is a tar file
        if ".tar" in out_file_name:
            if verbose:
                print(f"Unzipping {out_file_name} ...")
            with tarfile.open(out_file_path, "r") as tar_ref:
                with tarfile.open(out_file_path, "r") as tar_ref:

                    def is_within_directory(directory, target):
                        abs_directory = os.path.abspath(directory)
                        abs_target = os.path.abspath(target)

                        prefix = os.path.commonprefix([abs_directory, abs_target])

                        return prefix == abs_directory

                    def safe_extract(
                        tar, path=".", members=None, *, numeric_owner=False
                    ):
                        for member in tar.getmembers():
                            member_path = os.path.join(path, member.name)
                            if not is_within_directory(path, member_path):
                                raise Exception("Attempted Path Traversal in Tar File")

                        tar.extractall(path, members, numeric_owner=numeric_owner)

                    safe_extract(tar_ref, out_dir)
            final_path = os.path.join(
                os.path.abspath(out_dir), out_file_name.replace(".tar", "")
            )

    if verbose:
        print(f"Data downloaded to: {final_path}")

    return


def download_from_gdrive(gfile_url, file_name, out_dir=".", unzip=True, verbose=True):
    """Download a file shared via Google Drive
       (e.g., https://drive.google.com/file/d/18SUo_HcDGltuWYZs1s7PpOmOq_FvFn04/view?usp=sharing)

    Args:
        gfile_url (str): The Google Drive shared file URL
        file_name (str): The output file name to use.
        out_dir (str, optional): The output directory. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the output file if it is a zip file. Defaults to True.
        verbose (bool, optional): Whether to display or not the output of the function
    """
    try:
        from google_drive_downloader import GoogleDriveDownloader as gdd
    except ImportError:
        raise Exception(
            "Please install the google_drive_downloader package using `pip install googledrivedownloader`"
        )

    file_id = gfile_url.split("/")[5]
    if verbose:
        print(f"Google Drive file id: {file_id}")

    dest_path = os.path.join(out_dir, file_name)
    gdd.download_file_from_google_drive(file_id, dest_path, True, unzip)

    return


def create_download_link(filename, title="Click here to download: "):
    """Downloads a file from voila. Adopted from https://github.com/voila-dashboards/voila/issues/578

    Args:
        filename (str): The file path to the file to download
        title (str, optional): str. Defaults to "Click here to download: ".

    Returns:
        str: HTML download URL.
    """
    import base64

    from IPython.display import HTML

    data = open(filename, "rb").read()
    b64 = base64.b64encode(data)
    payload = b64.decode()
    basename = os.path.basename(filename)
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" style="color:#0000FF;" target="_blank">{title}</a>'
    html = html.format(payload=payload, title=title + f" {basename}", filename=basename)
    return HTML(html)


def edit_download_html(htmlWidget, filename, title="Click here to download: "):
    """Downloads a file from voila. Adopted from https://github.com/voila-dashboards/voila/issues/578#issuecomment-617668058

    Args:
        htmlWidget (object): The HTML widget to display the URL.
        filename (str): File path to download.
        title (str, optional): Download description. Defaults to "Click here to download: ".
    """

    # from IPython.display import HTML
    # import ipywidgets as widgets
    import base64

    # Change widget html temporarily to a font-awesome spinner
    htmlWidget.value = '<i class="fa fa-spinner fa-spin fa-2x fa-fw"></i><span class="sr-only">Loading...</span>'

    # Process raw data
    data = open(filename, "rb").read()
    b64 = base64.b64encode(data)
    payload = b64.decode()

    basename = os.path.basename(filename)

    # Create and assign html to widget
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
    htmlWidget.value = html.format(
        payload=payload, title=title + basename, filename=basename
    )

    # htmlWidget = widgets.HTML(value = '')
    # htmlWidget


########################################
#           Data Conversion            #
########################################


def xy_to_points(in_csv, latitude="latitude", longitude="longitude", encoding="utf-8"):
    """Converts a csv containing points (latitude and longitude) into an ee.FeatureCollection.

    Args:
        in_csv (str): File path or HTTP URL to the input csv file. For example, https://raw.githubusercontent.com/giswqs/data/main/world/world_cities.csv
        latitude (str, optional): Column name for the latitude column. Defaults to 'latitude'.
        longitude (str, optional): Column name for the longitude column. Defaults to 'longitude'.

    Returns:
        ee.FeatureCollection: The ee.FeatureCollection containing the points converted from the input csv.
    """

    geojson = csv_to_geojson(in_csv, None, latitude, longitude, encoding)
    fc = geojson_to_ee(geojson)
    return fc


def csv_points_to_shp(in_csv, out_shp, latitude="latitude", longitude="longitude"):
    """Converts a csv file containing points (latitude, longitude) into a shapefile.

    Args:
        in_csv (str): File path or HTTP URL to the input csv file. For example, https://raw.githubusercontent.com/giswqs/data/main/world/world_cities.csv
        out_shp (str): File path to the output shapefile.
        latitude (str, optional): Column name for the latitude column. Defaults to 'latitude'.
        longitude (str, optional): Column name for the longitude column. Defaults to 'longitude'.

    """
    import whitebox

    if in_csv.startswith("http") and in_csv.endswith(".csv"):
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        out_name = os.path.basename(in_csv)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        download_from_url(in_csv, out_dir=out_dir, verbose=False)
        in_csv = os.path.join(out_dir, out_name)

    wbt = whitebox.WhiteboxTools()
    in_csv = os.path.abspath(in_csv)
    out_shp = os.path.abspath(out_shp)

    if not os.path.exists(in_csv):
        raise Exception("The provided csv file does not exist.")

    with open(in_csv, encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fields = reader.fieldnames
        xfield = fields.index(longitude)
        yfield = fields.index(latitude)

    wbt.csv_points_to_vector(in_csv, out_shp, xfield=xfield, yfield=yfield, epsg=4326)


def csv_to_shp(
    in_csv, out_shp, latitude="latitude", longitude="longitude", encoding="utf-8"
):
    """Converts a csv file with latlon info to a point shapefile.

    Args:
        in_csv (str): The input csv file containing longitude and latitude columns.
        out_shp (str): The file path to the output shapefile.
        latitude (str, optional): The column name of the latitude column. Defaults to 'latitude'.
        longitude (str, optional): The column name of the longitude column. Defaults to 'longitude'.
    """
    import shapefile as shp

    if in_csv.startswith("http") and in_csv.endswith(".csv"):
        in_csv = github_raw_url(in_csv)
        in_csv = download_file(in_csv, quiet=True, overwrite=True)

    try:
        points = shp.Writer(out_shp, shapeType=shp.POINT)
        with open(in_csv, encoding=encoding) as csvfile:
            csvreader = csv.DictReader(csvfile)
            header = csvreader.fieldnames
            [points.field(field) for field in header]
            for row in csvreader:
                points.point((float(row[longitude])), (float(row[latitude])))
                points.record(*tuple([row[f] for f in header]))

        out_prj = out_shp.replace(".shp", ".prj")
        with open(out_prj, "w") as f:
            prj_str = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]] '
            f.write(prj_str)

    except Exception as e:
        raise Exception(e)


def csv_to_geojson(
    in_csv,
    out_geojson=None,
    latitude="latitude",
    longitude="longitude",
    encoding="utf-8",
):
    """Creates points for a CSV file and exports data as a GeoJSON.

    Args:
        in_csv (str): The file path to the input CSV file.
        out_geojson (str): The file path to the exported GeoJSON. Default to None.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    """

    import pandas as pd

    in_csv = github_raw_url(in_csv)

    if out_geojson is not None:
        out_geojson = check_file_path(out_geojson)

    df = pd.read_csv(in_csv)
    geojson = df_to_geojson(
        df, latitude=latitude, longitude=longitude, encoding=encoding
    )

    if out_geojson is None:
        return geojson
    else:
        with open(out_geojson, "w", encoding=encoding) as f:
            f.write(json.dumps(geojson))


def df_to_geojson(
    df,
    out_geojson=None,
    latitude="latitude",
    longitude="longitude",
    encoding="utf-8",
):
    """Creates points for a Pandas DataFrame and exports data as a GeoJSON.

    Args:
        df (pandas.DataFrame): The input Pandas DataFrame.
        out_geojson (str): The file path to the exported GeoJSON. Default to None.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    """

    from geojson import Feature, FeatureCollection, Point

    if out_geojson is not None:
        out_dir = os.path.dirname(os.path.abspath(out_geojson))
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    features = df.apply(
        lambda row: Feature(
            geometry=Point((float(row[longitude]), float(row[latitude]))),
            properties=dict(row),
        ),
        axis=1,
    ).tolist()

    geojson = FeatureCollection(features=features)

    if out_geojson is None:
        return geojson
    else:
        with open(out_geojson, "w", encoding=encoding) as f:
            f.write(json.dumps(geojson))


def csv_to_ee(
    in_csv, latitude="latitude", longitude="longitude", encoding="utf-8", geodesic=True
):
    """Creates points for a CSV file and exports data as a GeoJSON.

    Args:
        in_csv (str): The file path to the input CSV file.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".
        geodesic (bool, optional): Whether line segments should be interpreted as spherical geodesics. If false, indicates that line segments should be interpreted as planar lines in the specified CRS. If absent, defaults to true if the CRS is geographic (including the default EPSG:4326), or to false if the CRS is projected.

    Returns:
        ee_object: An ee.Geometry object
    """

    geojson = csv_to_geojson(
        in_csv, latitude=latitude, longitude=longitude, encoding=encoding
    )
    fc = geojson_to_ee(geojson, geodesic=geodesic)
    return fc


def csv_to_gdf(in_csv, latitude="latitude", longitude="longitude", encoding="utf-8"):
    """Creates points for a CSV file and converts them to a GeoDataFrame.

    Args:
        in_csv (str): The file path to the input CSV file.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    Returns:
        object: GeoDataFrame.
    """

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    out_dir = os.getcwd()

    out_geojson = os.path.join(out_dir, random_string() + ".geojson")
    csv_to_geojson(in_csv, out_geojson, latitude, longitude, encoding)

    gdf = gpd.read_file(out_geojson)
    os.remove(out_geojson)
    return gdf


def csv_to_vector(
    in_csv,
    output,
    latitude="latitude",
    longitude="longitude",
    encoding="utf-8",
    **kwargs,
):
    """Creates points for a CSV file and converts them to a vector dataset.

    Args:
        in_csv (str): The file path to the input CSV file.
        output (str): The file path to the output vector dataset.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    """
    gdf = csv_to_gdf(in_csv, latitude, longitude, encoding)
    gdf.to_file(output, **kwargs)


def ee_to_geojson(ee_object, filename=None, indent=2, **kwargs):
    """Converts Earth Engine object to geojson.

    Args:
        ee_object (object): An Earth Engine object.
        filename (str, optional): The file path to save the geojson. Defaults to None.

    Returns:
        object: GeoJSON object.
    """

    try:
        if (
            isinstance(ee_object, ee.Geometry)
            or isinstance(ee_object, ee.Feature)
            or isinstance(ee_object, ee.FeatureCollection)
        ):
            json_object = ee_object.getInfo()
            if filename is not None:
                filename = os.path.abspath(filename)
                if not os.path.exists(os.path.dirname(filename)):
                    os.makedirs(os.path.dirname(filename))
                with open(filename, "w") as f:
                    f.write(json.dumps(json_object, indent=indent, **kwargs) + "\n")
            else:
                return json_object
        else:
            print("Could not convert the Earth Engine object to geojson")
    except Exception as e:
        raise Exception(e)


def ee_to_bbox(ee_object):
    """Get the bounding box of an Earth Engine object as a list in the format [xmin, ymin, xmax, ymax].

    Args:
        ee_object (ee.Image | ee.Geometry | ee.Feature | ee.FeatureCollection): The input Earth Engine object.

    Returns:
        list: The bounding box of the Earth Engine object in the format [xmin, ymin, xmax, ymax].
    """
    if (
        isinstance(ee_object, ee.Image)
        or isinstance(ee_object, ee.Feature)
        or isinstance(ee_object, ee.FeatureCollection)
    ):
        geometry = ee_object.geometry()
    elif isinstance(ee_object, ee.Geometry):
        geometry = ee_object
    else:
        raise Exception(
            "The ee_object must be an ee.Image, ee.Feature, ee.FeatureCollection or ee.Geometry object."
        )

    bounds = geometry.bounds().getInfo()["coordinates"][0]
    xmin = bounds[0][0]
    ymin = bounds[0][1]
    xmax = bounds[1][0]
    ymax = bounds[2][1]
    bbox = [xmin, ymin, xmax, ymax]
    return bbox


def shp_to_geojson(in_shp, filename=None, **kwargs):
    """Converts a shapefile to GeoJSON.

    Args:
        in_shp (str): File path of the input shapefile.
        filename (str, optional): File path of the output GeoJSON. Defaults to None.

    Returns:
        object: The json object representing the shapefile.
    """
    try:
        import shapefile

        # from datetime import date

        in_shp = os.path.abspath(in_shp)

        if filename is not None:
            ext = os.path.splitext(filename)[1]
            print(ext)
            if ext.lower() not in [".json", ".geojson"]:
                raise TypeError("The output file extension must the .json or .geojson.")

            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

        if not is_GCS(in_shp):
            try:
                import geopandas as gpd

            except Exception:
                raise ImportError(
                    "GeoPandas is required to perform reprojection of the data. See https://geopandas.org/install.html"
                )

            try:
                in_gdf = gpd.read_file(in_shp)
                out_gdf = in_gdf.to_crs(epsg="4326")
                out_shp = in_shp.replace(".shp", "_gcs.shp")
                out_gdf.to_file(out_shp)
                in_shp = out_shp
            except Exception as e:
                raise Exception(e)

        if "encoding" in kwargs:
            reader = shapefile.Reader(in_shp, encoding=kwargs.pop("encoding"))
        else:
            reader = shapefile.Reader(in_shp)
        out_dict = reader.__geo_interface__
        # fields = reader.fields[1:]
        # field_names = [field[0] for field in fields]
        # # pyShp returns dates as `datetime.date` or as `bytes` when they are empty
        # # This is not JSON compatible, so we keep track of them to convert them to str
        # date_fields_names = [field[0] for field in fields if field[1] == "D"]
        # buffer = []
        # for sr in reader.shapeRecords():
        #     atr = dict(zip(field_names, sr.record))
        #     for date_field in date_fields_names:
        #         value = atr[date_field]
        #         # convert date to string, similar to pyShp writing
        #         # https://github.com/GeospatialPython/pyshp/blob/69c60f6d07c329f7d3ac2cba79bc03643bd424d8/shapefile.py#L1814
        #         if isinstance(value, date):
        #             value = "{:04d}{:02d}{:02d}".format(
        #                 value.year, value.month, value.day
        #             )
        #         elif not value:  # empty bytes string
        #             value = "0" * 8  # QGIS NULL for date type
        #         atr[date_field] = value
        #     geom = sr.shape.__geo_interface__
        #     buffer.append(dict(type="Feature", geometry=geom, properties=atr))

        # out_dict = {"type": "FeatureCollection", "features": buffer}

        if filename is not None:
            # from json import dumps

            with open(filename, "w") as geojson:
                geojson.write(json.dumps(out_dict, indent=2) + "\n")
        else:
            return out_dict

    except Exception as e:
        raise Exception(e)


def shp_to_ee(in_shp, **kwargs):
    """Converts a shapefile to Earth Engine objects. Note that the CRS of the shapefile must be EPSG:4326

    Args:
        in_shp (str): File path to a shapefile.

    Returns:
        object: Earth Engine objects representing the shapefile.
    """
    # ee_initialize()
    try:
        if "encoding" in kwargs:
            json_data = shp_to_geojson(in_shp, encoding=kwargs.pop("encoding"))
        else:
            json_data = shp_to_geojson(in_shp)
        ee_object = geojson_to_ee(json_data)
        return ee_object
    except Exception as e:
        print(e)


########################################
#              Export Data             #
########################################


def filter_polygons(ftr):
    """Converts GeometryCollection to Polygon/MultiPolygon

    Args:
        ftr (object): ee.Feature

    Returns:
        object: ee.Feature
    """
    # ee_initialize()
    geometries = ftr.geometry().geometries()
    geometries = geometries.map(
        lambda geo: ee.Feature(ee.Geometry(geo)).set("geoType", ee.Geometry(geo).type())
    )

    polygons = (
        ee.FeatureCollection(geometries)
        .filter(ee.Filter.eq("geoType", "Polygon"))
        .geometry()
    )
    return ee.Feature(polygons).copyProperties(ftr)


def ee_to_shp(
    ee_object,
    filename,
    columns=None,
    sort_columns=False,
    **kwargs,
):
    """Downloads an ee.FeatureCollection as a shapefile.

    Args:
        ee_object (object): ee.FeatureCollection
        filename (str): The output filepath of the shapefile.
        columns (list, optional): A list of attributes to export. Defaults to None.
        sort_columns (bool, optional): Whether to sort the columns alphabetically. Defaults to False.
        kwargs: Additional arguments passed to ee_to_gdf().

    """
    try:
        if filename.lower().endswith(".shp"):
            gdf = ee_to_gdf(ee_object, columns, sort_columns, **kwargs)
            gdf.to_file(filename)
        else:
            print("The filename must end with .shp")

    except Exception as e:
        print(e)


def ee_to_csv(
    ee_object,
    filename,
    columns=None,
    remove_geom=True,
    sort_columns=False,
    **kwargs,
):
    """Downloads an ee.FeatureCollection as a CSV file.

    Args:
        ee_object (object): ee.FeatureCollection
        filename (str): The output filepath of the CSV file.
        columns (list, optional): A list of attributes to export. Defaults to None.
        remove_geom (bool, optional): Whether to remove the geometry column. Defaults to True.
        sort_columns (bool, optional): Whether to sort the columns alphabetically. Defaults to False.
        kwargs: Additional arguments passed to ee_to_df().

    """
    try:
        if filename.lower().endswith(".csv"):
            df = ee_to_df(ee_object, columns, remove_geom, sort_columns, **kwargs)
            df.to_csv(filename, index=False)
        else:
            print("The filename must end with .csv")

    except Exception as e:
        print(e)


def dict_to_csv(data_dict, out_csv, by_row=False, timeout=300, proxies=None):
    """Downloads an ee.Dictionary as a CSV file.

    Args:
        data_dict (ee.Dictionary): The input ee.Dictionary.
        out_csv (str): The output file path to the CSV file.
        by_row (bool, optional): Whether to use by row or by column. Defaults to False.
        timeout (int, optional): Timeout in seconds. Defaults to 300 seconds.
        proxies (dict, optional): Proxy settings. Defaults to None.
    """

    out_dir = os.path.dirname(out_csv)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not by_row:
        csv_feature = ee.Feature(None, data_dict)
        csv_feat_col = ee.FeatureCollection([csv_feature])
    else:
        keys = data_dict.keys()
        data = keys.map(lambda k: ee.Dictionary({"name": k, "value": data_dict.get(k)}))
        csv_feature = data.map(lambda f: ee.Feature(None, f))
        csv_feat_col = ee.FeatureCollection(csv_feature)

    ee_export_vector(csv_feat_col, out_csv, timeout=timeout, proxies=proxies)


def get_image_thumbnail(
    ee_object,
    out_img,
    vis_params,
    dimensions=500,
    region=None,
    format="jpg",
    crs="EPSG:3857",
    timeout=300,
    proxies=None,
):
    """Download a thumbnail for an ee.Image.

    Args:
        ee_object (object): The ee.Image instance.
        out_img (str): The output file path to the png thumbnail.
        vis_params (dict): The visualization parameters.
        dimensions (int, optional):(a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 500.
        region (object, optional): Geospatial region of the image to render, it may be an ee.Geometry, GeoJSON, or an array of lat/lon points (E,S,W,N). If not set the default is the bounds image. Defaults to None.
        format (str, optional): Either 'png' or 'jpg'. Default to 'jpg'.
        timeout (int, optional): The number of seconds after which the request will be terminated. Defaults to 300.
        proxies (dict, optional): A dictionary of proxy servers to use for the request. Defaults to None.
    """

    if not isinstance(ee_object, ee.Image):
        raise TypeError("The ee_object must be an ee.Image.")

    ext = os.path.splitext(out_img)[1][1:]
    if ext not in ["png", "jpg"]:
        raise ValueError("The output image format must be png or jpg.")
    else:
        format = ext

    out_image = os.path.abspath(out_img)
    out_dir = os.path.dirname(out_image)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if region is not None:
        vis_params["region"] = region

    vis_params["dimensions"] = dimensions
    vis_params["format"] = format
    vis_params["crs"] = crs
    url = ee_object.getThumbURL(vis_params)

    try:
        r = requests.get(url, stream=True, timeout=timeout, proxies=proxies)
    except Exception as e:
        print("An error occurred while downloading.")
        print(e)

    if r.status_code != 200:
        print("An error occurred while downloading.")
        print(r.json()["error"]["message"])

    else:
        with open(out_img, "wb") as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)


def get_image_collection_thumbnails(
    ee_object,
    out_dir,
    vis_params,
    dimensions=500,
    region=None,
    format="jpg",
    names=None,
    verbose=True,
    timeout=300,
    proxies=None,
):
    """Download thumbnails for all images in an ImageCollection.

    Args:
        ee_object (object): The ee.ImageCollection instance.
        out_dir ([str): The output directory to store thumbnails.
        vis_params (dict): The visualization parameters.
        dimensions (int, optional):(a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 500.
        region (object, optional): Geospatial region of the image to render, it may be an ee.Geometry, GeoJSON, or an array of lat/lon points (E,S,W,N). If not set the default is the bounds image. Defaults to None.
        format (str, optional): Either 'png' or 'jpg'. Default to 'jpg'.
        names (list, optional): The list of output file names. Defaults to None.
        verbose (bool, optional): Whether or not to print hints. Defaults to True.
        timeout (int, optional): The number of seconds after which the request will be terminated. Defaults to 300.
        proxies (dict, optional): A dictionary of proxy servers to use for the request. Defaults to None.
    """
    if not isinstance(ee_object, ee.ImageCollection):
        print("The ee_object must be an ee.ImageCollection.")
        raise TypeError("The ee_object must be an ee.Image.")

    if format not in ["png", "jpg"]:
        raise ValueError("The output image format must be png or jpg.")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        count = int(ee_object.size().getInfo())
        if verbose:
            print(f"Total number of images: {count}\n")

        if (names is not None) and (len(names) != count):
            print("The number of names is not equal to the number of images.")
            return

        if names is None:
            names = ee_object.aggregate_array("system:index").getInfo()

        images = ee_object.toList(count)

        for i in range(0, count):
            image = ee.Image(images.get(i))
            name = str(names[i])
            ext = os.path.splitext(name)[1][1:]
            if ext != format:
                name = name + "." + format
            out_img = os.path.join(out_dir, name)
            if verbose:
                print(f"Downloading {i+1}/{count}: {name} ...")

            get_image_thumbnail(
                image,
                out_img,
                vis_params,
                dimensions,
                region,
                format,
                timeout=timeout,
                proxies=proxies,
            )

    except Exception as e:
        print(e)


def netcdf_to_ee(nc_file, var_names, band_names=None, lon="lon", lat="lat", decimal=2):
    """
    Creates an ee.Image from netCDF variables band_names that are read from nc_file. Currently only supports variables in a regular longitude/latitude grid (EPSG:4326).

    Args:
        nc_file (str): the name of the netCDF file to read
        var_names (str or list): the name(s) of the variable(s) to read
        band_names (list, optional): if given, the bands are renamed to band_names. Defaults to the original var_names
        lon (str, optional): the name of the longitude variable in the netCDF file. Defaults to "lon"
        lat (str, optional): the name of the latitude variable in the netCDF file. Defaults to "lat"
        decimal (int, optional): the number of decimal places to round the longitude and latitude values to. Defaults to 2.

    Returns:
        image: An ee.Image

    """
    try:
        import xarray as xr

    except Exception:
        raise ImportError(
            "You need to install xarray first. See https://github.com/pydata/xarray"
        )

    import numpy as np
    from collections import Counter

    def most_common_value(lst):
        counter = Counter(lst)
        most_common = counter.most_common(1)
        return float(format(most_common[0][0], f".{decimal}f"))

    try:
        if not isinstance(nc_file, str):
            print("The input file must be a string.")
            return
        if band_names and not isinstance(band_names, (list, str)):
            print("Band names must be a string or list.")
            return
        if not isinstance(lon, str) or not isinstance(lat, str):
            print("The longitude and latitude variable names must be a string.")
            return

        ds = xr.open_dataset(nc_file)
        data = ds[var_names]

        lon_data = data[lon]
        lat_data = data[lat]

        dim_lon = np.unique(np.ediff1d(lon_data))
        dim_lat = np.unique(np.ediff1d(lat_data))
        dim_lon = [most_common_value(dim_lon)]
        dim_lat = [most_common_value(dim_lat)]

        # if (len(dim_lon) != 1) or (len(dim_lat) != 1):
        #     print("The netCDF file is not a regular longitude/latitude grid")
        #     return

        try:
            data = data.to_array()
            # ^ this is only needed (and works) if we have more than 1 variable
            # axis_for_roll will be used in case we need to use np.roll
            # and should be 1 for the case with more than 1 variable
            axis_for_roll = 1
        except Exception:
            axis_for_roll = 0
            # .to_array() does not work (and is not needed!) if there is only 1 variable
            # in this case, the axis_for_roll needs to be 0

        data_np = np.array(data)

        do_transpose = True  # To do: figure out if we need to transpose the data or not
        if do_transpose:
            try:
                data_np = np.transpose(data_np, (0, 2, 1))
            except Exception:
                data_np = np.transpose(data_np)

        # Figure out if we need to roll the data or not
        # (see https://github.com/gee-community/geemap/issues/285#issuecomment-791385176)
        if np.max(lon_data) > 180:
            data_np = np.roll(data_np, 180, axis=axis_for_roll)
            west_lon = lon_data[0] - 180
        else:
            west_lon = lon_data[0]

        transform = [dim_lon[0], 0, float(west_lon), 0, dim_lat[0], float(lat_data[0])]

        if band_names is None:
            band_names = var_names

        image = numpy_to_ee(
            data_np, "EPSG:4326", transform=transform, band_names=band_names
        )

        return image

    except Exception as e:
        print(e)


def numpy_to_ee(np_array, crs=None, transform=None, transformWkt=None, band_names=None):
    """
    Creates an ee.Image from a 3D numpy array where each 2D numpy slice is added to a band, and a geospatial transform that indicates where to put the data. If the np_array is already 2D only, then it is only a one-band image.

    Args:
        np_array (np.array): the 3D (or 2D) numpy array to add to an image
        crs (str): The base coordinate reference system of this Projection, given as a well-known authority code (e.g. 'EPSG:4326') or a WKT string.
        transform (list): The transform between projected coordinates and the base coordinate system, specified as a 2x3 affine transform matrix in row-major order: [xScale, xShearing, xTranslation, yShearing, yScale, yTranslation]. May not specify both this and 'transformWkt'.
        transformWkt (str): The transform between projected coordinates and the base coordinate system, specified as a WKT string. May not specify both this and 'transform'.
        band_names (str or list, optional): The list of names for the bands. The default names are 'constant', and 'constant_1', 'constant_2', etc.

    Returns:
        image: An ee.Image

    """
    import numpy as np

    if not isinstance(np_array, np.ndarray):
        print("The input must be a numpy.ndarray.")
        return
    if not len(np_array.shape) in [2, 3]:
        print("The input must have 2 or 3 dimensions")
        return
    if band_names and not isinstance(band_names, (list, str)):
        print("Band names must be a str or list")
        return

    try:
        projection = ee.Projection(crs, transform, transformWkt)
        coords = ee.Image.pixelCoordinates(projection).floor().int32()
        x = coords.select("x")
        y = coords.select("y")
        s = np_array.shape
        if len(s) < 3:
            dimx = s[0]
            dimy = s[1]
        else:
            dimx = s[1]
            dimy = s[2]
            dimz = s[0]

        coord_mask = x.gte(0).And(y.gte(0)).And(x.lt(dimx)).And(y.lt(dimy))
        coords = coords.updateMask(coord_mask)

        def list_to_ee(a_list):
            ee_data = ee.Array(a_list)
            image = ee.Image(ee_data).arrayGet(coords)
            return image

        if len(s) < 3:
            image = list_to_ee(np_array.tolist())
        else:
            image = list_to_ee(np_array[0].tolist())
            for z in np.arange(1, dimz):
                image = image.addBands(list_to_ee(np_array[z].tolist()))

        if band_names:
            image = image.rename(band_names)

        return image

    except Exception as e:
        print(e)


def ee_to_numpy(ee_object, region=None, scale=None, bands=None, **kwargs):
    """Extracts a rectangular region of pixels from an image into a numpy array.

    Args:
        ee_object (ee.Image): The image to sample.
        region (ee.Geometry, optional): The region to sample. Defaults to None.
        bands (list, optional): The list of band names to extract. Defaults to None.
        scale (int, optional): A nominal scale in meters of the projection to sample in. Defaults to None.

    Returns:
        np.ndarray: A 3D numpy array in the format of [row, column, band].
    """
    import numpy as np

    if (region is not None) or (scale is not None):
        ee_object = ee_object.clipToBoundsAndScale(geometry=region, scale=scale)

    kwargs["expression"] = ee_object
    kwargs["fileFormat"] = "NUMPY_NDARRAY"
    if bands is not None:
        kwargs["bandIds"] = bands

    try:
        struct_array = ee.data.computePixels(kwargs)
        array = np.dstack(([struct_array[band] for band in struct_array.dtype.names]))
        return array
    except Exception as e:
        raise Exception(e)


def ee_to_xarray(
    dataset,
    drop_variables=None,
    io_chunks=None,
    n_images=-1,
    mask_and_scale=True,
    decode_times=True,
    decode_timedelta=None,
    use_cftime=None,
    concat_characters=True,
    decode_coords=True,
    crs=None,
    scale=None,
    projection=None,
    geometry=None,
    primary_dim_name=None,
    primary_dim_property=None,
    ee_mask_value=None,
    ee_initialize=True,
    **kwargs,
):
    """Open an Earth Engine ImageCollection as an Xarray Dataset. This function is a wrapper for
        xee. EarthEngineBackendEntrypoint.open_dataset().
        See https://github.com/google/Xee/blob/main/xee/ext.py#L886

    Args:
        dataset: An asset ID for an ImageCollection, or an
            ee.ImageCollection object.
        drop_variables (optional): Variables or bands to drop before opening.
        io_chunks (optional): Specifies the chunking strategy for loading data
            from EE. By default, this automatically calculates optional chunks based
            on the `request_byte_limit`.
        n_images (optional): The max number of EE images in the collection to
            open. Useful when there are a large number of images in the collection
            since calculating collection size can be slow. -1 indicates that all
            images should be included.
        mask_and_scale (optional): Lazily scale (using scale_factor and
            add_offset) and mask (using _FillValue).
        decode_times (optional): Decode cf times (e.g., integers since "hours
            since 2000-01-01") to np.datetime64.
        decode_timedelta (optional): If True, decode variables and coordinates
            with time units in {"days", "hours", "minutes", "seconds",
            "milliseconds", "microseconds"} into timedelta objects. If False, leave
            them encoded as numbers. If None (default), assume the same value of
            decode_time.
        use_cftime (optional): Only relevant if encoded dates come from a standard
            calendar (e.g. "gregorian", "proleptic_gregorian", "standard", or not
            specified).  If None (default), attempt to decode times to
            ``np.datetime64[ns]`` objects; if this is not possible, decode times to
            ``cftime.datetime`` objects. If True, always decode times to
            ``cftime.datetime`` objects, regardless of whether or not they can be
            represented using ``np.datetime64[ns]`` objects.  If False, always
            decode times to ``np.datetime64[ns]`` objects; if this is not possible
            raise an error.
        concat_characters (optional): Should character arrays be concatenated to
            strings, for example: ["h", "e", "l", "l", "o"] -> "hello"
        decode_coords (optional): bool or {"coordinates", "all"}, Controls which
            variables are set as coordinate variables: - "coordinates" or True: Set
            variables referred to in the ``'coordinates'`` attribute of the datasets
            or individual variables as coordinate variables. - "all": Set variables
            referred to in  ``'grid_mapping'``, ``'bounds'`` and other attributes as
            coordinate variables.
        crs (optional): The coordinate reference system (a CRS code or WKT
            string). This defines the frame of reference to coalesce all variables
            upon opening. By default, data is opened with `EPSG:4326'.
        scale (optional): The scale in the `crs` or `projection`'s units of
            measure -- either meters or degrees. This defines the scale that all
            data is represented in upon opening. By default, the scale is 1° when
            the CRS is in degrees or 10,000 when in meters.
        projection (optional): Specify an `ee.Projection` object to define the
            `scale` and `crs` (or other coordinate reference system) with which to
            coalesce all variables upon opening. By default, the scale and reference
            system is set by the the `crs` and `scale` arguments.
        geometry (optional): Specify an `ee.Geometry` to define the regional
            bounds when opening the data. When not set, the bounds are defined by
            the CRS's 'area_of_use` boundaries. If those aren't present, the bounds
            are derived from the geometry of the first image of the collection.
        primary_dim_name (optional): Override the name of the primary dimension of
            the output Dataset. By default, the name is 'time'.
        primary_dim_property (optional): Override the `ee.Image` property for
            which to derive the values of the primary dimension. By default, this is
            'system:time_start'.
        ee_mask_value (optional): Value to mask to EE nodata values. By default,
            this is 'np.iinfo(np.int32).max' i.e. 2147483647.
        request_byte_limit: the max allowed bytes to request at a time from Earth
            Engine. By default, it is 48MBs.
        ee_initialize (optional): Whether to initialize ee with the high-volume endpoint. Defaults to True.

    Returns:
      An xarray.Dataset that streams in remote data from Earth Engine.
    """
    try:
        import xee
    except ImportError:
        install_package("xee")
        import xee

    import xarray as xr

    kwargs["drop_variables"] = drop_variables
    kwargs["io_chunks"] = io_chunks
    kwargs["n_images"] = n_images
    kwargs["mask_and_scale"] = mask_and_scale
    kwargs["decode_times"] = decode_times
    kwargs["decode_timedelta"] = decode_timedelta
    kwargs["use_cftime"] = use_cftime
    kwargs["concat_characters"] = concat_characters
    kwargs["decode_coords"] = decode_coords
    kwargs["crs"] = crs
    kwargs["scale"] = scale
    kwargs["projection"] = projection
    kwargs["geometry"] = geometry
    kwargs["primary_dim_name"] = primary_dim_name
    kwargs["primary_dim_property"] = primary_dim_property
    kwargs["ee_mask_value"] = ee_mask_value
    kwargs["engine"] = "ee"

    if ee_initialize:
        opt_url = "https://earthengine-highvolume.googleapis.com"
        ee.Initialize(opt_url=opt_url)

    if isinstance(dataset, str):
        if not dataset.startswith("ee://"):
            dataset = "ee://" + dataset
    elif isinstance(dataset, ee.Image):
        dataset = ee.ImageCollection(dataset)
    elif isinstance(dataset, ee.ImageCollection):
        pass
    elif isinstance(dataset, list):
        items = []
        for item in dataset:
            if isinstance(item, str) and not item.startswith("ee://"):
                item = "ee://" + item
            items.append(item)
        dataset = items
    else:
        raise ValueError(
            "The dataset must be an ee.Image, ee.ImageCollection, or a list of ee.Image."
        )

    if isinstance(dataset, list):
        ds = xr.open_mfdataset(dataset, **kwargs)
    else:
        ds = xr.open_dataset(dataset, **kwargs)

    return ds


def download_ee_video(collection, video_args, out_gif, timeout=300, proxies=None):
    """Downloads a video thumbnail as a GIF image from Earth Engine.

    Args:
        collection (object): An ee.ImageCollection.
        video_args (object): Parameters for expring the video thumbnail.
        out_gif (str): File path to the output GIF.
        timeout (int, optional): The number of seconds the request will be timed out. Defaults to 300.
        proxies (dict, optional): A dictionary of proxy servers to use. Defaults to None.
    """

    out_gif = os.path.abspath(out_gif)
    if not out_gif.endswith(".gif"):
        print("The output file must have an extension of .gif.")
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if "region" in video_args.keys():
        roi = video_args["region"]

        if not isinstance(roi, ee.Geometry):
            try:
                roi = roi.geometry()
            except Exception as e:
                print("Could not convert the provided roi to ee.Geometry")
                print(e)
                return

        video_args["region"] = roi
    if "dimensions" not in video_args:
        video_args["dimensions"] = 768

    try:
        print("Generating URL...")
        url = collection.getVideoThumbURL(video_args)

        print(f"Downloading GIF image from {url}\nPlease wait ...")
        r = requests.get(url, stream=True, timeout=timeout, proxies=proxies)

        if r.status_code != 200:
            print("An error occurred while downloading.")
            print(r.json()["error"]["message"])
            return
        else:
            with open(out_gif, "wb") as fd:
                for chunk in r.iter_content(chunk_size=1024):
                    fd.write(chunk)
            print(f"The GIF image has been saved to: {out_gif}")
    except Exception as e:
        print(e)


def screen_capture(filename, monitor=1):
    """Takes a full screenshot of the selected monitor.

    Args:
        filename (str): The output file path to the screenshot.
        monitor (int, optional): The monitor to take the screenshot. Defaults to 1.
    """
    try:
        from mss import mss
    except ImportError:
        raise ImportError("Please install mss package using 'pip install mss'")

    out_dir = os.path.dirname(filename)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not isinstance(monitor, int):
        print("The monitor number must be an integer.")
        return

    try:
        with mss() as sct:
            sct.shot(output=filename, mon=monitor)
            return filename

    except Exception as e:
        print(e)


########################################
#               geemap GUI             #
########################################


def api_docs():
    """Open a browser and navigate to the geemap API documentation."""
    import webbrowser

    url = "https://geemap.org/geemap"
    webbrowser.open_new_tab(url)


def show_youtube(id="h0pz3S6Tvx0"):
    """Displays a YouTube video within Jupyter notebooks.

    Args:
        id (str, optional): Unique ID of the video. Defaults to 'h0pz3S6Tvx0'.

    """
    from IPython.display import YouTubeVideo, display

    if "/" in id:
        id = id.split("/")[-1]

    try:
        out = widgets.Output(layout={"width": "815px"})
        # layout={'border': '1px solid black', 'width': '815px'})
        out.outputs = ()
        display(out)
        with out:
            display(YouTubeVideo(id, width=800, height=450))
    except Exception as e:
        print(e)


def create_colorbar(
    width=150,
    height=30,
    palette=["blue", "green", "red"],
    add_ticks=True,
    add_labels=True,
    labels=None,
    vertical=False,
    out_file=None,
    font_type="arial.ttf",
    font_size=12,
    font_color="black",
    add_outline=True,
    outline_color="black",
):
    """Creates a colorbar based on the provided palette.

    Args:
        width (int, optional): Width of the colorbar in pixels. Defaults to 150.
        height (int, optional): Height of the colorbar in pixels. Defaults to 30.
        palette (list, optional): Palette for the colorbar. Each color can be provided as a string (e.g., 'red'), a hex string (e.g., '#ff0000'), or an RGB tuple (255, 0, 255). Defaults to ['blue', 'green', 'red'].
        add_ticks (bool, optional): Whether to add tick markers to the colorbar. Defaults to True.
        add_labels (bool, optional): Whether to add labels to the colorbar. Defaults to True.
        labels (list, optional): A list of labels to add to the colorbar. Defaults to None.
        vertical (bool, optional): Whether to rotate the colorbar vertically. Defaults to False.
        out_file (str, optional): File path to the output colorbar in png format. Defaults to None.
        font_type (str, optional): Font type to use for labels. Defaults to 'arial.ttf'.
        font_size (int, optional): Font size to use for labels. Defaults to 12.
        font_color (str, optional): Font color to use for labels. Defaults to 'black'.
        add_outline (bool, optional): Whether to add an outline to the colorbar. Defaults to True.
        outline_color (str, optional): Color for the outline of the colorbar. Defaults to 'black'.

    Returns:
        str: File path of the output colorbar in png format.

    """
    import decimal

    # import io
    import pkg_resources
    from colour import Color
    from PIL import Image, ImageDraw, ImageFont

    warnings.simplefilter("ignore")
    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))

    if out_file is None:
        filename = "colorbar_" + random_string() + ".png"
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        out_file = os.path.join(out_dir, filename)
    elif not out_file.endswith(".png"):
        print("The output file must end with .png")
        return
    else:
        out_file = os.path.abspath(out_file)

    if not os.path.exists(os.path.dirname(out_file)):
        os.makedirs(os.path.dirname(out_file))

    im = Image.new("RGBA", (width, height))
    ld = im.load()

    def float_range(start, stop, step):
        while start < stop:
            yield float(start)
            start += decimal.Decimal(step)

    n_colors = len(palette)
    decimal_places = 2
    rgb_colors = [Color(check_color(c)).rgb for c in palette]
    keys = [
        round(c, decimal_places)
        for c in list(float_range(0, 1.0001, 1.0 / (n_colors - 1)))
    ]

    heatmap = []
    for index, item in enumerate(keys):
        pair = [item, rgb_colors[index]]
        heatmap.append(pair)

    def gaussian(x, a, b, c, d=0):
        return a * math.exp(-((x - b) ** 2) / (2 * c**2)) + d

    def pixel(x, width=100, map=[], spread=1):
        width = float(width)
        r = sum(
            [
                gaussian(x, p[1][0], p[0] * width, width / (spread * len(map)))
                for p in map
            ]
        )
        g = sum(
            [
                gaussian(x, p[1][1], p[0] * width, width / (spread * len(map)))
                for p in map
            ]
        )
        b = sum(
            [
                gaussian(x, p[1][2], p[0] * width, width / (spread * len(map)))
                for p in map
            ]
        )
        return min(1.0, r), min(1.0, g), min(1.0, b)

    for x in range(im.size[0]):
        r, g, b = pixel(x, width=width, map=heatmap)
        r, g, b = [int(256 * v) for v in (r, g, b)]
        for y in range(im.size[1]):
            ld[x, y] = r, g, b

    if add_outline:
        draw = ImageDraw.Draw(im)
        draw.rectangle(
            [(0, 0), (width - 1, height - 1)], outline=check_color(outline_color)
        )
        del draw

    if add_ticks:
        tick_length = height * 0.1
        x = [key * width for key in keys]
        y_top = height - tick_length
        y_bottom = height
        draw = ImageDraw.Draw(im)
        for i in x:
            shape = [(i, y_top), (i, y_bottom)]
            draw.line(shape, fill="black", width=0)
        del draw

    if vertical:
        im = im.transpose(Image.ROTATE_90)

    width, height = im.size

    if labels is None:
        labels = [str(c) for c in keys]
    elif len(labels) == 2:
        try:
            lowerbound = float(labels[0])
            upperbound = float(labels[1])
            step = (upperbound - lowerbound) / (len(palette) - 1)
            labels = [str(lowerbound + c * step) for c in range(0, len(palette))]
        except Exception as e:
            print(e)
            print("The labels are invalid.")
            return
    elif len(labels) == len(palette):
        labels = [str(c) for c in labels]
    else:
        print("The labels must have the same length as the palette.")
        return

    if add_labels:
        default_font = os.path.join(pkg_dir, "data/fonts/arial.ttf")
        if font_type == "arial.ttf":
            font = ImageFont.truetype(default_font, font_size)
        else:
            try:
                font_list = system_fonts(show_full_path=True)
                font_names = [os.path.basename(f) for f in font_list]
                if (font_type in font_list) or (font_type in font_names):
                    font = ImageFont.truetype(font_type, font_size)
                else:
                    print(
                        "The specified font type could not be found on your system. Using the default font instead."
                    )
                    font = ImageFont.truetype(default_font, font_size)
            except Exception as e:
                print(e)
                font = ImageFont.truetype(default_font, font_size)

        font_color = check_color(font_color)

        draw = ImageDraw.Draw(im)
        w, h = draw.textsize(labels[0], font=font)

        for label in labels:
            w_tmp, h_tmp = draw.textsize(label, font)
            if w_tmp > w:
                w = w_tmp
            if h_tmp > h:
                h = h_tmp

        W, H = width + w * 2, height + h * 2
        background = Image.new("RGBA", (W, H))
        draw = ImageDraw.Draw(background)

        if vertical:
            xy = (0, h)
        else:
            xy = (w, 0)
        background.paste(im, xy, im)

        for index, label in enumerate(labels):
            w_tmp, h_tmp = draw.textsize(label, font)

            if vertical:
                spacing = 5
                x = width + spacing
                y = int(height + h - keys[index] * height - h_tmp / 2 - 1)
                draw.text((x, y), label, font=font, fill=font_color)

            else:
                x = int(keys[index] * width + w - w_tmp / 2)
                spacing = int(h * 0.05)
                y = height + spacing
                draw.text((x, y), label, font=font, fill=font_color)

        im = background.copy()

    im.save(out_file)
    return out_file


def save_colorbar(
    out_fig=None,
    width=4.0,
    height=0.3,
    vmin=0,
    vmax=1.0,
    palette=None,
    vis_params=None,
    cmap="gray",
    discrete=False,
    label=None,
    label_size=10,
    label_weight="normal",
    tick_size=8,
    bg_color="white",
    orientation="horizontal",
    dpi="figure",
    transparent=False,
    show_colorbar=True,
    **kwargs,
):
    """Create a standalone colorbar and save it as an image.

    Args:
        out_fig (str): Path to the output image.
        width (float): Width of the colorbar in inches. Default is 4.0.
        height (float): Height of the colorbar in inches. Default is 0.3.
        vmin (float): Minimum value of the colorbar. Default is 0.
        vmax (float): Maximum value of the colorbar. Default is 1.0.
        palette (list): List of colors to use for the colorbar. It can also be a cmap name, such as ndvi, ndwi, dem, coolwarm. Default is None.
        vis_params (dict): Visualization parameters as a dictionary. See https://developers.google.com/earth-engine/guides/image_visualization for options.
        cmap (str, optional): Matplotlib colormap. Defaults to "gray". See https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py for options.
        discrete (bool, optional): Whether to create a discrete colorbar. Defaults to False.
        label (str, optional): Label for the colorbar. Defaults to None.
        label_size (int, optional): Font size for the colorbar label. Defaults to 12.
        label_weight (str, optional): Font weight for the colorbar label, can be "normal", "bold", etc. Defaults to "normal".
        tick_size (int, optional): Font size for the colorbar tick labels. Defaults to 10.
        bg_color (str, optional): Background color for the colorbar. Defaults to "white".
        orientation (str, optional): Orientation of the colorbar, such as "vertical" and "horizontal". Defaults to "horizontal".
        dpi (float | str, optional): The resolution in dots per inch.  If 'figure', use the figure's dpi value. Defaults to "figure".
        transparent (bool, optional): Whether to make the background transparent. Defaults to False.
        show_colorbar (bool, optional): Whether to show the colorbar. Defaults to True.
        **kwargs: Other keyword arguments to pass to matplotlib.pyplot.savefig().

    Returns:
        str: Path to the output image.
    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import numpy as np
    from .colormaps import palettes, get_palette

    if out_fig is None:
        out_fig = temp_file_path("png")
    else:
        out_fig = check_file_path(out_fig)

    if vis_params is None:
        vis_params = {}
    elif not isinstance(vis_params, dict):
        raise TypeError("The vis_params must be a dictionary.")

    if palette is not None:
        if palette in ["ndvi", "ndwi", "dem"]:
            palette = palettes[palette]
        elif palette in list(palettes.keys()):
            palette = get_palette(palette)
        vis_params["palette"] = palette

    orientation = orientation.lower()
    if orientation not in ["horizontal", "vertical"]:
        raise ValueError("The orientation must be either horizontal or vertical.")

    if "opacity" in vis_params:
        alpha = vis_params["opacity"]
        if type(alpha) not in (int, float):
            raise ValueError("The provided opacity value must be type scalar.")
    else:
        alpha = 1

    if cmap is not None:
        cmap = mpl.pyplot.get_cmap(cmap)
        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    if "palette" in vis_params:
        hexcodes = to_hex_colors(vis_params["palette"])
        if discrete:
            cmap = mpl.colors.ListedColormap(hexcodes)
            vals = np.linspace(vmin, vmax, cmap.N + 1)
            norm = mpl.colors.BoundaryNorm(vals, cmap.N)

        else:
            cmap = mpl.colors.LinearSegmentedColormap.from_list(
                "custom", hexcodes, N=256
            )
            norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    elif cmap is not None:
        cmap = mpl.pyplot.get_cmap(cmap)
        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    else:
        raise ValueError(
            'cmap keyword or "palette" key in vis_params must be provided.'
        )

    fig, ax = plt.subplots(figsize=(width, height))
    cb = mpl.colorbar.ColorbarBase(
        ax, norm=norm, alpha=alpha, cmap=cmap, orientation=orientation, **kwargs
    )
    if label is not None:
        cb.set_label(label=label, size=label_size, weight=label_weight)
    cb.ax.tick_params(labelsize=tick_size)

    if transparent:
        bg_color = None

    if bg_color is not None:
        kwargs["facecolor"] = bg_color
    if "bbox_inches" not in kwargs:
        kwargs["bbox_inches"] = "tight"

    fig.savefig(out_fig, dpi=dpi, transparent=transparent, **kwargs)
    if not show_colorbar:
        plt.close(fig)
    return out_fig


def minimum_bounding_box(geojson):
    """Gets the minimum bounding box for a geojson polygon.

    Args:
        geojson (dict): A geojson dictionary.

    Returns:
        tuple: Returns a tuple containing the minimum bounding box in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -120)).
    """
    coordinates = []
    try:
        if "geometry" in geojson.keys():
            coordinates = geojson["geometry"]["coordinates"][0]
        else:
            coordinates = geojson["coordinates"][0]
        lower_left = min([x[1] for x in coordinates]), min(
            [x[0] for x in coordinates]
        )  # (lat, lon)
        upper_right = max([x[1] for x in coordinates]), max(
            [x[0] for x in coordinates]
        )  # (lat, lon)
        bounds = (lower_left, upper_right)
        return bounds
    except Exception as e:
        raise Exception(e)


def geocode(location, max_rows=10, reverse=False):
    """Search location by address and lat/lon coordinates.

    Args:
        location (str): Place name or address
        max_rows (int, optional): Maximum number of records to return. Defaults to 10.
        reverse (bool, optional): Search place based on coordinates. Defaults to False.

    Returns:
        list: Returns a list of locations.
    """
    import geocoder

    if not isinstance(location, str):
        print("The location must be a string.")
        return None

    if not reverse:
        locations = []
        addresses = set()
        g = geocoder.arcgis(location, maxRows=max_rows)

        for result in g:
            address = result.address
            if address not in addresses:
                addresses.add(address)
                locations.append(result)

        if len(locations) > 0:
            return locations
        else:
            return None

    else:
        try:
            if "," in location:
                latlon = [float(x) for x in location.split(",")]
            elif " " in location:
                latlon = [float(x) for x in location.split(" ")]
            else:
                print(
                    "The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3"
                )
                return
            g = geocoder.arcgis(latlon, method="reverse")
            locations = []
            addresses = set()

            for result in g:
                address = result.address
                if address not in addresses:
                    addresses.add(address)
                    locations.append(result)

            if len(locations) > 0:
                return locations
            else:
                return None

        except Exception as e:
            print(e)
            return None


def is_latlon_valid(location):
    """Checks whether a pair of coordinates is valid.

    Args:
        location (str): A pair of latlon coordinates separated by comma or space.

    Returns:
        bool: Returns True if valid.
    """
    latlon = []
    if "," in location:
        latlon = [float(x) for x in location.split(",")]
    elif " " in location:
        latlon = [float(x) for x in location.split(" ")]
    else:
        print(
            "The coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3"
        )
        return False

    try:
        lat, lon = float(latlon[0]), float(latlon[1])
        if lat >= -90 and lat <= 90 and lon >= -180 and lon <= 180:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def latlon_from_text(location):
    """Extracts latlon from text.

    Args:
        location (str): A pair of latlon coordinates separated by comma or space.

    Returns:
        bool: Returns (lat, lon) if valid.
    """
    latlon = []
    try:
        if "," in location:
            latlon = [float(x) for x in location.split(",")]
        elif " " in location:
            latlon = [float(x) for x in location.split(" ")]
        else:
            print(
                "The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3"
            )
            return None

        lat, lon = latlon[0], latlon[1]
        if lat >= -90 and lat <= 90 and lon >= -180 and lon <= 180:
            return lat, lon
        else:
            return None

    except Exception as e:
        print(e)
        print(
            "The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3"
        )
        return None


def search_ee_data(
    keywords,
    regex=False,
    source="ee",
    types=None,
    keys=["id", "provider", "tags", "title"],
):
    """Searches Earth Engine data catalog.

    Args:
        keywords (str | list): Keywords to search for can be id, provider, tag and so on. Split by space if string, e.g. "1 2" becomes ['1','2'].
        regex (bool, optional): Allow searching for regular expressions. Defaults to false.
        source (str, optional): Can be 'ee', 'community' or 'all'. Defaults to 'ee'. For more details, see https://github.com/samapriya/awesome-gee-community-datasets/blob/master/community_datasets.json
        types (list, optional): List of valid collection types. Defaults to None so no filter is applied. A possible filter ['image_collection']
        keys (list, optional): List of metadata fields to search from.  Defaults to ['id','provider','tags','title']

    Returns:
        list: Returns a list of assets.
    """
    if isinstance(keywords, str):
        keywords = keywords.split(" ")

    import re
    from functools import reduce

    def search_collection(pattern, dict_):
        if regex:
            if any(re.match(pattern, dict_[key]) for key in keys):
                return dict_
        elif any(pattern in dict_[key] for key in keys):
            return dict_
        return {}

    def search_all(pattern):
        # updated daily
        a = "https://raw.githubusercontent.com/samapriya/Earth-Engine-Datasets-List/master/gee_catalog.json"
        b = "https://raw.githubusercontent.com/samapriya/awesome-gee-community-datasets/master/community_datasets.json"
        sources = {"ee": [a], "community": [b], "all": [a, b]}
        matches = []
        for link in sources[source]:
            r = requests.get(link)
            catalog_list = r.json()
            matches += [search_collection(pattern, x) for x in catalog_list]
        matches = [x for x in matches if x]
        if types:
            return [x for x in matches if x["type"] in types]
        return matches

    try:
        assets = list(
            {json.dumps(match) for match in search_all(pattern=k)} for k in keywords
        )
        assets = sorted(list(reduce(set.intersection, assets)))
        assets = [json.loads(x) for x in assets]

        results = []
        for asset in assets:
            asset_dates = (
                asset.get("start_date", "Unknown")
                + " - "
                + asset.get("end_date", "Unknown")
            )
            asset_snippet = asset["id"]
            if "ee." in asset_snippet:
                start_index = asset_snippet.index("'") + 1
                end_index = asset_snippet.index("'", start_index)
                asset_id = asset_snippet[start_index:end_index]
            else:
                asset_id = asset_snippet

            asset["dates"] = asset_dates
            asset["id"] = asset_id
            asset["uid"] = asset_id.replace("/", "_")

            results.append(asset)

        return results

    except Exception as e:
        print(e)


def ee_data_thumbnail(asset_id, timeout=300, proxies=None):
    """Retrieves the thumbnail URL of an Earth Engine asset.

    Args:
        asset_id (str): An Earth Engine asset id.
        timeout (int, optional): Timeout in seconds. Defaults to 300.
        proxies (dict, optional): Proxy settings. Defaults to None.

    Returns:
        str: An http url of the thumbnail.
    """
    import urllib

    from bs4 import BeautifulSoup

    asset_uid = asset_id.replace("/", "_")
    asset_url = "https://developers.google.com/earth-engine/datasets/catalog/{}".format(
        asset_uid
    )
    thumbnail_url = "https://mw1.google.com/ges/dd/images/{}_sample.png".format(
        asset_uid
    )

    r = requests.get(thumbnail_url, timeout=timeout, proxies=proxies)

    try:
        if r.status_code != 200:
            html_page = urllib.request.urlopen(asset_url)
            soup = BeautifulSoup(html_page, features="html.parser")

            for img in soup.findAll("img"):
                if "sample.png" in img.get("src"):
                    thumbnail_url = img.get("src")
                    return thumbnail_url

        return thumbnail_url
    except Exception as e:
        print(e)


def ee_data_html(asset):
    """Generates HTML from an asset to be used in the HTML widget.

    Args:
        asset (dict): A dictionary containing an Earth Engine asset.

    Returns:
        str: A string containing HTML.
    """
    try:
        asset_title = asset.get("title", "Unknown")
        asset_dates = asset.get("dates", "Unknown")
        ee_id_snippet = asset.get("id", "Unknown")
        asset_uid = asset.get("uid", None)
        asset_url = asset.get("asset_url", "")
        code_url = asset.get("sample_code", None)
        thumbnail_url = asset.get("thumbnail_url", None)
        asset_type = asset.get("type", "Unknown")

        if asset_type == "image":
            ee_id_snippet = "ee.Image('{}')".format(ee_id_snippet)
        elif asset_type == "image_collection":
            ee_id_snippet = "ee.ImageCollection('{}')".format(ee_id_snippet)
        elif asset_type == "table":
            ee_id_snippet = "ee.FeatureCollection('{}')".format(ee_id_snippet)

        if not code_url and asset_uid:
            coder_url = f"""https://code.earthengine.google.com/?scriptPath=Examples%3ADatasets%2F{asset_uid}"""
        else:
            coder_url = code_url

        ## ee datasets always have a asset_url, and should have a thumbnail
        catalog = (
            bool(asset_url)
            * f"""
                    <h4>Data Catalog</h4>
                        <p style="margin-left: 40px"><a href="{asset_url.replace('terms-of-use','description')}" target="_blank">Description</a></p>
                        <p style="margin-left: 40px"><a href="{asset_url.replace('terms-of-use','bands')}" target="_blank">Bands</a></p>
                        <p style="margin-left: 40px"><a href="{asset_url.replace('terms-of-use','image-properties')}" target="_blank">Properties</a></p>
                        <p style="margin-left: 40px"><a href="{coder_url}" target="_blank">Example</a></p>
                    """
        )
        thumbnail = (
            bool(thumbnail_url)
            * f"""
                    <h4>Dataset Thumbnail</h4>
                    <img src="{thumbnail_url}">
                    """
        )
        ## only community datasets have a code_url
        alternative = (
            bool(code_url)
            * f"""
                    <h4>Community Catalog</h4>
                        <p style="margin-left: 40px">{asset.get('provider','Provider unknown')}</p>
                        <p style="margin-left: 40px">{asset.get('tags','Tags unknown')}</p>
                        <p style="margin-left: 40px"><a href="{coder_url}" target="_blank">Example</a></p>
                    """
        )

        template = f"""
            <html>
            <body>
                <h3>{asset_title}</h3>
                <h4>Dataset Availability</h4>
                    <p style="margin-left: 40px">{asset_dates}</p>
                <h4>Earth Engine Snippet</h4>
                    <p style="margin-left: 40px">{ee_id_snippet}</p>
                {catalog}
                {alternative}
                {thumbnail}
            </body>
            </html>
        """
        return template

    except Exception as e:
        print(e)


def ee_api_to_csv(outfile=None, timeout=300, proxies=None):
    """Extracts Earth Engine API documentation from https://developers.google.com/earth-engine/api_docs as a csv file.

    Args:
        outfile (str, optional): The output file path to a csv file. Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 300.
        proxies (dict, optional): Proxy settings. Defaults to None.
    """
    import pkg_resources

    from bs4 import BeautifulSoup

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    data_dir = os.path.join(pkg_dir, "data")
    template_dir = os.path.join(data_dir, "template")
    csv_file = os.path.join(template_dir, "ee_api_docs.csv")

    if outfile is None:
        outfile = csv_file
    else:
        if not outfile.endswith(".csv"):
            print("The output file must end with .csv")
            return
        else:
            out_dir = os.path.dirname(outfile)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

    url = "https://developers.google.com/earth-engine/api_docs"

    try:
        r = requests.get(url, timeout=timeout, proxies=proxies)
        soup = BeautifulSoup(r.content, "html.parser")

        names = []
        descriptions = []
        functions = []
        returns = []
        arguments = []
        types = []
        details = []

        names = [h2.text for h2 in soup.find_all("h2")]
        descriptions = [h2.next_sibling.next_sibling.text for h2 in soup.find_all("h2")]
        func_tables = soup.find_all("table", class_="blue")
        functions = [func_table.find("code").text for func_table in func_tables]
        returns = [func_table.find_all("td")[1].text for func_table in func_tables]

        detail_tables = []
        tables = soup.find_all("table", class_="blue")

        for table in tables:
            item = table.next_sibling
            if item.attrs == {"class": ["details"]}:
                detail_tables.append(item)
            else:
                detail_tables.append("")

        for detail_table in detail_tables:
            if detail_table != "":
                items = [item.text for item in detail_table.find_all("code")]
            else:
                items = ""
            arguments.append(items)

        for detail_table in detail_tables:
            if detail_table != "":
                items = [item.text for item in detail_table.find_all("td")]
                items = items[1::3]
            else:
                items = ""
            types.append(items)

        for detail_table in detail_tables:
            if detail_table != "":
                items = [item.text for item in detail_table.find_all("p")]
            else:
                items = ""
            details.append(items)

        with open(outfile, "w", encoding="utf-8") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter="\t")

            csv_writer.writerow(
                [
                    "name",
                    "description",
                    "function",
                    "returns",
                    "argument",
                    "type",
                    "details",
                ]
            )

            for i in range(len(names)):
                name = names[i]
                description = descriptions[i]
                function = functions[i]
                return_type = returns[i]
                argument = "|".join(arguments[i])
                argu_type = "|".join(types[i])
                detail = "|".join(details[i])

                csv_writer.writerow(
                    [
                        name,
                        description,
                        function,
                        return_type,
                        argument,
                        argu_type,
                        detail,
                    ]
                )

    except Exception as e:
        print(e)


def read_api_csv():
    """Extracts Earth Engine API from a csv file and returns a dictionary containing information about each function.

    Returns:
        dict: The dictionary containing information about each function, including name, description, function form, return type, arguments, html.
    """
    import copy

    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    data_dir = os.path.join(pkg_dir, "data")
    template_dir = os.path.join(data_dir, "template")
    csv_file = os.path.join(template_dir, "ee_api_docs.csv")
    html_file = os.path.join(template_dir, "ee_api_docs.html")

    with open(html_file) as f:
        in_html_lines = f.readlines()

    api_dict = {}

    with open(csv_file, "r", encoding="utf-8") as f:
        csv_reader = csv.DictReader(f, delimiter="\t")

        for line in csv_reader:
            out_html_lines = copy.copy(in_html_lines)
            out_html_lines[65] = in_html_lines[65].replace(
                "function_name", line["name"]
            )
            out_html_lines[66] = in_html_lines[66].replace(
                "function_description", line.get("description")
            )
            out_html_lines[74] = in_html_lines[74].replace(
                "function_usage", line.get("function")
            )
            out_html_lines[75] = in_html_lines[75].replace(
                "function_returns", line.get("returns")
            )

            arguments = line.get("argument")
            types = line.get("type")
            details = line.get("details")

            if "|" in arguments:
                argument_items = arguments.split("|")
            else:
                argument_items = [arguments]

            if "|" in types:
                types_items = types.split("|")
            else:
                types_items = [types]

            if "|" in details:
                details_items = details.split("|")
            else:
                details_items = [details]

            out_argument_lines = []

            for index in range(len(argument_items)):
                in_argument_lines = in_html_lines[87:92]
                in_argument_lines[1] = in_argument_lines[1].replace(
                    "function_argument", argument_items[index]
                )
                in_argument_lines[2] = in_argument_lines[2].replace(
                    "function_type", types_items[index]
                )
                in_argument_lines[3] = in_argument_lines[3].replace(
                    "function_details", details_items[index]
                )
                out_argument_lines.append("".join(in_argument_lines))

            out_html_lines = (
                out_html_lines[:87] + out_argument_lines + out_html_lines[92:]
            )

            contents = "".join(out_html_lines)

            api_dict[line["name"]] = {
                "description": line.get("description"),
                "function": line.get("function"),
                "returns": line.get("returns"),
                "argument": line.get("argument"),
                "type": line.get("type"),
                "details": line.get("details"),
                "html": contents,
            }

    return api_dict


def ee_function_tree(name):
    """Construct the tree structure based on an Earth Engine function. For example, the function "ee.Algorithms.FMask.matchClouds" will return a list ["ee.Algorithms", "ee.Algorithms.FMask", "ee.Algorithms.FMask.matchClouds"]

    Args:
        name (str): The name of the Earth Engine function

    Returns:
        list: The list for parent functions.
    """
    func_list = []
    try:
        items = name.split(".")
        if items[0] == "ee":
            for i in range(2, len(items) + 1):
                func_list.append(".".join(items[0:i]))
        else:
            for i in range(1, len(items) + 1):
                func_list.append(".".join(items[0:i]))

        return func_list
    except Exception as e:
        print(e)
        print("The provided function name is invalid.")


def build_api_tree(api_dict, output_widget, layout_width="100%"):
    """Builds an Earth Engine API tree view.

    Args:
        api_dict (dict): The dictionary containing information about each Earth Engine API function.
        output_widget (object): An Output widget.
        layout_width (str, optional): The percentage width of the widget. Defaults to '100%'.

    Returns:
        tuple: Returns a tuple containing two items: a tree Output widget and a tree dictionary.
    """

    warnings.filterwarnings("ignore")

    tree = Tree()
    tree_dict = {}

    names = api_dict.keys()

    def handle_click(event):
        if event["new"]:
            name = event["owner"].name
            values = api_dict[name]

            with output_widget:
                output_widget.outputs = ()
                html_widget = widgets.HTML(value=values["html"])
                display(html_widget)

    for name in names:
        func_list = ee_function_tree(name)
        first = func_list[0]

        if first not in tree_dict.keys():
            tree_dict[first] = Node(first)
            tree_dict[first].opened = False
            tree.add_node(tree_dict[first])

        for index, func in enumerate(func_list):
            if index > 0:
                if func not in tree_dict.keys():
                    node = tree_dict[func_list[index - 1]]
                    node.opened = False
                    tree_dict[func] = Node(func)
                    node.add_node(tree_dict[func])

                    if index == len(func_list) - 1:
                        node = tree_dict[func_list[index]]
                        node.icon = "file"
                        node.observe(handle_click, "selected")

    return tree, tree_dict


def search_api_tree(keywords, api_tree):
    """Search Earth Engine API and return functions containing the specified keywords

    Args:
        keywords (str): The keywords to search for.
        api_tree (dict): The dictionary containing the Earth Engine API tree.

    Returns:
        object: An ipytree object/widget.
    """

    warnings.filterwarnings("ignore")

    sub_tree = Tree()

    for key in api_tree.keys():
        if keywords.lower() in key.lower():
            sub_tree.add_node(api_tree[key])

    return sub_tree


def ee_search(asset_limit=100):
    """Search Earth Engine API and user assets. If you received a warning (IOPub message rate exceeded) in Jupyter notebook, you can relaunch Jupyter notebook using the following command:
        jupyter notebook --NotebookApp.iopub_msg_rate_limit=10000

    Args:
        asset_limit (int, optional): The number of assets to display for each asset type, i.e., Image, ImageCollection, and FeatureCollection. Defaults to 100.
    """

    warnings.filterwarnings("ignore")

    class Flags:
        def __init__(
            self,
            repos=None,
            docs=None,
            assets=None,
            docs_dict=None,
            asset_dict=None,
            asset_import=None,
        ):
            self.repos = repos
            self.docs = docs
            self.assets = assets
            self.docs_dict = docs_dict
            self.asset_dict = asset_dict
            self.asset_import = asset_import

    flags = Flags()

    search_type = widgets.ToggleButtons(
        options=["Scripts", "Docs", "Assets"],
        tooltips=[
            "Search Earth Engine Scripts",
            "Search Earth Engine API",
            "Search Earth Engine Assets",
        ],
        button_style="primary",
    )
    search_type.style.button_width = "100px"

    search_box = widgets.Text(placeholder="Filter scripts...", value="Loading...")
    search_box.layout.width = "310px"

    tree_widget = widgets.Output()

    left_widget = widgets.VBox()
    right_widget = widgets.VBox()
    output_widget = widgets.Output()
    output_widget.layout.max_width = "650px"

    search_widget = widgets.HBox()
    search_widget.children = [left_widget, right_widget]
    display(search_widget)

    repo_tree, repo_output, _ = build_repo_tree()
    left_widget.children = [search_type, repo_tree]
    right_widget.children = [repo_output]

    flags.repos = repo_tree
    search_box.value = ""

    def search_type_changed(change):
        search_box.value = ""

        output_widget.outputs = ()
        tree_widget.outputs = ()
        if change["new"] == "Scripts":
            search_box.placeholder = "Filter scripts..."
            left_widget.children = [search_type, repo_tree]
            right_widget.children = [repo_output]
        elif change["new"] == "Docs":
            search_box.placeholder = "Filter methods..."
            search_box.value = "Loading..."
            left_widget.children = [search_type, search_box, tree_widget]
            right_widget.children = [output_widget]
            if flags.docs is None:
                api_dict = read_api_csv()
                ee_api_tree, tree_dict = build_api_tree(api_dict, output_widget)
                flags.docs = ee_api_tree
                flags.docs_dict = tree_dict
            else:
                ee_api_tree = flags.docs
            with tree_widget:
                tree_widget.outputs = ()
                display(ee_api_tree)
                right_widget.children = [output_widget]
            search_box.value = ""
        elif change["new"] == "Assets":
            search_box.placeholder = "Filter assets..."
            left_widget.children = [search_type, search_box, tree_widget]
            right_widget.children = [output_widget]
            search_box.value = "Loading..."
            if flags.assets is None:
                asset_tree, asset_widget, asset_dict = build_asset_tree(
                    limit=asset_limit
                )
                flags.assets = asset_tree
                flags.asset_dict = asset_dict
                flags.asset_import = asset_widget

            with tree_widget:
                tree_widget.outputs = ()
                display(flags.assets)
            right_widget.children = [flags.asset_import]
            search_box.value = ""

    search_type.observe(search_type_changed, names="value")

    def search_box_callback(text):
        if search_type.value == "Docs":
            with tree_widget:
                if text.value == "":
                    print("Loading...")
                    tree_widget.outputs = ()
                    display(flags.docs)
                else:
                    tree_widget.outputs = ()
                    print("Searching...")
                    tree_widget.outputs = ()
                    sub_tree = search_api_tree(text.value, flags.docs_dict)
                    display(sub_tree)
        elif search_type.value == "Assets":
            with tree_widget:
                if text.value == "":
                    print("Loading...")
                    tree_widget.outputs = ()
                    display(flags.assets)
                else:
                    tree_widget.outputs = ()
                    print("Searching...")
                    tree_widget.outputs = ()
                    sub_tree = search_api_tree(text.value, flags.asset_dict)
                    display(sub_tree)

    search_box.on_submit(search_box_callback)


def ee_user_id():
    """Gets Earth Engine account user id.

    Returns:
        str: A string containing the user id.
    """
    # ee_initialize()
    roots = ee.data.getAssetRoots()
    if len(roots) == 0:
        return None
    else:
        root = ee.data.getAssetRoots()[0]
        user_id = root["id"].replace("projects/earthengine-legacy/assets/", "")
        return user_id


def build_asset_tree(limit=100):
    import geeadd.ee_report as geeadd

    warnings.filterwarnings("ignore")

    # ee_initialize()

    tree = Tree(multiple_selection=False)
    tree_dict = {}
    asset_types = {}

    asset_icons = {
        "FOLDER": "folder",
        "TABLE": "table",
        "IMAGE": "image",
        "IMAGE_COLLECTION": "file",
    }

    info_widget = widgets.HBox()

    import_btn = widgets.Button(
        description="import",
        button_style="primary",
        tooltip="Click to import the selected asset",
        disabled=True,
    )
    import_btn.layout.min_width = "57px"
    import_btn.layout.max_width = "57px"

    path_widget = widgets.Text()
    path_widget.layout.min_width = "500px"
    # path_widget.disabled = True

    info_widget.children = [import_btn, path_widget]

    user_id = ee_user_id()
    if user_id is None:
        print(
            "Your GEE account does not have any assets. Please create a repository at https://code.earthengine.google.com"
        )
        return

    user_path = "projects/earthengine-legacy/assets/" + user_id
    root_node = Node(user_id)
    root_node.opened = True
    tree_dict[user_id] = root_node
    tree.add_node(root_node)

    collection_list, table_list, image_list, folder_paths = geeadd.fparse(user_path)
    collection_list = collection_list[:limit]
    table_list = table_list[:limit]
    image_list = image_list[:limit]
    folder_paths = folder_paths[:limit]
    folders = [p[35:] for p in folder_paths[1:]]

    asset_type = "FOLDER"
    for folder in folders:
        bare_folder = folder.replace(user_id + "/", "")
        if folder not in tree_dict.keys():
            node = Node(bare_folder)
            node.opened = False
            node.icon = asset_icons[asset_type]
            root_node.add_node(node)
            tree_dict[folder] = node
            asset_types[folder] = asset_type

    def import_btn_clicked(b):
        if path_widget.value != "":
            dataset_uid = "dataset_" + random_string(string_length=3)
            layer_name = path_widget.value.split("/")[-1][:-2:]
            line1 = "{} = {}\n".format(dataset_uid, path_widget.value)
            line2 = "Map.addLayer(" + dataset_uid + ', {}, "' + layer_name + '")'
            contents = "".join([line1, line2])
            create_code_cell(contents)

    import_btn.on_click(import_btn_clicked)

    def handle_click(event):
        if event["new"]:
            cur_node = event["owner"]
            for key in tree_dict.keys():
                if cur_node is tree_dict[key]:
                    if asset_types[key] == "IMAGE":
                        path_widget.value = "ee.Image('{}')".format(key)
                    elif asset_types[key] == "IMAGE_COLLECTION":
                        path_widget.value = "ee.ImageCollection('{}')".format(key)
                    elif asset_types[key] == "TABLE":
                        path_widget.value = "ee.FeatureCollection('{}')".format(key)
                    if import_btn.disabled:
                        import_btn.disabled = False
                    break

    assets = [collection_list, image_list, table_list]
    for index, asset_list in enumerate(assets):
        if index == 0:
            asset_type = "IMAGE_COLLECTION"
        elif index == 1:
            asset_type = "IMAGE"
        else:
            asset_type = "TABLE"

        for asset in asset_list:
            items = asset.split("/")
            parent = "/".join(items[:-1])
            child = items[-1]
            parent_node = tree_dict[parent]
            child_node = Node(child)
            child_node.icon = asset_icons[asset_type]
            parent_node.add_node(child_node)
            tree_dict[asset] = child_node
            asset_types[asset] = asset_type
            child_node.observe(handle_click, "selected")

    return tree, info_widget, tree_dict


def build_repo_tree(out_dir=None, name="gee_repos"):
    """Builds a repo tree for GEE account.

    Args:
        out_dir (str): The output directory for the repos. Defaults to None.
        name (str, optional): The output name for the repo directory. Defaults to 'gee_repos'.

    Returns:
        tuple: Returns a tuple containing a tree widget, an output widget, and a tree dictionary containing nodes.
    """

    warnings.filterwarnings("ignore")

    if out_dir is None:
        out_dir = os.path.join(os.path.expanduser("~"))

    repo_dir = os.path.join(out_dir, name)
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)

    URLs = {
        # 'Owner': 'https://earthengine.googlesource.com/{ee_user_id()}/default',
        "Writer": "",
        "Reader": "https://github.com/gee-community/geemap",
        "Examples": "https://github.com/giswqs/earthengine-py-examples",
        "Archive": "https://earthengine.googlesource.com/EGU2017-EE101",
    }

    user_id = ee_user_id()
    if user_id is not None:
        URLs["Owner"] = f"https://earthengine.googlesource.com/{ee_user_id()}/default"

    path_widget = widgets.Text(placeholder="Enter the link to a Git repository here...")
    path_widget.layout.width = "475px"
    clone_widget = widgets.Button(
        description="Clone",
        button_style="primary",
        tooltip="Clone the repository to folder.",
    )
    info_widget = widgets.HBox()

    groups = ["Owner", "Writer", "Reader", "Examples", "Archive"]
    for group in groups:
        group_dir = os.path.join(repo_dir, group)
        if not os.path.exists(group_dir):
            os.makedirs(group_dir)

    example_dir = os.path.join(repo_dir, "Examples/earthengine-py-examples")
    if not os.path.exists(example_dir):
        clone_github_repo(URLs["Examples"], out_dir=example_dir)

    left_widget, right_widget, tree_dict = file_browser(
        in_dir=repo_dir,
        add_root_node=False,
        search_description="Filter scripts...",
        use_import=True,
        return_sep_widgets=True,
    )
    info_widget.children = [right_widget]

    def handle_folder_click(event):
        if event["new"]:
            url = ""
            selected = event["owner"]
            if selected.name in URLs.keys():
                url = URLs[selected.name]

            path_widget.value = url
            clone_widget.disabled = False
            info_widget.children = [path_widget, clone_widget]
        else:
            info_widget.children = [right_widget]

    for group in groups:
        dirname = os.path.join(repo_dir, group)
        node = tree_dict[dirname]
        node.observe(handle_folder_click, "selected")

    def handle_clone_click(b):
        url = path_widget.value
        default_dir = os.path.join(repo_dir, "Examples")
        if url == "":
            path_widget.value = "Please enter a valid URL to the repository."
        else:
            for group in groups:
                key = os.path.join(repo_dir, group)
                node = tree_dict[key]
                if node.selected:
                    default_dir = key
            try:
                path_widget.value = "Cloning..."
                clone_dir = os.path.join(default_dir, os.path.basename(url))
                if url.find("github.com") != -1:
                    clone_github_repo(url, out_dir=clone_dir)
                elif url.find("googlesource") != -1:
                    clone_google_repo(url, out_dir=clone_dir)
                path_widget.value = "Cloned to {}".format(clone_dir)
                clone_widget.disabled = True
            except Exception as e:
                path_widget.value = (
                    "An error occurred when trying to clone the repository " + str(e)
                )
                clone_widget.disabled = True

    clone_widget.on_click(handle_clone_click)

    return left_widget, info_widget, tree_dict


def file_browser(
    in_dir=None,
    show_hidden=False,
    add_root_node=True,
    search_description=None,
    use_import=False,
    return_sep_widgets=False,
    node_icon="file",
):
    """Creates a simple file browser and text editor.

    Args:
        in_dir (str, optional): The input directory. Defaults to None, which will use the current working directory.
        show_hidden (bool, optional): Whether to show hidden files/folders. Defaults to False.
        add_root_node (bool, optional): Whether to add the input directory as a root node. Defaults to True.
        search_description (str, optional): The description of the search box. Defaults to None.
        use_import (bool, optional): Whether to show the import button. Defaults to False.
        return_sep_widgets (bool, optional): Whether to return the results as separate widgets. Defaults to False.

    Returns:
        object: An ipywidget.
    """
    import platform

    if in_dir is None:
        in_dir = os.getcwd()

    if not os.path.exists(in_dir):
        print("The provided directory does not exist.")
        return
    elif not os.path.isdir(in_dir):
        print("The provided path is not a valid directory.")
        return

    sep = "/"
    if platform.system() == "Windows":
        sep = "\\"

    if in_dir.endswith(sep):
        in_dir = in_dir[:-1]

    full_widget = widgets.HBox()
    left_widget = widgets.VBox()

    right_widget = widgets.VBox()

    import_btn = widgets.Button(
        description="import",
        button_style="primary",
        tooltip="import the content to a new cell",
        disabled=True,
    )
    import_btn.layout.width = "70px"
    path_widget = widgets.Text()
    path_widget.layout.min_width = "400px"
    # path_widget.layout.max_width = '400px'
    save_widget = widgets.Button(
        description="Save",
        button_style="primary",
        tooltip="Save edits to file.",
        disabled=True,
    )
    info_widget = widgets.HBox()
    info_widget.children = [path_widget, save_widget]
    if use_import:
        info_widget.children = [import_btn, path_widget, save_widget]

    text_widget = widgets.Textarea()
    text_widget.layout.width = "630px"
    text_widget.layout.height = "600px"

    right_widget.children = [info_widget, text_widget]
    full_widget.children = [left_widget]

    if search_description is None:
        search_description = "Search files/folders..."
    search_box = widgets.Text(placeholder=search_description)
    search_box.layout.width = "310px"
    tree_widget = widgets.Output()
    tree_widget.layout.max_width = "310px"
    tree_widget.overflow = "auto"

    left_widget.children = [search_box, tree_widget]

    tree = Tree(multiple_selection=False)
    tree_dict = {}

    def on_button_clicked(b):
        content = text_widget.value
        out_file = path_widget.value

        out_dir = os.path.dirname(out_file)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        with open(out_file, "w") as f:
            f.write(content)

        text_widget.disabled = True
        text_widget.value = "The content has been saved successfully."
        save_widget.disabled = True
        path_widget.disabled = True

        if (out_file not in tree_dict.keys()) and (out_dir in tree_dict.keys()):
            node = Node(os.path.basename(out_file))
            tree_dict[out_file] = node
            parent_node = tree_dict[out_dir]
            parent_node.add_node(node)

    save_widget.on_click(on_button_clicked)

    def import_btn_clicked(b):
        if (text_widget.value != "") and (path_widget.value.endswith(".py")):
            create_code_cell(text_widget.value)

    import_btn.on_click(import_btn_clicked)

    def search_box_callback(text):
        with tree_widget:
            if text.value == "":
                print("Loading...")
                tree_widget.outputs = ()
                display(tree)
            else:
                tree_widget.outputs = ()
                print("Searching...")
                tree_widget.outputs = ()
                sub_tree = search_api_tree(text.value, tree_dict)
                display(sub_tree)

    search_box.on_submit(search_box_callback)

    def handle_file_click(event):
        if event["new"]:
            cur_node = event["owner"]
            for key in tree_dict.keys():
                if (cur_node is tree_dict[key]) and (os.path.isfile(key)):
                    if key.endswith(".py"):
                        import_btn.disabled = False
                    else:
                        import_btn.disabled = True
                    try:
                        with open(key) as f:
                            content = f.read()
                            text_widget.value = content
                            text_widget.disabled = False
                            path_widget.value = key
                            path_widget.disabled = False
                            save_widget.disabled = False
                            full_widget.children = [left_widget, right_widget]
                    except Exception as e:
                        path_widget.value = key
                        path_widget.disabled = True
                        save_widget.disabled = True
                        text_widget.disabled = True
                        text_widget.value = (
                            "Failed to open {}.".format(cur_node.name) + "\n\n" + str(e)
                        )
                        full_widget.children = [left_widget, right_widget]
                        return
                    break

    def handle_folder_click(event):
        if event["new"]:
            full_widget.children = [left_widget]
            text_widget.value = ""

    if add_root_node:
        root_name = in_dir.split(sep)[-1]
        root_node = Node(root_name)
        tree_dict[in_dir] = root_node
        tree.add_node(root_node)
        root_node.observe(handle_folder_click, "selected")

    for root, d_names, f_names in os.walk(in_dir):
        if not show_hidden:
            folders = root.split(sep)
            for folder in folders:
                if folder.startswith("."):
                    continue
            for d_name in d_names:
                if d_name.startswith("."):
                    d_names.remove(d_name)
            for f_name in f_names:
                if f_name.startswith("."):
                    f_names.remove(f_name)

        d_names.sort()
        f_names.sort()

        if (not add_root_node) and (root == in_dir):
            for d_name in d_names:
                node = Node(d_name)
                tree_dict[os.path.join(in_dir, d_name)] = node
                tree.add_node(node)
                node.opened = False
                node.observe(handle_folder_click, "selected")

        if (root != in_dir) and (root not in tree_dict.keys()):
            name = root.split(sep)[-1]
            dir_name = os.path.dirname(root)
            parent_node = tree_dict[dir_name]
            node = Node(name)
            tree_dict[root] = node
            parent_node.add_node(node)
            node.observe(handle_folder_click, "selected")

        if len(f_names) > 0:
            parent_node = tree_dict[root]
            parent_node.opened = False
            for f_name in f_names:
                node = Node(f_name)
                node.icon = node_icon
                full_path = os.path.join(root, f_name)
                tree_dict[full_path] = node
                parent_node.add_node(node)
                node.observe(handle_file_click, "selected")

    with tree_widget:
        tree_widget.outputs = ()
        display(tree)

    if return_sep_widgets:
        return left_widget, right_widget, tree_dict
    else:
        return full_widget


########################################
#             EE Utilities             #
########################################


def date_sequence(start, end, unit, date_format="YYYY-MM-dd", step=1):
    """Creates a date sequence.

    Args:
        start (str): The start date, e.g., '2000-01-01'.
        end (str): The end date, e.g., '2000-12-31'.
        unit (str): One of 'year', 'quarter', 'month' 'week', 'day', 'hour', 'minute', or 'second'.
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html. Defaults to 'YYYY-MM-dd'.
        step (int, optional): The step size. Defaults to 1.

    Returns:
        ee.List: A list of date sequence.
    """

    def get_quarter(d):
        return str((int(d[5:7]) - 1) // 3 * 3 + 1).zfill(2)

    def get_monday(d):
        date_obj = datetime.datetime.strptime(d, "%Y-%m-%d")
        start_of_week = date_obj - datetime.timedelta(days=date_obj.weekday())
        return start_of_week.strftime("%Y-%m-%d")

    if unit == "year":
        start = start[:4] + "-01-01"
    elif unit == "month":
        start = start[:7] + "-01"
    elif unit == "quarter":
        start = start[:5] + get_quarter(start) + "-01"
    elif unit == "week":
        start = get_monday(start)

    start_date = ee.Date(start)
    end_date = ee.Date(end)

    if unit != "quarter":
        count = ee.Number(end_date.difference(start_date, unit)).toInt()
        num_seq = ee.List.sequence(0, count)
        if step > 1:
            num_seq = num_seq.slice(0, num_seq.size(), step)
        date_seq = num_seq.map(
            lambda d: start_date.advance(d, unit).format(date_format)
        )

    else:
        unit = "month"
        count = ee.Number(end_date.difference(start_date, unit)).divide(3).toInt()
        num_seq = ee.List.sequence(0, count.multiply(3), 3)
        date_seq = num_seq.map(
            lambda d: start_date.advance(d, unit).format(date_format)
        )

    return date_seq


def legend_from_ee(ee_class_table):
    """Extract legend from an Earth Engine class table on the Earth Engine Data Catalog page
    such as https://developers.google.com/earth-engine/datasets/catalog/MODIS_051_MCD12Q1

    Args:
        ee_class_table (str): An Earth Engine class table with triple quotes.

    Returns:
        dict: Returns a legend dictionary that can be used to create a legend.
    """
    try:
        ee_class_table = ee_class_table.strip()
        lines = ee_class_table.split("\n")[1:]

        if lines[0] == "Value\tColor\tDescription":
            lines = lines[1:]

        legend_dict = {}
        for _, line in enumerate(lines):
            items = line.split("\t")
            items = [item.strip() for item in items]
            color = items[1]
            key = items[0] + " " + items[2]
            legend_dict[key] = color

        return legend_dict

    except Exception as e:
        print(e)


def vis_to_qml(ee_class_table, out_qml):
    """Create a QGIS Layer Style (.qml) based on an Earth Engine class table from the Earth Engine Data Catalog page
    such as https://developers.google.com/earth-engine/datasets/catalog/MODIS_051_MCD12Q1

    Args:
        ee_class_table (str): An Earth Engine class table with triple quotes.
        out_qml (str): File path to the output QGIS Layer Style (.qml).
    """
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    data_dir = os.path.join(pkg_dir, "data")
    template_dir = os.path.join(data_dir, "template")
    qml_template = os.path.join(template_dir, "NLCD.qml")

    out_dir = os.path.dirname(out_qml)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(qml_template) as f:
        lines = f.readlines()
        header = lines[:31]
        footer = lines[51:]

    entries = []
    try:
        ee_class_table = ee_class_table.strip()
        lines = ee_class_table.split("\n")[1:]

        if lines[0] == "Value\tColor\tDescription":
            lines = lines[1:]

        for line in lines:
            items = line.split("\t")
            items = [item.strip() for item in items]
            value = items[0]
            color = items[1]
            label = items[2]
            entry = '        <paletteEntry alpha="255" color="#{}" value="{}" label="{}"/>\n'.format(
                color, value, label
            )
            entries.append(entry)

        out_lines = header + entries + footer
        with open(out_qml, "w") as f:
            f.writelines(out_lines)

    except Exception as e:
        print(e)


def create_nlcd_qml(out_qml):
    """Create a QGIS Layer Style (.qml) for NLCD data

    Args:
        out_qml (str): File path to the output qml.
    """
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    data_dir = os.path.join(pkg_dir, "data")
    template_dir = os.path.join(data_dir, "template")
    qml_template = os.path.join(template_dir, "NLCD.qml")

    out_dir = os.path.dirname(out_qml)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    shutil.copyfile(qml_template, out_qml)


def load_GeoTIFF(URL):
    """Loads a Cloud Optimized GeoTIFF (COG) as an Image. Only Google Cloud Storage is supported. The URL can be one of the following formats:
    Option 1: gs://pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 2: https://storage.googleapis.com/pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 3: https://storage.cloud.google.com/gcp-public-data-landsat/LC08/01/044/034/LC08_L1TP_044034_20131228_20170307_01_T1/LC08_L1TP_044034_20131228_20170307_01_T1_B5.TIF

    Args:
        URL (str): The Cloud Storage URL of the GeoTIFF to load.

    Returns:
        ee.Image: an Earth Engine image.
    """

    uri = URL.strip()

    if uri.startswith("http"):
        uri = get_direct_url(uri)

    if uri.startswith("https://storage.googleapis.com/"):
        uri = uri.replace("https://storage.googleapis.com/", "gs://")
    elif uri.startswith("https://storage.cloud.google.com/"):
        uri = uri.replace("https://storage.cloud.google.com/", "gs://")

    if not uri.startswith("gs://"):
        raise Exception(
            f'Invalid GCS URL: {uri}. Expected something of the form "gs://bucket/path/to/object.tif".'
        )

    if not uri.lower().endswith(".tif"):
        raise Exception(
            f'Invalid GCS URL: {uri}. Expected something of the form "gs://bucket/path/to/object.tif".'
        )

    cloud_image = ee.Image.loadGeoTIFF(uri)
    return cloud_image


def load_GeoTIFFs(URLs):
    """Loads a list of Cloud Optimized GeoTIFFs (COG) as an ImageCollection. URLs is a list of URL, which can be one of the following formats:
    Option 1: gs://pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 2: https://storage.googleapis.com/pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 3: https://storage.cloud.google.com/gcp-public-data-landsat/LC08/01/044/034/LC08_L1TP_044034_20131228_20170307_01_T1/LC08_L1TP_044034_20131228_20170307_01_T1_B5.TIF

    Args:
        URLs (list): A list of Cloud Storage URL of the GeoTIFF to load.

    Returns:
        ee.ImageCollection: An Earth Engine ImageCollection.
    """

    if not isinstance(URLs, list):
        raise Exception("The URLs argument must be a list.")

    URIs = []
    for URL in URLs:
        uri = URL.strip()

        if uri.startswith("http"):
            uri = get_direct_url(uri)

        if uri.startswith("https://storage.googleapis.com/"):
            uri = uri.replace("https://storage.googleapis.com/", "gs://")
        elif uri.startswith("https://storage.cloud.google.com/"):
            uri = uri.replace("https://storage.cloud.google.com/", "gs://")

        if not uri.startswith("gs://"):
            raise Exception(
                f'Invalid GCS URL: {uri}. Expected something of the form "gs://bucket/path/to/object.tif".'
            )

        if not uri.lower().endswith(".tif"):
            raise Exception(
                f'Invalid GCS URL: {uri}. Expected something of the form "gs://bucket/path/to/object.tif".'
            )

        URIs.append(uri)

    URIs = ee.List(URIs)
    collection = URIs.map(lambda uri: ee.Image.loadGeoTIFF(uri))
    return ee.ImageCollection(collection)


def cog_tile(
    url,
    bands=None,
    titiler_endpoint=None,
    timeout=300,
    proxies=None,
    **kwargs,
):
    """Get a tile layer from a Cloud Optimized GeoTIFF (COG).
        Source code adapted from https://developmentseed.org/titiler/examples/notebooks/Working_with_CloudOptimizedGeoTIFF_simple/

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        timeout (int, optional): Timeout in seconds. Defaults to 300.
        proxies (dict, optional): Proxies to use. Defaults to None.

    Returns:
        tuple: Returns the COG Tile layer URL and bounds.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    url = get_direct_url(url)

    kwargs["url"] = url

    band_names = cog_bands(url, titiler_endpoint)

    if bands is None and "bidx" not in kwargs:
        if len(band_names) >= 3:
            kwargs["bidx"] = [1, 2, 3]
    elif bands is not None and "bidx" not in kwargs:
        if all(isinstance(x, int) for x in bands):
            kwargs["bidx"] = bands
        elif all(isinstance(x, str) for x in bands):
            kwargs["bidx"] = [band_names.index(x) + 1 for x in bands]
        else:
            raise ValueError("Bands must be a list of integers or strings.")

    if "palette" in kwargs:
        kwargs["colormap_name"] = kwargs.pop("palette")

    if "colormap" in kwargs:
        kwargs["colormap_name"] = kwargs.pop("colormap")

    if "rescale" not in kwargs:
        stats = cog_stats(url, titiler_endpoint)
        percentile_2 = min([stats[s]["percentile_2"] for s in stats])
        percentile_98 = max([stats[s]["percentile_98"] for s in stats])
        kwargs["rescale"] = f"{percentile_2},{percentile_98}"

    TileMatrixSetId = "WebMercatorQuad"
    if "TileMatrixSetId" in kwargs.keys():
        TileMatrixSetId = kwargs["TileMatrixSetId"]
        kwargs.pop("TileMatrixSetId")

    r = requests.get(
        f"{titiler_endpoint}/cog/{TileMatrixSetId}/tilejson.json",
        params=kwargs,
        timeout=timeout,
        proxies=proxies,
    ).json()

    return r["tiles"][0]


def cog_mosaic(
    links,
    titiler_endpoint=None,
    username="anonymous",
    layername=None,
    overwrite=False,
    verbose=True,
    timeout=300,
    **kwargs,
):
    """Creates a COG mosaic from a list of COG URLs.

    Args:
        links (list): A list containing COG HTTP URLs.
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        username (str, optional): User name for the titiler endpoint. Defaults to "anonymous".
        layername ([type], optional): Layer name to use. Defaults to None.
        overwrite (bool, optional): Whether to overwrite the layer name if existing. Defaults to False.
        verbose (bool, optional): Whether to print out descriptive information. Defaults to True.
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Raises:
        Exception: If the COG mosaic fails to create.

    Returns:
        str: The tile URL for the COG mosaic.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if layername is None:
        layername = "layer_" + random_string(5)

    try:
        if verbose:
            print("Creating COG masaic ...")

        # Create token
        r = requests.post(
            f"{titiler_endpoint}/tokens/create",
            json={"username": username, "scope": ["mosaic:read", "mosaic:create"]},
        ).json()
        token = r["token"]

        # Create mosaic
        requests.post(
            f"{titiler_endpoint}/mosaicjson/create",
            json={
                "username": username,
                "layername": layername,
                "files": links,
                # "overwrite": overwrite
            },
            params={
                "access_token": token,
            },
        ).json()

        r2 = requests.get(
            f"{titiler_endpoint}/mosaicjson/{username}.{layername}/tilejson.json",
            timeout=timeout,
        ).json()

        return r2["tiles"][0]

    except Exception as e:
        raise Exception(e)


def cog_mosaic_from_file(
    filepath,
    skip_rows=0,
    titiler_endpoint=None,
    username="anonymous",
    layername=None,
    overwrite=False,
    verbose=True,
    **kwargs,
):
    """Creates a COG mosaic from a csv/txt file stored locally for through HTTP URL.

    Args:
        filepath (str): Local path or HTTP URL to the csv/txt file containing COG URLs.
        skip_rows (int, optional): The number of rows to skip in the file. Defaults to 0.
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        username (str, optional): User name for the titiler endpoint. Defaults to "anonymous".
        layername ([type], optional): Layer name to use. Defaults to None.
        overwrite (bool, optional): Whether to overwrite the layer name if existing. Defaults to False.
        verbose (bool, optional): Whether to print out descriptive information. Defaults to True.

    Returns:
        str: The tile URL for the COG mosaic.
    """
    import urllib

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    links = []
    if filepath.startswith("http"):
        data = urllib.request.urlopen(filepath)
        for line in data:
            links.append(line.decode("utf-8").strip())

    else:
        with open(filepath) as f:
            links = [line.strip() for line in f.readlines()]

    links = links[skip_rows:]
    # print(links)
    mosaic = cog_mosaic(
        links, titiler_endpoint, username, layername, overwrite, verbose, **kwargs
    )
    return mosaic


def cog_bounds(url, titiler_endpoint=None, timeout=300):
    """Get the bounding box of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A list of values representing [left, bottom, right, top]
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    url = get_direct_url(url)

    r = requests.get(
        f"{titiler_endpoint}/cog/bounds", params={"url": url}, timeout=timeout
    ).json()

    if "bounds" in r.keys():
        bounds = r["bounds"]
    else:
        bounds = None
    return bounds


def cog_center(url, titiler_endpoint=None):
    """Get the centroid of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        tuple: A tuple representing (longitude, latitude)
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    url = get_direct_url(url)
    bounds = cog_bounds(url, titiler_endpoint)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lat, lon)
    return center


def cog_bands(url, titiler_endpoint=None, timeout=300):
    """Get band names of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A list of band names
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    url = get_direct_url(url)
    r = requests.get(
        f"{titiler_endpoint}/cog/info",
        params={
            "url": url,
        },
        timeout=timeout,
    ).json()

    bands = [b[0] for b in r["band_descriptions"]]
    return bands


def cog_stats(url, titiler_endpoint=None, timeout=300):
    """Get band statistics of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A dictionary of band statistics.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    url = get_direct_url(url)
    r = requests.get(
        f"{titiler_endpoint}/cog/statistics",
        params={
            "url": url,
        },
        timeout=timeout,
    ).json()

    return r


def cog_info(url, titiler_endpoint=None, return_geojson=False, timeout=300):
    """Get band statistics of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A dictionary of band info.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    url = get_direct_url(url)
    info = "info"
    if return_geojson:
        info = "info.geojson"

    r = requests.get(
        f"{titiler_endpoint}/cog/{info}",
        params={
            "url": url,
        },
        timeout=timeout,
    ).json()

    return r


def cog_pixel_value(
    lon,
    lat,
    url,
    bidx=None,
    titiler_endpoint=None,
    timeout=300,
    **kwargs,
):
    """Get pixel value from COG.

    Args:
        lon (float): Longitude of the pixel.
        lat (float): Latitude of the pixel.
        url (str): HTTP URL to a COG, e.g., 'https://github.com/opengeos/data/releases/download/raster/Libya-2023-07-01.tif'
        bidx (str, optional): Dataset band indexes (e.g bidx=1, bidx=1&bidx=2&bidx=3). Defaults to None.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A dictionary of band info.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    url = get_direct_url(url)
    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    kwargs["url"] = url
    if bidx is not None:
        kwargs["bidx"] = bidx

    r = requests.get(
        f"{titiler_endpoint}/cog/point/{lon},{lat}", params=kwargs, timeout=timeout
    ).json()
    bands = cog_bands(url, titiler_endpoint)
    # if isinstance(titiler_endpoint, str):
    #     r = requests.get(f"{titiler_endpoint}/cog/point/{lon},{lat}", params=kwargs).json()
    # else:
    #     r = requests.get(
    #         titiler_endpoint.url_for_stac_pixel_value(lon, lat), params=kwargs
    #     ).json()

    if "detail" in r:
        print(r["detail"])
        return None
    else:
        values = r["values"]
        result = dict(zip(bands, values))
        return result


def stac_tile(
    url=None,
    collection=None,
    item=None,
    assets=None,
    bands=None,
    titiler_endpoint=None,
    timeout=300,
    **kwargs,
):
    """Get a tile layer from a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "https://planetarycomputer.microsoft.com/api/data/v1", "planetary-computer", "pc". Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        str: Returns the STAC Tile layer URL.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        url = get_direct_url(url)
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    if "palette" in kwargs:
        kwargs["colormap_name"] = kwargs["palette"]
        del kwargs["palette"]

    if isinstance(bands, list) and len(set(bands)) == 1:
        bands = bands[0]

    if isinstance(assets, list) and len(set(assets)) == 1:
        assets = assets[0]

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)

    if "expression" in kwargs and ("asset_as_band" not in kwargs):
        kwargs["asset_as_band"] = True

    if isinstance(titiler_endpoint, PlanetaryComputerEndpoint):
        if isinstance(bands, str):
            bands = bands.split(",")
        if isinstance(assets, str):
            assets = assets.split(",")
        if assets is None and (bands is not None):
            assets = bands
        else:
            kwargs["bidx"] = bands

        kwargs["assets"] = assets

        # if ("expression" in kwargs) and ("rescale" not in kwargs):
        #     stats = stac_stats(
        #         collection=collection,
        #         item=item,
        #         expression=kwargs["expression"],
        #         titiler_endpoint=titiler_endpoint,
        #     )
        #     kwargs[
        #         "rescale"
        #     ] = f"{stats[0]['percentile_2']},{stats[0]['percentile_98']}"

        # if ("asset_expression" in kwargs) and ("rescale" not in kwargs):
        #     stats = stac_stats(
        #         collection=collection,
        #         item=item,
        #         expression=kwargs["asset_expression"],
        #         titiler_endpoint=titiler_endpoint,
        #     )
        #     kwargs[
        #         "rescale"
        #     ] = f"{stats[0]['percentile_2']},{stats[0]['percentile_98']}"

        if (
            (assets is not None)
            and ("asset_expression" not in kwargs)
            and ("expression" not in kwargs)
            and ("rescale" not in kwargs)
        ):
            stats = stac_stats(
                collection=collection,
                item=item,
                assets=assets,
                titiler_endpoint=titiler_endpoint,
            )
            if "detail" not in stats:
                try:
                    percentile_2 = min([stats[s]["percentile_2"] for s in stats])
                    percentile_98 = max([stats[s]["percentile_98"] for s in stats])
                except:
                    percentile_2 = min(
                        [
                            stats[s][list(stats[s].keys())[0]]["percentile_2"]
                            for s in stats
                        ]
                    )
                    percentile_98 = max(
                        [
                            stats[s][list(stats[s].keys())[0]]["percentile_98"]
                            for s in stats
                        ]
                    )
                kwargs["rescale"] = f"{percentile_2},{percentile_98}"
            else:
                print(stats["detail"])  # When operation times out.

    else:
        if isinstance(bands, str):
            bands = bands.split(",")
        if isinstance(assets, str):
            assets = assets.split(",")

        if assets is None and (bands is not None):
            assets = bands
        else:
            kwargs["asset_bidx"] = bands
        kwargs["assets"] = assets

    TileMatrixSetId = "WebMercatorQuad"
    if "TileMatrixSetId" in kwargs.keys():
        TileMatrixSetId = kwargs["TileMatrixSetId"]
        kwargs.pop("TileMatrixSetId")

    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/stac/{TileMatrixSetId}/tilejson.json",
            params=kwargs,
            timeout=timeout,
        ).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_item(), params=kwargs, timeout=timeout
        ).json()

    return r["tiles"][0]


def stac_bounds(
    url=None, collection=None, item=None, titiler_endpoint=None, timeout=300, **kwargs
):
    """Get the bounding box of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A list of values representing [left, bottom, right, top]
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        url = get_direct_url(url)
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/stac/bounds", params=kwargs, timeout=timeout
        ).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_bounds(), params=kwargs, timeout=timeout
        ).json()

    bounds = r["bounds"]
    return bounds


def stac_center(url=None, collection=None, item=None, titiler_endpoint=None, **kwargs):
    """Get the centroid of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        tuple: A tuple representing (longitude, latitude)
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if isinstance(url, str):
        url = get_direct_url(url)
    bounds = stac_bounds(url, collection, item, titiler_endpoint, **kwargs)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lon, lat)
    return center


def stac_bands(
    url=None, collection=None, item=None, titiler_endpoint=None, timeout=300, **kwargs
):
    """Get band names of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A list of band names
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        url = get_direct_url(url)
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/stac/assets", params=kwargs, timeout=timeout
        ).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_assets(), params=kwargs, timeout=timeout
        ).json()

    return r


def stac_stats(
    url=None,
    collection=None,
    item=None,
    assets=None,
    titiler_endpoint=None,
    timeout=300,
    **kwargs,
):
    """Get band statistics of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A dictionary of band statistics.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        url = get_direct_url(url)
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item
    if assets is not None:
        kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/stac/statistics", params=kwargs, timeout=timeout
        ).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_statistics(), params=kwargs, timeout=timeout
        ).json()

    return r


def stac_info(
    url=None,
    collection=None,
    item=None,
    assets=None,
    titiler_endpoint=None,
    timeout=300,
    **kwargs,
):
    """Get band info of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A dictionary of band info.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        url = get_direct_url(url)
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item
    if assets is not None:
        kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/stac/info", params=kwargs, timeout=timeout
        ).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_info(), params=kwargs, timeout=timeout
        ).json()

    return r


def stac_info_geojson(
    url=None,
    collection=None,
    item=None,
    assets=None,
    titiler_endpoint=None,
    timeout=300,
    **kwargs,
):
    """Get band info of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A dictionary of band info.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        url = get_direct_url(url)
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item
    if assets is not None:
        kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/stac/info.geojson", params=kwargs, timeout=timeout
        ).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_info_geojson(), params=kwargs, timeout=timeout
        ).json()

    return r


def stac_assets(
    url=None, collection=None, item=None, titiler_endpoint=None, timeout=300, **kwargs
):
    """Get all assets of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A list of assets.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        url = get_direct_url(url)
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/stac/assets", params=kwargs, timeout=timeout
        ).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_assets(), params=kwargs, timeout=timeout
        ).json()

    return r


def stac_pixel_value(
    lon,
    lat,
    url=None,
    collection=None,
    item=None,
    assets=None,
    titiler_endpoint=None,
    verbose=True,
    timeout=300,
    **kwargs,
):
    """Get pixel value from STAC assets.

    Args:
        lon (float): Longitude of the pixel.
        lat (float): Latitude of the pixel.
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        item (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        verbose (bool, optional): Print out the error message. Defaults to True.
        timeout (int, optional): Timeout in seconds. Defaults to 300.

    Returns:
        list: A dictionary of pixel values for each asset.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        url = get_direct_url(url)
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if item is not None:
        kwargs["item"] = item

    if assets is None:
        assets = stac_assets(
            url=url,
            collection=collection,
            item=item,
            titiler_endpoint=titiler_endpoint,
        )
        assets = ",".join(assets)
    kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/stac/{lon},{lat}", params=kwargs, timeout=timeout
        ).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_pixel_value(lon, lat),
            params=kwargs,
            timeout=timeout,
        ).json()

    if "detail" in r:
        if verbose:
            print(r["detail"])
        return None
    else:
        values = [v[0] for v in r["values"]]
        result = dict(zip(assets.split(","), values))
        return result


def local_tile_pixel_value(
    lon,
    lat,
    tile_client,
    verbose=True,
    **kwargs,
):
    """Get pixel value from COG.

    Args:
        lon (float): Longitude of the pixel.
        lat (float): Latitude of the pixel.
        url (str): HTTP URL to a COG, e.g., 'https://github.com/opengeos/data/releases/download/raster/Libya-2023-07-01.tif'
        bidx (str, optional): Dataset band indexes (e.g bidx=1, bidx=1&bidx=2&bidx=3). Defaults to None.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.
        verbose (bool, optional): Print status messages. Defaults to True.

    Returns:
        PointData: rio-tiler point data.
    """
    return tile_client.point(lon, lat, coord_crs="EPSG:4326", **kwargs)


def local_tile_vmin_vmax(
    source,
    bands=None,
    **kwargs,
):
    """Get vmin and vmax from COG.

    Args:
        source (str | TileClient): A local COG file path or TileClient object.
        bands (str | list, optional): A list of band names. Defaults to None.

    Raises:
        ValueError: If source is not a TileClient object or a local COG file path.

    Returns:
        tuple: A tuple of vmin and vmax.
    """
    check_package("localtileserver", "https://github.com/banesullivan/localtileserver")
    from localtileserver import TileClient

    if isinstance(source, str):
        tile_client = TileClient(source)
    elif isinstance(source, TileClient):
        tile_client = source
    else:
        raise ValueError("source must be a string or TileClient object.")

    bandnames = tile_client.band_names
    stats = tile_client.reader.statistics()

    if isinstance(bands, str):
        bands = [bands]
    elif isinstance(bands, list):
        pass
    elif bands is None:
        bands = bandnames

    if all(b in bandnames for b in bands):
        vmin = min([stats[b]["min"] for b in bands])
        vmax = max([stats[b]["max"] for b in bands])
    else:
        vmin = min([stats[b]["min"] for b in bandnames])
        vmax = max([stats[b]["max"] for b in bandnames])
    return vmin, vmax


def local_tile_bands(source):
    """Get band names from COG.

    Args:
        source (str | TileClient): A local COG file path or TileClient

    Returns:
        list: A list of band names.
    """
    check_package("localtileserver", "https://github.com/banesullivan/localtileserver")
    from localtileserver import TileClient

    if isinstance(source, str):
        tile_client = TileClient(source)
    elif isinstance(source, TileClient):
        tile_client = source
    else:
        raise ValueError("source must be a string or TileClient object.")

    return tile_client.band_names


def bbox_to_geojson(bounds):
    """Convert coordinates of a bounding box to a geojson.

    Args:
        bounds (list): A list of coordinates representing [left, bottom, right, top].

    Returns:
        dict: A geojson feature.
    """
    return {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [bounds[0], bounds[3]],
                    [bounds[0], bounds[1]],
                    [bounds[2], bounds[1]],
                    [bounds[2], bounds[3]],
                    [bounds[0], bounds[3]],
                ]
            ],
        },
        "type": "Feature",
    }


def coords_to_geojson(coords):
    """Convert a list of bbox coordinates representing [left, bottom, right, top] to geojson FeatureCollection.

    Args:
        coords (list): A list of bbox coordinates representing [left, bottom, right, top].

    Returns:
        dict: A geojson FeatureCollection.
    """

    features = []
    for bbox in coords:
        features.append(bbox_to_geojson(bbox))
    return {"type": "FeatureCollection", "features": features}


def explode(coords):
    """Explode a GeoJSON geometry's coordinates object and yield
    coordinate tuples. As long as the input is conforming, the type of
    the geometry doesn't matter.  From Fiona 1.4.8

    Args:
        coords (list): A list of coordinates.

    Yields:
        [type]: [description]
    """

    for e in coords:
        if isinstance(e, (float, int)):
            yield coords
            break
        else:
            for f in explode(e):
                yield f


def get_bounds(geometry, north_up=True, transform=None):
    """Bounding box of a GeoJSON geometry, GeometryCollection, or FeatureCollection.
    left, bottom, right, top
    *not* xmin, ymin, xmax, ymax
    If not north_up, y will be switched to guarantee the above.
    Source code adapted from https://github.com/mapbox/rasterio/blob/master/rasterio/features.py#L361

    Args:
        geometry (dict): A GeoJSON dict.
        north_up (bool, optional): . Defaults to True.
        transform ([type], optional): . Defaults to None.

    Returns:
        list: A list of coordinates representing [left, bottom, right, top]
    """

    if "bbox" in geometry:
        return tuple(geometry["bbox"])

    geometry = geometry.get("geometry") or geometry

    # geometry must be a geometry, GeometryCollection, or FeatureCollection
    if not (
        "coordinates" in geometry or "geometries" in geometry or "features" in geometry
    ):
        raise ValueError(
            "geometry must be a GeoJSON-like geometry, GeometryCollection, "
            "or FeatureCollection"
        )

    if "features" in geometry:
        # Input is a FeatureCollection
        xmins = []
        ymins = []
        xmaxs = []
        ymaxs = []
        for feature in geometry["features"]:
            xmin, ymin, xmax, ymax = get_bounds(feature["geometry"])
            xmins.append(xmin)
            ymins.append(ymin)
            xmaxs.append(xmax)
            ymaxs.append(ymax)
        if north_up:
            return min(xmins), min(ymins), max(xmaxs), max(ymaxs)
        else:
            return min(xmins), max(ymaxs), max(xmaxs), min(ymins)

    elif "geometries" in geometry:
        # Input is a geometry collection
        xmins = []
        ymins = []
        xmaxs = []
        ymaxs = []
        for geometry in geometry["geometries"]:
            xmin, ymin, xmax, ymax = get_bounds(geometry)
            xmins.append(xmin)
            ymins.append(ymin)
            xmaxs.append(xmax)
            ymaxs.append(ymax)
        if north_up:
            return min(xmins), min(ymins), max(xmaxs), max(ymaxs)
        else:
            return min(xmins), max(ymaxs), max(xmaxs), min(ymins)

    elif "coordinates" in geometry:
        # Input is a singular geometry object
        if transform is not None:
            xyz = list(explode(geometry["coordinates"]))
            xyz_px = [transform * point for point in xyz]
            xyz = tuple(zip(*xyz_px))
            return min(xyz[0]), max(xyz[1]), max(xyz[0]), min(xyz[1])
        else:
            xyz = tuple(zip(*list(explode(geometry["coordinates"]))))
            if north_up:
                return min(xyz[0]), min(xyz[1]), max(xyz[0]), max(xyz[1])
            else:
                return min(xyz[0]), max(xyz[1]), max(xyz[0]), min(xyz[1])

    # all valid inputs returned above, so whatever falls through is an error
    raise ValueError(
        "geometry must be a GeoJSON-like geometry, GeometryCollection, "
        "or FeatureCollection"
    )


def get_center(geometry, north_up=True, transform=None):
    """Get the centroid of a GeoJSON.

    Args:
        geometry (dict): A GeoJSON dict.
        north_up (bool, optional): . Defaults to True.
        transform ([type], optional): . Defaults to None.

    Returns:
        list: [lon, lat]
    """
    bounds = get_bounds(geometry, north_up, transform)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lat, lon)
    return center


def image_props(img, date_format="YYYY-MM-dd"):
    """Gets image properties.

    Args:
        img (ee.Image): The input image.
        date_format (str, optional): The output date format. Defaults to 'YYYY-MM-dd HH:mm:ss'.

    Returns:
        dd.Dictionary: The dictionary containing image properties.
    """
    if not isinstance(img, ee.Image):
        print("The input object must be an ee.Image")
        return

    keys = img.propertyNames().remove("system:footprint").remove("system:bands")
    values = keys.map(lambda p: img.get(p))
    props = ee.Dictionary.fromLists(keys, values)

    names = keys.getInfo()

    bands = img.bandNames()
    scales = bands.map(lambda b: img.select([b]).projection().nominalScale())
    scale = ee.Algorithms.If(
        scales.distinct().size().gt(1),
        ee.Dictionary.fromLists(bands.getInfo(), scales),
        scales.get(0),
    )

    props = props.set("NOMINAL_SCALE", scale)

    if "system:time_start" in names:
        image_date = ee.Date(img.get("system:time_start")).format(date_format)
        time_start = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd HH:mm:ss")
        # time_end = ee.Date(img.get('system:time_end')).format('YYYY-MM-dd HH:mm:ss')
        time_end = ee.Algorithms.If(
            ee.List(img.propertyNames()).contains("system:time_end"),
            ee.Date(img.get("system:time_end")).format("YYYY-MM-dd HH:mm:ss"),
            time_start,
        )
        props = props.set("system:time_start", time_start)
        props = props.set("system:time_end", time_end)
        props = props.set("IMAGE_DATE", image_date)

    if "system:asset_size" in names:
        asset_size = (
            ee.Number(img.get("system:asset_size"))
            .divide(1e6)
            .format()
            .cat(ee.String(" MB"))
        )

        props = props.set("system:asset_size", asset_size)

    return props


def image_stats(img, region=None, scale=None):
    """Gets image descriptive statistics.

    Args:
        img (ee.Image): The input image to calculate descriptive statistics.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        ee.Dictionary: A dictionary containing the description statistics of the input image.
    """

    if not isinstance(img, ee.Image):
        print("The input object must be an ee.Image")
        return

    stat_types = ["min", "max", "mean", "std", "sum"]

    image_min = image_min_value(img, region, scale)
    image_max = image_max_value(img, region, scale)
    image_mean = image_mean_value(img, region, scale)
    image_std = image_std_value(img, region, scale)
    image_sum = image_sum_value(img, region, scale)

    stat_results = ee.List([image_min, image_max, image_mean, image_std, image_sum])

    stats = ee.Dictionary.fromLists(stat_types, stat_results)

    return stats


def adjust_longitude(in_fc):
    """Adjusts longitude if it is less than -180 or greater than 180.

    Args:
        in_fc (dict): The input dictionary containing coordinates.

    Returns:
        dict: A dictionary containing the converted longitudes
    """
    try:
        keys = in_fc.keys()

        if "geometry" in keys:
            coordinates = in_fc["geometry"]["coordinates"]

            if in_fc["geometry"]["type"] == "Point":
                longitude = coordinates[0]
                if longitude < -180:
                    longitude = 360 + longitude
                elif longitude > 180:
                    longitude = longitude - 360
                in_fc["geometry"]["coordinates"][0] = longitude

            elif in_fc["geometry"]["type"] == "Polygon":
                for index1, item in enumerate(coordinates):
                    for index2, element in enumerate(item):
                        longitude = element[0]
                        if longitude < -180:
                            longitude = 360 + longitude
                        elif longitude > 180:
                            longitude = longitude - 360
                        in_fc["geometry"]["coordinates"][index1][index2][0] = longitude

            elif in_fc["geometry"]["type"] == "LineString":
                for index, element in enumerate(coordinates):
                    longitude = element[0]
                    if longitude < -180:
                        longitude = 360 + longitude
                    elif longitude > 180:
                        longitude = longitude - 360
                    in_fc["geometry"]["coordinates"][index][0] = longitude

        elif "type" in keys:
            coordinates = in_fc["coordinates"]

            if in_fc["type"] == "Point":
                longitude = coordinates[0]
                if longitude < -180:
                    longitude = 360 + longitude
                elif longitude > 180:
                    longitude = longitude - 360
                in_fc["coordinates"][0] = longitude

            elif in_fc["type"] == "Polygon":
                for index1, item in enumerate(coordinates):
                    for index2, element in enumerate(item):
                        longitude = element[0]
                        if longitude < -180:
                            longitude = 360 + longitude
                        elif longitude > 180:
                            longitude = longitude - 360
                        in_fc["coordinates"][index1][index2][0] = longitude

            elif in_fc["type"] == "LineString":
                for index, element in enumerate(coordinates):
                    longitude = element[0]
                    if longitude < -180:
                        longitude = 360 + longitude
                    elif longitude > 180:
                        longitude = longitude - 360
                    in_fc["coordinates"][index][0] = longitude

        return in_fc

    except Exception as e:
        print(e)
        return None


def zonal_stats(
    in_value_raster,
    in_zone_vector,
    out_file_path=None,
    stat_type="MEAN",
    scale=None,
    crs=None,
    tile_scale=1.0,
    return_fc=False,
    verbose=True,
    timeout=300,
    proxies=None,
    **kwargs,
):
    """Summarizes the values of a raster within the zones of another dataset and exports the results as a csv, shp, json, kml, or kmz.

    Args:
        in_value_raster (object): An ee.Image or ee.ImageCollection that contains the values on which to calculate a statistic.
        in_zone_vector (object): An ee.FeatureCollection that defines the zones.
        out_file_path (str): Output file path that will contain the summary of the values in each zone. The file type can be: csv, shp, json, kml, kmz
        stat_type (str, optional): Statistical type to be calculated. Defaults to 'MEAN'. For 'HIST', you can provide three parameters: max_buckets, min_bucket_width, and max_raw. For 'FIXED_HIST', you must provide three parameters: hist_min, hist_max, and hist_steps.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        crs (str, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        tile_scale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.0.
        verbose (bool, optional): Whether to print descriptive text when the programming is running. Default to True.
        return_fc (bool, optional): Whether to return the results as an ee.FeatureCollection. Defaults to False.
        timeout (int, optional): Timeout in seconds. Default to 300.
        proxies (dict, optional): A dictionary of proxy servers to use for the request. Default to None.
    """

    if isinstance(in_value_raster, ee.ImageCollection):
        in_value_raster = in_value_raster.toBands()

    if not isinstance(in_value_raster, ee.Image):
        print("The input raster must be an ee.Image.")
        return

    if not isinstance(in_zone_vector, ee.FeatureCollection):
        print("The input zone data must be an ee.FeatureCollection.")
        return

    if out_file_path is None:
        out_file_path = os.path.join(os.getcwd(), "zonal_stats.csv")

    if "statistics_type" in kwargs:
        stat_type = kwargs.pop("statistics_type")

    allowed_formats = ["csv", "geojson", "kml", "kmz", "shp"]
    filename = os.path.abspath(out_file_path)
    basename = os.path.basename(filename)
    # name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()

    if not (filetype in allowed_formats):
        print(
            "The file type must be one of the following: {}".format(
                ", ".join(allowed_formats)
            )
        )
        return

    # Parameters for histogram
    # The maximum number of buckets to use when building a histogram; will be rounded up to a power of 2.
    max_buckets = None
    # The minimum histogram bucket width, or null to allow any power of 2.
    min_bucket_width = None
    # The number of values to accumulate before building the initial histogram.
    max_raw = None
    hist_min = 1.0  # The lower (inclusive) bound of the first bucket.
    hist_max = 100.0  # The upper (exclusive) bound of the last bucket.
    hist_steps = 10  # The number of buckets to use.

    if "max_buckets" in kwargs.keys():
        max_buckets = kwargs["max_buckets"]
    if "min_bucket_width" in kwargs.keys():
        min_bucket_width = kwargs["min_bucket"]
    if "max_raw" in kwargs.keys():
        max_raw = kwargs["max_raw"]

    if isinstance(stat_type, str):
        if (
            stat_type.upper() == "FIXED_HIST"
            and ("hist_min" in kwargs.keys())
            and ("hist_max" in kwargs.keys())
            and ("hist_steps" in kwargs.keys())
        ):
            hist_min = kwargs["hist_min"]
            hist_max = kwargs["hist_max"]
            hist_steps = kwargs["hist_steps"]
        elif stat_type.upper() == "FIXED_HIST":
            print(
                "To use fixedHistogram, please provide these three parameters: hist_min, hist_max, and hist_steps."
            )
            return

    allowed_statistics = {
        "COUNT": ee.Reducer.count(),
        "MEAN": ee.Reducer.mean(),
        "MEAN_UNWEIGHTED": ee.Reducer.mean().unweighted(),
        "MAXIMUM": ee.Reducer.max(),
        "MEDIAN": ee.Reducer.median(),
        "MINIMUM": ee.Reducer.min(),
        "MODE": ee.Reducer.mode(),
        "STD": ee.Reducer.stdDev(),
        "MIN_MAX": ee.Reducer.minMax(),
        "SUM": ee.Reducer.sum(),
        "VARIANCE": ee.Reducer.variance(),
        "HIST": ee.Reducer.histogram(
            maxBuckets=max_buckets, minBucketWidth=min_bucket_width, maxRaw=max_raw
        ),
        "FIXED_HIST": ee.Reducer.fixedHistogram(hist_min, hist_max, hist_steps),
        "COMBINED_COUNT_MEAN": ee.Reducer.count().combine(
            ee.Reducer.mean(), sharedInputs=True
        ),
        "COMBINED_COUNT_MEAN_UNWEIGHTED": ee.Reducer.count().combine(
            ee.Reducer.mean().unweighted(), sharedInputs=True
        ),
    }

    if isinstance(stat_type, str):
        if not (stat_type.upper() in allowed_statistics.keys()):
            print(
                "The statistics type must be one of the following: {}".format(
                    ", ".join(list(allowed_statistics.keys()))
                )
            )
            return
        reducer = allowed_statistics[stat_type.upper()]
    elif isinstance(stat_type, ee.Reducer):
        reducer = stat_type
    else:
        raise ValueError("statistics_type must be either a string or ee.Reducer.")

    if scale is None:
        scale = in_value_raster.projection().nominalScale().multiply(10)

    try:
        if verbose:
            print("Computing statistics ...")
        result = in_value_raster.reduceRegions(
            collection=in_zone_vector,
            reducer=reducer,
            scale=scale,
            crs=crs,
            tileScale=tile_scale,
        )
        if return_fc:
            return result
        else:
            ee_export_vector(result, filename, timeout=timeout, proxies=proxies)
    except Exception as e:
        raise Exception(e)


zonal_statistics = zonal_stats


def zonal_stats_by_group(
    in_value_raster,
    in_zone_vector,
    out_file_path=None,
    stat_type="SUM",
    decimal_places=0,
    denominator=1.0,
    scale=None,
    crs=None,
    crs_transform=None,
    best_effort=True,
    max_pixels=1e7,
    tile_scale=1.0,
    return_fc=False,
    verbose=True,
    timeout=300,
    proxies=None,
    **kwargs,
):
    """Summarizes the area or percentage of a raster by group within the zones of another dataset and exports the results as a csv, shp, json, kml, or kmz.

    Args:
        in_value_raster (object): An integer Image that contains the values on which to calculate area/percentage.
        in_zone_vector (object): An ee.FeatureCollection that defines the zones.
        out_file_path (str): Output file path that will contain the summary of the values in each zone. The file type can be: csv, shp, json, kml, kmz
        stat_type (str, optional): Can be either 'SUM' or 'PERCENTAGE' . Defaults to 'SUM'.
        decimal_places (int, optional): The number of decimal places to use. Defaults to 0.
        denominator (float, optional): To convert area units (e.g., from square meters to square kilometers). Defaults to 1.0.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        crs (str, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        crs_transform (list, optional): The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and replaces any transform already set on the projection.
        best_effort (bool, optional): If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed.
        max_pixels (int, optional): The maximum number of pixels to reduce. Defaults to 1e7.
        tile_scale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.0.
        verbose (bool, optional): Whether to print descriptive text when the programming is running. Default to True.
        return_fc (bool, optional): Whether to return the results as an ee.FeatureCollection. Defaults to False.
        timeout (int, optional): Timeout in seconds. Defaults to 300.
        proxies (dict, optional): A dictionary of proxies to use. Defaults to None.

    """

    if isinstance(in_value_raster, ee.ImageCollection):
        in_value_raster = in_value_raster.toBands()

    if not isinstance(in_value_raster, ee.Image):
        print("The input raster must be an ee.Image.")
        return

    if out_file_path is None:
        out_file_path = os.path.join(os.getcwd(), "zonal_stats_by_group.csv")

    if "statistics_type" in kwargs:
        stat_type = kwargs.pop("statistics_type")

    band_count = in_value_raster.bandNames().size().getInfo()

    band_name = ""
    if band_count == 1:
        band_name = in_value_raster.bandNames().get(0)
    else:
        print("The input image can only have one band.")
        return

    band_types = in_value_raster.bandTypes().get(band_name).getInfo()
    band_type = band_types.get("precision")
    if band_type != "int":
        print("The input image band must be integer type.")
        return

    if not isinstance(in_zone_vector, ee.FeatureCollection):
        print("The input zone data must be an ee.FeatureCollection.")
        return

    allowed_formats = ["csv", "geojson", "kml", "kmz", "shp"]
    filename = os.path.abspath(out_file_path)
    basename = os.path.basename(filename)
    # name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:]

    if not (filetype.lower() in allowed_formats):
        print(
            "The file type must be one of the following: {}".format(
                ", ".join(allowed_formats)
            )
        )
        return

    out_dir = os.path.dirname(filename)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    allowed_statistics = ["SUM", "PERCENTAGE"]
    if not (stat_type.upper() in allowed_statistics):
        print(
            "The statistics type can only be one of {}".format(
                ", ".join(allowed_statistics)
            )
        )
        return

    if scale is None:
        scale = in_value_raster.projection().nominalScale().multiply(10)

    try:
        if verbose:
            print("Computing ... ")
        geometry = in_zone_vector.geometry()

        hist = in_value_raster.reduceRegion(
            ee.Reducer.frequencyHistogram(),
            geometry=geometry,
            scale=scale,
            crs=crs,
            crsTransform=crs_transform,
            bestEffort=best_effort,
            maxPixels=max_pixels,
            tileScale=tile_scale,
        )
        class_values = (
            ee.Dictionary(hist.get(band_name))
            .keys()
            .map(lambda v: ee.Number.parse(v))
            .sort()
        )

        class_names = class_values.map(
            lambda c: ee.String("Class_").cat(ee.Number(c).format())
        )

        # class_count = class_values.size().getInfo()
        dataset = ee.Image.pixelArea().divide(denominator).addBands(in_value_raster)

        init_result = dataset.reduceRegions(
            **{
                "collection": in_zone_vector,
                "reducer": ee.Reducer.sum().group(
                    **{
                        "groupField": 1,
                        "groupName": "group",
                    }
                ),
                "scale": scale,
            }
        )

        # def build_dict(input_list):

        #     decimal_format = '%.{}f'.format(decimal_places)
        #     in_dict = input_list.map(lambda x: ee.Dictionary().set(ee.String('Class_').cat(
        #         ee.Number(ee.Dictionary(x).get('group')).format()), ee.Number.parse(ee.Number(ee.Dictionary(x).get('sum')).format(decimal_format))))
        #     return in_dict

        def get_keys(input_list):
            return input_list.map(
                lambda x: ee.String("Class_").cat(
                    ee.Number(ee.Dictionary(x).get("group")).format()
                )
            )

        def get_values(input_list):
            decimal_format = "%.{}f".format(decimal_places)
            return input_list.map(
                lambda x: ee.Number.parse(
                    ee.Number(ee.Dictionary(x).get("sum")).format(decimal_format)
                )
            )

        def set_attribute(f):
            groups = ee.List(f.get("groups"))
            keys = get_keys(groups)
            values = get_values(groups)
            total_area = ee.List(values).reduce(ee.Reducer.sum())

            def get_class_values(x):
                cls_value = ee.Algorithms.If(
                    keys.contains(x), values.get(keys.indexOf(x)), 0
                )
                cls_value = ee.Algorithms.If(
                    ee.String(stat_type).compareTo(ee.String("SUM")),
                    ee.Number(cls_value).divide(ee.Number(total_area)),
                    cls_value,
                )
                return cls_value

            full_values = class_names.map(lambda x: get_class_values(x))
            attr_dict = ee.Dictionary.fromLists(class_names, full_values)
            attr_dict = attr_dict.set("Class_sum", total_area)

            return f.set(attr_dict).set("groups", None)

        final_result = init_result.map(set_attribute)
        if return_fc:
            return final_result
        else:
            ee_export_vector(final_result, filename, timeout=timeout, proxies=proxies)

    except Exception as e:
        raise Exception(e)


zonal_statistics_by_group = zonal_stats_by_group


def vec_area(fc):
    """Calculate the area (m2) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({"area_m2": f.area(1).round()}))


def vec_area_km2(fc):
    """Calculate the area (km2) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({"area_km2": f.area(1).divide(1e6).round()}))


def vec_area_mi2(fc):
    """Calculate the area (square mile) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({"area_mi2": f.area(1).divide(2.59e6).round()}))


def vec_area_ha(fc):
    """Calculate the area (hectare) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({"area_ha": f.area(1).divide(1e4).round()}))


def remove_geometry(fc):
    """Remove .geo coordinate field from a FeatureCollection

    Args:
        fc (object): The input FeatureCollection.

    Returns:
        object: The output FeatureCollection without the geometry field.
    """
    return fc.select([".*"], None, False)


def image_cell_size(img):
    """Retrieves the image cell size (e.g., spatial resolution)

    Args:
        img (object): ee.Image

    Returns:
        float: The nominal scale in meters.
    """
    bands = img.bandNames()
    scales = bands.map(lambda b: img.select([b]).projection().nominalScale())
    scale = ee.Algorithms.If(
        scales.distinct().size().gt(1),
        ee.Dictionary.fromLists(bands.getInfo(), scales),
        scales.get(0),
    )
    return scale


def image_scale(img):
    """Retrieves the image cell size (e.g., spatial resolution)

    Args:
        img (object): ee.Image

    Returns:
        float: The nominal scale in meters.
    """
    # bands = img.bandNames()
    # scales = bands.map(lambda b: img.select([b]).projection().nominalScale())
    # scale = ee.Algorithms.If(scales.distinct().size().gt(1), ee.Dictionary.fromLists(bands.getInfo(), scales), scales.get(0))
    return img.select(0).projection().nominalScale()


def image_band_names(img):
    """Gets image band names.

    Args:
        img (ee.Image): The input image.

    Returns:
        ee.List: The returned list of image band names.
    """
    return img.bandNames()


def image_date(img, date_format="YYYY-MM-dd"):
    """Retrieves the image acquisition date.

    Args:
        img (object): ee.Image
        date_format (str, optional): The date format to use. Defaults to 'YYYY-MM-dd'.

    Returns:
        str: A string representing the acquisition of the image.
    """
    return ee.Date(img.get("system:time_start")).format(date_format)


def image_dates(img_col, date_format="YYYY-MM-dd"):
    """Get image dates of all images in an ImageCollection.

    Args:
        img_col (object): ee.ImageCollection
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html; if omitted will use ISO standard date formatting. Defaults to 'YYYY-MM-dd'.

    Returns:
        object: ee.List
    """
    dates = img_col.aggregate_array("system:time_start")
    new_dates = dates.map(lambda d: ee.Date(d).format(date_format))
    return new_dates


def image_area(img, region=None, scale=None, denominator=1.0):
    """Calculates the area of an image.

    Args:
        img (object): ee.Image
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        denominator (float, optional): The denominator to use for converting size from square meters to other units. Defaults to 1.0.

    Returns:
        object: ee.Dictionary
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    pixel_area = (
        img.unmask().neq(ee.Image(0)).multiply(ee.Image.pixelArea()).divide(denominator)
    )
    img_area = pixel_area.reduceRegion(
        **{
            "geometry": region,
            "reducer": ee.Reducer.sum(),
            "scale": scale,
            "maxPixels": 1e12,
        }
    )
    return img_area


def image_area_by_group(
    img,
    groups=None,
    region=None,
    scale=None,
    denominator=1.0,
    out_csv=None,
    labels=None,
    decimal_places=4,
    verbose=True,
):
    """Calculates the area of each class of an image.

    Args:
        img (object): ee.Image
        groups (object, optional): The groups to use for the area calculation. Defaults to None.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        denominator (float, optional): The denominator to use for converting size from square meters to other units. Defaults to 1.0.
        out_csv (str, optional): The path to the output CSV file. Defaults to None.
        labels (object, optional): The class labels to use in the output CSV file. Defaults to None.
        decimal_places (int, optional): The number of decimal places to use for the output. Defaults to 2.
        verbose (bool, optional): If True, print the progress. Defaults to True.

    Returns:
        object: pandas.DataFrame
    """
    import pandas as pd

    values = []
    if region is None:
        region = ee.Geometry.BBox(-179.9, -89.5, 179.9, 89.5)

    if groups is None:
        groups = image_value_list(img, region, scale)

    if not isinstance(groups, list):
        groups = groups.getInfo()

    groups.sort(key=int)

    for group in groups:
        if verbose:
            print(f"Calculating area for group {group} ...")
        area = image_area(img.eq(float(group)), region, scale, denominator)
        values.append(area.values().get(0).getInfo())

    d = {"group": groups, "area": values}
    df = pd.DataFrame(data=d)
    df = df.set_index("group")
    df["percentage"] = df["area"] / df["area"].sum()
    df = df.astype(float).round(decimal_places)
    if isinstance(labels, list) and len(labels) == len(values):
        df["labels"] = labels

    if out_csv is not None:
        df.to_csv(out_csv)
    else:
        return df


def image_max_value(img, region=None, scale=None):
    """Retrieves the maximum value of an image.

    Args:
        img (object): The image to calculate the maximum value.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    max_value = img.reduceRegion(
        **{
            "reducer": ee.Reducer.max(),
            "geometry": region,
            "scale": scale,
            "maxPixels": 1e12,
            "bestEffort": True,
        }
    )
    return max_value


def image_min_value(img, region=None, scale=None):
    """Retrieves the minimum value of an image.

    Args:
        img (object): The image to calculate the minimum value.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    min_value = img.reduceRegion(
        **{
            "reducer": ee.Reducer.min(),
            "geometry": region,
            "scale": scale,
            "maxPixels": 1e12,
            "bestEffort": True,
        }
    )
    return min_value


def image_mean_value(img, region=None, scale=None):
    """Retrieves the mean value of an image.

    Args:
        img (object): The image to calculate the mean value.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    mean_value = img.reduceRegion(
        **{
            "reducer": ee.Reducer.mean(),
            "geometry": region,
            "scale": scale,
            "maxPixels": 1e12,
            "bestEffort": True,
        }
    )
    return mean_value


def image_std_value(img, region=None, scale=None):
    """Retrieves the standard deviation of an image.

    Args:
        img (object): The image to calculate the standard deviation.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    std_value = img.reduceRegion(
        **{
            "reducer": ee.Reducer.stdDev(),
            "geometry": region,
            "scale": scale,
            "maxPixels": 1e12,
            "bestEffort": True,
        }
    )
    return std_value


def image_sum_value(img, region=None, scale=None):
    """Retrieves the sum of an image.

    Args:
        img (object): The image to calculate the standard deviation.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    sum_value = img.reduceRegion(
        **{
            "reducer": ee.Reducer.sum(),
            "geometry": region,
            "scale": scale,
            "maxPixels": 1e12,
            "bestEffort": True,
        }
    )
    return sum_value


def image_value_list(img, region=None, scale=None, return_hist=False, **kwargs):
    """Get the unique values of an image.

    Args:
        img (ee.Image): The image to calculate the unique values.
        region (ee.Geometry | ee.FeatureCollection, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        return_hist (bool, optional): If True, return a histogram of the values. Defaults to False.

    Returns:
        ee.List | ee.Dictionary: A list of unique values or a dictionary containing a list of unique values and a histogram.
    """
    if region is None:
        geom = img.geometry().bounds()
        region = ee.FeatureCollection([ee.Feature(geom)])
    elif isinstance(region, ee.Geometry):
        region = ee.FeatureCollection([ee.Feature(region)])
    elif isinstance(region, ee.FeatureCollection):
        pass
    else:
        raise ValueError("region must be an ee.Geometry or ee.FeatureCollection")

    if scale is None:
        scale = img.select(0).projection().nominalScale().multiply(10)

    reducer = ee.Reducer.frequencyHistogram()
    kwargs["scale"] = scale
    kwargs["reducer"] = reducer
    kwargs["collection"] = region

    result = img.reduceRegions(**kwargs)
    hist = ee.Dictionary(result.first().get("histogram"))
    if return_hist:
        return hist
    else:
        return hist.keys()


def image_histogram(
    img,
    region=None,
    scale=None,
    x_label=None,
    y_label=None,
    title=None,
    width=None,
    height=500,
    plot_args={},
    layout_args={},
    return_df=False,
    **kwargs,
):
    """Create a histogram of an image.

    Args:
        img (ee.Image): The image to calculate the histogram.
        region (ee.Geometry | ee.FeatureCollection, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        x_label (str, optional): Label for the x axis. Defaults to None.
        y_label (str, optional): Label for the y axis. Defaults to None.
        title (str, optional): Title for the plot. Defaults to None.
        width (int, optional): Width of the plot in pixels. Defaults to None.
        height (int, optional): Height of the plot in pixels. Defaults to 500.
        layout_args (dict, optional): Layout arguments for the plot to be passed to fig.update_layout(),
        return_df (bool, optional): If True, return a pandas dataframe. Defaults to False.

    Returns:
        pandas DataFrame | plotly figure object: A dataframe or plotly figure object.
    """
    import pandas as pd
    import plotly.express as px

    hist = image_value_list(img, region, scale, return_hist=True, **kwargs).getInfo()
    keys = sorted(hist, key=int)
    values = [hist.get(key) for key in keys]

    data = pd.DataFrame({"key": keys, "value": values})

    if return_df:
        return data
    else:
        labels = {}

        if x_label is not None:
            labels["key"] = x_label
        if y_label is not None:
            labels["value"] = y_label

        try:
            fig = px.bar(
                data,
                x="key",
                y="value",
                labels=labels,
                title=title,
                width=width,
                height=height,
                **plot_args,
            )

            if isinstance(layout_args, dict):
                fig.update_layout(**layout_args)

            return fig
        except Exception as e:
            raise Exception(e)


def image_stats_by_zone(
    image,
    zones,
    out_csv=None,
    labels=None,
    region=None,
    scale=None,
    reducer="MEAN",
    bestEffort=True,
    **kwargs,
):
    """Calculate statistics for an image by zone.

    Args:
        image (ee.Image): The image to calculate statistics for.
        zones (ee.Image): The zones to calculate statistics for.
        out_csv (str, optional): The path to the output CSV file. Defaults to None.
        labels (list, optional): The list of zone labels to use for the output CSV. Defaults to None.
        region (ee.Geometry, optional): The region over which to reduce data. Defaults to the footprint of zone image.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        reducer (str | ee.Reducer, optional): The reducer to use. It can be one of MEAN, MAXIMUM, MINIMUM, MODE, STD, MIN_MAX, SUM, VARIANCE. Defaults to MEAN.
        bestEffort (bool, optional): If the polygon would contain too many pixels at the given scale, compute and use a larger scale which would allow the operation to succeed. Defaults to True.

    Returns:
        str | pd.DataFrame: The path to the output CSV file or a pandas DataFrame.
    """
    import pandas as pd

    if region is not None:
        if isinstance(region, ee.Geometry):
            pass
        elif isinstance(region, ee.FeatureCollection):
            region = region.geometry()
        else:
            raise ValueError("region must be an ee.Geometry or ee.FeatureCollection")

    if scale is None:
        scale = image_scale(image)

    allowed_stats = {
        "MEAN": ee.Reducer.mean(),
        "MAXIMUM": ee.Reducer.max(),
        "MEDIAN": ee.Reducer.median(),
        "MINIMUM": ee.Reducer.min(),
        "MODE": ee.Reducer.mode(),
        "STD": ee.Reducer.stdDev(),
        "MIN_MAX": ee.Reducer.minMax(),
        "SUM": ee.Reducer.sum(),
        "VARIANCE": ee.Reducer.variance(),
    }

    if isinstance(reducer, str):
        if reducer.upper() not in allowed_stats:
            raise ValueError(
                "reducer must be one of: {}".format(", ".join(allowed_stats.keys()))
            )
        else:
            reducer = allowed_stats[reducer.upper()]
    elif isinstance(reducer, ee.Reducer):
        pass
    else:
        raise ValueError(
            "reducer must be one of: {}".format(", ".join(allowed_stats.keys()))
        )

    values = image_value_list(zones, region=region)
    values = values.map(lambda x: ee.Number.parse(x))

    def get_stats(value):
        img = image.updateMask(zones.eq(ee.Number(value)))
        kwargs["reducer"] = reducer
        kwargs["scale"] = scale
        kwargs["geometry"] = region
        kwargs["bestEffort"] = bestEffort
        stat = img.reduceRegion(**kwargs)
        return ee.Image().set({"zone": value}).set({"stat": stat.values().get(0)})

    collection = ee.ImageCollection(values.map(lambda x: get_stats(x)))
    keys = collection.aggregate_array("zone").getInfo()
    values = collection.aggregate_array("stat").getInfo()

    if labels is not None and isinstance(labels, list):
        if len(labels) != len(keys):
            warnings.warn("labels are not the same length as keys, ignoring labels.")
            df = pd.DataFrame({"zone": keys, "stat": values})
        else:
            df = pd.DataFrame({"zone": keys, "label": labels, "stat": values})
    else:
        df = pd.DataFrame({"zone": keys, "stat": values})

    if out_csv is not None:
        check_file_path(out_csv)
        df.to_csv(out_csv, index=False)
        return out_csv
    else:
        return df


def latitude_grid(step=1.0, west=-180, east=180, south=-85, north=85):
    """Create a latitude grid.

    Args:
        step (float, optional): The step size in degrees. Defaults to 1.0.
        west (int, optional): The west boundary in degrees. Defaults to -180.
        east (int, optional): The east boundary in degrees. Defaults to 180.
        south (int, optional): The south boundary in degrees. Defaults to -85.
        north (int, optional): The north boundary in degrees. Defaults to 85.

    Returns:
        ee.FeatureCollection: A feature collection of latitude grids.
    """
    values = ee.List.sequence(south, north - step, step)

    def create_feature(lat):
        return ee.Feature(
            ee.Geometry.BBox(west, lat, east, ee.Number(lat).add(step))
        ).set(
            {
                "south": lat,
                "west": west,
                "north": ee.Number(lat).add(step),
                "east": east,
            }
        )

    features = ee.FeatureCollection(values.map(create_feature))
    return features


def longitude_grid(step=1.0, west=-180, east=180, south=-85, north=85):
    """Create a longitude grid.

    Args:
        step (float, optional): The step size in degrees. Defaults to 1.0.
        west (int, optional): The west boundary in degrees. Defaults to -180.
        east (int, optional): The east boundary in degrees. Defaults to 180.
        south (int, optional): The south boundary in degrees. Defaults to -85.
        north (int, optional): The north boundary in degrees. Defaults to 85.

    Returns:
        ee.FeatureCollection: A feature collection of longitude grids.
    """

    values = ee.List.sequence(west, east - step, step)

    def create_feature(lon):
        return ee.Feature(
            ee.Geometry.BBox(lon, south, ee.Number(lon).add(step), north)
        ).set(
            {
                "south": south,
                "west": lon,
                "north": north,
                "east": ee.Number(lon).add(step),
            }
        )

    features = ee.FeatureCollection(values.map(create_feature))
    return features


def latlon_grid(lat_step=1.0, lon_step=1.0, west=-180, east=180, south=-85, north=85):
    """Create a rectangular grid of latitude and longitude.

    Args:
        lat_step (float, optional): The step size in degrees. Defaults to 1.0.
        lon_step (float, optional): The step size in degrees. Defaults to 1.0.
        west (int, optional): The west boundary in degrees. Defaults to -180.
        east (int, optional): The east boundary in degrees. Defaults to 180.
        south (int, optional): The south boundary in degrees. Defaults to -85.
        north (int, optional): The north boundary in degrees. Defaults to 85.

    Returns:
        ee.FeatureCollection: A feature collection of latitude and longitude grids.
    """
    longitudes = ee.List.sequence(west, east - lon_step, lon_step)
    latitudes = ee.List.sequence(south, north - lat_step, lat_step)

    def create_lat_feature(lat):
        def create_lon_features(lon):
            return ee.Feature(
                ee.Geometry.BBox(
                    lon, lat, ee.Number(lon).add(lon_step), ee.Number(lat).add(lat_step)
                )
            ).set(
                {
                    "south": lat,
                    "west": lon,
                    "north": ee.Number(lat).add(lat_step),
                    "east": ee.Number(lon).add(lon_step),
                }
            )

        return ee.FeatureCollection(longitudes.map(create_lon_features))

    return ee.FeatureCollection(latitudes.map(create_lat_feature)).flatten()


def fishnet(
    data,
    h_interval=1.0,
    v_interval=1.0,
    rows=None,
    cols=None,
    delta=1.0,
    intersect=True,
    output=None,
    **kwargs,
):
    """Create a fishnet (i.e., rectangular grid) based on an input vector dataset.

    Args:
        data (str | ee.Geometry | ee.Feature | ee.FeatureCollection): The input vector dataset. It can be a file path, HTTP URL, ee.Geometry, ee.Feature, or ee.FeatureCollection.
        h_interval (float, optional): The horizontal interval in degrees. It will be ignored if rows and cols are specified. Defaults to 1.0.
        v_interval (float, optional): The vertical interval in degrees. It will be ignored if rows and cols are specified. Defaults to 1.0.
        rows (int, optional): The number of rows. Defaults to None.
        cols (int, optional): The number of columns. Defaults to None.
        delta (float, optional): The buffer distance in degrees. Defaults to 1.0.
        intersect (bool, optional): If True, the output will be a feature collection of intersecting polygons. Defaults to True.
        output (str, optional): The output file path. Defaults to None.


    Returns:
        ee.FeatureCollection: The fishnet as an ee.FeatureCollection.
    """
    if isinstance(data, str):
        data = vector_to_ee(data, **kwargs)

    if isinstance(data, ee.FeatureCollection) or isinstance(data, ee.Feature):
        data = data.geometry()
    elif isinstance(data, ee.Geometry):
        pass
    else:
        raise ValueError(
            "data must be a string, ee.FeatureCollection, ee.Feature, or ee.Geometry."
        )

    coords = data.bounds().coordinates().getInfo()

    west = coords[0][0][0]
    east = coords[0][1][0]
    south = coords[0][0][1]
    north = coords[0][2][1]

    if rows is not None and cols is not None:
        v_interval = (north - south) / rows
        h_interval = (east - west) / cols

    # west = west - delta * h_interval
    east = east + delta * h_interval
    # south = south - delta * v_interval
    north = north + delta * v_interval

    grids = latlon_grid(v_interval, h_interval, west, east, south, north)

    if intersect:
        grids = grids.filterBounds(data)

    if output is not None:
        ee_export_vector(grids, output)

    else:
        return grids


def extract_values_to_points(
    in_fc,
    image,
    out_fc=None,
    scale=None,
    crs=None,
    crsTransform=None,
    tileScale=1,
    stats_type="FIRST",
    timeout=300,
    proxies=None,
    **kwargs,
):
    """Extracts image values to points.

    Args:
        in_fc (object): ee.FeatureCollection.
        image (object): The ee.Image to extract pixel values.
        out_fc (object, optional): The output feature collection. Defaults to None.
        scale (ee.Projectoin, optional): A nominal scale in meters of the projection to sample in. If unspecified,the scale of the image's first band is used.
        crs (str, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        crsTransform (list, optional): The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and will replace any transform already set on the projection.
        tile_scale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default.
        stats_type (str, optional): Statistic type to be calculated. Defaults to 'FIRST'.
        timeout (int, optional): The number of seconds after which the request will be terminated. Defaults to 300.
        proxies (dict, optional): A dictionary of proxy servers to use for each request. Defaults to None.

    Returns:
        object: ee.FeatureCollection
    """

    if "tile_scale" in kwargs:
        tileScale = kwargs["tile_scale"]
    if "crs_transform" in kwargs:
        crsTransform = kwargs["crs_transform"]

    allowed_stats = {
        "FIRST": ee.Reducer.first(),
        "MEAN": ee.Reducer.mean(),
        "MAXIMUM": ee.Reducer.max(),
        "MEDIAN": ee.Reducer.median(),
        "MINIMUM": ee.Reducer.min(),
        "STD": ee.Reducer.stdDev(),
        "MIN_MAX": ee.Reducer.minMax(),
        "SUM": ee.Reducer.sum(),
        "VARIANCE": ee.Reducer.variance(),
    }

    if stats_type.upper() not in allowed_stats:
        raise ValueError(
            f"The statistics_type must be one of the following {', '.join(allowed_stats.keys())}"
        )

    if not isinstance(in_fc, ee.FeatureCollection):
        try:
            in_fc = shp_to_ee(in_fc)
        except Exception as e:
            print(e)
            return

    if not isinstance(image, ee.Image):
        print("The image must be an instance of ee.Image.")
        return

    result = image.reduceRegions(
        collection=in_fc,
        reducer=allowed_stats[stats_type.upper()],
        scale=scale,
        crs=crs,
        crsTransform=crsTransform,
        tileScale=tileScale,
    )

    if out_fc is not None:
        ee_export_vector(result, out_fc, timeout=timeout, proxies=proxies)
    else:
        return result


def image_reclassify(img, in_list, out_list):
    """Reclassify an image.

    Args:
        img (object): The image to which the remapping is applied.
        in_list (list): The source values (numbers or EEArrays). All values in this list will be mapped to the corresponding value in 'out_list'.
        out_list (list): The destination values (numbers or EEArrays). These are used to replace the corresponding values in 'from'. Must have the same number of values as 'in_list'.

    Returns:
        object: ee.Image
    """
    image = img.remap(in_list, out_list)
    return image


def image_smoothing(img, reducer, kernel):
    """Smooths an image.

    Args:
        img (object): The image to be smoothed.
        reducer (object): ee.Reducer
        kernel (object): ee.Kernel

    Returns:
        object: ee.Image
    """
    image = img.reduceNeighborhood(
        **{
            "reducer": reducer,
            "kernel": kernel,
        }
    )
    return image


def rename_bands(img, in_band_names, out_band_names):
    """Renames image bands.

    Args:
        img (object): The image to be renamed.
        in_band_names (list): The list of input band names.
        out_band_names (list): The list of output band names.

    Returns:
        object: The output image with the renamed bands.
    """
    return img.select(in_band_names, out_band_names)


def bands_to_image_collection(img):
    """Converts all bands in an image to an image collection.

    Args:
        img (object): The image to convert.

    Returns:
        object: ee.ImageCollection
    """
    collection = ee.ImageCollection(img.bandNames().map(lambda b: img.select([b])))
    return collection


def find_landsat_by_path_row(landsat_col, path_num, row_num):
    """Finds Landsat images by WRS path number and row number.

    Args:
        landsat_col (str): The image collection id of Landsat.
        path_num (int): The WRS path number.
        row_num (int): the WRS row number.

    Returns:
        object: ee.ImageCollection
    """
    try:
        if isinstance(landsat_col, str):
            landsat_col = ee.ImageCollection(landsat_col)
            collection = landsat_col.filter(ee.Filter.eq("WRS_PATH", path_num)).filter(
                ee.Filter.eq("WRS_ROW", row_num)
            )
            return collection
    except Exception as e:
        print(e)


def str_to_num(in_str):
    """Converts a string to an ee.Number.

    Args:
        in_str (str): The string to convert to a number.

    Returns:
        object: ee.Number
    """
    return ee.Number.parse(str)


def array_sum(arr):
    """Accumulates elements of an array along the given axis.

    Args:
        arr (object): Array to accumulate.

    Returns:
        object: ee.Number
    """
    return ee.Array(arr).accum(0).get([-1])


def array_mean(arr):
    """Calculates the mean of an array along the given axis.

    Args:
        arr (object): Array to calculate mean.

    Returns:
        object: ee.Number
    """
    total = ee.Array(arr).accum(0).get([-1])
    size = arr.length()
    return ee.Number(total.divide(size))


def get_annual_NAIP(year, RGBN=True):
    """Filters NAIP ImageCollection by year.

    Args:
        year (int): The year to filter the NAIP ImageCollection.
        RGBN (bool, optional): Whether to retrieve 4-band NAIP imagery only. Defaults to True.

    Returns:
        object: ee.ImageCollection
    """
    try:
        collection = ee.ImageCollection("USDA/NAIP/DOQQ")
        start_date = str(year) + "-01-01"
        end_date = str(year) + "-12-31"
        naip = collection.filterDate(start_date, end_date)
        if RGBN:
            naip = naip.filter(ee.Filter.listContains("system:band_names", "N"))
        return naip
    except Exception as e:
        print(e)


def get_all_NAIP(start_year=2009, end_year=2019):
    """Creates annual NAIP imagery mosaic.

    Args:
        start_year (int, optional): The starting year. Defaults to 2009.
        end_year (int, optional): The ending year. Defaults to 2019.

    Returns:
        object: ee.ImageCollection
    """
    try:

        def get_annual_NAIP(year):
            try:
                collection = ee.ImageCollection("USDA/NAIP/DOQQ")
                start_date = ee.Date.fromYMD(year, 1, 1)
                end_date = ee.Date.fromYMD(year, 12, 31)
                naip = collection.filterDate(start_date, end_date).filter(
                    ee.Filter.listContains("system:band_names", "N")
                )
                return ee.ImageCollection(naip)
            except Exception as e:
                print(e)

        years = ee.List.sequence(start_year, end_year)
        collection = years.map(get_annual_NAIP)
        return collection

    except Exception as e:
        print(e)


def annual_NAIP(year, region):
    """Create an NAIP mosaic of a specified year for a specified region.

    Args:
        year (int): The specified year to create the mosaic for.
        region (object): ee.Geometry

    Returns:
        object: ee.Image
    """

    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = ee.Date.fromYMD(year, 12, 31)
    collection = (
        ee.ImageCollection("USDA/NAIP/DOQQ")
        .filterDate(start_date, end_date)
        .filterBounds(region)
    )

    time_start = ee.Date(
        ee.List(collection.aggregate_array("system:time_start")).sort().get(0)
    )
    time_end = ee.Date(
        ee.List(collection.aggregate_array("system:time_end")).sort().get(-1)
    )
    image = ee.Image(collection.mosaic().clip(region))
    NDWI = ee.Image(image).normalizedDifference(["G", "N"]).select(["nd"], ["ndwi"])
    NDVI = ee.Image(image).normalizedDifference(["N", "R"]).select(["nd"], ["ndvi"])
    image = image.addBands(NDWI)
    image = image.addBands(NDVI)
    return image.set({"system:time_start": time_start, "system:time_end": time_end})


def find_NAIP(region, add_NDVI=True, add_NDWI=True):
    """Create annual NAIP mosaic for a given region.

    Args:
        region (object): ee.Geometry
        add_NDVI (bool, optional): Whether to add the NDVI band. Defaults to True.
        add_NDWI (bool, optional): Whether to add the NDWI band. Defaults to True.

    Returns:
        object: ee.ImageCollection
    """

    init_collection = (
        ee.ImageCollection("USDA/NAIP/DOQQ")
        .filterBounds(region)
        .filterDate("2009-01-01", "2019-12-31")
        .filter(ee.Filter.listContains("system:band_names", "N"))
    )

    yearList = ee.List(
        init_collection.distinct(["system:time_start"]).aggregate_array(
            "system:time_start"
        )
    )
    init_years = yearList.map(lambda y: ee.Date(y).get("year"))

    # remove duplicates
    init_years = ee.Dictionary(
        init_years.reduce(ee.Reducer.frequencyHistogram())
    ).keys()
    years = init_years.map(lambda x: ee.Number.parse(x))
    # years = init_years.map(lambda x: x)

    # Available NAIP years with NIR band
    def NAIPAnnual(year):
        start_date = ee.Date.fromYMD(year, 1, 1)
        end_date = ee.Date.fromYMD(year, 12, 31)
        collection = init_collection.filterDate(start_date, end_date)
        # .filterBounds(geometry)
        # .filter(ee.Filter.listContains("system:band_names", "N"))
        time_start = ee.Date(
            ee.List(collection.aggregate_array("system:time_start")).sort().get(0)
        ).format("YYYY-MM-dd")
        time_end = ee.Date(
            ee.List(collection.aggregate_array("system:time_end")).sort().get(-1)
        ).format("YYYY-MM-dd")
        col_size = collection.size()
        image = ee.Image(collection.mosaic().clip(region))

        if add_NDVI:
            NDVI = (
                ee.Image(image)
                .normalizedDifference(["N", "R"])
                .select(["nd"], ["ndvi"])
            )
            image = image.addBands(NDVI)

        if add_NDWI:
            NDWI = (
                ee.Image(image)
                .normalizedDifference(["G", "N"])
                .select(["nd"], ["ndwi"])
            )
            image = image.addBands(NDWI)

        return image.set(
            {
                "system:time_start": time_start,
                "system:time_end": time_end,
                "tiles": col_size,
            }
        )

    # remove years with incomplete coverage
    naip = ee.ImageCollection(years.map(NAIPAnnual))
    mean_size = ee.Number(naip.aggregate_mean("tiles"))
    total_sd = ee.Number(naip.aggregate_total_sd("tiles"))
    threshold = mean_size.subtract(total_sd.multiply(1))
    naip = naip.filter(
        ee.Filter.Or(ee.Filter.gte("tiles", threshold), ee.Filter.gte("tiles", 15))
    )
    naip = naip.filter(ee.Filter.gte("tiles", 7))

    naip_count = naip.size()
    naip_seq = ee.List.sequence(0, naip_count.subtract(1))

    def set_index(index):
        img = ee.Image(naip.toList(naip_count).get(index))
        return img.set({"system:uid": ee.Number(index).toUint8()})

    naip = naip_seq.map(set_index)

    return ee.ImageCollection(naip)


def filter_NWI(HUC08_Id, region, exclude_riverine=True):
    """Retrieves NWI dataset for a given HUC8 watershed.

    Args:
        HUC08_Id (str): The HUC8 watershed id.
        region (object): ee.Geometry
        exclude_riverine (bool, optional): Whether to exclude riverine wetlands. Defaults to True.

    Returns:
        object: ee.FeatureCollection
    """
    nwi_asset_prefix = "users/wqs/NWI-HU8/HU8_"
    nwi_asset_suffix = "_Wetlands"
    nwi_asset_path = nwi_asset_prefix + HUC08_Id + nwi_asset_suffix
    nwi_huc = ee.FeatureCollection(nwi_asset_path).filterBounds(region)

    if exclude_riverine:
        nwi_huc = nwi_huc.filter(
            ee.Filter.notEquals(**{"leftField": "WETLAND_TY", "rightValue": "Riverine"})
        )
    return nwi_huc


def filter_HUC08(region):
    """Filters HUC08 watersheds intersecting a given region.

    Args:
        region (object): ee.Geometry

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC08 = ee.FeatureCollection("USGS/WBD/2017/HUC08")  # Subbasins
    HUC08 = USGS_HUC08.filterBounds(region)
    return HUC08


# Find HUC10 intersecting a geometry
def filter_HUC10(region):
    """Filters HUC10 watersheds intersecting a given region.

    Args:
        region (object): ee.Geometry

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC10 = ee.FeatureCollection("USGS/WBD/2017/HUC10")  # Watersheds
    HUC10 = USGS_HUC10.filterBounds(region)
    return HUC10


def find_HUC08(HUC08_Id):
    """Finds a HUC08 watershed based on a given HUC08 ID

    Args:
        HUC08_Id (str): The HUC08 ID.

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC08 = ee.FeatureCollection("USGS/WBD/2017/HUC08")  # Subbasins
    HUC08 = USGS_HUC08.filter(ee.Filter.eq("huc8", HUC08_Id))
    return HUC08


def find_HUC10(HUC10_Id):
    """Finds a HUC10 watershed based on a given HUC08 ID

    Args:
        HUC10_Id (str): The HUC10 ID.

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC10 = ee.FeatureCollection("USGS/WBD/2017/HUC10")  # Watersheds
    HUC10 = USGS_HUC10.filter(ee.Filter.eq("huc10", HUC10_Id))
    return HUC10


# find NWI by HUC08
def find_NWI(HUC08_Id, exclude_riverine=True):
    """Finds NWI dataset for a given HUC08 watershed.

    Args:
        HUC08_Id (str): The HUC08 watershed ID.
        exclude_riverine (bool, optional): Whether to exclude riverine wetlands. Defaults to True.

    Returns:
        object: ee.FeatureCollection
    """

    nwi_asset_prefix = "users/wqs/NWI-HU8/HU8_"
    nwi_asset_suffix = "_Wetlands"
    nwi_asset_path = nwi_asset_prefix + HUC08_Id + nwi_asset_suffix
    nwi_huc = ee.FeatureCollection(nwi_asset_path)
    if exclude_riverine:
        nwi_huc = nwi_huc.filter(
            ee.Filter.notEquals(**{"leftField": "WETLAND_TY", "rightValue": "Riverine"})
        )
    return nwi_huc


def nwi_add_color(fc):
    """Converts NWI vector dataset to image and add color to it.

    Args:
        fc (object): ee.FeatureCollection

    Returns:
        object: ee.Image
    """
    emergent = ee.FeatureCollection(
        fc.filter(ee.Filter.eq("WETLAND_TY", "Freshwater Emergent Wetland"))
    )
    emergent = emergent.map(lambda f: f.set("R", 127).set("G", 195).set("B", 28))
    # print(emergent.first())

    forested = fc.filter(
        ee.Filter.eq("WETLAND_TY", "Freshwater Forested/Shrub Wetland")
    )
    forested = forested.map(lambda f: f.set("R", 0).set("G", 136).set("B", 55))

    pond = fc.filter(ee.Filter.eq("WETLAND_TY", "Freshwater Pond"))
    pond = pond.map(lambda f: f.set("R", 104).set("G", 140).set("B", 192))

    lake = fc.filter(ee.Filter.eq("WETLAND_TY", "Lake"))
    lake = lake.map(lambda f: f.set("R", 19).set("G", 0).set("B", 124))

    riverine = fc.filter(ee.Filter.eq("WETLAND_TY", "Riverine"))
    riverine = riverine.map(lambda f: f.set("R", 1).set("G", 144).set("B", 191))

    fc = ee.FeatureCollection(
        emergent.merge(forested).merge(pond).merge(lake).merge(riverine)
    )

    #   base = ee.Image(0).mask(0).toInt8()
    base = ee.Image().byte()
    img = base.paint(fc, "R").addBands(
        base.paint(fc, "G").addBands(base.paint(fc, "B"))
    )

    return img


def nwi_rename(names):
    name_dict = ee.Dictionary(
        {
            "Freshwater Emergent Wetland": "Emergent",
            "Freshwater Forested/Shrub Wetland": "Forested",
            "Estuarine and Marine Wetland": "Estuarine",
            "Freshwater Pond": "Pond",
            "Lake": "Lake",
            "Riverine": "Riverine",
            "Estuarine and Marine Deepwater": "Deepwater",
            "Other": "Other",
        }
    )

    new_names = ee.List(names).map(lambda name: name_dict.get(name))
    return new_names


def summarize_by_group(
    collection, column, group, group_name, stats_type, return_dict=True
):
    """Calculates summary statistics by group.

    Args:
        collection (object): The input feature collection
        column (str): The value column to calculate summary statistics.
        group (str): The name of the group column.
        group_name (str): The new group name to use.
        stats_type (str): The type of summary statistics.
        return_dict (bool): Whether to return the result as a dictionary.

    Returns:
        object: ee.Dictionary or ee.List
    """
    stats_type = stats_type.lower()
    allowed_stats = ["min", "max", "mean", "median", "sum", "stdDev", "variance"]
    if stats_type not in allowed_stats:
        print(
            "The stats type must be one of the following: {}".format(
                ",".join(allowed_stats)
            )
        )
        return

    stats_dict = {
        "min": ee.Reducer.min(),
        "max": ee.Reducer.max(),
        "mean": ee.Reducer.mean(),
        "median": ee.Reducer.median(),
        "sum": ee.Reducer.sum(),
        "stdDev": ee.Reducer.stdDev(),
        "variance": ee.Reducer.variance(),
    }

    selectors = [column, group]
    stats = collection.reduceColumns(
        **{
            "selectors": selectors,
            "reducer": stats_dict[stats_type].group(
                **{"groupField": 1, "groupName": group_name}
            ),
        }
    )
    results = ee.List(ee.Dictionary(stats).get("groups"))
    if return_dict:
        keys = results.map(lambda k: ee.Dictionary(k).get(group_name))
        values = results.map(lambda v: ee.Dictionary(v).get(stats_type))
        results = ee.Dictionary.fromLists(keys, values)

    return results


def summary_stats(collection, column):
    """Aggregates over a given property of the objects in a collection, calculating the sum, min, max, mean,
    sample standard deviation, sample variance, total standard deviation and total variance of the selected property.

    Args:
        collection (FeatureCollection): The input feature collection to calculate summary statistics.
        column (str): The name of the column to calculate summary statistics.

    Returns:
        dict: The dictionary containing information about the summary statistics.
    """
    stats = collection.aggregate_stats(column).getInfo()
    return eval(str(stats))


def column_stats(collection, column, stats_type):
    """Aggregates over a given property of the objects in a collection, calculating the sum, min, max, mean,
    sample standard deviation, sample variance, total standard deviation and total variance of the selected property.

    Args:
        collection (FeatureCollection): The input feature collection to calculate statistics.
        column (str): The name of the column to calculate statistics.
        stats_type (str): The type of statistics to calculate.

    Returns:
        dict: The dictionary containing information about the requested statistics.
    """
    stats_type = stats_type.lower()
    allowed_stats = ["min", "max", "mean", "median", "sum", "stdDev", "variance"]
    if stats_type not in allowed_stats:
        print(
            "The stats type must be one of the following: {}".format(
                ",".join(allowed_stats)
            )
        )
        return

    stats_dict = {
        "min": ee.Reducer.min(),
        "max": ee.Reducer.max(),
        "mean": ee.Reducer.mean(),
        "median": ee.Reducer.median(),
        "sum": ee.Reducer.sum(),
        "stdDev": ee.Reducer.stdDev(),
        "variance": ee.Reducer.variance(),
    }

    selectors = [column]
    stats = collection.reduceColumns(
        **{"selectors": selectors, "reducer": stats_dict[stats_type]}
    )

    return stats


def ee_num_round(num, decimal=2):
    """Rounds a number to a specified number of decimal places.

    Args:
        num (ee.Number): The number to round.
        decimal (int, optional): The number of decimal places to round. Defaults to 2.

    Returns:
        ee.Number: The number with the specified decimal places rounded.
    """
    format_str = "%.{}f".format(decimal)
    return ee.Number.parse(ee.Number(num).format(format_str))


def num_round(num, decimal=2):
    """Rounds a number to a specified number of decimal places.

    Args:
        num (float): The number to round.
        decimal (int, optional): The number of decimal places to round. Defaults to 2.

    Returns:
        float: The number with the specified decimal places rounded.
    """
    return round(num, decimal)


def png_to_gif(in_dir, out_gif, fps=10, loop=0):
    """Convert a list of png images to gif.

    Args:
        in_dir (str): The input directory containing png images.
        out_gif (str): The output file path to the gif.
        fps (int, optional): Frames per second. Defaults to 10.
        loop (bool, optional): controls how many times the animation repeats. 1 means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.

    Raises:
        FileNotFoundError: No png images could be found.
    """
    import glob

    from PIL import Image

    if not out_gif.endswith(".gif"):
        raise ValueError("The out_gif must be a gif file.")

    out_gif = os.path.abspath(out_gif)

    out_dir = os.path.dirname(out_gif)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Create the frames
    frames = []
    imgs = list(glob.glob(os.path.join(in_dir, "*.png")))
    imgs.sort()

    if len(imgs) == 0:
        raise FileNotFoundError(f"No png could be found in {in_dir}.")

    for i in imgs:
        new_frame = Image.open(i)
        frames.append(new_frame)

    # Save into a GIF file that loops forever
    frames[0].save(
        out_gif,
        format="GIF",
        append_images=frames[1:],
        save_all=True,
        duration=1000 / fps,
        loop=loop,
    )


def jpg_to_gif(in_dir, out_gif, fps=10, loop=0):
    """Convert a list of jpg images to gif.

    Args:
        in_dir (str): The input directory containing jpg images.
        out_gif (str): The output file path to the gif.
        fps (int, optional): Frames per second. Defaults to 10.
        loop (bool, optional): controls how many times the animation repeats. 1 means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.

    Raises:
        FileNotFoundError: No jpg images could be found.
    """
    import glob

    from PIL import Image

    if not out_gif.endswith(".gif"):
        raise ValueError("The out_gif must be a gif file.")

    out_gif = os.path.abspath(out_gif)

    out_dir = os.path.dirname(out_gif)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Create the frames
    frames = []
    imgs = list(glob.glob(os.path.join(in_dir, "*.jpg")))
    imgs.sort()

    if len(imgs) == 0:
        raise FileNotFoundError(f"No jpg could be found in {in_dir}.")

    for i in imgs:
        new_frame = Image.open(i)
        frames.append(new_frame)

    # Save into a GIF file that loops forever
    frames[0].save(
        out_gif,
        format="GIF",
        append_images=frames[1:],
        save_all=True,
        duration=1000 / fps,
        loop=loop,
    )


def vector_styling(
    ee_object,
    column,
    palette,
    color="000000",
    colorOpacity=1.0,
    pointSize=3,
    pointShape="circle",
    width=1,
    lineType="solid",
    fillColorOpacity=0.66,
):
    """Add a new property to each feature containing a stylying dictionary.

    Args:
        ee_object (object): An ee.FeatureCollection.
        column (str): The column name to use for styling.
        palette (list | dict): The palette (e.g., list of colors or a dict containing label and color pairs) to use for styling.
        color (str, optional): A default color (CSS 3.0 color value e.g. 'FF0000' or 'red') to use for drawing the features. Defaults to "black".
        colorOpacity (float, optional): Opacity between 0-1 of the features. Defaults to 1
        pointSize (int, optional): The default size in pixels of the point markers. Defaults to 3.
        pointShape (str, optional): The default shape of the marker to draw at each point location. One of: circle, square, diamond, cross, plus, pentagram, hexagram, triangle, triangle_up, triangle_down, triangle_left, triangle_right, pentagon, hexagon, star5, star6. This argument also supports the following Matlab marker abbreviations: o, s, d, x, +, p, h, ^, v, <, >. Defaults to "circle".
        width (int, optional): The default line width for lines and outlines for polygons and point shapes. Defaults to 1.
        lineType (str, optional): The default line style for lines and outlines of polygons and point shapes. Defaults to 'solid'. One of: solid, dotted, dashed. Defaults to "solid".
        fillColorOpacity (float, optional): Opacity between 0-1 of the fill. Defaults to 0.66. Color of the fill is based on the column name or index in the palette.
    Raises:
        ValueError: The provided column name is invalid.
        TypeError: The provided palette is invalid.
        TypeError: The provided ee_object is not an ee.FeatureCollection.

    Returns:
        object: An ee.FeatureCollection containing the styling attribute.
    """
    from box import Box

    if isinstance(ee_object, ee.FeatureCollection):
        prop_names = ee.Feature(ee_object.first()).propertyNames().getInfo()
        arr = ee_object.aggregate_array(column).distinct().sort()

        if column not in prop_names:
            raise ValueError(f"The column name must of one of {', '.join(prop_names)}")

        if isinstance(palette, Box):
            try:
                palette = list(palette["default"])
            except Exception as e:
                print("The provided palette is invalid.")
                raise Exception(e)
        elif isinstance(palette, tuple):
            palette = list(palette)
        elif isinstance(palette, dict):
            values = list(arr.getInfo())
            labels = list(palette.keys())
            if not all(elem in values for elem in labels):
                raise ValueError(
                    f"The keys of the palette must contain the following elements: {', '.join(values)}"
                )
            else:
                colors = [palette[value] for value in values]
                palette = colors

        if not isinstance(palette, list):
            raise TypeError("The palette must be a list.")

        colors = ee.List(
            [
                color.strip() + str(hex(int(fillColorOpacity * 255)))[2:].zfill(2)
                for color in palette
            ]
        )
        fc = ee_object.map(lambda f: f.set({"styleIndex": arr.indexOf(f.get(column))}))
        step = arr.size().divide(colors.size()).ceil()
        fc = fc.map(
            lambda f: f.set(
                {
                    "style": {
                        "color": color + str(hex(int(colorOpacity * 255)))[2:].zfill(2),
                        "pointSize": pointSize,
                        "pointShape": pointShape,
                        "width": width,
                        "lineType": lineType,
                        "fillColor": colors.get(
                            ee.Number(
                                ee.Number(f.get("styleIndex")).divide(step)
                            ).floor()
                        ),
                    }
                }
            )
        )

        return fc

    else:
        raise TypeError("The ee_object must be an ee.FeatureCollection.")


def is_GCS(in_shp):
    import pycrs

    if not os.path.exists(in_shp):
        raise FileNotFoundError("The input shapefile could not be found.")

    if not in_shp.endswith(".shp"):
        raise TypeError("The input shapefile is invalid.")

    in_prj = in_shp.replace(".shp", ".prj")

    if not os.path.exists(in_prj):
        warnings.warn(
            f"The projection file {in_prj} could not be found. Assuming the dataset is in a geographic coordinate system (GCS)."
        )
        return True
    else:
        with open(in_prj) as f:
            esri_wkt = f.read()
        epsg4326 = pycrs.parse.from_epsg_code(4326).to_proj4()
        try:
            crs = pycrs.parse.from_esri_wkt(esri_wkt).to_proj4()
            return crs == epsg4326
            # if crs == epsg4326:
            #     return True
            # else:
            #     return False
        except Exception:
            return False


def kml_to_shp(in_kml, out_shp, **kwargs):
    """Converts a KML to shapefile.

    Args:
        in_kml (str): The file path to the input KML.
        out_shp (str): The file path to the output shapefile.

    Raises:
        FileNotFoundError: The input KML could not be found.
        TypeError: The output must be a shapefile.
    """

    warnings.filterwarnings("ignore")

    in_kml = os.path.abspath(in_kml)
    if not os.path.exists(in_kml):
        raise FileNotFoundError("The input KML could not be found.")

    out_shp = os.path.abspath(out_shp)
    if not out_shp.endswith(".shp"):
        raise TypeError("The output must be a shapefile.")

    out_dir = os.path.dirname(out_shp)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd
    import fiona

    # import fiona
    # print(fiona.supported_drivers)
    fiona.drvsupport.supported_drivers["KML"] = "rw"
    df = gpd.read_file(in_kml, driver="KML", **kwargs)
    df.to_file(out_shp, **kwargs)


def kml_to_geojson(in_kml, out_geojson=None, **kwargs):
    """Converts a KML to GeoJSON.

    Args:
        in_kml (str): The file path to the input KML.
        out_geojson (str): The file path to the output GeoJSON. Defaults to None.

    Raises:
        FileNotFoundError: The input KML could not be found.
        TypeError: The output must be a GeoJSON.
    """

    warnings.filterwarnings("ignore")

    in_kml = os.path.abspath(in_kml)
    if not os.path.exists(in_kml):
        raise FileNotFoundError("The input KML could not be found.")

    if out_geojson is not None:
        out_geojson = os.path.abspath(out_geojson)
        ext = os.path.splitext(out_geojson)[1].lower()
        if ext not in [".json", ".geojson"]:
            raise TypeError("The output file must be a GeoJSON.")

        out_dir = os.path.dirname(out_geojson)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd
    import fiona

    # print(fiona.supported_drivers)
    fiona.drvsupport.supported_drivers["KML"] = "rw"
    gdf = gpd.read_file(in_kml, driver="KML", **kwargs)

    if out_geojson is not None:
        gdf.to_file(out_geojson, driver="GeoJSON", **kwargs)
    else:
        return gdf.__geo_interface__


def kml_to_ee(in_kml, **kwargs):
    """Converts a KML to ee.FeatureCollection.

    Args:
        in_kml (str): The file path to the input KML.

    Raises:
        FileNotFoundError: The input KML could not be found.

    Returns:
        object: ee.FeatureCollection
    """

    warnings.filterwarnings("ignore")

    in_kml = os.path.abspath(in_kml)
    if not os.path.exists(in_kml):
        raise FileNotFoundError("The input KML could not be found.")

    out_json = os.path.join(os.getcwd(), "tmp.geojson")

    check_package(name="geopandas", URL="https://geopandas.org")

    kml_to_geojson(in_kml, out_json, **kwargs)
    ee_object = geojson_to_ee(out_json)
    os.remove(out_json)
    return ee_object


def kmz_to_ee(in_kmz, **kwargs):
    """Converts a KMZ to ee.FeatureCollection.

    Args:
        in_kmz (str): The file path to the input KMZ.

    Raises:
        FileNotFoundError: The input KMZ could not be found.

    Returns:
        object: ee.FeatureCollection
    """
    in_kmz = os.path.abspath(in_kmz)
    if not os.path.exists(in_kmz):
        raise FileNotFoundError("The input KMZ could not be found.")

    out_dir = os.path.dirname(in_kmz)
    out_kml = os.path.join(out_dir, "doc.kml")
    with zipfile.ZipFile(in_kmz, "r") as zip_ref:
        zip_ref.extractall(out_dir)

    fc = kml_to_ee(out_kml, **kwargs)
    os.remove(out_kml)
    return fc


def csv_to_df(in_csv, **kwargs):
    """Converts a CSV file to pandas dataframe.

    Args:
        in_csv (str): File path to the input CSV.

    Returns:
        pd.DataFrame: pandas DataFrame
    """
    import pandas as pd

    in_csv = github_raw_url(in_csv)

    try:
        return pd.read_csv(in_csv, **kwargs)
    except Exception as e:
        raise Exception(e)


def ee_to_df(
    ee_object,
    columns=None,
    remove_geom=True,
    sort_columns=False,
    **kwargs,
):
    """Converts an ee.FeatureCollection to pandas dataframe.

    Args:
        ee_object (ee.FeatureCollection): ee.FeatureCollection.
        columns (list): List of column names. Defaults to None.
        remove_geom (bool): Whether to remove the geometry column. Defaults to True.
        sort_columns (bool): Whether to sort the column names. Defaults to False.
        kwargs: Additional arguments passed to ee.data.computeFeature.

    Raises:
        TypeError: ee_object must be an ee.FeatureCollection

    Returns:
        pd.DataFrame: pandas DataFrame
    """
    if isinstance(ee_object, ee.Feature):
        ee_object = ee.FeatureCollection([ee_object])

    if not isinstance(ee_object, ee.FeatureCollection):
        raise TypeError("ee_object must be an ee.FeatureCollection")

    try:
        if remove_geom:
            data = ee_object.map(
                lambda f: ee.Feature(None, f.toDictionary(f.propertyNames().sort()))
            )
        else:
            data = ee_object

        kwargs["expression"] = data
        kwargs["fileFormat"] = "PANDAS_DATAFRAME"

        df = ee.data.computeFeatures(kwargs)

        if isinstance(columns, list):
            df = df[columns]

        if remove_geom and ("geo" in df.columns):
            df = df.drop(columns=["geo"], axis=1)

        if sort_columns:
            df = df.reindex(sorted(df.columns), axis=1)

        return df
    except Exception as e:
        raise Exception(e)


def shp_to_gdf(in_shp, **kwargs):
    """Converts a shapefile to Geopandas dataframe.

    Args:
        in_shp (str): File path to the input shapefile.

    Raises:
        FileNotFoundError: The provided shp could not be found.

    Returns:
        gpd.GeoDataFrame: geopandas.GeoDataFrame
    """

    warnings.filterwarnings("ignore")

    in_shp = os.path.abspath(in_shp)
    if not os.path.exists(in_shp):
        raise FileNotFoundError("The provided shp could not be found.")

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    try:
        return gpd.read_file(in_shp, **kwargs)
    except Exception as e:
        raise Exception(e)


shp_to_geopandas = shp_to_gdf


def ee_to_gdf(
    ee_object,
    columns=None,
    sort_columns=False,
    **kwargs,
):
    """Converts an ee.FeatureCollection to GeoPandas GeoDataFrame.

    Args:
        ee_object (ee.FeatureCollection): ee.FeatureCollection.
        columns (list): List of column names. Defaults to None.
        sort_columns (bool): Whether to sort the column names. Defaults to False.
        kwargs: Additional arguments passed to ee.data.computeFeature.

    Raises:
        TypeError: ee_object must be an ee.FeatureCollection

    Returns:
        gpd.GeoDataFrame: GeoPandas GeoDataFrame
    """
    if isinstance(ee_object, ee.Feature):
        ee_object = ee.FeatureCollection([ee_object])

    if not isinstance(ee_object, ee.FeatureCollection):
        raise TypeError("ee_object must be an ee.FeatureCollection")

    try:
        kwargs["expression"] = ee_object
        kwargs["fileFormat"] = "GEOPANDAS_GEODATAFRAME"

        crs = ee_object.first().geometry().projection().crs().getInfo()
        gdf = ee.data.computeFeatures(kwargs)

        if isinstance(columns, list):
            gdf = gdf[columns]

        if sort_columns:
            gdf = gdf.reindex(sorted(gdf.columns), axis=1)

        gdf.crs = crs
        return gdf
    except Exception as e:
        raise Exception(e)


def delete_shp(in_shp, verbose=False):
    """Deletes a shapefile.

    Args:
        in_shp (str): The input shapefile to delete.
        verbose (bool, optional): Whether to print out descriptive text. Defaults to False.
    """
    from pathlib import Path

    in_shp = os.path.abspath(in_shp)
    in_dir = os.path.dirname(in_shp)
    basename = os.path.basename(in_shp).replace(".shp", "")

    files = Path(in_dir).rglob(basename + ".*")

    for file in files:
        filepath = os.path.join(in_dir, str(file))
        try:
            os.remove(filepath)
            if verbose:
                print(f"Deleted {filepath}")
        except Exception as e:
            if verbose:
                print(e)


def df_to_ee(df, latitude="latitude", longitude="longitude", **kwargs):
    """Converts a pandas DataFrame to ee.FeatureCollection.

    Args:
        df (pandas.DataFrame): An input pandas.DataFrame.
        latitude (str, optional): Column name for the latitude column. Defaults to 'latitude'.
        longitude (str, optional): Column name for the longitude column. Defaults to 'longitude'.

    Raises:
        TypeError: The input data type must be pandas.DataFrame.

    Returns:
        ee.FeatureCollection: The ee.FeatureCollection converted from the input pandas DataFrame.
    """
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        raise TypeError("The input data type must be pandas.DataFrame.")

    geojson = df_to_geojson(df, latitude=latitude, longitude=longitude)
    fc = geojson_to_ee(geojson)

    return fc


pandas_to_ee = df_to_ee


def gdf_to_ee(gdf, geodesic=True, date=None, date_format="YYYY-MM-dd"):
    """Converts a GeoPandas GeoDataFrame to ee.FeatureCollection.

    Args:
        gdf (geopandas.GeoDataFrame): The input geopandas.GeoDataFrame to be converted ee.FeatureCollection.
        geodesic (bool, optional): Whether line segments should be interpreted as spherical geodesics. If false, indicates that line segments should be interpreted as planar lines in the specified CRS. If absent, defaults to true if the CRS is geographic (including the default EPSG:4326), or to false if the CRS is projected. Defaults to True.
        date (str, optional): Column name for the date column. Defaults to None.
        date_format (str, optional): Date format. A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html. Defaults to 'YYYY-MM-dd'.

    Raises:
        TypeError: The input data type must be geopandas.GeoDataFrame.

    Returns:
        ee.FeatureCollection: The output ee.FeatureCollection converted from the input geopandas.GeoDataFrame.
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("The input data type must be geopandas.GeoDataFrame.")

    out_json = os.path.join(os.getcwd(), random_string(6) + ".geojson")
    gdf = gdf.to_crs(4326)
    gdf.to_file(out_json, driver="GeoJSON")

    fc = geojson_to_ee(out_json, geodesic=geodesic)

    if date is not None:
        try:
            fc = fc.map(
                lambda x: x.set(
                    "system:time_start",
                    ee.Date.parse(date_format, x.get(date)).millis(),
                )
            )
        except Exception as e:
            raise Exception(e)

    os.remove(out_json)

    return fc


geopandas_to_ee = gdf_to_ee


def vector_to_geojson(
    filename, out_geojson=None, bbox=None, mask=None, rows=None, epsg="4326", **kwargs
):
    """Converts any geopandas-supported vector dataset to GeoJSON.

    Args:
        filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
        out_geojson (str, optional): The file path to the output GeoJSON. Defaults to None.
        bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
        mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter for features that intersect with the given dict-like geojson geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox. Defaults to None.
        rows (int or slice, optional): Load in specific rows by passing an integer (first n rows) or a slice() object.. Defaults to None.
        epsg (str, optional): The EPSG number to convert to. Defaults to "4326".

    Raises:
        ValueError: When the output file path is invalid.

    Returns:
        dict: A dictionary containing the GeoJSON.
    """

    warnings.filterwarnings("ignore")
    check_package(name="geopandas", URL="https://geopandas.org")
    import geopandas as gpd
    import fiona

    if not filename.startswith("http"):
        filename = os.path.abspath(filename)
    else:
        filename = download_file(github_raw_url(filename))
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".kml":
        fiona.drvsupport.supported_drivers["KML"] = "rw"
        df = gpd.read_file(
            filename, bbox=bbox, mask=mask, rows=rows, driver="KML", **kwargs
        )
    else:
        df = gpd.read_file(filename, bbox=bbox, mask=mask, rows=rows, **kwargs)
    gdf = df.to_crs(epsg=epsg)

    if out_geojson is not None:
        if not out_geojson.lower().endswith(".geojson"):
            raise ValueError("The output file must have a geojson file extension.")

        out_geojson = os.path.abspath(out_geojson)
        out_dir = os.path.dirname(out_geojson)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        gdf.to_file(out_geojson, driver="GeoJSON")

    else:
        return gdf.__geo_interface__


def vector_to_ee(
    filename,
    bbox=None,
    mask=None,
    rows=None,
    geodesic=True,
    **kwargs,
):
    """Converts any geopandas-supported vector dataset to ee.FeatureCollection.

    Args:
        filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
        bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
        mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter for features that intersect with the given dict-like geojson geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox. Defaults to None.
        rows (int or slice, optional): Load in specific rows by passing an integer (first n rows) or a slice() object.. Defaults to None.
        geodesic (bool, optional): Whether line segments should be interpreted as spherical geodesics. If false, indicates that line segments should be interpreted as planar lines in the specified CRS. If absent, defaults to true if the CRS is geographic (including the default EPSG:4326), or to false if the CRS is projected.

    Returns:
        ee.FeatureCollection: Earth Engine FeatureCollection.
    """
    geojson = vector_to_geojson(
        filename, bbox=bbox, mask=mask, rows=rows, epsg="4326", **kwargs
    )

    return geojson_to_ee(geojson, geodesic=geodesic)


def extract_pixel_values(
    ee_object, region, scale=None, projection=None, tileScale=1, getInfo=False
):
    """Samples the pixels of an image, returning them as a ee.Dictionary.

    Args:
        ee_object (ee.Image | ee.ImageCollection): The ee.Image or ee.ImageCollection to sample.
        region (ee.Geometry): The region to sample from. If unspecified, uses the image's whole footprint.
        scale (float, optional): A nominal scale in meters of the projection to sample in. Defaults to None.
        projection (str, optional): The projection in which to sample. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        tileScale (int, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.
        getInfo (bool, optional): Whether to use getInfo with the results, i.e., returning the values a list. Default to False.

    Raises:
        TypeError: The image must be an instance of ee.Image.
        TypeError: Region must be an instance of ee.Geometry.

    Returns:
        ee.Dictionary: The dictionary containing band names and pixel values.
    """
    if isinstance(ee_object, ee.ImageCollection):
        ee_object = ee_object.toBands()

    if not isinstance(ee_object, ee.Image):
        raise TypeError("The image must be an instance of ee.Image.")

    if not isinstance(region, ee.Geometry):
        raise TypeError("Region must be an instance of ee.Geometry.")

    dict_values = (
        ee_object.sample(region, scale, projection, tileScale=tileScale)
        .first()
        .toDictionary()
    )

    if getInfo:
        band_names = ee_object.bandNames().getInfo()
        values_tmp = dict_values.getInfo()
        values = [values_tmp[i] for i in band_names]
        return dict(zip(band_names, values))
    else:
        return dict_values


def list_vars(var_type=None):
    """Lists all defined avariables.

    Args:
        var_type (object, optional): The object type of variables to list. Defaults to None.

    Returns:
        list: A list of all defined variables.
    """
    result = []

    for var in globals():
        reserved_vars = [
            "In",
            "Out",
            "get_ipython",
            "exit",
            "quit",
            "json",
            "getsizeof",
            "NamespaceMagics",
            "np",
            "var_dic_list",
            "list_vars",
            "ee",
            "geemap",
        ]

        if (not var.startswith("_")) and (var not in reserved_vars):
            if var_type is not None and isinstance(eval(var), var_type):
                result.append(var)
            elif var_type is None:
                result.append(var)

    return result


def extract_transect(
    image,
    line,
    reducer="mean",
    n_segments=100,
    dist_interval=None,
    scale=None,
    crs=None,
    crsTransform=None,
    tileScale=1.0,
    to_pandas=False,
    **kwargs,
):
    """Extracts transect from an image. Credits to Gena for providing the JavaScript example https://code.earthengine.google.com/b09759b8ac60366ee2ae4eccdd19e615.

    Args:
        image (ee.Image): The image to extract transect from.
        line (ee.Geometry.LineString): The LineString used to extract transect from an image.
        reducer (str, optional): The ee.Reducer to use, e.g., 'mean', 'median', 'min', 'max', 'stdDev'. Defaults to "mean".
        n_segments (int, optional): The number of segments that the LineString will be split into. Defaults to 100.
        dist_interval (float, optional): The distance interval used for splitting the LineString. If specified, the n_segments parameter will be ignored. Defaults to None.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        crs (ee.Projection, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        crsTransform (list, optional): The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and will replace any transform already set on the projection. Defaults to None.
        tileScale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.
        to_pandas (bool, optional): Whether to convert the result to a pandas dataframe. Default to False.

    Raises:
        TypeError: If the geometry type is not LineString.
        Exception: If the program fails to compute.

    Returns:
        ee.FeatureCollection: The FeatureCollection containing the transect with distance and reducer values.
    """
    try:
        geom_type = line.type().getInfo()
        if geom_type != "LineString":
            raise TypeError("The geometry type must be LineString.")

        reducer = eval("ee.Reducer." + reducer + "()")
        maxError = image.projection().nominalScale().divide(5)

        length = line.length(maxError)
        if dist_interval is None:
            dist_interval = length.divide(n_segments)

        distances = ee.List.sequence(0, length, dist_interval)
        lines = line.cutLines(distances, maxError).geometries()

        def set_dist_attr(l):
            l = ee.List(l)
            geom = ee.Geometry(l.get(0))
            distance = ee.Number(l.get(1))
            geom = ee.Geometry.LineString(geom.coordinates())
            return ee.Feature(geom, {"distance": distance})

        lines = lines.zip(distances).map(set_dist_attr)
        lines = ee.FeatureCollection(lines)

        transect = image.reduceRegions(
            **{
                "collection": ee.FeatureCollection(lines),
                "reducer": reducer,
                "scale": scale,
                "crs": crs,
                "crsTransform": crsTransform,
                "tileScale": tileScale,
            }
        )

        if to_pandas:
            return ee_to_df(transect)
        return transect

    except Exception as e:
        raise Exception(e)


def random_sampling(
    image,
    region=None,
    scale=None,
    projection=None,
    factor=None,
    numPixels=None,
    seed=0,
    dropNulls=True,
    tileScale=1.0,
    geometries=True,
    to_pandas=False,
):
    """Samples the pixels of an image, returning them as a FeatureCollection. Each feature will have 1 property per band in the input image. Note that the default behavior is to drop features that intersect masked pixels, which result in null-valued properties (see dropNulls argument).

    Args:
        image (ee.Image): The image to sample.
        region (ee.Geometry, optional): The region to sample from. If unspecified, uses the image's whole footprint. Defaults to None.
        scale (float, optional): A nominal scale in meters of the projection to sample in.. Defaults to None.
        projection (ee.Projection, optional): The projection in which to sample. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.. Defaults to None.
        factor (float, optional): A subsampling factor, within (0, 1]. If specified, 'numPixels' must not be specified. Defaults to no subsampling. Defaults to None.
        numPixels (int, optional): The approximate number of pixels to sample. If specified, 'factor' must not be specified. Defaults to None.
        seed (int, optional): A randomization seed to use for subsampling. Defaults to True. Defaults to 0.
        dropNulls (bool, optional): Post filter the result to drop features that have null-valued properties. Defaults to True.
        tileScale (float, optional): Post filter the result to drop features that have null-valued properties. Defaults to 1.
        geometries (bool, optional): If true, adds the center of the sampled pixel as the geometry property of the output feature. Otherwise, geometries will be omitted (saving memory). Defaults to True.
        to_pandas (bool, optional): Whether to return the result as a pandas dataframe. Defaults to False.

    Raises:
        TypeError: If the input image is not an ee.Image.

    Returns:
        ee.FeatureCollection: Random sampled points.
    """
    if not isinstance(image, ee.Image):
        raise TypeError("The image must be ee.Image")

    points = image.sample(
        **{
            "region": region,
            "scale": scale,
            "projection": projection,
            "factor": factor,
            "numPixels": numPixels,
            "seed": seed,
            "dropNulls": dropNulls,
            "tileScale": tileScale,
            "geometries": geometries,
        }
    )

    if to_pandas:
        return ee_to_df(points)
    else:
        return points


def osm_to_gdf(
    query,
    which_result=None,
    by_osmid=False,
    buffer_dist=None,
):
    """Retrieves place(s) by name or ID from the Nominatim API as a GeoDataFrame.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        which_result (INT, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.

    Returns:
        GeoDataFrame: A GeoPandas GeoDataFrame.
    """
    check_package(
        "geopandas", "https://geopandas.org/getting_started.html#installation"
    )
    check_package("osmnx", "https://osmnx.readthedocs.io/en/stable/")

    try:
        import osmnx as ox

        gdf = ox.geocode_to_gdf(query, which_result, by_osmid, buffer_dist)
        return gdf
    except Exception as e:
        raise Exception(e)


osm_to_geopandas = osm_to_gdf


def osm_to_ee(
    query, which_result=None, by_osmid=False, buffer_dist=None, geodesic=True
):
    """Retrieves place(s) by name or ID from the Nominatim API as an ee.FeatureCollection.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        which_result (INT, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.
        geodesic (bool, optional): Whether line segments should be interpreted as spherical geodesics. If false, indicates that line segments should be interpreted as planar lines in the specified CRS. If absent, defaults to true if the CRS is geographic (including the default EPSG:4326), or to false if the CRS is projected.

    Returns:
        ee.FeatureCollection: An Earth Engine FeatureCollection.
    """
    gdf = osm_to_gdf(query, which_result, by_osmid, buffer_dist)
    fc = gdf_to_ee(gdf, geodesic)
    return fc


def osm_to_geojson(query, which_result=None, by_osmid=False, buffer_dist=None):
    """Retrieves place(s) by name or ID from the Nominatim API as an ee.FeatureCollection.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        which_result (INT, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.

    Returns:
        ee.FeatureCollection: An Earth Engine FeatureCollection.
    """
    gdf = osm_to_gdf(query, which_result, by_osmid, buffer_dist)
    return gdf.__geo_interface__


def planet_monthly_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet monthly imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    # from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = datetime.date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))

    links = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/planet_medres_normalized_analytic_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2020, year_now + 1):
        for month in range(1, 13):
            m_str = str(year) + "-" + str(month).zfill(2)

            if year == 2020 and month < 9:
                continue
            if year == year_now and month >= month_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            links.append(url)

    return links


def planet_biannual_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    dates = [
        "2015-12_2016-05",
        "2016-06_2016-11",
        "2016-12_2017-05",
        "2017-06_2017-11",
        "2017-12_2018-05",
        "2018-06_2018-11",
        "2018-12_2019-05",
        "2019-06_2019-11",
        "2019-12_2020-05",
        "2020-06_2020-08",
    ]

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/planet_medres_normalized_analytic_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for d in dates:
        url = f"{prefix}{d}{subfix}{api_key}"
        link.append(url)

    return link


def planet_catalog_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual and monthly imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Returns:
        list: A list of tile URLs.
    """
    biannual = planet_biannual_tropical(api_key, token_name)
    monthly = planet_monthly_tropical(api_key, token_name)
    return biannual + monthly


def planet_monthly_tiles_tropical(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  monthly imagery TileLayer based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """
    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    link = planet_monthly_tropical(api_key, token_name)
    for url in link:
        index = url.find("20")
        name = "Planet_" + url[index : index + 7]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles


def planet_biannual_tiles_tropical(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  bi-annual imagery TileLayer based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    link = planet_biannual_tropical(api_key, token_name)
    for url in link:
        index = url.find("20")
        name = "Planet_" + url[index : index + 15]
        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )
        tiles[name] = tile

    return tiles


def planet_tiles_tropical(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  monthly imagery TileLayer based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    catalog = {}
    biannul = planet_biannual_tiles_tropical(api_key, token_name, tile_format)
    monthly = planet_monthly_tiles_tropical(api_key, token_name, tile_format)

    for key in biannul:
        catalog[key] = biannul[key]

    for key in monthly:
        catalog[key] = monthly[key]

    return catalog


def planet_monthly(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet monthly imagery URLs based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    # from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = datetime.date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_monthly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2016, year_now + 1):
        for month in range(1, 13):
            m_str = str(year) + "_" + str(month).zfill(2)

            if year == year_now and month >= month_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            link.append(url)

    return link


def planet_quarterly(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet quarterly imagery URLs based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    # from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = datetime.date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))
    quarter_now = (month_now - 1) // 3 + 1

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_quarterly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2016, year_now + 1):
        for quarter in range(1, 5):
            m_str = str(year) + "q" + str(quarter)

            if year == year_now and quarter >= quarter_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            link.append(url)

    return link


def planet_catalog(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual and monthly imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Returns:
        list: A list of tile URLs.
    """
    quarterly = planet_quarterly(api_key, token_name)
    monthly = planet_monthly(api_key, token_name)
    return quarterly + monthly


def planet_monthly_tiles(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  monthly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """
    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    link = planet_monthly(api_key, token_name)

    for url in link:
        index = url.find("20")
        name = "Planet_" + url[index : index + 7]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles


def planet_quarterly_tiles(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  quarterly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """
    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    links = planet_quarterly(api_key, token_name)

    for url in links:
        index = url.find("20")
        name = "Planet_" + url[index : index + 6]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles


def planet_tiles(api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"):
    """Generates Planet imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    catalog = {}
    quarterly = planet_quarterly_tiles(api_key, token_name, tile_format)
    monthly = planet_monthly_tiles(api_key, token_name, tile_format)

    for key in quarterly:
        catalog[key] = quarterly[key]

    for key in monthly:
        catalog[key] = monthly[key]

    return catalog


def planet_by_quarter(
    year=2016,
    quarter=1,
    api_key=None,
    token_name="PLANET_API_KEY",
):
    """Gets Planet global mosaic tile url by quarter. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        quarter (int, optional): The quarter of Planet global mosaic, must be 1-4. Defaults to 1.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: The Planet API key is not provided.
        ValueError: The year is invalid.
        ValueError: The quarter is invalid.
        ValueError: The quarter is invalid.

    Returns:
        str: A Planet global mosaic tile url.
    """
    # from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = datetime.date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))
    quarter_now = (month_now - 1) // 3 + 1

    if year > year_now:
        raise ValueError(f"Year must be between 2016 and {year_now}.")
    elif year == year_now and quarter >= quarter_now:
        raise ValueError(f"Quarter must be less than {quarter_now} for year {year_now}")

    if quarter < 1 or quarter > 4:
        raise ValueError("Quarter must be between 1 and 4.")

    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_quarterly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    m_str = str(year) + "q" + str(quarter)
    url = f"{prefix}{m_str}{subfix}{api_key}"

    return url


def planet_by_month(
    year=2016,
    month=1,
    api_key=None,
    token_name="PLANET_API_KEY",
):
    """Gets Planet global mosaic tile url by month. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        month (int, optional): The month of Planet global mosaic, must be 1-12. Defaults to 1.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: The Planet API key is not provided.
        ValueError: The year is invalid.
        ValueError: The month is invalid.
        ValueError: The month is invalid.

    Returns:
        str: A Planet global mosaic tile url.
    """
    # from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = datetime.date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))
    # quarter_now = (month_now - 1) // 3 + 1

    if year > year_now:
        raise ValueError(f"Year must be between 2016 and {year_now}.")
    elif year == year_now and month >= month_now:
        raise ValueError(f"Month must be less than {month_now} for year {year_now}")

    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")

    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_monthly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    m_str = str(year) + "_" + str(month).zfill(2)
    url = f"{prefix}{m_str}{subfix}{api_key}"

    return url


def planet_tile_by_quarter(
    year=2016,
    quarter=1,
    name=None,
    api_key=None,
    token_name="PLANET_API_KEY",
    tile_format="ipyleaflet",
):
    """Generates Planet quarterly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        quarter (int, optional): The quarter of Planet global mosaic, must be 1-4. Defaults to 1.
        name (str, optional): The layer name to use. Defaults to None.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    url = planet_by_quarter(year, quarter, api_key, token_name)

    if name is None:
        name = "Planet_" + str(year) + "_q" + str(quarter)

    if tile_format == "ipyleaflet":
        tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
    else:
        tile = folium.TileLayer(
            tiles=url,
            attr="Planet",
            name=name,
            overlay=True,
            control=True,
        )

    return tile


def planet_tile_by_month(
    year=2016,
    month=1,
    name=None,
    api_key=None,
    token_name="PLANET_API_KEY",
    tile_format="ipyleaflet",
):
    """Generates Planet monthly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        month (int, optional): The month of Planet global mosaic, must be 1-12. Defaults to 1.
        name (str, optional): The layer name to use. Defaults to None.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """
    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    url = planet_by_month(year, month, api_key, token_name)

    if name is None:
        name = "Planet_" + str(year) + "_" + str(month).zfill(2)

    if tile_format == "ipyleaflet":
        tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
    else:
        tile = folium.TileLayer(
            tiles=url,
            attr="Planet",
            name=name,
            overlay=True,
            control=True,
        )

    return tile


def get_current_latlon():
    """Get the current latitude and longitude based on the user's location."""
    import geocoder

    g = geocoder.ip("me")
    props = g.geojson["features"][0]["properties"]
    lat = props["lat"]
    lon = props["lng"]
    return lat, lon


def get_census_dict(reset=False):
    """Returns a dictionary of Census data.

    Args:
        reset (bool, optional): Reset the dictionary. Defaults to False.

    Returns:
        dict: A dictionary of Census data.
    """
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    census_data = os.path.join(pkg_dir, "data/census_data.json")

    if reset:
        try:
            from owslib.wms import WebMapService
        except ImportError:
            raise ImportError(
                'The owslib package must be installed to use this function. Install with "pip install owslib"'
            )

        census_dict = {}

        names = [
            "Current",
            "ACS 2021",
            "ACS 2019",
            "ACS 2018",
            "ACS 2017",
            "ACS 2016",
            "ACS 2015",
            "ACS 2014",
            "ACS 2013",
            "ACS 2012",
            "ECON 2012",
            "Census 2020",
            "Census 2010",
            "Physical Features",
            "Decennial Census 2020",
            "Decennial Census 2010",
            "Decennial Census 2000",
            "Decennial Physical Features",
        ]

        links = {}

        print("Retrieving data. Please wait ...")
        for name in names:
            if "Decennial" not in name:
                links[name] = (
                    f"https://tigerweb.geo.census.gov/arcgis/services/TIGERweb/tigerWMS_{name.replace(' ', '')}/MapServer/WMSServer"
                )
            else:
                links[name] = (
                    f"https://tigerweb.geo.census.gov/arcgis/services/Census2020/tigerWMS_{name.replace('Decennial', '').replace(' ', '')}/MapServer/WMSServer"
                )

            wms = WebMapService(links[name], timeout=300)
            layers = list(wms.contents)
            layers.sort()
            census_dict[name] = {
                "url": links[name],
                "layers": layers,
                # "title": wms.identification.title,
                # "abstract": wms.identification.abstract,
            }

        with open(census_data, "w") as f:
            json.dump(census_dict, f, indent=4)

    else:
        with open(census_data, "r") as f:
            census_dict = json.load(f)

    return census_dict


def search_xyz_services(keyword, name=None, list_only=True, add_prefix=True):
    """Search for XYZ tile providers from xyzservices.

    Args:
        keyword (str): The keyword to search for.
        name (str, optional): The name of the xyz tile. Defaults to None.
        list_only (bool, optional): If True, only the list of services will be returned. Defaults to True.
        add_prefix (bool, optional): If True, the prefix "xyz." will be added to the service name. Defaults to True.

    Returns:
        list: A list of XYZ tile providers.
    """

    import xyzservices.providers as xyz

    if name is None:
        providers = xyz.filter(keyword=keyword).flatten()
    else:
        providers = xyz.filter(name=name).flatten()

    if list_only:
        if add_prefix:
            return ["xyz." + provider for provider in providers]
        else:
            return [provider for provider in providers]
    else:
        return providers


def search_qms(keyword, limit=10, list_only=True, add_prefix=True, timeout=300):
    """Search for QMS tile providers from Quick Map Services.

    Args:
        keyword (str): The keyword to search for.
        limit (int, optional): The maximum number of results to return. Defaults to 10.
        list_only (bool, optional): If True, only the list of services will be returned. Defaults to True.
        add_prefix (bool, optional): If True, the prefix "qms." will be added to the service name. Defaults to True.
        timeout (int, optional): The timeout in seconds. Defaults to 300.

    Returns:
        list: A list of QMS tile providers.
    """

    QMS_API = "https://qms.nextgis.com/api/v1/geoservices"
    services = requests.get(
        f"{QMS_API}/?search={keyword}&type=tms&epsg=3857&limit={limit}", timeout=timeout
    )
    services = services.json()
    if services["results"]:
        providers = services["results"]
        if list_only:
            if add_prefix:
                return ["qms." + provider["name"] for provider in providers]
            else:
                return [provider["name"] for provider in providers]
        else:
            return providers
    else:
        return None


def get_wms_layers(url, return_titles=False):
    """Returns a list of WMS layers from a WMS service.

    Args:
        url (str): The URL of the WMS service.
        return_titles (bool, optional): If True, the titles of the layers will be returned. Defaults to False.

    Returns:
        list: A list of WMS layers.
    """
    from owslib.wms import WebMapService

    wms = WebMapService(url)
    layers = list(wms.contents)
    layers.sort()
    if return_titles:
        return layers, [wms[layer].title for layer in layers]
    else:
        return layers


def read_file_from_url(url, return_type="list", encoding="utf-8"):
    """Reads a file from a URL.

    Args:
        url (str): The URL of the file.
        return_type (str, optional): The return type, can either be string or list. Defaults to "list".
        encoding (str, optional): The encoding of the file. Defaults to "utf-8".

    Raises:
        ValueError: The return type must be either list or string.

    Returns:
        str | list: The contents of the file.
    """
    from urllib.request import urlopen

    if return_type == "list":
        return [line.decode(encoding).rstrip() for line in urlopen(url).readlines()]
    elif return_type == "string":
        return urlopen(url).read().decode(encoding)
    else:
        raise ValueError("The return type must be either list or string.")


def create_download_button(
    label,
    data,
    file_name=None,
    mime=None,
    key=None,
    help=None,
    on_click=None,
    args=None,
    **kwargs,
):
    """Streamlit function to create a download button.

    Args:
        label (str): A short label explaining to the user what this button is for..
        data (str | list): The contents of the file to be downloaded. See example below for caching techniques to avoid recomputing this data unnecessarily.
        file_name (str, optional): An optional string to use as the name of the file to be downloaded, such as 'my_file.csv'. If not specified, the name will be automatically generated. Defaults to None.
        mime (str, optional): The MIME type of the data. If None, defaults to "text/plain" (if data is of type str or is a textual file) or "application/octet-stream" (if data is of type bytes or is a binary file). Defaults to None.
        key (str, optional): An optional string or integer to use as the unique key for the widget. If this is omitted, a key will be generated for the widget based on its content. Multiple widgets of the same type may not share the same key. Defaults to None.
        help (str, optional): An optional tooltip that gets displayed when the button is hovered over. Defaults to None.
        on_click (str, optional): An optional callback invoked when this button is clicked. Defaults to None.
        args (list, optional): An optional tuple of args to pass to the callback. Defaults to None.
        kwargs (dict, optional): An optional tuple of args to pass to the callback.

    """
    try:
        import streamlit as st
        import pandas as pd

        if isinstance(data, str):
            if file_name is None:
                file_name = data.split("/")[-1]

            if data.endswith(".csv"):
                data = pd.read_csv(data).to_csv()
                if mime is None:
                    mime = "text/csv"
                return st.download_button(
                    label, data, file_name, mime, key, help, on_click, args, **kwargs
                )
            elif (
                data.endswith(".gif") or data.endswith(".png") or data.endswith(".jpg")
            ):
                if mime is None:
                    mime = f"image/{os.path.splitext(data)[1][1:]}"

                with open(data, "rb") as file:
                    return st.download_button(
                        label,
                        file,
                        file_name,
                        mime,
                        key,
                        help,
                        on_click,
                        args,
                        **kwargs,
                    )

            else:
                return st.download_button(
                    label,
                    label,
                    data,
                    file_name,
                    mime,
                    key,
                    help,
                    on_click,
                    args,
                    **kwargs,
                )

    except ImportError:
        print("Streamlit is not installed. Please run 'pip install streamlit'.")
        return
    except Exception as e:
        raise Exception(e)


def gdf_to_geojson(gdf, out_geojson=None, epsg=None):
    """Converts a GeoDataFame to GeoJSON.

    Args:
        gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
        out_geojson (str, optional): File path to he output GeoJSON. Defaults to None.
        epsg (str, optional): An EPSG string, e.g., "4326". Defaults to None.

    Raises:
        TypeError: When the output file extension is incorrect.
        Exception: When the conversion fails.

    Returns:
        dict: When the out_json is None returns a dict.
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    try:
        if epsg is not None:
            gdf = gdf.to_crs(epsg=epsg)
        geojson = gdf.__geo_interface__

        if out_geojson is None:
            return geojson
        else:
            ext = os.path.splitext(out_geojson)[1]
            if ext.lower() not in [".json", ".geojson"]:
                raise TypeError(
                    "The output file extension must be either .json or .geojson"
                )
            out_dir = os.path.dirname(out_geojson)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            gdf.to_file(out_geojson, driver="GeoJSON")
    except Exception as e:
        raise Exception(e)


def get_temp_dir():
    """Returns the temporary directory.

    Returns:
        str: The temporary directory.
    """

    import tempfile

    return tempfile.gettempdir()


def create_contours(
    image, min_value, max_value, interval, kernel=None, region=None, values=None
):
    """Creates contours from an image. Code adapted from https://mygeoblog.com/2017/01/28/contour-lines-in-gee. Credits to MyGeoBlog.

    Args:
        image (ee.Image): An image to create contours.
        min_value (float): The minimum value of contours.
        max_value (float): The maximum value of contours.
        interval (float):  The interval between contours.
        kernel (ee.Kernel, optional): The kernel to use for smoothing image. Defaults to None.
        region (ee.Geometry | ee.FeatureCollection, optional): The region of interest. Defaults to None.
        values (list, optional): A list of values to create contours for. Defaults to None.

    Raises:
        TypeError: The image must be an ee.Image.
        TypeError: The region must be an ee.Geometry or ee.FeatureCollection.

    Returns:
        ee.Image: The image containing contours.
    """
    if not isinstance(image, ee.Image):
        raise TypeError("The image must be an ee.Image.")
    if region is not None:
        if isinstance(region, ee.FeatureCollection) or isinstance(region, ee.Geometry):
            pass
        else:
            raise TypeError(
                "The region must be an ee.Geometry or ee.FeatureCollection."
            )

    if kernel is None:
        kernel = ee.Kernel.gaussian(5, 3)

    if isinstance(values, list):
        values = ee.List(values)
    elif isinstance(values, ee.List):
        pass

    if values is None:
        values = ee.List.sequence(min_value, max_value, interval)

    def contouring(value):
        mycountour = (
            image.convolve(kernel)
            .subtract(ee.Image.constant(value))
            .zeroCrossing()
            .multiply(ee.Image.constant(value).toFloat())
        )
        return mycountour.mask(mycountour)

    contours = values.map(contouring)

    if region is not None:
        if isinstance(region, ee.FeatureCollection):
            return ee.ImageCollection(contours).mosaic().clipToCollection(region)
        elif isinstance(region, ee.Geometry):
            return ee.ImageCollection(contours).mosaic().clip(region)
    else:
        return ee.ImageCollection(contours).mosaic()


def get_local_tile_layer(
    source,
    port="default",
    debug=False,
    indexes=None,
    colormap=None,
    vmin=None,
    vmax=None,
    nodata=None,
    attribution=None,
    tile_format="ipyleaflet",
    layer_name="Local COG",
    return_client=False,
    quiet=False,
    **kwargs,
):
    """Generate an ipyleaflet/folium TileLayer from a local raster dataset or remote Cloud Optimized GeoTIFF (COG).
        If you are using this function in JupyterHub on a remote server and the raster does not render properly, try
        running the following two lines before calling this function:

        import os
        os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'

    Args:
        source (str): The path to the GeoTIFF file or the URL of the Cloud Optimized GeoTIFF.
        port (str, optional): The port to use for the server. Defaults to "default".
        debug (bool, optional): If True, the server will be started in debug mode. Defaults to False.
        indexes (int, optional): The band(s) to use. Band indexing starts at 1. Defaults to None.
        colormap (str, optional): The name of the colormap from `matplotlib` to use when plotting a single band. See https://matplotlib.org/stable/gallery/color/colormap_reference.html. Default is greyscale.
        vmin (float, optional): The minimum value to use when colormapping the colormap when plotting a single band. Defaults to None.
        vmax (float, optional): The maximum value to use when colormapping the colormap when plotting a single band. Defaults to None.
        nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
        attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
        tile_format (str, optional): The tile layer format. Can be either ipyleaflet or folium. Defaults to "ipyleaflet".
        layer_name (str, optional): The layer name to use. Defaults to None.
        return_client (bool, optional): If True, the tile client will be returned. Defaults to False.
        quiet (bool, optional): If True, the error messages will be suppressed. Defaults to False.

    Returns:
        ipyleaflet.TileLayer | folium.TileLayer: An ipyleaflet.TileLayer or folium.TileLayer.
    """
    import rasterio

    check_package(
        "localtileserver", URL="https://github.com/banesullivan/localtileserver"
    )

    # Handle legacy localtileserver kwargs
    if "cmap" in kwargs:
        warnings.warn(
            "`cmap` is a deprecated keyword argument for get_local_tile_layer. Please use `colormap`."
        )
    if "palette" in kwargs:
        warnings.warn(
            "`palette` is a deprecated keyword argument for get_local_tile_layer. Please use `colormap`."
        )
    if "band" in kwargs or "bands" in kwargs:
        warnings.warn(
            "`band` and `bands` are deprecated keyword arguments for get_local_tile_layer. Please use `indexes`."
        )
    if "projection" in kwargs:
        warnings.warn(
            "`projection` is a deprecated keyword argument for get_local_tile_layer and will be ignored."
        )
    if "style" in kwargs:
        warnings.warn(
            "`style` is a deprecated keyword argument for get_local_tile_layer and will be ignored."
        )

    if "max_zoom" not in kwargs:
        kwargs["max_zoom"] = 30
    if "max_native_zoom" not in kwargs:
        kwargs["max_native_zoom"] = 30
    if "cmap" in kwargs:
        colormap = kwargs.pop("cmap")
    if "palette" in kwargs:
        colormap = kwargs.pop("palette")
    if "band" in kwargs:
        indexes = kwargs.pop("band")
    if "bands" in kwargs:
        indexes = kwargs.pop("bands")

    # Make it compatible with binder and JupyterHub
    if os.environ.get("JUPYTERHUB_SERVICE_PREFIX") is not None:
        os.environ["LOCALTILESERVER_CLIENT_PREFIX"] = (
            f"{os.environ['JUPYTERHUB_SERVICE_PREFIX'].lstrip('/')}/proxy/{{port}}"
        )

    if is_studio_lab():
        os.environ["LOCALTILESERVER_CLIENT_PREFIX"] = (
            f"studiolab/default/jupyter/proxy/{{port}}"
        )
    elif is_on_aws():
        os.environ["LOCALTILESERVER_CLIENT_PREFIX"] = "proxy/{port}"
    elif "prefix" in kwargs:
        os.environ["LOCALTILESERVER_CLIENT_PREFIX"] = kwargs["prefix"]
        kwargs.pop("prefix")

    from localtileserver import (
        get_leaflet_tile_layer,
        get_folium_tile_layer,
        TileClient,
    )

    # if "show_loading" not in kwargs:
    #     kwargs["show_loading"] = False

    if isinstance(source, str):
        if not source.startswith("http"):
            if source.startswith("~"):
                source = os.path.expanduser(source)
            # else:
            #     source = os.path.abspath(source)
            # if not os.path.exists(source):
            #     raise ValueError("The source path does not exist.")
        else:
            source = github_raw_url(source)
    elif isinstance(source, TileClient) or isinstance(
        source, rasterio.io.DatasetReader
    ):
        pass

    else:
        raise ValueError("The source must either be a string or TileClient")

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    if layer_name is None:
        if source.startswith("http"):
            layer_name = "RemoteTile_" + random_string(3)
        else:
            layer_name = "LocalTile_" + random_string(3)

    if isinstance(source, str) or isinstance(source, rasterio.io.DatasetReader):
        tile_client = TileClient(source, port=port, debug=debug)
    else:
        tile_client = source

    if quiet:
        output = widgets.Output()
        with output:
            if tile_format == "ipyleaflet":
                tile_layer = get_leaflet_tile_layer(
                    tile_client,
                    port=port,
                    debug=debug,
                    indexes=indexes,
                    colormap=colormap,
                    vmin=vmin,
                    vmax=vmax,
                    nodata=nodata,
                    attribution=attribution,
                    name=layer_name,
                    **kwargs,
                )
            else:
                tile_layer = get_folium_tile_layer(
                    tile_client,
                    port=port,
                    debug=debug,
                    indexes=indexes,
                    colormap=colormap,
                    vmin=vmin,
                    vmax=vmax,
                    nodata=nodata,
                    attr=attribution,
                    overlay=True,
                    name=layer_name,
                    **kwargs,
                )
    else:
        if tile_format == "ipyleaflet":
            tile_layer = get_leaflet_tile_layer(
                tile_client,
                port=port,
                debug=debug,
                indexes=indexes,
                colormap=colormap,
                vmin=vmin,
                vmax=vmax,
                nodata=nodata,
                attribution=attribution,
                name=layer_name,
                **kwargs,
            )
        else:
            tile_layer = get_folium_tile_layer(
                tile_client,
                port=port,
                debug=debug,
                indexes=indexes,
                colormap=colormap,
                vmin=vmin,
                vmax=vmax,
                nodata=nodata,
                attr=attribution,
                overlay=True,
                name=layer_name,
                **kwargs,
            )

    if return_client:
        return tile_layer, tile_client
    else:
        return tile_layer

    # center = tile_client.center()
    # bounds = tile_client.bounds()  # [ymin, ymax, xmin, xmax]
    # bounds = (bounds[2], bounds[0], bounds[3], bounds[1])  # [minx, miny, maxx, maxy]

    # if get_center and get_bounds:
    #     return tile_layer, center, bounds
    # elif get_center:
    #     return tile_layer, center
    # elif get_bounds:
    #     return tile_layer, bounds
    # else:
    #     return tile_layer


def get_palettable(types=None):
    """Get a list of palettable color palettes.

    Args:
        types (list, optional): A list of palettable types to return, e.g., types=['matplotlib', 'cartocolors']. Defaults to None.

    Returns:
        list: A list of palettable color palettes.
    """
    try:
        import palettable
    except ImportError:
        raise ImportError(
            "The palettable package is not installed. Please install it with `pip install palettable`."
        )

    if types is not None and (not isinstance(types, list)):
        raise ValueError("The types must be a list.")

    allowed_palettes = [
        "cartocolors",
        "cmocean",
        "colorbrewer",
        "cubehelix",
        "lightbartlein",
        "matplotlib",
        "mycarta",
        "scientific",
        "tableau",
        "wesanderson",
    ]

    if types is None:
        types = allowed_palettes[:]

    if all(x in allowed_palettes for x in types):
        pass
    else:
        raise ValueError(
            "The types must be one of the following: " + ", ".join(allowed_palettes)
        )

    palettes = []

    if "cartocolors" in types:
        cartocolors_diverging = [
            f"cartocolors.diverging.{c}"
            for c in dir(palettable.cartocolors.diverging)[:-19]
        ]
        cartocolors_qualitative = [
            f"cartocolors.qualitative.{c}"
            for c in dir(palettable.cartocolors.qualitative)[:-19]
        ]
        cartocolors_sequential = [
            f"cartocolors.sequential.{c}"
            for c in dir(palettable.cartocolors.sequential)[:-41]
        ]

        palettes = (
            palettes
            + cartocolors_diverging
            + cartocolors_qualitative
            + cartocolors_sequential
        )

    if "cmocean" in types:
        cmocean_diverging = [
            f"cmocean.diverging.{c}" for c in dir(palettable.cmocean.diverging)[:-19]
        ]
        cmocean_sequential = [
            f"cmocean.sequential.{c}" for c in dir(palettable.cmocean.sequential)[:-19]
        ]

        palettes = palettes + cmocean_diverging + cmocean_sequential

    if "colorbrewer" in types:
        colorbrewer_diverging = [
            f"colorbrewer.diverging.{c}"
            for c in dir(palettable.colorbrewer.diverging)[:-19]
        ]
        colorbrewer_qualitative = [
            f"colorbrewer.qualitative.{c}"
            for c in dir(palettable.colorbrewer.qualitative)[:-19]
        ]
        colorbrewer_sequential = [
            f"colorbrewer.sequential.{c}"
            for c in dir(palettable.colorbrewer.sequential)[:-41]
        ]

        palettes = (
            palettes
            + colorbrewer_diverging
            + colorbrewer_qualitative
            + colorbrewer_sequential
        )

    if "cubehelix" in types:
        cubehelix = [
            "classic_16",
            "cubehelix1_16",
            "cubehelix2_16",
            "cubehelix3_16",
            "jim_special_16",
            "perceptual_rainbow_16",
            "purple_16",
            "red_16",
        ]
        cubehelix = [f"cubehelix.{c}" for c in cubehelix]
        palettes = palettes + cubehelix

    if "lightbartlein" in types:
        lightbartlein_diverging = [
            f"lightbartlein.diverging.{c}"
            for c in dir(palettable.lightbartlein.diverging)[:-19]
        ]
        lightbartlein_sequential = [
            f"lightbartlein.sequential.{c}"
            for c in dir(palettable.lightbartlein.sequential)[:-19]
        ]

        palettes = palettes + lightbartlein_diverging + lightbartlein_sequential

    if "matplotlib" in types:
        matplotlib_colors = [
            f"matplotlib.{c}" for c in dir(palettable.matplotlib)[:-16]
        ]
        palettes = palettes + matplotlib_colors

    if "mycarta" in types:
        mycarta = [f"mycarta.{c}" for c in dir(palettable.mycarta)[:-16]]
        palettes = palettes + mycarta

    if "scientific" in types:
        scientific_diverging = [
            f"scientific.diverging.{c}"
            for c in dir(palettable.scientific.diverging)[:-19]
        ]
        scientific_sequential = [
            f"scientific.sequential.{c}"
            for c in dir(palettable.scientific.sequential)[:-19]
        ]

        palettes = palettes + scientific_diverging + scientific_sequential

    if "tableau" in types:
        tableau = [f"tableau.{c}" for c in dir(palettable.tableau)[:-14]]
        palettes = palettes + tableau

    return palettes


def connect_postgis(
    database, host="localhost", user=None, password=None, port=5432, use_env_var=False
):
    """Connects to a PostGIS database.

    Args:
        database (str): Name of the database
        host (str, optional): Hosting server for the database. Defaults to "localhost".
        user (str, optional): User name to access the database. Defaults to None.
        password (str, optional): Password to access the database. Defaults to None.
        port (int, optional): Port number to connect to at the server host. Defaults to 5432.
        use_env_var (bool, optional): Whether to use environment variables. It set to True, user and password are treated as an environment variables with default values user="SQL_USER" and password="SQL_PASSWORD". Defaults to False.

    Raises:
        ValueError: If user is not specified.
        ValueError: If password is not specified.

    Returns:
        [type]: [description]
    """
    check_package(name="geopandas", URL="https://geopandas.org")
    check_package(
        name="sqlalchemy",
        URL="https://docs.sqlalchemy.org/en/14/intro.html#installation",
    )

    from sqlalchemy import create_engine

    if use_env_var:
        if user is not None:
            user = os.getenv(user)
        else:
            user = os.getenv("SQL_USER")

        if password is not None:
            password = os.getenv(password)
        else:
            password = os.getenv("SQL_PASSWORD")

        if user is None:
            raise ValueError("user is not specified.")
        if password is None:
            raise ValueError("password is not specified.")

    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(connection_string)

    return engine


def read_postgis(sql, con, geom_col="geom", crs=None, **kwargs):
    """Reads data from a PostGIS database and returns a GeoDataFrame.

    Args:
        sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
        con (sqlalchemy.engine.Engine): Active connection to the database to query.
        geom_col (str, optional): Column name to convert to shapely geometries. Defaults to "geom".
        crs (str | dict, optional): CRS to use for the returned GeoDataFrame; if not set, tries to determine CRS from the SRID associated with the first geometry in the database, and assigns that to all geometries. Defaults to None.

    Returns:
        [type]: [description]
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    gdf = gpd.read_postgis(sql, con, geom_col, crs, **kwargs)
    return gdf


def postgis_to_ee(sql, con, geom_col="geom", crs=None, geodestic=False, **kwargs):
    """Reads data from a PostGIS database and returns a GeoDataFrame.

    Args:
        sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
        con (sqlalchemy.engine.Engine): Active connection to the database to query.
        geom_col (str, optional): Column name to convert to shapely geometries. Defaults to "geom".
        crs (str | dict, optional): CRS to use for the returned GeoDataFrame; if not set, tries to determine CRS from the SRID associated with the first geometry in the database, and assigns that to all geometries. Defaults to None.
        geodestic (bool, optional): Whether to use geodestic coordinates. Defaults to False.

    Returns:
        [type]: [description]
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    gdf = read_postgis(sql, con, geom_col, crs=crs, **kwargs)
    fc = gdf_to_ee(gdf, geodesic=geodestic)
    return fc


def points_from_xy(data, x="longitude", y="latitude", z=None, crs=None, **kwargs):
    """Create a GeoPandas GeoDataFrame from a csv or Pandas DataFrame containing x, y, z values.

    Args:
        data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
        x (str, optional): The column name for the x values. Defaults to "longitude".
        y (str, optional): The column name for the y values. Defaults to "latitude".
        z (str, optional): The column name for the z values. Defaults to None.
        crs (str | int, optional): The coordinate reference system for the GeoDataFrame. Defaults to None.

    Returns:
        geopandas.GeoDataFrame: A GeoPandas GeoDataFrame containing x, y, z values.
    """
    check_package(name="geopandas", URL="https://geopandas.org")
    import geopandas as gpd
    import pandas as pd

    if crs is None:
        crs = "epsg:4326"

    data = github_raw_url(data)

    if isinstance(data, pd.DataFrame):
        df = data
    elif isinstance(data, str):
        if not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        else:
            df = pd.read_csv(data, **kwargs)
    else:
        raise TypeError("The data must be a pandas DataFrame or a csv file path.")

    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x], df[y], z=z, crs=crs))

    return gdf


def vector_centroids(ee_object):
    """Returns the centroids of an ee.FeatureCollection.

    Args:
        ee_object (ee.FeatureCollection): The ee.FeatureCollection to get the centroids of.

    Raises:
        TypeError: If the ee_object is not an ee.FeatureCollection.

    Returns:
        ee.FeatureCollection: The centroids of the ee_object.
    """
    if not isinstance(ee_object, ee.FeatureCollection):
        raise TypeError("The input must be an Earth Engine FeatureCollection.")

    centroids = ee_object.map(
        lambda f: ee.Feature(f.geometry().centroid(0.001), f.toDictionary())
    )

    centroids = centroids.map(
        lambda f: f.set(
            {
                "longitude": f.geometry().coordinates().get(0),
                "latitude": f.geometry().coordinates().get(1),
            }
        )
    )

    return centroids


def bbox_to_gdf(bbox, crs="EPSG:4326"):
    """Converts a bounding box to a GeoDataFrame.

    Args:
        bbox (tuple): A bounding box in the form of a tuple (minx, miny, maxx, maxy).
        crs (str, optional): The coordinate reference system of the bounding box to convert to. Defaults to "EPSG:4326".

    Returns:
        geopandas.GeoDataFrame: A GeoDataFrame containing the bounding box.
    """
    check_package(name="geopandas", URL="https://geopandas.org")
    from shapely.geometry import box
    import geopandas as gpd

    minx, miny, maxx, maxy = bbox
    geometry = box(minx, miny, maxx, maxy)
    d = {"geometry": [geometry]}
    gdf = gpd.GeoDataFrame(d, crs="EPSG:4326")
    gdf.to_crs(crs=crs, inplace=True)
    return gdf


def check_dir(dir_path, make_dirs=True):
    """Checks if a directory exists and creates it if it does not.

    Args:
        dir_path ([str): The path to the directory.
        make_dirs (bool, optional): Whether to create the directory if it does not exist. Defaults to True.

    Raises:
        FileNotFoundError: If the directory could not be found.
        TypeError: If the input directory path is not a string.

    Returns:
        str: The path to the directory.
    """

    if isinstance(dir_path, str):
        if dir_path.startswith("~"):
            dir_path = os.path.expanduser(dir_path)
        else:
            dir_path = os.path.abspath(dir_path)

        if not os.path.exists(dir_path) and make_dirs:
            os.makedirs(dir_path)

        if os.path.exists(dir_path):
            return dir_path
        else:
            raise FileNotFoundError("The provided directory could not be found.")
    else:
        raise TypeError("The provided directory path must be a string.")


def check_file_path(file_path, make_dirs=True):
    """Gets the absolute file path.

    Args:
        file_path ([str): The path to the file.
        make_dirs (bool, optional): Whether to create the directory if it does not exist. Defaults to True.

    Raises:
        FileNotFoundError: If the directory could not be found.
        TypeError: If the input directory path is not a string.

    Returns:
        str: The absolute path to the file.
    """
    if isinstance(file_path, str):
        if file_path.startswith("~"):
            file_path = os.path.expanduser(file_path)
        else:
            file_path = os.path.abspath(file_path)

        file_dir = os.path.dirname(file_path)
        if not os.path.exists(file_dir) and make_dirs:
            os.makedirs(file_dir)

        return file_path

    else:
        raise TypeError("The provided file path must be a string.")


def image_to_cog(source, dst_path=None, profile="deflate", **kwargs):
    """Converts an image to a COG file.

    Args:
        source (str): A dataset path, URL or rasterio.io.DatasetReader object.
        dst_path (str, optional): An output dataset path or or PathLike object. Defaults to None.
        profile (str, optional): COG profile. More at https://cogeotiff.github.io/rio-cogeo/profile. Defaults to "deflate".

    Raises:
        ImportError: If rio-cogeo is not installed.
        FileNotFoundError: If the source file could not be found.
    """
    try:
        from rio_cogeo.cogeo import cog_translate
        from rio_cogeo.profiles import cog_profiles

    except ImportError:
        raise ImportError(
            "The rio-cogeo package is not installed. Please install it with `pip install rio-cogeo` or `conda install rio-cogeo -c conda-forge`."
        )

    if not source.startswith("http"):
        source = check_file_path(source)

        if not os.path.exists(source):
            raise FileNotFoundError("The provided input file could not be found.")

    if dst_path is None:
        if not source.startswith("http"):
            dst_path = os.path.splitext(source)[0] + "_cog.tif"
        else:
            dst_path = temp_file_path(extension=".tif")

    dst_path = check_file_path(dst_path)

    dst_profile = cog_profiles.get(profile)
    cog_translate(source, dst_path, dst_profile, **kwargs)


def cog_validate(source, verbose=False):
    """Validate Cloud Optimized Geotiff.

    Args:
        source (str): A dataset path or URL. Will be opened in "r" mode.
        verbose (bool, optional): Whether to print the output of the validation. Defaults to False.

    Raises:
        ImportError: If the rio-cogeo package is not installed.
        FileNotFoundError: If the provided file could not be found.

    Returns:
        tuple: A tuple containing the validation results (True is src_path is a valid COG, List of validation errors, and a list of validation warnings).
    """
    try:
        from rio_cogeo.cogeo import cog_validate, cog_info
    except ImportError:
        raise ImportError(
            "The rio-cogeo package is not installed. Please install it with `pip install rio-cogeo` or `conda install rio-cogeo -c conda-forge`."
        )

    if not source.startswith("http"):
        source = check_file_path(source)

        if not os.path.exists(source):
            raise FileNotFoundError("The provided input file could not be found.")

    if verbose:
        return cog_info(source)
    else:
        return cog_validate(source)


def gdf_to_df(gdf, drop_geom=True):
    """Converts a GeoDataFrame to a pandas DataFrame.

    Args:
        gdf (gpd.GeoDataFrame): A GeoDataFrame.
        drop_geom (bool, optional): Whether to drop the geometry column. Defaults to True.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the GeoDataFrame.
    """
    import pandas as pd

    if drop_geom:
        df = pd.DataFrame(gdf.drop(columns=["geometry"]))
    else:
        df = pd.DataFrame(gdf)

    return df


def geojson_to_df(in_geojson, encoding="utf-8", drop_geometry=True):
    """Converts a GeoJSON object to a pandas DataFrame.

    Args:
        in_geojson (str | dict): The input GeoJSON file or dict.
        encoding (str, optional): The encoding of the GeoJSON object. Defaults to "utf-8".
        drop_geometry (bool, optional): Whether to drop the geometry column. Defaults to True.

    Raises:
        FileNotFoundError: If the input GeoJSON file could not be found.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the GeoJSON object.
    """

    import pandas as pd
    from urllib.request import urlopen

    if isinstance(in_geojson, str):
        if in_geojson.startswith("http"):
            in_geojson = github_raw_url(in_geojson)
            with urlopen(in_geojson) as f:
                data = json.load(f)
        else:
            in_geojson = os.path.abspath(in_geojson)
            if not os.path.exists(in_geojson):
                raise FileNotFoundError("The provided GeoJSON file could not be found.")

            with open(in_geojson, encoding=encoding) as f:
                data = json.load(f)

    elif isinstance(in_geojson, dict):
        data = in_geojson

    df = pd.json_normalize(data["features"])
    df.columns = [col.replace("properties.", "") for col in df.columns]
    if drop_geometry:
        df = df[df.columns.drop(list(df.filter(regex="geometry")))]
    return df


def ee_join_table(ee_object, data, src_key, dst_key=None):
    """Join a table to an ee.FeatureCollection attribute table.

    Args:
        ee_object (ee.FeatureCollection): The ee.FeatureCollection to be joined by a table.
        data (str | pd.DataFraem | gpd.GeoDataFrame): The table to join to the ee.FeatureCollection.
        src_key (str): The key of ee.FeatureCollection attribute table to join.
        dst_key (str, optional): The key of the table to be joined to the ee.FeatureCollection. Defaults to None.

    Returns:
        ee.FeatureCollection: The joined ee.FeatureCollection.
    """
    import pandas as pd

    if not isinstance(ee_object, ee.FeatureCollection):
        raise TypeError("The input ee_object must be of type ee.FeatureCollection.")

    if not isinstance(src_key, str):
        raise TypeError("The input src_key must be of type str.")

    if dst_key is None:
        dst_key = src_key

    if isinstance(data, str):
        data = github_raw_url(data)
        if data.endswith(".csv"):
            df = pd.read_csv(data)
        elif data.endswith(".geojson"):
            df = geojson_to_df(data)
        else:
            import geopandas as gpd

            gdf = gpd.read_file(data)
            df = gdf_to_df(gdf)
    elif isinstance(data, pd.DataFrame):
        if "geometry" in data.columns:
            df = data.drop(columns=["geometry"])
        elif "geom" in data.columns:
            df = data.drop(columns=["geom"])
        else:
            df = data
    else:
        raise TypeError("The input data must be of type str or pandas.DataFrame.")

    df[dst_key] = df[dst_key].astype(str)
    df.set_index(dst_key, inplace=True)
    df = df[~df.index.duplicated(keep="first")]
    table = ee.Dictionary(df.to_dict("index"))

    fc = ee_object.map(lambda f: f.set(table.get(f.get(src_key), ee.Dictionary())))
    return fc


def gdf_bounds(gdf, return_geom=False):
    """Returns the bounding box of a GeoDataFrame.

    Args:
        gdf (gpd.GeoDataFrame): A GeoDataFrame.
        return_geom (bool, optional): Whether to return the bounding box as a GeoDataFrame. Defaults to False.

    Returns:
        list | gpd.GeoDataFrame: A bounding box in the form of a list (minx, miny, maxx, maxy) or GeoDataFrame.
    """
    bounds = gdf.total_bounds
    if return_geom:
        return bbox_to_gdf(bbox=bounds)
    else:
        return bounds


def gdf_centroid(gdf, return_geom=False):
    """Returns the centroid of a GeoDataFrame.

    Args:
        gdf (gpd.GeoDataFrame): A GeoDataFrame.
        return_geom (bool, optional): Whether to return the bounding box as a GeoDataFrame. Defaults to False.

    Returns:
        list | gpd.GeoDataFrame: A bounding box in the form of a list (lon, lat) or GeoDataFrame.
    """

    warnings.filterwarnings("ignore")

    centroid = gdf_bounds(gdf, return_geom=True).centroid
    if return_geom:
        return centroid
    else:
        return centroid.x[0], centroid.y[0]


def gdf_geom_type(gdf, first_only=True):
    """Returns the geometry type of a GeoDataFrame.

    Args:
        gdf (gpd.GeoDataFrame): A GeoDataFrame.
        first_only (bool, optional): Whether to return the geometry type of the first feature in the GeoDataFrame. Defaults to True.

    Returns:
        str: The geometry type of the GeoDataFrame.
    """

    if first_only:
        return gdf.geometry.type[0]
    else:
        return gdf.geometry.type


def image_to_numpy(image):
    """Converts an image to a numpy array.

    Args:
        image (str): A dataset path, URL or rasterio.io.DatasetReader object.

    Raises:
        FileNotFoundError: If the provided file could not be found.

    Returns:
        np.array: A numpy array.
    """
    import rasterio
    from osgeo import gdal
    from contextlib import contextmanager

    @contextmanager
    def gdal_error_handler():
        """Context manager for GDAL error handler."""
        gdal.PushErrorHandler("CPLQuietErrorHandler")
        try:
            yield
        finally:
            gdal.PopErrorHandler()

    gdal.UseExceptions()

    with gdal_error_handler():

        if not os.path.exists(image):
            raise FileNotFoundError("The provided input file could not be found.")

        with rasterio.open(image, "r") as ds:
            arr = ds.read()  # read all raster values

    return arr


def numpy_to_cog(
    np_array, out_cog, bounds=None, profile=None, dtype=None, crs="epsg:4326"
):
    """Converts a numpy array to a COG file.

    Args:
        np_array (np.array): A numpy array representing the image.
        out_cog (str): The output COG file path.
        bounds (tuple, optional): The bounds of the image in the format of (minx, miny, maxx, maxy). Defaults to None.
        profile (str | dict, optional): File path to an existing COG file or a dictionary representing the profile. Defaults to None.
        dtype (str, optional): The data type of the output COG file. Defaults to None.
        crs (str, optional): The coordinate reference system of the output COG file. Defaults to "epsg:4326".

    """

    import numpy as np
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.transform import from_bounds

    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    warnings.filterwarnings("ignore")

    if not isinstance(np_array, np.ndarray):
        raise TypeError("The input array must be a numpy array.")

    out_dir = os.path.dirname(out_cog)
    check_dir(out_dir)

    if profile is not None:
        if isinstance(profile, str):
            if not os.path.exists(profile):
                raise FileNotFoundError("The provided file could not be found.")
            with rasterio.open(profile) as ds:
                bounds = ds.bounds
        elif isinstance(profile, rasterio.profiles.Profile):
            profile = dict(profile)
        elif not isinstance(profile, dict):
            raise TypeError("The provided profile must be a file path or a dictionary.")

    if bounds is None:
        bounds = (-180.0, -85.0511287798066, 180.0, 85.0511287798066)

    if not isinstance(bounds, tuple) and len(bounds) != 4:
        raise TypeError("The provided bounds must be a tuple of length 4.")

    # Rasterio uses numpy array of shape of `(bands, height, width)`

    if len(np_array.shape) == 3:
        nbands = np_array.shape[0]
        height = np_array.shape[1]
        width = np_array.shape[2]
    elif len(np_array.shape) == 2:
        nbands = 1
        height = np_array.shape[0]
        width = np_array.shape[1]
        np_array = np_array.reshape((1, height, width))
    else:
        raise ValueError("The input array must be a 2D or 3D numpy array.")

    src_transform = from_bounds(*bounds, width=width, height=height)
    if dtype is None:
        dtype = str(np_array.dtype)

    if isinstance(profile, dict):
        src_profile = profile
        src_profile["count"] = nbands
    else:
        src_profile = dict(
            driver="GTiff",
            dtype=dtype,
            count=nbands,
            height=height,
            width=width,
            crs=crs,
            transform=src_transform,
        )

    with MemoryFile() as memfile:
        with memfile.open(**src_profile) as mem:
            # Populate the input file with numpy array
            mem.write(np_array)

            dst_profile = cog_profiles.get("deflate")
            cog_translate(
                mem,
                out_cog,
                dst_profile,
                in_memory=True,
                quiet=True,
            )


def view_lidar(filename, cmap="terrain", backend="pyvista", background=None, **kwargs):
    """View LiDAR data in 3D.

    Args:
        filename (str): The filepath to the LiDAR data.
        cmap (str, optional): The colormap to use. Defaults to "terrain". cmap currently does not work for the open3d backend.
        backend (str, optional): The plotting backend to use, can be pyvista, ipygany, panel, and open3d. Defaults to "pyvista".
        background (str, optional): The background color to use. Defaults to None.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the backend is not supported.
    """

    if in_colab_shell():
        print("The view_lidar() function is not supported in Colab.")
        return

    warnings.filterwarnings("ignore")
    filename = os.path.abspath(filename)
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist.")

    backend = backend.lower()
    if backend in ["pyvista", "ipygany", "panel"]:
        try:
            import pyntcloud
        except ImportError:
            print(
                "The pyvista and pyntcloud packages are required for this function. Use pip install geemap[lidar] to install them."
            )
            return

        try:
            if backend == "pyvista":
                backend = None
            if backend == "ipygany":
                cmap = None
            data = pyntcloud.PyntCloud.from_file(filename)
            mesh = data.to_instance("pyvista", mesh=False)
            mesh = mesh.elevation()
            mesh.plot(
                scalars="Elevation",
                cmap=cmap,
                jupyter_backend=backend,
                background=background,
                **kwargs,
            )

        except Exception as e:
            print("Something went wrong.")
            print(e)
            return

    elif backend == "open3d":
        try:
            import laspy
            import open3d as o3d
            import numpy as np
        except ImportError:
            print(
                "The laspy and open3d packages are required for this function. Use pip install laspy open3d to install them."
            )
            return

        try:
            las = laspy.read(filename)
            point_data = np.stack([las.X, las.Y, las.Z], axis=0).transpose((1, 0))
            geom = o3d.geometry.PointCloud()
            geom.points = o3d.utility.Vector3dVector(point_data)
            # geom.colors =  o3d.utility.Vector3dVector(colors)  # need to add colors. A list in the form of [[r,g,b], [r,g,b]] with value range 0-1. https://github.com/isl-org/Open3D/issues/614
            o3d.visualization.draw_geometries([geom], **kwargs)

        except Exception as e:
            print("Something went wrong.")
            print(e)
            return

    else:
        raise ValueError(f"{backend} is not a valid backend.")


def read_lidar(filename, **kwargs):
    """Read a LAS file.

    Args:
        filename (str): A local file path or HTTP URL to a LAS file.

    Returns:
        LasData: The LasData object return by laspy.read.
    """
    try:
        import laspy
    except ImportError:
        print(
            "The laspy package is required for this function. Use `pip install laspy[lazrs,laszip]` to install it."
        )
        return

    if (
        isinstance(filename, str)
        and filename.startswith("http")
        and (filename.endswith(".las") or filename.endswith(".laz"))
    ):
        filename = github_raw_url(filename)
        filename = download_file(filename)

    return laspy.read(filename, **kwargs)


def convert_lidar(
    source, destination=None, point_format_id=None, file_version=None, **kwargs
):
    """Converts a Las from one point format to another Automatically upgrades the file version if source file version
        is not compatible with the new point_format_id

    Args:
        source (str | laspy.lasdatas.base.LasBase): The source data to be converted.
        destination (str, optional): The destination file path. Defaults to None.
        point_format_id (int, optional): The new point format id (the default is None, which won't change the source format id).
        file_version (str, optional): The new file version. None by default which means that the file_version may be upgraded
            for compatibility with the new point_format. The file version will not be downgraded.

    Returns:
        aspy.lasdatas.base.LasBase: The converted LasData object.
    """
    try:
        import laspy
    except ImportError:
        print(
            "The laspy package is required for this function. Use `pip install laspy[lazrs,laszip]` to install it."
        )
        return

    if isinstance(source, str):
        source = read_lidar(source)

    las = laspy.convert(
        source, point_format_id=point_format_id, file_version=file_version
    )

    if destination is None:
        return las
    else:
        destination = check_file_path(destination)
        write_lidar(las, destination, **kwargs)
        return destination


def write_lidar(source, destination, do_compress=None, laz_backend=None):
    """Writes to a stream or file.

    Args:
        source (str | laspy.lasdatas.base.LasBase): The source data to be written.
        destination (str): The destination filepath.
        do_compress (bool, optional): Flags to indicate if you want to compress the data. Defaults to None.
        laz_backend (str, optional): The laz backend to use. Defaults to None.
    """

    try:
        import laspy
    except ImportError:
        print(
            "The laspy package is required for this function. Use `pip install laspy[lazrs,laszip]` to install it."
        )
        return

    if isinstance(source, str):
        source = read_lidar(source)

    source.write(destination, do_compress=do_compress, laz_backend=laz_backend)


def download_folder(
    url=None,
    id=None,
    output=None,
    quiet=False,
    proxy=None,
    speed=None,
    use_cookies=True,
    remaining_ok=False,
):
    """Downloads the entire folder from URL.

    Args:
        url (str, optional): URL of the Google Drive folder. Must be of the format 'https://drive.google.com/drive/folders/{url}'. Defaults to None.
        id (str, optional): Google Drive's folder ID. Defaults to None.
        output (str, optional):  String containing the path of the output folder. Defaults to current working directory.
        quiet (bool, optional): Suppress terminal output. Defaults to False.
        proxy (str, optional): Proxy. Defaults to None.
        speed (float, optional): Download byte size per second (e.g., 256KB/s = 256 * 1024). Defaults to None.
        use_cookies (bool, optional): Flag to use cookies. Defaults to True.
        resume (bool, optional): Resume the download from existing tmp file if possible. Defaults to False.

    Returns:
        list: List of files downloaded, or None if failed.
    """
    import gdown

    files = gdown.download_folder(
        url, id, output, quiet, proxy, speed, use_cookies, remaining_ok
    )
    return files


def blend(
    top_layer,
    bottom_layer=None,
    top_vis=None,
    bottom_vis=None,
    hillshade=True,
    expression="a*b",
    **kwargs,
):
    """Create a blended image that is a combination of two images, e.g., DEM and hillshade. This function was inspired by Jesse Anderson. See https://github.com/jessjaco/gee-blend.

    Args:
        top_layer (ee.Image): The top layer image, e.g., ee.Image("CGIAR/SRTM90_V4")
        bottom_layer (ee.Image, optional): The bottom layer image. If not specified, it will use the top layer image.
        top_vis (dict, optional): The top layer image vis parameters as a dictionary. Defaults to None.
        bottom_vis (dict, optional): The bottom layer image vis parameters as a dictionary. Defaults to None.
        hillshade (bool, optional): Flag to use hillshade. Defaults to True.
        expression (str, optional): The expression to use for the blend. Defaults to 'a*b'.

    Returns:
        ee.Image: The blended image.
    """
    from box import Box

    if not isinstance(top_layer, ee.Image):
        raise ValueError("top_layer must be an ee.Image.")

    if bottom_layer is None:
        bottom_layer = top_layer

    if not isinstance(bottom_layer, ee.Image):
        raise ValueError("bottom_layer must be an ee.Image.")

    if top_vis is not None:
        if not isinstance(top_vis, dict):
            raise ValueError("top_vis must be a dictionary.")
        elif "palette" in top_vis and isinstance(top_vis["palette"], Box):
            try:
                top_vis["palette"] = top_vis["palette"]["default"]
            except Exception as e:
                print("The provided palette is invalid.")
                raise Exception(e)

    if bottom_vis is not None:
        if not isinstance(bottom_vis, dict):
            raise ValueError("top_vis must be a dictionary.")
        elif "palette" in bottom_vis and isinstance(bottom_vis["palette"], Box):
            try:
                bottom_vis["palette"] = bottom_vis["palette"]["default"]
            except Exception as e:
                print("The provided palette is invalid.")
                raise Exception(e)

    if top_vis is None:
        top_bands = top_layer.bandNames().getInfo()
        top_vis = {"bands": top_bands}
        if hillshade:
            top_vis["palette"] = ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"]
            top_vis["min"] = 0
            top_vis["max"] = 6000

    if bottom_vis is None:
        bottom_bands = bottom_layer.bandNames().getInfo()
        bottom_vis = {"bands": bottom_bands}
        if hillshade:
            bottom_vis["bands"] = ["hillshade"]

    top = top_layer.visualize(**top_vis).divide(255)

    if hillshade:
        bottom = ee.Terrain.hillshade(bottom_layer).visualize(**bottom_vis).divide(255)
    else:
        bottom = bottom_layer.visualize(**bottom_vis).divide(255)

    if "a" not in expression or ("b" not in expression):
        raise ValueError("expression must contain 'a' and 'b'.")

    result = ee.Image().expression(expression, {"a": top, "b": bottom})
    return result


def clip_image(image, mask, output):
    """Clip an image by mask.

    Args:
        image (str): Path to the image file in GeoTIFF format.
        mask (str | list | dict): The mask used to extract the image. It can be a path to vector datasets (e.g., GeoJSON, Shapefile), a list of coordinates, or m.user_roi.
        output (str): Path to the output file.

    Raises:
        ImportError: If the fiona or rasterio package is not installed.
        FileNotFoundError: If the image is not found.
        ValueError: If the mask is not a valid GeoJSON or raster file.
        FileNotFoundError: If the mask file is not found.
    """
    try:
        import fiona
        import rasterio
        import rasterio.mask
    except ImportError as e:
        raise ImportError(e)

    if not os.path.exists(image):
        raise FileNotFoundError(f"{image} does not exist.")

    if not output.endswith(".tif"):
        raise ValueError("Output must be a tif file.")

    output = check_file_path(output)

    if isinstance(mask, ee.Geometry):
        mask = mask.coordinates().getInfo()[0]

    if isinstance(mask, str):
        if mask.startswith("http"):
            mask = download_file(mask, output)
        if not os.path.exists(mask):
            raise FileNotFoundError(f"{mask} does not exist.")
    elif isinstance(mask, list) or isinstance(mask, dict):
        if isinstance(mask, list):
            geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {"type": "Polygon", "coordinates": [mask]},
                    }
                ],
            }
        else:
            geojson = {
                "type": "FeatureCollection",
                "features": [mask],
            }
        mask = temp_file_path(".geojson")
        with open(mask, "w") as f:
            json.dump(geojson, f)

    with fiona.open(mask, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]

    with rasterio.open(image) as src:
        out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)
        out_meta = src.meta

    out_meta.update(
        {
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
        }
    )

    with rasterio.open(output, "w", **out_meta) as dest:
        dest.write(out_image)


def netcdf_to_tif(
    filename,
    output=None,
    variables=None,
    shift_lon=True,
    lat="lat",
    lon="lon",
    return_vars=False,
    **kwargs,
):
    """Convert a netcdf file to a GeoTIFF file.

    Args:
        filename (str): Path to the netcdf file.
        output (str, optional): Path to the output GeoTIFF file. Defaults to None. If None, the output file will be the same as the input file with the extension changed to .tif.
        variables (str | list, optional): Name of the variable or a list of variables to extract. Defaults to None. If None, all variables will be extracted.
        shift_lon (bool, optional): Flag to shift longitude values from [0, 360] to the range [-180, 180]. Defaults to True.
        lat (str, optional): Name of the latitude variable. Defaults to 'lat'.
        lon (str, optional): Name of the longitude variable. Defaults to 'lon'.
        return_vars (bool, optional): Flag to return all variables. Defaults to False.

    Raises:
        ImportError: If the xarray or rioxarray package is not installed.
        FileNotFoundError: If the netcdf file is not found.
        ValueError: If the variable is not found in the netcdf file.
    """
    try:
        import xarray as xr
    except ImportError as e:
        raise ImportError(e)

    if filename.startswith("http"):
        filename = download_file(filename)

    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist.")

    if output is None:
        output = filename.replace(".nc", ".tif")
    else:
        output = check_file_path(output)

    xds = xr.open_dataset(filename, **kwargs)

    if shift_lon:
        xds.coords[lon] = (xds.coords[lon] + 180) % 360 - 180
        xds = xds.sortby(xds.lon)

    allowed_vars = list(xds.data_vars.keys())
    if isinstance(variables, str):
        if variables not in allowed_vars:
            raise ValueError(f"{variables} is not a valid variable.")
        variables = [variables]

    if variables is not None and (not set(variables).issubset(allowed_vars)):
        raise ValueError(f"{variables} must be a subset of {allowed_vars}.")

    if variables is None:
        xds.rio.set_spatial_dims(x_dim=lon, y_dim=lat).rio.to_raster(output)
    else:
        xds[variables].rio.set_spatial_dims(x_dim=lon, y_dim=lat).rio.to_raster(output)

    if return_vars:
        return output, allowed_vars
    else:
        return output


def read_netcdf(filename, **kwargs):
    """Read a netcdf file.

    Args:
        filename (str): File path or HTTP URL to the netcdf file.

    Raises:
        ImportError: If the xarray or rioxarray package is not installed.
        FileNotFoundError: If the netcdf file is not found.

    Returns:
        xarray.Dataset: The netcdf file as an xarray dataset.
    """
    try:
        import xarray as xr
    except ImportError as e:
        raise ImportError(e)

    if filename.startswith("http"):
        filename = download_file(filename)

    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist.")

    xds = xr.open_dataset(filename, **kwargs)
    return xds


def netcdf_tile_layer(
    filename,
    variables=None,
    colormap=None,
    vmin=None,
    vmax=None,
    nodata=None,
    port="default",
    debug=False,
    attribution=None,
    tile_format="ipyleaflet",
    layer_name="NetCDF layer",
    return_client=False,
    shift_lon=True,
    lat="lat",
    lon="lon",
    **kwargs,
):
    """Generate an ipyleaflet/folium TileLayer from a netCDF file.
        If you are using this function in JupyterHub on a remote server (e.g., Binder, Microsoft Planetary Computer),
        try adding to following two lines to the beginning of the notebook if the raster does not render properly.

        import os
        os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = f'{os.environ['JUPYTERHUB_SERVICE_PREFIX'].lstrip('/')}/proxy/{{port}}'

    Args:
        filename (str): File path or HTTP URL to the netCDF file.
        variables (int, optional): The variable/band names to extract data from the netCDF file. Defaults to None. If None, all variables will be extracted.
        port (str, optional): The port to use for the server. Defaults to "default".
        colormap (str, optional): The name of the colormap from `matplotlib` to use when plotting a single band. See https://matplotlib.org/stable/gallery/color/colormap_reference.html. Default is greyscale.
        vmin (float, optional): The minimum value to use when colormapping the colormap when plotting a single band. Defaults to None.
        vmax (float, optional): The maximum value to use when colormapping the colormap when plotting a single band. Defaults to None.
        nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
        debug (bool, optional): If True, the server will be started in debug mode. Defaults to False.
        projection (str, optional): The projection of the GeoTIFF. Defaults to "EPSG:3857".
        attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
        tile_format (str, optional): The tile layer format. Can be either ipyleaflet or folium. Defaults to "ipyleaflet".
        layer_name (str, optional): The layer name to use. Defaults to "NetCDF layer".
        return_client (bool, optional): If True, the tile client will be returned. Defaults to False.
        shift_lon (bool, optional): Flag to shift longitude values from [0, 360] to the range [-180, 180]. Defaults to True.
        lat (str, optional): Name of the latitude variable. Defaults to 'lat'.
        lon (str, optional): Name of the longitude variable. Defaults to 'lon'.

    Returns:
        ipyleaflet.TileLayer | folium.TileLayer: An ipyleaflet.TileLayer or folium.TileLayer.
    """

    check_package(
        "localtileserver", URL="https://github.com/banesullivan/localtileserver"
    )

    try:
        import xarray as xr
    except ImportError as e:
        raise ImportError(e)

    if filename.startswith("http"):
        filename = download_file(filename)

    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist.")

    output = filename.replace(".nc", ".tif")

    xds = xr.open_dataset(filename, **kwargs)

    if shift_lon:
        xds.coords[lon] = (xds.coords[lon] + 180) % 360 - 180
        xds = xds.sortby(xds.lon)

    allowed_vars = list(xds.data_vars.keys())
    if isinstance(variables, str):
        if variables not in allowed_vars:
            raise ValueError(f"{variables} is not a subset of {allowed_vars}.")
        variables = [variables]

    if variables is not None and len(variables) > 3:
        raise ValueError("Only 3 variables can be plotted at a time.")

    if variables is not None and (not set(variables).issubset(allowed_vars)):
        raise ValueError(f"{variables} must be a subset of {allowed_vars}.")

    xds.rio.set_spatial_dims(x_dim=lon, y_dim=lat).rio.to_raster(output)
    if variables is None:
        if len(allowed_vars) >= 3:
            band_idx = [1, 2, 3]
        else:
            band_idx = [1]
    else:
        band_idx = [allowed_vars.index(var) + 1 for var in variables]

    tile_layer = get_local_tile_layer(
        output,
        port=port,
        debug=debug,
        indexes=band_idx,
        colormap=colormap,
        vmin=vmin,
        vmax=vmax,
        nodata=nodata,
        attribution=attribution,
        tile_format=tile_format,
        layer_name=layer_name,
        return_client=return_client,
    )
    return tile_layer


def classify(
    data,
    column,
    cmap=None,
    colors=None,
    labels=None,
    scheme="Quantiles",
    k=5,
    legend_kwds=None,
    classification_kwds=None,
):
    """Classify a dataframe column using a variety of classification schemes.

    Args:
        data (str | pd.DataFrame | gpd.GeoDataFrame): The data to classify. It can be a filepath to a vector dataset, a pandas dataframe, or a geopandas geodataframe.
        column (str): The column to classify.
        cmap (str, optional): The name of a colormap recognized by matplotlib. Defaults to None.
        colors (list, optional): A list of colors to use for the classification. Defaults to None.
        labels (list, optional): A list of labels to use for the legend. Defaults to None.
        scheme (str, optional): Name of a choropleth classification scheme (requires mapclassify).
            Name of a choropleth classification scheme (requires mapclassify).
            A mapclassify.MapClassifier object will be used
            under the hood. Supported are all schemes provided by mapclassify (e.g.
            'BoxPlot', 'EqualInterval', 'FisherJenks', 'FisherJenksSampled',
            'HeadTailBreaks', 'JenksCaspall', 'JenksCaspallForced',
            'JenksCaspallSampled', 'MaxP', 'MaximumBreaks',
            'NaturalBreaks', 'Quantiles', 'Percentiles', 'StdMean',
            'UserDefined'). Arguments can be passed in classification_kwds.
        k (int, optional): Number of classes (ignored if scheme is None or if column is categorical). Default to 5.
        legend_kwds (dict, optional): Keyword arguments to pass to :func:`matplotlib.pyplot.legend` or `matplotlib.pyplot.colorbar`. Defaults to None.
            Keyword arguments to pass to :func:`matplotlib.pyplot.legend` or
            Additional accepted keywords when `scheme` is specified:
            fmt : string
                A formatting specification for the bin edges of the classes in the
                legend. For example, to have no decimals: ``{"fmt": "{:.0f}"}``.
            labels : list-like
                A list of legend labels to override the auto-generated labblels.
                Needs to have the same number of elements as the number of
                classes (`k`).
            interval : boolean (default False)
                An option to control brackets from mapclassify legend.
                If True, open/closed interval brackets are shown in the legend.
        classification_kwds (dict, optional): Keyword arguments to pass to mapclassify. Defaults to None.

    Returns:
        pd.DataFrame, dict: A pandas dataframe with the classification applied and a legend dictionary.
    """

    import numpy as np
    import pandas as pd
    import geopandas as gpd
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    try:
        import mapclassify
    except ImportError:
        raise ImportError(
            'mapclassify is required for this function. Install with "pip install mapclassify".'
        )

    if isinstance(data, gpd.GeoDataFrame) or isinstance(data, pd.DataFrame):
        df = data
    else:
        try:
            df = gpd.read_file(data)
        except Exception:
            raise TypeError(
                "Data must be a GeoDataFrame or a path to a file that can be read by geopandas.read_file()."
            )

    if df.empty:
        warnings.warn(
            "The GeoDataFrame you are attempting to plot is "
            "empty. Nothing has been displayed.",
            UserWarning,
        )
        return

    columns = df.columns.values.tolist()
    if column not in columns:
        raise ValueError(
            f"{column} is not a column in the GeoDataFrame. It must be one of {columns}."
        )

    # Convert categorical data to numeric
    init_column = None
    value_list = None
    if np.issubdtype(df[column].dtype, np.object0):
        value_list = df[column].unique().tolist()
        value_list.sort()
        df["category"] = df[column].replace(value_list, range(0, len(value_list)))
        init_column = column
        column = "category"
        k = len(value_list)

    if legend_kwds is not None:
        legend_kwds = legend_kwds.copy()

    # To accept pd.Series and np.arrays as column
    if isinstance(column, (np.ndarray, pd.Series)):
        if column.shape[0] != df.shape[0]:
            raise ValueError(
                "The dataframe and given column have different number of rows."
            )
        else:
            values = column

            # Make sure index of a Series matches index of df
            if isinstance(values, pd.Series):
                values = values.reindex(df.index)
    else:
        values = df[column]

    values = df[column]
    nan_idx = np.asarray(pd.isna(values), dtype="bool")

    if cmap is None:
        cmap = "Blues"
    try:
        cmap = plt.get_cmap(cmap, k)
    except:
        cmap = plt.cm.get_cmap(cmap, k)
    if colors is None:
        colors = [mpl.colors.rgb2hex(cmap(i))[1:] for i in range(cmap.N)]
        colors = ["#" + i for i in colors]
    elif isinstance(colors, list):
        colors = [check_color(i) for i in colors]
    elif isinstance(colors, str):
        colors = [check_color(colors)] * k

    allowed_schemes = [
        "BoxPlot",
        "EqualInterval",
        "FisherJenks",
        "FisherJenksSampled",
        "HeadTailBreaks",
        "JenksCaspall",
        "JenksCaspallForced",
        "JenksCaspallSampled",
        "MaxP",
        "MaximumBreaks",
        "NaturalBreaks",
        "Quantiles",
        "Percentiles",
        "StdMean",
        "UserDefined",
    ]

    if scheme.lower() not in [s.lower() for s in allowed_schemes]:
        raise ValueError(
            f"{scheme} is not a valid scheme. It must be one of {allowed_schemes}."
        )

    if classification_kwds is None:
        classification_kwds = {}
    if "k" not in classification_kwds:
        classification_kwds["k"] = k

    binning = mapclassify.classify(
        np.asarray(values[~nan_idx]), scheme, **classification_kwds
    )
    df["category"] = binning.yb
    df["color"] = [colors[i] for i in df["category"]]

    if legend_kwds is None:
        legend_kwds = {}

    if "interval" not in legend_kwds:
        legend_kwds["interval"] = True

    if "fmt" not in legend_kwds:
        if np.issubdtype(df[column].dtype, np.floating):
            legend_kwds["fmt"] = "{:.2f}"
        else:
            legend_kwds["fmt"] = "{:.0f}"

    if labels is None:
        # set categorical to True for creating the legend
        if legend_kwds is not None and "labels" in legend_kwds:
            if len(legend_kwds["labels"]) != binning.k:
                raise ValueError(
                    "Number of labels must match number of bins, "
                    "received {} labels for {} bins".format(
                        len(legend_kwds["labels"]), binning.k
                    )
                )
            else:
                labels = list(legend_kwds.pop("labels"))
        else:
            # fmt = "{:.2f}"
            if legend_kwds is not None and "fmt" in legend_kwds:
                fmt = legend_kwds.pop("fmt")

            labels = binning.get_legend_classes(fmt)
            if legend_kwds is not None:
                show_interval = legend_kwds.pop("interval", False)
            else:
                show_interval = False
            if not show_interval:
                labels = [c[1:-1] for c in labels]

        if init_column is not None:
            labels = value_list
    elif isinstance(labels, list):
        if len(labels) != len(colors):
            raise ValueError("The number of labels must match the number of colors.")
    else:
        raise ValueError("labels must be a list or None.")

    legend_dict = dict(zip(labels, colors))
    df["category"] = df["category"] + 1
    return df, legend_dict


def image_count(
    collection, region=None, band=None, start_date=None, end_date=None, clip=False
):
    """Create an image with the number of available images for a specific region.
    Args:
        collection (ee.ImageCollection): The collection to be queried.
        region (ee.Geometry | ee.FeatureCollection, optional): The region to be queried.
        start_date (str | ee.Date, optional): The start date of the query.
        band (str, optional): The band to be queried.
        end_date (str | ee.Date, optional): The end date of the query.
        clip (bool, optional): Whether to clip the image to the region.

    Returns:
        ee.Image: The image with each pixel value representing the number of available images.
    """
    if not isinstance(collection, ee.ImageCollection):
        raise TypeError("collection must be an ee.ImageCollection.")

    if region is not None:
        if isinstance(region, ee.Geometry) or isinstance(region, ee.FeatureCollection):
            pass
        else:
            raise TypeError("region must be an ee.Geometry or ee.FeatureCollection.")

    if (start_date is not None) and (end_date is not None):
        pass
    elif (start_date is None) and (end_date is None):
        pass
    else:
        raise ValueError("start_date and end_date must be provided.")

    if band is None:
        first_image = collection.first()
        band = first_image.bandNames().get(0)

    if region is not None:
        collection = collection.filterBounds(region)

    if start_date is not None and end_date is not None:
        collection = collection.filterDate(start_date, end_date)

    image = (
        collection.filter(ee.Filter.listContains("system:band_names", band))
        .select([band])
        .reduce(ee.Reducer.count())
    )

    if clip:
        image = image.clip(region)

    return image


def dynamic_world(
    region=None,
    start_date="2020-01-01",
    end_date="2021-01-01",
    clip=False,
    reducer=None,
    projection="EPSG:3857",
    scale=10,
    return_type="hillshade",
):
    """Create 10-m land cover composite based on Dynamic World. The source code is adapted from the following tutorial by Spatial Thoughts:
    https://developers.google.com/earth-engine/tutorials/community/introduction-to-dynamic-world-pt-1

    Args:
        region (ee.Geometry | ee.FeatureCollection): The region of interest.
        start_date (str | ee.Date): The start date of the query. Default to "2020-01-01".
        end_date (str | ee.Date): The end date of the query. Default to "2021-01-01".
        clip (bool, optional): Whether to clip the image to the region. Default to False.
        reducer (ee.Reducer, optional): The reducer to be used. Default to None.
        projection (str, optional): The projection to be used for creating hillshade. Default to "EPSG:3857".
        scale (int, optional): The scale to be used for creating hillshade. Default to 10.
        return_type (str, optional): The type of image to be returned. Can be one of 'hillshade', 'visualize', 'class', or 'probability'. Default to "hillshade".

    Returns:
        ee.Image: The image with the specified return_type.
    """

    if return_type not in ["hillshade", "visualize", "class", "probability"]:
        raise ValueError(
            f"{return_type} must be one of 'hillshade', 'visualize', 'class', or 'probability'."
        )

    if reducer is None:
        reducer = ee.Reducer.mode()

    dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filter(
        ee.Filter.date(start_date, end_date)
    )

    if isinstance(region, ee.FeatureCollection) or isinstance(region, ee.Geometry):
        dw = dw.filterBounds(region)
    else:
        raise ValueError("region must be an ee.FeatureCollection or ee.Geometry.")

    # Create a Mode Composite
    classification = dw.select("label")
    dwComposite = classification.reduce(reducer)
    if clip and (region is not None):
        if isinstance(region, ee.Geometry):
            dwComposite = dwComposite.clip(region)
        elif isinstance(region, ee.FeatureCollection):
            dwComposite = dwComposite.clipToCollection(region)
        elif isinstance(region, ee.Feature):
            dwComposite = dwComposite.clip(region.geometry())

    dwVisParams = {
        "min": 0,
        "max": 8,
        "palette": [
            "#419BDF",
            "#397D49",
            "#88B053",
            "#7A87C6",
            "#E49635",
            "#DFC35A",
            "#C4281B",
            "#A59B8F",
            "#B39FE1",
        ],
    }

    if return_type == "class":
        return dwComposite
    elif return_type == "visualize":
        return dwComposite.visualize(**dwVisParams)
    else:
        # Create a Top-1 Probability Hillshade Visualization
        probabilityBands = [
            "water",
            "trees",
            "grass",
            "flooded_vegetation",
            "crops",
            "shrub_and_scrub",
            "built",
            "bare",
            "snow_and_ice",
        ]

        # Select probability bands
        probabilityCol = dw.select(probabilityBands)

        # Create a multi-band image with the average pixel-wise probability
        # for each band across the time-period
        meanProbability = probabilityCol.reduce(ee.Reducer.mean())

        # Composites have a default projection that is not suitable
        # for hillshade computation.
        # Set a EPSG:3857 projection with 10m scale
        proj = ee.Projection(projection).atScale(scale)
        meanProbability = meanProbability.setDefaultProjection(proj)

        # Create the Top1 Probability Hillshade
        top1Probability = meanProbability.reduce(ee.Reducer.max())

        if clip and (region is not None):
            if isinstance(region, ee.Geometry):
                top1Probability = top1Probability.clip(region)
            elif isinstance(region, ee.FeatureCollection):
                top1Probability = top1Probability.clipToCollection(region)
            elif isinstance(region, ee.Feature):
                top1Probability = top1Probability.clip(region.geometry())

        if return_type == "probability":
            return top1Probability
        else:
            top1Confidence = top1Probability.multiply(100).int()
            hillshade = ee.Terrain.hillshade(top1Confidence).divide(255)
            rgbImage = dwComposite.visualize(**dwVisParams).divide(255)
            probabilityHillshade = rgbImage.multiply(hillshade)

            return probabilityHillshade


def dynamic_world_s2(
    region=None,
    start_date="2020-01-01",
    end_date="2021-01-01",
    clip=False,
    cloud_pct=0.35,
    reducer=None,
):
    """Create Sentinel-2 composite for the Dynamic World Land Cover product.

    Args:
        region (ee.Geometry | ee.FeatureCollection): The region of interest. Default to None.
        start_date (str | ee.Date): The start date of the query. Default to "2020-01-01".
        end_date (str | ee.Date): The end date of the query. Default to "2021-01-01".
        clip (bool, optional): Whether to clip the image to the region. Default to False.
        cloud_pct (float, optional): The percentage of cloud cover to be used for filtering. Default to 0.35.
        reducer (ee.Reducer, optional): The reducer to be used for creating image composite. Default to None.

    Returns:
        ee.Image: The Sentinel-2 composite.
    """
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct * 100))
    )

    if isinstance(region, ee.FeatureCollection) or isinstance(region, ee.Geometry):
        s2 = s2.filterBounds(region)
    else:
        raise ValueError("region must be an ee.FeatureCollection or ee.Geometry.")

    if reducer is None:
        reducer = ee.Reducer.median()

    image = s2.reduce(reducer).rename(s2.first().bandNames())

    if clip and (region is not None):
        if isinstance(region, ee.Geometry):
            image = image.clip(region)
        elif isinstance(region, ee.FeatureCollection):
            image = image.clipToCollection(region)

    return image


def download_ee_image(
    image,
    filename,
    region=None,
    crs=None,
    crs_transform=None,
    scale=None,
    resampling="near",
    dtype=None,
    overwrite=True,
    num_threads=None,
    max_tile_size=None,
    max_tile_dim=None,
    shape=None,
    scale_offset=False,
    unmask_value=None,
    **kwargs,
):
    """Download an Earth Engine Image as a GeoTIFF. Images larger than the `Earth Engine size limit are split and downloaded as
        separate tiles, then re-assembled into a single GeoTIFF. See https://github.com/dugalh/geedim/blob/main/geedim/download.py#L574

    Args:
        image (ee.Image): The image to be downloaded.
        filename (str): Name of the destination file.
        region (ee.Geometry, optional): Region defined by geojson polygon in WGS84. Defaults to the entire image granule.
        crs (str, optional): Reproject image(s) to this EPSG or WKT CRS.  Where image bands have different CRSs, all are
            re-projected to this CRS. Defaults to the CRS of the minimum scale band.
        crs_transform (list, optional): tuple of float, list of float, rio.Affine, optional
            List of 6 numbers specifying an affine transform in the specified CRS.  In row-major order:
            [xScale, xShearing, xTranslation, yShearing, yScale, yTranslation].  All bands are re-projected to
            this transform.
        scale (float, optional): Resample image(s) to this pixel scale (size) (m).  Where image bands have different scales,
            all are resampled to this scale.  Defaults to the minimum scale of image bands.
        resampling (ResamplingMethod, optional): Resampling method, can be 'near', 'bilinear', 'bicubic', or 'average'. Defaults to None.
        dtype (str, optional): Convert to this data type (`uint8`, `int8`, `uint16`, `int16`, `uint32`, `int32`, `float32`
            or `float64`).  Defaults to auto select a minimum size type that can represent the range of pixel values.
        overwrite (bool, optional): Overwrite the destination file if it exists. Defaults to True.
        num_threads (int, optional): Number of tiles to download concurrently. Defaults to a sensible auto value.
        max_tile_size: int, optional
            Maximum tile size (MB).  If None, defaults to the Earth Engine download size limit (32 MB).
        max_tile_dim: int, optional
            Maximum tile width/height (pixels).  If None, defaults to Earth Engine download limit (10000).
        shape: tuple of int, optional
            (height, width) dimensions to export (pixels).
        scale_offset: bool, optional
            Whether to apply any EE band scales and offsets to the image.
        unmask_value (float, optional): The value to use for pixels that are masked in the input image. If the exported image contains
            zero values, you should set the unmask value to a  non-zero value so that the zero values are not treated as missing data. Defaults to None.

    """

    if os.environ.get("USE_MKDOCS") is not None:
        return

    try:
        import geedim as gd
    except ImportError:
        raise ImportError(
            "Please install geedim using `pip install geedim` or `conda install -c conda-forge geedim`"
        )

    if not isinstance(image, ee.Image):
        raise ValueError("image must be an ee.Image.")

    if unmask_value is not None:
        if isinstance(region, ee.Geometry):
            image = image.clip(region)
        elif isinstance(region, ee.FeatureCollection):
            image = image.clipToCollection(region)
        image = image.unmask(unmask_value, sameFootprint=False)

    if region is not None:
        kwargs["region"] = region

    if crs is not None:
        kwargs["crs"] = crs

    if crs_transform is not None:
        kwargs["crs_transform"] = crs_transform

    if scale is not None:
        kwargs["scale"] = scale

    if resampling is not None:
        kwargs["resampling"] = resampling

    if dtype is not None:
        kwargs["dtype"] = dtype

    if max_tile_size is not None:
        kwargs["max_tile_size"] = max_tile_size

    if max_tile_dim is not None:
        kwargs["max_tile_dim"] = max_tile_dim

    if shape is not None:
        kwargs["shape"] = shape

    if scale_offset:
        kwargs["scale_offset"] = scale_offset

    img = gd.download.BaseImage(image)
    img.download(filename, overwrite=overwrite, num_threads=num_threads, **kwargs)


def download_ee_image_tiles(
    image,
    features,
    out_dir=None,
    prefix=None,
    crs=None,
    crs_transform=None,
    scale=None,
    resampling="near",
    dtype=None,
    overwrite=True,
    num_threads=None,
    max_tile_size=None,
    max_tile_dim=None,
    shape=None,
    scale_offset=False,
    unmask_value=None,
    column=None,
    **kwargs,
):
    """Download an Earth Engine Image as small tiles based on ee.FeatureCollection. Images larger than the `Earth Engine size limit are split and downloaded as
        separate tiles, then re-assembled into a single GeoTIFF. See https://github.com/dugalh/geedim/blob/main/geedim/download.py#L574

    Args:
        image (ee.Image): The image to be downloaded.
        features (ee.FeatureCollection): The features to loop through to download image.
        out_dir (str, optional): The output directory. Defaults to None.
        prefix (str, optional): The prefix for the output file. Defaults to None.
        crs (str, optional): Reproject image(s) to this EPSG or WKT CRS.  Where image bands have different CRSs, all are
            re-projected to this CRS. Defaults to the CRS of the minimum scale band.
        crs_transform (list, optional): tuple of float, list of float, rio.Affine, optional
            List of 6 numbers specifying an affine transform in the specified CRS.  In row-major order:
            [xScale, xShearing, xTranslation, yShearing, yScale, yTranslation].  All bands are re-projected to
            this transform.
        scale (float, optional): Resample image(s) to this pixel scale (size) (m).  Where image bands have different scales,
            all are resampled to this scale.  Defaults to the minimum scale of image bands.
        resampling (ResamplingMethod, optional): Resampling method, can be 'near', 'bilinear', 'bicubic', or 'average'. Defaults to None.
        dtype (str, optional): Convert to this data type (`uint8`, `int8`, `uint16`, `int16`, `uint32`, `int32`, `float32`
            or `float64`).  Defaults to auto select a minimum size type that can represent the range of pixel values.
        overwrite (bool, optional): Overwrite the destination file if it exists. Defaults to True.
        num_threads (int, optional): Number of tiles to download concurrently. Defaults to a sensible auto value.
        max_tile_size: int, optional
            Maximum tile size (MB).  If None, defaults to the Earth Engine download size limit (32 MB).
        max_tile_dim: int, optional
            Maximum tile width/height (pixels).  If None, defaults to Earth Engine download limit (10000).
        shape: tuple of int, optional
            (height, width) dimensions to export (pixels).
        scale_offset: bool, optional
            Whether to apply any EE band scales and offsets to the image.
        unmask_value (float, optional): The value to use for pixels that are masked in the input image. If the exported image contains zero values,
            you should set the unmask value to a  non-zero value so that the zero values are not treated as missing data. Defaults to None.
        column (str, optional): The column name to use for the filename. Defaults to None.

    """
    import time

    start = time.time()

    if os.environ.get("USE_MKDOCS") is not None:
        return

    if not isinstance(features, ee.FeatureCollection):
        raise ValueError("features must be an ee.FeatureCollection.")

    if out_dir is None:
        out_dir = os.getcwd()

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if prefix is None:
        prefix = ""

    count = features.size().getInfo()
    collection = features.toList(count)

    if column is not None:
        names = features.aggregate_array(column).getInfo()
    else:
        names = [str(i + 1).zfill(len(str(count))) for i in range(count)]

    for i in range(count):
        region = ee.Feature(collection.get(i)).geometry()
        filename = os.path.join(
            out_dir, "{}{}.tif".format(prefix, names[i].replace("/", "_"))
        )
        print(f"Downloading {i + 1}/{count}: {filename}")
        download_ee_image(
            image,
            filename,
            region,
            crs,
            crs_transform,
            scale,
            resampling,
            dtype,
            overwrite,
            num_threads,
            max_tile_size,
            max_tile_dim,
            shape,
            scale_offset,
            unmask_value,
            **kwargs,
        )

    print(f"Downloaded {count} tiles in {time.time() - start} seconds.")


def download_ee_image_tiles_parallel(
    image,
    features,
    out_dir=None,
    prefix=None,
    crs=None,
    crs_transform=None,
    scale=None,
    resampling="near",
    dtype=None,
    overwrite=True,
    num_threads=None,
    max_tile_size=None,
    max_tile_dim=None,
    shape=None,
    scale_offset=False,
    unmask_value=None,
    column=None,
    job_args={"n_jobs": -1},
    ee_init=True,
    project_id=None,
    **kwargs,
):
    """Download an Earth Engine Image as small tiles based on ee.FeatureCollection. Images larger than the `Earth Engine size limit are split and downloaded as
        separate tiles, then re-assembled into a single GeoTIFF. See https://github.com/dugalh/geedim/blob/main/geedim/download.py#L574

    Args:
        image (ee.Image): The image to be downloaded.
        features (ee.FeatureCollection): The features to loop through to download image.
        out_dir (str, optional): The output directory. Defaults to None.
        prefix (str, optional): The prefix for the output file. Defaults to None.
        crs (str, optional): Reproject image(s) to this EPSG or WKT CRS.  Where image bands have different CRSs, all are
            re-projected to this CRS. Defaults to the CRS of the minimum scale band.
        crs_transform (list, optional): tuple of float, list of float, rio.Affine, optional
            List of 6 numbers specifying an affine transform in the specified CRS.  In row-major order:
            [xScale, xShearing, xTranslation, yShearing, yScale, yTranslation].  All bands are re-projected to
            this transform.
        scale (float, optional): Resample image(s) to this pixel scale (size) (m).  Where image bands have different scales,
            all are resampled to this scale.  Defaults to the minimum scale of image bands.
        resampling (ResamplingMethod, optional): Resampling method, can be 'near', 'bilinear', 'bicubic', or 'average'. Defaults to None.
        dtype (str, optional): Convert to this data type (`uint8`, `int8`, `uint16`, `int16`, `uint32`, `int32`, `float32`
            or `float64`).  Defaults to auto select a minimum size type that can represent the range of pixel values.
        overwrite (bool, optional): Overwrite the destination file if it exists. Defaults to True.
        num_threads (int, optional): Number of tiles to download concurrently. Defaults to a sensible auto value.
        max_tile_size: int, optional
            Maximum tile size (MB).  If None, defaults to the Earth Engine download size limit (32 MB).
        max_tile_dim: int, optional
            Maximum tile width/height (pixels).  If None, defaults to Earth Engine download limit (10000).
        shape: tuple of int, optional
            (height, width) dimensions to export (pixels).
        scale_offset: bool, optional
            Whether to apply any EE band scales and offsets to the image.
        unmask_value (float, optional): The value to use for pixels that are masked in the input image. If the exported image contains zero values,
            you should set the unmask value to a  non-zero value so that the zero values are not treated as missing data. Defaults to None.
        column (str, optional): The column name in the feature collection to use as the filename. Defaults to None.
        job_args (dict, optional): The arguments to pass to joblib.Parallel. Defaults to {"n_jobs": -1}.
        ee_init (bool, optional): Whether to initialize Earth Engine. Defaults to True.
        project_id (str, optional): The Earth Engine project ID. Defaults to None.

    """
    import joblib
    import time

    start = time.time()

    if os.environ.get("USE_MKDOCS") is not None:
        return

    if not isinstance(features, ee.FeatureCollection):
        raise ValueError("features must be an ee.FeatureCollection.")

    if out_dir is None:
        out_dir = os.getcwd()

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if prefix is None:
        prefix = ""

    count = features.size().getInfo()
    if column is not None:
        names = features.aggregate_array(column).getInfo()
    else:
        names = [str(i + 1).zfill(len(str(count))) for i in range(count)]
    collection = features.toList(count)

    def download_data(index):
        if ee_init:
            ee_initialize(
                opt_url="https://earthengine-highvolume.googleapis.com",
                project=project_id,
            )
        region = ee.Feature(collection.get(index)).geometry()
        filename = os.path.join(
            out_dir, "{}{}.tif".format(prefix, names[index].replace("/", "_"))
        )
        print(f"Downloading {index + 1}/{count}: {filename}")

        download_ee_image(
            image,
            filename,
            region,
            crs,
            crs_transform,
            scale,
            resampling,
            dtype,
            overwrite,
            num_threads,
            max_tile_size,
            max_tile_dim,
            shape,
            scale_offset,
            unmask_value,
            **kwargs,
        )

    with joblib.Parallel(**job_args) as parallel:
        parallel(joblib.delayed(download_data)(index) for index in range(count))

    end = time.time()
    print(f"Finished in {end - start} seconds.")


def download_ee_image_collection(
    collection,
    out_dir=None,
    filenames=None,
    region=None,
    crs=None,
    crs_transform=None,
    scale=None,
    resampling="near",
    dtype=None,
    overwrite=True,
    num_threads=None,
    max_tile_size=None,
    max_tile_dim=None,
    shape=None,
    scale_offset=False,
    unmask_value=None,
    **kwargs,
):
    """Download an Earth Engine ImageCollection as GeoTIFFs. Images larger than the `Earth Engine size limit are split and downloaded as
        separate tiles, then re-assembled into a single GeoTIFF. See https://github.com/dugalh/geedim/blob/main/geedim/download.py#L574

    Args:
        collection (ee.ImageCollection): The image collection to be downloaded.
        out_dir (str, optional): The directory to save the downloaded images. Defaults to the current directory.
        filenames (list, optional): A list of filenames to use for the downloaded images. Defaults to the image ID.
        region (ee.Geometry, optional): Region defined by geojson polygon in WGS84. Defaults to the entire image granule.
        crs (str, optional): Reproject image(s) to this EPSG or WKT CRS.  Where image bands have different CRSs, all are
            re-projected to this CRS. Defaults to the CRS of the minimum scale band.
        crs_transform (list, optional): tuple of float, list of float, rio.Affine, optional
            List of 6 numbers specifying an affine transform in the specified CRS.  In row-major order:
            [xScale, xShearing, xTranslation, yShearing, yScale, yTranslation].  All bands are re-projected to
            this transform.
        scale (float, optional): Resample image(s) to this pixel scale (size) (m).  Where image bands have different scales,
            all are resampled to this scale.  Defaults to the minimum scale of image bands.
        resampling (ResamplingMethod, optional): Resampling method, can be 'near', 'bilinear', 'bicubic', or 'average'. Defaults to None.
        dtype (str, optional): Convert to this data type (`uint8`, `int8`, `uint16`, `int16`, `uint32`, `int32`, `float32`
            or `float64`).  Defaults to auto select a minimum size type that can represent the range of pixel values.
        overwrite (bool, optional): Overwrite the destination file if it exists. Defaults to True.
        num_threads (int, optional): Number of tiles to download concurrently. Defaults to a sensible auto value.
        max_tile_size: int, optional
            Maximum tile size (MB).  If None, defaults to the Earth Engine download size limit (32 MB).
        max_tile_dim: int, optional
            Maximum tile width/height (pixels).  If None, defaults to Earth Engine download limit (10000).
        shape: tuple of int, optional
            (height, width) dimensions to export (pixels).
        scale_offset: bool, optional
            Whether to apply any EE band scales and offsets to the image.
        unmask_value (float, optional): The value to use for pixels that are masked in the input image. If the exported image contains zero values,
            you should set the unmask value to a  non-zero value so that the zero values are not treated as missing data. Defaults to None.
    """

    if not isinstance(collection, ee.ImageCollection):
        raise ValueError("ee_object must be an ee.ImageCollection.")

    if out_dir is None:
        out_dir = os.getcwd()

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        count = int(collection.size().getInfo())
        print(f"Total number of images: {count}\n")

        if filenames is not None:
            if len(filenames) != count:
                raise ValueError(
                    f"The number of filenames must match the number of image: {count}"
                )

        for i in range(0, count):
            image = ee.Image(collection.toList(count).get(i))
            if filenames is not None:
                name = filenames[i]
                if not name.endswith(".tif"):
                    name = name + ".tif"
            else:
                name = image.get("system:index").getInfo() + ".tif"
            filename = os.path.join(os.path.abspath(out_dir), name)
            print(f"Downloading {i + 1}/{count}: {name}")
            download_ee_image(
                image,
                filename,
                region,
                crs,
                crs_transform,
                scale,
                resampling,
                dtype,
                overwrite,
                num_threads,
                max_tile_size,
                max_tile_dim,
                shape,
                scale_offset,
                unmask_value,
                **kwargs,
            )

    except Exception as e:
        raise Exception(f"Error downloading image collection: {e}")


def get_palette_colors(cmap_name=None, n_class=None, hashtag=False):
    """Get a palette from a matplotlib colormap. See the list of colormaps at https://matplotlib.org/stable/tutorials/colors/colormaps.html.

    Args:
        cmap_name (str, optional): The name of the matplotlib colormap. Defaults to None.
        n_class (int, optional): The number of colors. Defaults to None.
        hashtag (bool, optional): Whether to return a list of hex colors. Defaults to False.

    Returns:
        list: A list of hex colors.
    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    try:
        cmap = plt.get_cmap(cmap_name, n_class)
    except:
        cmap = plt.cm.get_cmap(cmap_name, n_class)
    colors = [mpl.colors.rgb2hex(cmap(i))[1:] for i in range(cmap.N)]
    if hashtag:
        colors = ["#" + i for i in colors]
    return colors


def plot_raster(
    image,
    band=None,
    cmap="terrain",
    proj="EPSG:3857",
    figsize=None,
    open_kwargs={},
    **kwargs,
):
    """Plot a raster image.

    Args:
        image (str | xarray.DataArray ): The input raster image, can be a file path, HTTP URL, or xarray.DataArray.
        band (int, optional): The band index, starting from zero. Defaults to None.
        cmap (str, optional): The matplotlib colormap to use. Defaults to "terrain".
        proj (str, optional): The EPSG projection code. Defaults to "EPSG:3857".
        figsize (tuple, optional): The figure size as a tuple, such as (10, 8). Defaults to None.
        open_kwargs (dict, optional): The keyword arguments to pass to rioxarray.open_rasterio. Defaults to {}.
        **kwargs: Additional keyword arguments to pass to xarray.DataArray.plot().

    """
    if os.environ.get("USE_MKDOCS") is not None:
        return

    if in_colab_shell():
        print("The plot_raster() function is not supported in Colab.")
        return

    try:
        import pvxarray
        import rioxarray
        import xarray
    except ImportError:
        raise ImportError(
            "pyxarray and rioxarray are required for plotting. Please install them using 'pip install rioxarray pyvista-xarray'."
        )

    if isinstance(image, str):
        da = rioxarray.open_rasterio(image, **open_kwargs)
    elif isinstance(image, xarray.DataArray):
        da = image
    else:
        raise ValueError("image must be a string or xarray.Dataset.")

    if band is not None:
        da = da[dict(band=band)]

    da = da.rio.reproject(proj)
    kwargs["cmap"] = cmap
    kwargs["figsize"] = figsize
    da.plot(**kwargs)


def plot_raster_3d(
    image,
    band=None,
    cmap="terrain",
    factor=1.0,
    proj="EPSG:3857",
    background=None,
    x=None,
    y=None,
    z=None,
    order=None,
    component=None,
    open_kwargs={},
    mesh_kwargs={},
    **kwargs,
):
    """Plot a raster image in 3D.

    Args:
        image (str | xarray.DataArray): The input raster image, can be a file path, HTTP URL, or xarray.DataArray.
        band (int, optional): The band index, starting from zero. Defaults to None.
        cmap (str, optional): The matplotlib colormap to use. Defaults to "terrain".
        factor (float, optional): The scaling factor for the raster. Defaults to 1.0.
        proj (str, optional): The EPSG projection code. Defaults to "EPSG:3857".
        background (str, optional): The background color. Defaults to None.
        x (str, optional): The x coordinate. Defaults to None.
        y (str, optional): The y coordinate. Defaults to None.
        z (str, optional): The z coordinate. Defaults to None.
        order (str, optional): The order of the coordinates. Defaults to None.
        component (str, optional): The component of the coordinates. Defaults to None.
        open_kwargs (dict, optional): The keyword arguments to pass to rioxarray.open_rasterio. Defaults to {}.
        mesh_kwargs (dict, optional): The keyword arguments to pass to pyvista.mesh.warp_by_scalar(). Defaults to {}.
        **kwargs: Additional keyword arguments to pass to xarray.DataArray.plot().
    """

    if os.environ.get("USE_MKDOCS") is not None:
        return

    if in_colab_shell():
        print("The plot_raster_3d() function is not supported in Colab.")
        return

    try:
        import pvxarray
        import pyvista
        import rioxarray
        import xarray
    except ImportError:
        raise ImportError(
            "pyxarray and rioxarray are required for plotting. Please install them using 'pip install rioxarray pyvista-xarray'."
        )

    if isinstance(background, str):
        pyvista.global_theme.background = background

    if isinstance(image, str):
        da = rioxarray.open_rasterio(image, **open_kwargs)
    elif isinstance(image, xarray.DataArray):
        da = image
    else:
        raise ValueError("image must be a string or xarray.Dataset.")

    if band is not None:
        da = da[dict(band=band)]

    da = da.rio.reproject(proj)
    mesh_kwargs["factor"] = factor
    kwargs["cmap"] = cmap

    coords = list(da.coords)

    if x is None:
        if "x" in coords:
            x = "x"
        elif "lon" in coords:
            x = "lon"
    if y is None:
        if "y" in coords:
            y = "y"
        elif "lat" in coords:
            y = "lat"
    if z is None:
        if "z" in coords:
            z = "z"
        elif "elevation" in coords:
            z = "elevation"
        elif "band" in coords:
            z = "band"

    # Grab the mesh object for use with PyVista
    mesh = da.pyvista.mesh(x=x, y=y, z=z, order=order, component=component)

    # Warp top and plot in 3D
    mesh.warp_by_scalar(**mesh_kwargs).plot(**kwargs)


def display_html(src, width=950, height=600):
    """Display an HTML file in a Jupyter Notebook.

    Args
        src (str): File path to HTML file.
        width (int, optional): Width of the map. Defaults to 950.
        height (int, optional): Height of the map. Defaults to 600.
    """
    if not os.path.isfile(src):
        raise ValueError(f"{src} is not a valid file path.")
    display(IFrame(src=src, width=width, height=height))


def bbox_coords(geometry, decimals=4):
    """Get the bounding box coordinates of a geometry.

    Args:
        geometry (ee.Geometry | ee.FeatureCollection): The input geometry.
        decimals (int, optional): The number of decimals to round to. Defaults to 4.

    Returns:
        list: The bounding box coordinates in the form [west, south, east, north].
    """
    if isinstance(geometry, ee.FeatureCollection):
        geometry = geometry.geometry()

    if geometry is not None:
        if not isinstance(geometry, ee.Geometry):
            raise ValueError("geometry must be an ee.Geometry.")

        coords = geometry.bounds().coordinates().getInfo()[0]
        x = [p[0] for p in coords]
        y = [p[1] for p in coords]
        west = round(min(x), decimals)
        east = round(max(x), decimals)
        south = round(min(y), decimals)
        north = round(max(y), decimals)
        return [west, south, east, north]
    else:
        return None


def requireJS(lib_path=None, Map=None):
    """Import Earth Engine JavaScript libraries. Based on the Open Earth Engine Library (OEEL).
        For more info, visit https://www.open-geocomputing.org/OpenEarthEngineLibrary.

    Args:
        lib_path (str, optional): A local file path or HTTP URL to a JavaScript library. It can also be in a format like 'users/gena/packages:grid'. Defaults to None.
        Map (geemap.Map, optional): An geemap.Map object. Defaults to None.

    Returns:
        object: oeel object.
    """
    try:
        from oeel import oeel
    except ImportError:
        raise ImportError(
            "oeel is required for requireJS. Please install it using 'pip install oeel'."
        )

    ee_initialize()

    if lib_path is None:
        if Map is not None:
            oeel.setMap(Map)
        return oeel
    elif isinstance(lib_path, str):
        if lib_path.startswith("http"):
            lib_path = get_direct_url(lib_path)

        lib_path = change_require(lib_path)

        if Map is not None:
            oeel.setMap(Map)
        return oeel.requireJS(lib_path)

    else:
        raise ValueError("lib_path must be a string.")


def setupJS():
    """Install npm packages for Earth Engine JavaScript libraries. Based on the Open Earth Engine Library (OEEL)."""
    try:
        os.system("npm install @google/earthengine")
        os.system("npm install zeromq@6.0.0-beta.6")
        os.system("npm install request")
    except Exception as e:
        raise Exception(
            f"Error installing npm packages: {e}. Make sure that you have installed nodejs. See https://nodejs.org/"
        )


def change_require(lib_path):
    if not isinstance(lib_path, str):
        raise ValueError("lib_path must be a string.")

    if lib_path.startswith("http"):
        if lib_path.startswith("https://github.com") and "blob" in lib_path:
            lib_path = lib_path.replace("blob", "raw")
        basename = os.path.basename(lib_path)
        r = requests.get(lib_path, allow_redirects=True)
        open(basename, "wb").write(r.content)
        lib_path = basename

    elif (
        lib_path.startswith("user") or lib_path.startswith("projects")
    ) and ":" in lib_path:
        repo = f'https://earthengine.googlesource.com/{lib_path.split(":")[0]}'
        start_index = lib_path.index("/", lib_path.index("/") + 1) + 1
        lib_path = lib_path[start_index:].replace(":", "/")
        if not os.path.exists(lib_path):
            cmd = f"git clone {repo}"
            os.system(cmd)

    if not os.path.exists(lib_path):
        raise ValueError(f"{lib_path} does not exist.")

    output = []
    with open(lib_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        if "require(" in line and ":" in line and (not line.strip().startswith("//")):
            new_line = "// " + line
            output.append(new_line)

            if "users/" in line:
                start_index = line.index("users/")
                end_index = line.index("/", start_index + 6)
            elif "projects" in line:
                start_index = line.index("projects/")
                end_index = line.index("/", start_index + 9)

            header = line[start_index:end_index]
            new_line = line.replace(header, os.getcwd()).replace(":", "/")
            output.append(new_line)

        else:
            output.append(line)

    with open(lib_path, "w") as f:
        f.writelines(output)

    return lib_path


def ee_vector_style(
    collection,
    column,
    labels=None,
    color="black",
    pointSize=3,
    pointShape="circle",
    width=2,
    fillColor=None,
    lineType="solid",
    neighborhood=5,
    return_fc=False,
):
    """Create a vector style for a feature collection.

    Args:
        collection (ee.FeatureCollection): The input feature collection.
        column (str): The name of the column to use for styling.
        labels (list, optional): A list of labels to use for styling. Defaults to None.
        color (str | list, optional): A default color (CSS 3.0 color value e.g. 'FF0000' or 'red') to use for drawing the features. Supports opacity (e.g.: 'FF000088' for 50% transparent red). Defaults to "black".
        pointSize (int | list, optional): The default size in pixels of the point markers. Defaults to 3.
        pointShape (str | list, optional): The default shape of the marker to draw at each point location. One of: circle, square, diamond, cross, plus, pentagram, hexagram, triangle, triangle_up, triangle_down, triangle_left, triangle_right, pentagon, hexagon, star5, star6. This argument also supports the following Matlab marker abbreviations: o, s, d, x, +, p, h, ^, v, <, >. Defaults to "circle".
        width (int | list, optional): The default line width for lines and outlines for polygons and point shapes. Defaults to 2.
        fillColor (str | list, optional): The color for filling polygons and point shapes. Defaults to 'color' at 0.66 opacity. Defaults to None.
        lineType (str | list, optional): The default line style for lines and outlines of polygons and point shapes. Defaults to 'solid'. One of: solid, dotted, dashed. Defaults to "solid".
        neighborhood (int, optional): If styleProperty is used and any feature has a pointSize or width larger than the defaults, tiling artifacts can occur. Specifies the maximum neighborhood (pointSize + width) needed for any feature. Defaults to 5.
        return_fc (bool, optional): If True, return an ee.FeatureCollection with a style property. Otherwise, return a styled ee.Image. Defaults to False.

    Returns:
        ee.FeatureCollection | ee.Image: The styled Earth Engine FeatureCollection or Image.
    """
    if not isinstance(collection, ee.FeatureCollection):
        raise ValueError("collection must be an ee.FeatureCollection.")

    if not isinstance(column, str):
        raise ValueError("column must be a string.")

    prop_names = ee.Feature(collection.first()).propertyNames().getInfo()
    if column not in prop_names:
        raise ValueError(
            f"{column} is not a property name of the collection. It must be one of {','.join(prop_names)}."
        )

    if labels is None:
        labels = collection.aggregate_array(column).distinct().sort().getInfo()
    elif isinstance(labels, list):
        collection = collection.filter(ee.Filter.inList(column, labels))
    elif not isinstance(labels, list):
        raise ValueError("labels must be a list.")

    size = len(labels)
    if isinstance(color, str):
        color = [color] * size
    elif size != len(color):
        raise ValueError("labels and color must be the same length.")
    elif not isinstance(color, list):
        raise ValueError("color must be a string or a list.")

    if isinstance(pointSize, int):
        pointSize = [pointSize] * size
    elif not isinstance(pointSize, list):
        raise ValueError("pointSize must be an integer or a list.")

    if isinstance(pointShape, str):
        pointShape = [pointShape] * size
    elif not isinstance(pointShape, list):
        raise ValueError("pointShape must be a string or a list.")

    if isinstance(width, int):
        width = [width] * size
    elif not isinstance(width, list):
        raise ValueError("width must be an integer or a list.")

    if fillColor is None:
        fillColor = color
    elif isinstance(fillColor, str):
        fillColor = [fillColor] * size
    elif not isinstance(fillColor, list):
        raise ValueError("fillColor must be a list.")

    if not isinstance(neighborhood, int):
        raise ValueError("neighborhood must be an integer.")

    if isinstance(lineType, str):
        lineType = [lineType] * size
    elif not isinstance(lineType, list):
        raise ValueError("lineType must be a string or list.")

    style_dict = {}

    for i, label in enumerate(labels):
        style_dict[label] = {
            "color": color[i],
            "pointSize": pointSize[i],
            "pointShape": pointShape[i],
            "width": width[i],
            "fillColor": fillColor[i],
            "lineType": lineType[i],
        }

    style = ee.Dictionary(style_dict)

    result = collection.map(lambda f: f.set("style", style.get(f.get(column))))

    if return_fc:
        return result
    else:
        return result.style(**{"styleProperty": "style", "neighborhood": neighborhood})


def get_direct_url(url):
    """Get the direct URL for a given URL.

    Args:
        url (str): The URL to get the direct URL for.

    Returns:
        str: The direct URL.
    """

    if not isinstance(url, str):
        raise ValueError("url must be a string.")

    if not url.startswith("http"):
        raise ValueError("url must start with http.")

    r = requests.head(url, allow_redirects=True)
    return r.url


def add_crs(filename, epsg):
    """Add a CRS to a raster dataset.

    Args:
        filename (str): The filename of the raster dataset.
        epsg (int | str): The EPSG code of the CRS.

    """
    try:
        import rasterio
    except ImportError:
        raise ImportError(
            "rasterio is required for adding a CRS to a raster. Please install it using 'pip install rasterio'."
        )

    if not os.path.exists(filename):
        raise ValueError("filename must exist.")

    if isinstance(epsg, int):
        epsg = f"EPSG:{epsg}"
    elif isinstance(epsg, str):
        epsg = "EPSG:" + epsg
    else:
        raise ValueError("epsg must be an integer or string.")

    crs = rasterio.crs.CRS({"init": epsg})
    with rasterio.open(filename, mode="r+") as src:
        src.crs = crs


def jrc_hist_monthly_history(
    collection=None,
    region=None,
    start_date="1984-03-16",
    end_date=None,
    start_month=1,
    end_month=12,
    scale=None,
    frequency="year",
    reducer="mean",
    denominator=1e4,
    x_label=None,
    y_label=None,
    title=None,
    width=None,
    height=None,
    layout_args={},
    return_df=False,
    **kwargs,
):
    """Create a JRC monthly history plot.

    Args:
        collection (ee.ImageCollection, optional): The image collection of JRC surface water monthly history.
            Default to ee.ImageCollection('JRC/GSW1_4/MonthlyHistory')
        region (ee.Geometry | ee.FeatureCollection, optional): The region to plot. Default to None.
        start_date (str, optional): The start date of the plot. Default to '1984-03-16'.
        end_date (str, optional): The end date of the plot. Default to the current date.
        start_month (int, optional): The start month of the plot. Default to 1.
        end_month (int, optional): The end month of the plot. Default to 12.
        scale (float, optional): The scale to compute the statistics. Default to None.
        frequency (str, optional): The frequency of the plot. Can be either 'year' or 'month', Default to 'year'.
        reducer (str, optional): The reducer to compute the statistics. Can be either 'mean', 'min', 'max', 'median', etc. Default to 'mean'.
        denominator (int, optional): The denominator to convert area from square meters to other units. Default to 1e4, converting to hectares.
        x_label (str, optional): Label for the x axis. Defaults to None.
        y_label (str, optional): Label for the y axis. Defaults to None.
        title (str, optional): Title for the plot. Defaults to None.
        width (int, optional): Width of the plot in pixels. Defaults to None.
        height (int, optional): Height of the plot in pixels. Defaults to 500.
        layout_args (dict, optional): Layout arguments for the plot to be passed to fig.update_layout(),
        return_df (bool, optional): Whether to return the dataframe of the plot. Defaults to False.

    Returns:
        pd.DataFrame: Pandas dataframe of the plot.
    """

    from datetime import date
    import pandas as pd
    import plotly.express as px

    if end_date is None:
        end_date = date.today().strftime("%Y-%m-%d")

    if collection is None:
        collection = ee.ImageCollection("JRC/GSW1_4/MonthlyHistory")

    if frequency not in ["year", "month"]:
        raise ValueError("frequency must be 'year' or 'month'.")

    images = (
        collection.filterDate(start_date, end_date)
        .filter(ee.Filter.calendarRange(start_month, end_month, "month"))
        .map(lambda img: img.eq(2).selfMask())
    )

    def cal_area(img):
        pixel_area = img.multiply(ee.Image.pixelArea()).divide(denominator)
        img_area = pixel_area.reduceRegion(
            **{
                "geometry": region,
                "reducer": ee.Reducer.sum(),
                "scale": scale,
                "maxPixels": 1e12,
                "bestEffort": True,
            }
        )
        return img.set({"area": img_area})

    areas = images.map(cal_area)
    stats = areas.aggregate_array("area").getInfo()
    values = [item["water"] for item in stats]
    labels = areas.aggregate_array("system:index").getInfo()
    months = [label.split("_")[1] for label in labels]

    if frequency == "month":
        area_df = pd.DataFrame({"Month": labels, "Area": values, "month": months})
    else:
        dates = [d[:4] for d in labels]
        data_dict = {"Date": labels, "Year": dates, "Area": values}
        df = pd.DataFrame(data_dict)
        result = df.groupby("Year").agg(reducer)
        area_df = pd.DataFrame({"Year": result.index, "Area": result["Area"]})
        area_df = area_df.reset_index(drop=True)

    if return_df:
        return area_df
    else:
        labels = {}

        if x_label is not None:
            labels[frequency.title()] = x_label
        if y_label is not None:
            labels["Area"] = y_label

        fig = px.bar(
            area_df,
            x=frequency.title(),
            y="Area",
            labels=labels,
            title=title,
            width=width,
            height=height,
            **kwargs,
        )

        fig.update_layout(**layout_args)

        return fig


def html_to_streamlit(
    filename, width=None, height=None, scrolling=False, replace_dict={}
):
    """Renders an HTML file as a Streamlit component.
    Args:
        filename (str): The filename of the HTML file.
        width (int, optional): Width of the map. Defaults to None.
        height (int, optional): Height of the map. Defaults to 600.
        scrolling (bool, optional): Whether to allow the map to scroll. Defaults to False.
        replace_dict (dict, optional): A dictionary of strings to replace in the HTML file. Defaults to {}.

    Raises:
        ValueError: If the filename does not exist.

    Returns:
        streamlit.components: components.html object.
    """

    import streamlit.components.v1 as components

    if not os.path.exists(filename):
        raise ValueError("filename must exist.")

    f = open(filename, "r")

    html = f.read()

    for key, value in replace_dict.items():
        html = html.replace(key, value)

    f.close()
    return components.html(html, width=width, height=height, scrolling=scrolling)


def image_convolution(
    image, kernel=None, resample=None, projection="EPSG:3857", **kwargs
):
    """Performs a convolution on an image.

    Args:
        image (ee.Image | ee.ImageCollection): The image to convolve.
        kernel (ee.Kernel, optional): The kernel to convolve with. Defaults to None, a 7x7 gaussian kernel.
        resample (str, optional): The resample method to use. It can be either 'bilinear' or 'bicubic'". Defaults to None, which uses the image's resample method.
        projection (str, optional): The projection to use. Defaults to 'EPSG:3857'.

    Returns:
        ee.Image: The convolved image.
    """
    if isinstance(image, ee.ImageCollection):
        image = image.mosaic()
    elif not isinstance(image, ee.Image):
        raise ValueError("image must be an ee.Image or ee.ImageCollection.")

    if kernel is None:
        kernel = ee.Kernel.gaussian(radius=3, sigma=2, units="pixels", normalize=True)
    elif not isinstance(kernel, ee.Kernel):
        raise ValueError("kernel must be an ee.Kernel.")

    if resample is not None:
        if resample not in ["bilinear", "bicubic"]:
            raise ValueError("resample must be one of 'bilinear' or 'bicubic'")

    result = image.convolve(kernel)

    if resample is not None:
        result = result.resample(resample)

    return result.setDefaultProjection(projection)


def download_ned(region, out_dir=None, return_url=False, download_args={}, **kwargs):
    """Download the US National Elevation Datasets (NED) for a region.

    Args:
        region (str | list): A filepath to a vector dataset or a list of bounds in the form of [minx, miny, maxx, maxy].
        out_dir (str, optional): The directory to download the files to. Defaults to None, which uses the current working directory.
        return_url (bool, optional): Whether to return the download URLs of the files. Defaults to False.
        download_args (dict, optional): A dictionary of arguments to pass to the download_file function. Defaults to {}.

    Returns:
        list: A list of the download URLs of the files if return_url is True.
    """
    import geopandas as gpd

    if out_dir is None:
        out_dir = os.getcwd()
    else:
        out_dir = os.path.abspath(out_dir)

    if isinstance(region, str):
        if region.startswith("http"):
            region = github_raw_url(region)
            region = download_file(region)
        elif not os.path.exists(region):
            raise ValueError("region must be a path or a URL to a vector dataset.")

        roi = gpd.read_file(region, **kwargs)
        roi = roi.to_crs(epsg=4326)
        bounds = roi.total_bounds

    elif isinstance(region, list):
        bounds = region

    else:
        raise ValueError(
            "region must be a filepath or a list of bounds in the form of [minx, miny, maxx, maxy]."
        )
    minx, miny, maxx, maxy = [float(x) for x in bounds]
    tiles = []
    left = abs(math.floor(minx))
    right = abs(math.floor(maxx)) - 1
    upper = math.ceil(maxy)
    bottom = math.ceil(miny) - 1

    for y in range(upper, bottom, -1):
        for x in range(left, right, -1):
            tile_id = "n{}w{}".format(str(y).zfill(2), str(x).zfill(3))
            tiles.append(tile_id)

    links = []
    filepaths = []

    for index, tile in enumerate(tiles):
        tif_url = f"https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/{tile}/USGS_13_{tile}.tif"

        r = requests.head(tif_url)
        if r.status_code == 200:
            tif = os.path.join(out_dir, os.path.basename(tif_url))
            links.append(tif_url)
            filepaths.append(tif)
        else:
            print(f"{tif_url} does not exist.")

    if return_url:
        return links
    else:
        for index, link in enumerate(links):
            print(f"Downloading {index + 1} of {len(links)}: {os.path.basename(link)}")
            download_file(link, filepaths[index], **download_args)


def mosaic(images, output, merge_args={}, verbose=True, **kwargs):
    """Mosaics a list of images into a single image. Inspired by https://bit.ly/3A6roDK.

    Args:
        images (str | list): An input directory containing images or a list of images.
        output (str): The output image filepath.
        merge_args (dict, optional): A dictionary of arguments to pass to the rasterio.merge function. Defaults to {}.
        verbose (bool, optional): Whether to print progress. Defaults to True.

    """
    from rasterio.merge import merge
    import rasterio as rio
    from pathlib import Path

    output = os.path.abspath(output)

    if isinstance(images, str):
        path = Path(images)
        raster_files = list(path.iterdir())
    elif isinstance(images, list):
        raster_files = images
    else:
        raise ValueError("images must be a list of raster files.")

    raster_to_mosiac = []

    if not os.path.exists(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))

    for index, p in enumerate(raster_files):
        if verbose:
            print(f"Reading {index+1}/{len(raster_files)}: {os.path.basename(p)}")
        raster = rio.open(p, **kwargs)
        raster_to_mosiac.append(raster)

    if verbose:
        print("Merging rasters...")
    arr, transform = merge(raster_to_mosiac, **merge_args)

    output_meta = raster.meta.copy()
    output_meta.update(
        {
            "driver": "GTiff",
            "height": arr.shape[1],
            "width": arr.shape[2],
            "transform": transform,
        }
    )

    with rio.open(output, "w", **output_meta) as m:
        m.write(arr)


def reproject(image, output, dst_crs="EPSG:4326", resampling="nearest", **kwargs):
    """Reprojects an image.

    Args:
        image (str): The input image filepath.
        output (str): The output image filepath.
        dst_crs (str, optional): The destination CRS. Defaults to "EPSG:4326".
        resampling (Resampling, optional): The resampling method. Defaults to "nearest".
        **kwargs: Additional keyword arguments to pass to rasterio.open.

    """
    import rasterio as rio
    from rasterio.warp import calculate_default_transform, reproject, Resampling

    if isinstance(resampling, str):
        resampling = getattr(Resampling, resampling)

    image = os.path.abspath(image)
    output = os.path.abspath(output)

    if not os.path.exists(os.path.dirname(output)):
        os.makedirs(os.path.dirname(output))

    with rio.open(image, **kwargs) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        kwargs = src.meta.copy()
        kwargs.update(
            {
                "crs": dst_crs,
                "transform": transform,
                "width": width,
                "height": height,
            }
        )

        with rio.open(output, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=resampling,
                    **kwargs,
                )


def download_3dep_lidar(region, filename, scale=1.0, crs="EPSG:3857"):
    dataset = ee.ImageCollection("USGS/3DEP/1m")

    if isinstance(region, ee.Geometry) or isinstance(region, ee.Feature):
        region = ee.FeatureCollection([region])

    if isinstance(region, ee.FeatureCollection):
        image = dataset.filterBounds(region).mosaic().clipToCollection(region)

    download_ee_image(image, filename, region=region.geometry(), scale=scale, crs=crs)


def use_mkdocs():
    """Test if the current notebook is running in mkdocs.

    Returns:
        bool: True if the notebook is running in mkdocs.
    """
    if os.environ.get("USE_MKDOCS") is not None:
        return True
    else:
        return False


def create_legend(
    title="Legend",
    labels=None,
    colors=None,
    legend_dict=None,
    builtin_legend=None,
    opacity=1.0,
    position="bottomright",
    draggable=True,
    output=None,
    style={},
):
    """Create a legend in HTML format. Reference: https://bit.ly/3oV6vnH

    Args:
        title (str, optional): Title of the legend. Defaults to 'Legend'. Defaults to "Legend".
        colors (list, optional): A list of legend colors. Defaults to None.
        labels (list, optional): A list of legend labels. Defaults to None.
        legend_dict (dict, optional): A dictionary containing legend items as keys and color as values.
            If provided, legend_keys and legend_colors will be ignored. Defaults to None.
        builtin_legend (str, optional): Name of the builtin legend to add to the map. Defaults to None.
        opacity (float, optional): The opacity of the legend. Defaults to 1.0.
        position (str, optional): The position of the legend, can be one of the following:
            "topleft", "topright", "bottomleft", "bottomright". Defaults to "bottomright".
        draggable (bool, optional): If True, the legend can be dragged to a new position. Defaults to True.
        output (str, optional): The output file path (*.html) to save the legend. Defaults to None.
        style: Additional keyword arguments to style the legend, such as position, bottom, right, z-index,
            border, background-color, border-radius, padding, font-size, etc. The default style is:
            style = {
                'position': 'fixed',
                'z-index': '9999',
                'border': '2px solid grey',
                'background-color': 'rgba(255, 255, 255, 0.8)',
                'border-radius': '5px',
                'padding': '10px',
                'font-size': '14px',
                'bottom': '20px',
                'right': '5px'
            }

    Returns:
        str: The HTML code of the legend.
    """

    import pkg_resources
    from .legends import builtin_legends

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    legend_template = os.path.join(pkg_dir, "data/template/legend_style.html")

    if draggable:
        legend_template = os.path.join(pkg_dir, "data/template/legend.txt")

    if not os.path.exists(legend_template):
        raise FileNotFoundError("The legend template does not exist.")

    if labels is not None:
        if not isinstance(labels, list):
            print("The legend keys must be a list.")
            return
    else:
        labels = ["One", "Two", "Three", "Four", "etc"]

    if colors is not None:
        if not isinstance(colors, list):
            print("The legend colors must be a list.")
            return
        elif all(isinstance(item, tuple) for item in colors):
            try:
                colors = [rgb_to_hex(x) for x in colors]
            except Exception as e:
                print(e)
        elif all((item.startswith("#") and len(item) == 7) for item in colors):
            pass
        elif all((len(item) == 6) for item in colors):
            pass
        else:
            print("The legend colors must be a list of tuples.")
            return
    else:
        colors = [
            "#8DD3C7",
            "#FFFFB3",
            "#BEBADA",
            "#FB8072",
            "#80B1D3",
        ]

    if len(labels) != len(colors):
        print("The legend keys and values must be the same length.")
        return

    allowed_builtin_legends = builtin_legends.keys()
    if builtin_legend is not None:
        if builtin_legend not in allowed_builtin_legends:
            print(
                "The builtin legend must be one of the following: {}".format(
                    ", ".join(allowed_builtin_legends)
                )
            )
            return
        else:
            legend_dict = builtin_legends[builtin_legend]
            labels = list(legend_dict.keys())
            colors = list(legend_dict.values())

    if legend_dict is not None:
        if not isinstance(legend_dict, dict):
            print("The legend dict must be a dictionary.")
            return
        else:
            labels = list(legend_dict.keys())
            colors = list(legend_dict.values())
            if all(isinstance(item, tuple) for item in colors):
                try:
                    colors = [rgb_to_hex(x) for x in colors]
                except Exception as e:
                    print(e)

    allowed_positions = [
        "topleft",
        "topright",
        "bottomleft",
        "bottomright",
    ]
    if position not in allowed_positions:
        raise ValueError(
            "The position must be one of the following: {}".format(
                ", ".join(allowed_positions)
            )
        )

    if position == "bottomright":
        if "bottom" not in style:
            style["bottom"] = "20px"
        if "right" not in style:
            style["right"] = "5px"
        if "left" in style:
            del style["left"]
        if "top" in style:
            del style["top"]
    elif position == "bottomleft":
        if "bottom" not in style:
            style["bottom"] = "5px"
        if "left" not in style:
            style["left"] = "5px"
        if "right" in style:
            del style["right"]
        if "top" in style:
            del style["top"]
    elif position == "topright":
        if "top" not in style:
            style["top"] = "5px"
        if "right" not in style:
            style["right"] = "5px"
        if "left" in style:
            del style["left"]
        if "bottom" in style:
            del style["bottom"]
    elif position == "topleft":
        if "top" not in style:
            style["top"] = "5px"
        if "left" not in style:
            style["left"] = "5px"
        if "right" in style:
            del style["right"]
        if "bottom" in style:
            del style["bottom"]

    if "position" not in style:
        style["position"] = "fixed"
    if "z-index" not in style:
        style["z-index"] = "9999"
    if "background-color" not in style:
        style["background-color"] = "rgba(255, 255, 255, 0.8)"
    if "padding" not in style:
        style["padding"] = "10px"
    if "border-radius" not in style:
        style["border-radius"] = "5px"
    if "font-size" not in style:
        style["font-size"] = "14px"

    content = []

    with open(legend_template) as f:
        lines = f.readlines()

    if draggable:
        for index, line in enumerate(lines):
            if index < 36:
                content.append(line)
            elif index == 36:
                line = lines[index].replace("Legend", title)
                content.append(line)
            elif index < 39:
                content.append(line)
            elif index == 39:
                for i, color in enumerate(colors):
                    item = f"    <li><span style='background:{check_color(color)};opacity:{opacity};'></span>{labels[i]}</li>\n"
                    content.append(item)
            elif index > 41:
                content.append(line)
        content = content[3:-1]

    else:
        for index, line in enumerate(lines):
            if index < 8:
                content.append(line)
            elif index == 8:
                for key, value in style.items():
                    content.append(
                        "              {}: {};\n".format(key.replace("_", "-"), value)
                    )
            elif index < 17:
                pass
            elif index < 19:
                content.append(line)
            elif index == 19:
                content.append(line.replace("Legend", title))
            elif index < 22:
                content.append(line)
            elif index == 22:
                for index, key in enumerate(labels):
                    color = colors[index]
                    if not color.startswith("#"):
                        color = "#" + color
                    item = "                    <li><span style='background:{};opacity:{};'></span>{}</li>\n".format(
                        color, opacity, key
                    )
                    content.append(item)
            elif index < 33:
                pass
            else:
                content.append(line)

    legend_text = "".join(content)

    if output is not None:
        with open(output, "w") as f:
            f.write(legend_text)
    else:
        return legend_text


def is_arcpy():
    """Check if arcpy is available.

    Returns:
        book: True if arcpy is available, False otherwise.
    """
    import sys

    if "arcpy" in sys.modules:
        return True
    else:
        return False


def arc_active_map():
    """Get the active map in ArcGIS Pro.

    Returns:
        arcpy.Map: The active map in ArcGIS Pro.
    """
    if is_arcpy():
        import arcpy

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        m = aprx.activeMap
        return m
    else:
        return None


def arc_active_view():
    """Get the active view in ArcGIS Pro.

    Returns:
        arcpy.MapView: The active view in ArcGIS Pro.
    """
    if is_arcpy():
        import arcpy

        aprx = arcpy.mp.ArcGISProject("CURRENT")
        view = aprx.activeView
        return view
    else:
        return None


def arc_add_layer(url, name=None, shown=True, opacity=1.0):
    """Add a layer to the active map in ArcGIS Pro.

    Args:
        url (str): The URL of the tile layer to add.
        name (str, optional): The name of the layer. Defaults to None.
        shown (bool, optional): Whether the layer is shown. Defaults to True.
        opacity (float, optional): The opacity of the layer. Defaults to 1.0.
    """
    if is_arcpy():
        m = arc_active_map()
        if m is not None:
            m.addDataFromPath(url)
            if isinstance(name, str):
                layers = m.listLayers("Tiled service layer")
                if len(layers) > 0:
                    layer = layers[0]
                    layer.name = name
                    layer.visible = shown
                    layer.transparency = 100 - (opacity * 100)


def arc_zoom_to_extent(xmin, ymin, xmax, ymax):
    """Zoom to an extent in ArcGIS Pro.

    Args:
        xmin (float): The minimum x value of the extent.
        ymin (float): The minimum y value of the extent.
        xmax (float): The maximum x value of the extent.
        ymax (float): The maximum y value of the extent.
    """
    if is_arcpy():
        import arcpy

        view = arc_active_view()
        if view is not None:
            view.camera.setExtent(
                arcpy.Extent(
                    xmin,
                    ymin,
                    xmax,
                    ymax,
                    spatial_reference=arcpy.SpatialReference(4326),
                )
            )

        # if isinstance(zoom, int):
        #     scale = 156543.04 * math.cos(0) / math.pow(2, zoom)
        #     view.camera.scale = scale  # Not working properly


def get_current_year():
    """Get the current year.

    Returns:
        int: The current year.
    """
    today = datetime.date.today()
    return today.year


def html_to_gradio(html, width="100%", height="500px", **kwargs):
    """Converts the map to an HTML string that can be used in Gradio. Removes unsupported elements, such as
        attribution and any code blocks containing functions. See https://github.com/gradio-app/gradio/issues/3190

    Args:
        width (str, optional): The width of the map. Defaults to '100%'.
        height (str, optional): The height of the map. Defaults to '500px'.

    Returns:
        str: The HTML string to use in Gradio.
    """

    if isinstance(width, int):
        width = f"{width}px"

    if isinstance(height, int):
        height = f"{height}px"

    if isinstance(html, str):
        with open(html, "r") as f:
            lines = f.readlines()
    elif isinstance(html, list):
        lines = html
    else:
        raise TypeError("html must be a file path or a list of strings")

    output = []
    skipped_lines = []
    for index, line in enumerate(lines):
        if index in skipped_lines:
            continue
        if line.lstrip().startswith('{"attribution":'):
            continue
        elif "on(L.Draw.Event.CREATED, function(e)" in line:
            for i in range(14):
                skipped_lines.append(index + i)
        elif "L.Control.geocoder" in line:
            for i in range(5):
                skipped_lines.append(index + i)
        elif "function(e)" in line:
            print(
                f"Warning: The folium plotting backend does not support functions in code blocks. Please delete line {index + 1}."
            )
        else:
            output.append(line + "\n")

    return f"""<iframe style="width: {width}; height: {height}" name="result" allow="midi; geolocation; microphone; camera;
    display-capture; encrypted-media;" sandbox="allow-modals allow-forms
    allow-scripts allow-same-origin allow-popups
    allow-top-navigation-by-user-activation allow-downloads" allowfullscreen=""
    allowpaymentrequest="" frameborder="0" srcdoc='{"".join(output)}'></iframe>"""


def image_check(image):
    from localtileserver import TileClient

    if isinstance(image, str):
        if image.startswith("http") or os.path.exists(image):
            pass
        else:
            raise ValueError("image must be a URL or filepath.")
    elif isinstance(image, TileClient):
        pass
    else:
        raise ValueError("image must be a URL or filepath.")


def image_client(image, **kwargs):
    """Get a LocalTileserver TileClient from an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        TileClient: A LocalTileserver TileClient.
    """
    image_check(image)

    _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    return client


def image_center(image, **kwargs):
    """Get the center of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        tuple: A tuple of (latitude, longitude).
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return client.center()


def image_bounds(image, **kwargs):
    """Get the bounds of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        list: A list of bounds in the form of [(south, west), (north, east)].
    """

    image_check(image)
    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    bounds = client.bounds()
    return [(bounds[0], bounds[2]), (bounds[1], bounds[3])]


def image_metadata(image, **kwargs):
    """Get the metadata of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        dict: A dictionary of image metadata.
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return client.metadata()


def image_bandcount(image, **kwargs):
    """Get the number of bands in an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        int: The number of bands in the image.
    """

    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return len(client.metadata()["bands"])


def image_size(image, **kwargs):
    """Get the size (width, height) of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        tuple: A tuple of (width, height).
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image

    metadata = client.metadata()
    return metadata["sourceSizeX"], metadata["sourceSizeY"]


def image_projection(image, **kwargs):
    """Get the projection of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        str: The projection of the image.
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return client.metadata()["Projection"]


def image_set_crs(image, epsg):
    """Define the CRS of an image.

    Args:
        image (str): The input image filepath
        epsg (int): The EPSG code of the CRS to set.
    """

    from rasterio.crs import CRS
    import rasterio

    with rasterio.open(image, "r+") as rds:
        rds.crs = CRS.from_epsg(epsg)


def image_geotransform(image, **kwargs):
    """Get the geotransform of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        list: A list of geotransform values.
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return client.metadata()["GeoTransform"]


def image_resolution(image, **kwargs):
    """Get the resolution of an image.

    Args:
        image (str): The input image filepath or URL.

    Returns:
        float: The resolution of the image.
    """
    image_check(image)

    if isinstance(image, str):
        _, client = get_local_tile_layer(image, return_client=True, **kwargs)
    else:
        client = image
    return client.metadata()["GeoTransform"][1]


def find_files(input_dir, ext=None, fullpath=True, recursive=True):
    """Find files in a directory.

    Args:
        input_dir (str): The input directory.
        ext (str, optional): The file extension to match. Defaults to None.
        fullpath (bool, optional): Whether to return the full path. Defaults to True.
        recursive (bool, optional): Whether to search recursively. Defaults to True.

    Returns:
        list: A list of matching files.
    """

    from pathlib import Path

    files = []

    if ext is None:
        ext = "*"
    else:
        ext = ext.replace(".", "")

    ext = f"*.{ext}"

    if recursive:
        if fullpath:
            files = [str(path.joinpath()) for path in Path(input_dir).rglob(ext)]
        else:
            files = [str(path.name) for path in Path(input_dir).rglob(ext)]
    else:
        if fullpath:
            files = [str(path.joinpath()) for path in Path(input_dir).glob(ext)]
        else:
            files = [path.name for path in Path(input_dir).glob(ext)]

    return files


def zoom_level_resolution(zoom, latitude=0):
    """Returns the approximate pixel scale based on zoom level and latutude.
        See https://blogs.bing.com/maps/2006/02/25/map-control-zoom-levels-gt-resolution

    Args:
        zoom (int): The zoom level.
        latitude (float, optional): The latitude. Defaults to 0.

    Returns:
        float: Map resolution in meters.
    """
    import math

    resolution = 156543.04 * math.cos(latitude) / math.pow(2, zoom)
    return abs(resolution)


def lnglat_to_meters(longitude, latitude):
    """coordinate conversion between lat/lon in decimal degrees to web mercator

    Args:
        longitude (float): The longitude.
        latitude (float): The latitude.

    Returns:
        tuple: A tuple of (x, y) in meters.
    """
    import numpy as np

    origin_shift = np.pi * 6378137
    easting = longitude * origin_shift / 180.0
    northing = np.log(np.tan((90 + latitude) * np.pi / 360.0)) * origin_shift / np.pi

    if np.isnan(easting):
        if longitude > 0:
            easting = 20026376
        else:
            easting = -20026376

    if np.isnan(northing):
        if latitude > 0:
            northing = 20048966
        else:
            northing = -20048966

    return (easting, northing)


def meters_to_lnglat(x, y):
    """coordinate conversion between web mercator to lat/lon in decimal degrees

    Args:
        x (float): The x coordinate.
        y (float): The y coordinate.

    Returns:
        tuple: A tuple of (longitude, latitude) in decimal degrees.
    """
    import numpy as np

    origin_shift = np.pi * 6378137
    longitude = (x / origin_shift) * 180.0
    latitude = (y / origin_shift) * 180.0
    latitude = (
        180 / np.pi * (2 * np.arctan(np.exp(latitude * np.pi / 180.0)) - np.pi / 2.0)
    )
    return (longitude, latitude)


def bounds_to_xy_range(bounds):
    """Convert bounds to x and y range to be used as input to bokeh map.

    Args:
        bounds (list): A list of bounds in the form [(south, west), (north, east)] or [xmin, ymin, xmax, ymax].

    Returns:
        tuple: A tuple of (x_range, y_range).
    """

    if isinstance(bounds, tuple):
        bounds = list(bounds)
    elif not isinstance(bounds, list):
        raise TypeError("bounds must be a list")

    if len(bounds) == 4:
        west, south, east, north = bounds
    elif len(bounds) == 2:
        south, west = bounds[0]
        north, east = bounds[1]

    xmin, ymin = lnglat_to_meters(west, south)
    xmax, ymax = lnglat_to_meters(east, north)
    x_range = (xmin, xmax)
    y_range = (ymin, ymax)
    return x_range, y_range


def center_zoom_to_xy_range(center, zoom):
    """Convert center and zoom to x and y range to be used as input to bokeh map.

    Args:
        center (tuple): A tuple of (latitude, longitude).
        zoom (int): The zoom level.

    Returns:
        tuple: A tuple of (x_range, y_range).
    """

    if isinstance(center, tuple) or isinstance(center, list):
        pass
    else:
        raise TypeError("center must be a tuple or list")

    if not isinstance(zoom, int):
        raise TypeError("zoom must be an integer")

    latitude, longitude = center
    x_range = (-179, 179)
    y_range = (-70, 70)
    x_full_length = x_range[1] - x_range[0]
    y_full_length = y_range[1] - y_range[0]

    x_length = x_full_length / 2 ** (zoom - 2)
    y_length = y_full_length / 2 ** (zoom - 2)

    south = latitude - y_length / 2
    north = latitude + y_length / 2
    west = longitude - x_length / 2
    east = longitude + x_length / 2

    xmin, ymin = lnglat_to_meters(west, south)
    xmax, ymax = lnglat_to_meters(east, north)

    x_range = (xmin, xmax)
    y_range = (ymin, ymax)

    return x_range, y_range


def get_geometry_coords(row, geom, coord_type, shape_type, mercator=False):
    """
    Returns the coordinates ('x' or 'y') of edges of a Polygon exterior.

    :param: (GeoPandas Series) row : The row of each of the GeoPandas DataFrame.
    :param: (str) geom : The column name.
    :param: (str) coord_type : Whether it's 'x' or 'y' coordinate.
    :param: (str) shape_type
    """

    # Parse the exterior of the coordinate
    if shape_type.lower() in ["polygon", "multipolygon"]:
        exterior = row[geom].geoms[0].exterior
        if coord_type == "x":
            # Get the x coordinates of the exterior
            coords = list(exterior.coords.xy[0])
            if mercator:
                coords = [lnglat_to_meters(x, 0)[0] for x in coords]
            return coords

        elif coord_type == "y":
            # Get the y coordinates of the exterior
            coords = list(exterior.coords.xy[1])
            if mercator:
                coords = [lnglat_to_meters(0, y)[1] for y in coords]
            return coords

    elif shape_type.lower() in ["linestring", "multilinestring"]:
        if coord_type == "x":
            coords = list(row[geom].coords.xy[0])
            if mercator:
                coords = [lnglat_to_meters(x, 0)[0] for x in coords]
            return coords
        elif coord_type == "y":
            coords = list(row[geom].coords.xy[1])
            if mercator:
                coords = [lnglat_to_meters(0, y)[1] for y in coords]
            return coords

    elif shape_type.lower() in ["point", "multipoint"]:
        exterior = row[geom]

        if coord_type == "x":
            # Get the x coordinates of the exterior
            coords = exterior.coords.xy[0][0]
            if mercator:
                coords = lnglat_to_meters(coords, 0)[0]
            return coords

        elif coord_type == "y":
            # Get the y coordinates of the exterior
            coords = exterior.coords.xy[1][0]
            if mercator:
                coords = lnglat_to_meters(0, coords)[1]
            return coords


def landsat_scaling(image, thermal_bands=True, apply_fmask=False):
    """Apply scaling factors to a Landsat image. See an example at
        https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC09_C02_T1_L2

    Args:
        image (ee.Image): The input Landsat image.
        thermal_bands (bool, optional): Whether to apply scaling to thermal bands. Defaults to True.
        apply_fmask (bool, optional): Whether to apply Fmask cloud mask. Defaults to False.

    Returns:
        ee.Image: The scaled Landsat image.
    """

    # Apply the scaling factors to the appropriate bands.
    opticalBands = image.select("SR_B.").multiply(0.0000275).add(-0.2)
    if thermal_bands:
        thermalBands = image.select("ST_B.*").multiply(0.00341802).add(149)

    if apply_fmask:
        # Replace the original bands with the scaled ones and apply the masks.
        # Bit 0 - Fill
        # Bit 1 - Dilated Cloud
        # Bit 2 - Cirrus
        # Bit 3 - Cloud
        # Bit 4 - Cloud Shadow
        qaMask = image.select("QA_PIXEL").bitwiseAnd(int("11111", 2)).eq(0)
        if thermal_bands:
            return (
                image.addBands(thermalBands, None, True)
                .addBands(opticalBands, None, True)
                .updateMask(qaMask)
            )
        else:
            return image.addBands(opticalBands, None, True).updateMask(qaMask)

    else:
        if thermal_bands:
            return image.addBands(thermalBands, None, True).addBands(
                opticalBands, None, True
            )
        else:
            return image.addBands(opticalBands, None, True)


def tms_to_geotiff(
    output,
    bbox,
    zoom=None,
    resolution=None,
    source="OpenStreetMap",
    crs="EPSG:3857",
    to_cog=False,
    quiet=False,
    **kwargs,
):
    """Download TMS tiles and convert them to a GeoTIFF. The source is adapted from https://github.com/gumblex/tms2geotiff.
        Credits to the GitHub user @gumblex.

    Args:
        output (str): The output GeoTIFF file.
        bbox (list): The bounding box [minx, miny, maxx, maxy], e.g., [-122.5216, 37.733, -122.3661, 37.8095]
        zoom (int, optional): The map zoom level. Defaults to None.
        resolution (float, optional): The resolution in meters. Defaults to None.
        source (str, optional): The tile source. It can be one of the following: "OPENSTREETMAP", "ROADMAP",
            "SATELLITE", "TERRAIN", "HYBRID", or an HTTP URL. Defaults to "OpenStreetMap".
        crs (str, optional): The coordinate reference system. Defaults to "EPSG:3857".
        to_cog (bool, optional): Convert to Cloud Optimized GeoTIFF. Defaults to False.
        quiet (bool, optional): Suppress output. Defaults to False.
        **kwargs: Additional arguments to pass to gdal.GetDriverByName("GTiff").Create().

    """

    import io
    import math
    import itertools
    import concurrent.futures

    import numpy
    from PIL import Image

    from osgeo import gdal, osr

    gdal.UseExceptions()

    try:
        import httpx

        SESSION = httpx.Client()
    except ImportError:
        import requests

        SESSION = requests.Session()

    xyz_tiles = {
        "OpenStreetMap": {
            "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attribution": "OpenStreetMap",
            "name": "OpenStreetMap",
        },
        "ROADMAP": {
            "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            "attribution": "Esri",
            "name": "Esri.WorldStreetMap",
        },
        "SATELLITE": {
            "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "attribution": "Esri",
            "name": "Esri.WorldImagery",
        },
        "TERRAIN": {
            "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
            "attribution": "Esri",
            "name": "Esri.WorldTopoMap",
        },
        "HYBRID": {
            "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "attribution": "Esri",
            "name": "Esri.WorldImagery",
        },
    }

    if isinstance(source, str) and source.upper() in xyz_tiles:
        source = xyz_tiles[source.upper()]["url"]
    elif isinstance(source, str) and source.startswith("http"):
        pass
    else:
        raise ValueError(
            'source must be one of "OpenStreetMap", "ROADMAP", "SATELLITE", "TERRAIN", "HYBRID", or a URL'
        )

    def resolution_to_zoom_level(resolution):
        """
        Convert map resolution in meters to zoom level for Web Mercator (EPSG:3857) tiles.
        """
        # Web Mercator tile size in meters at zoom level 0
        initial_resolution = 156543.03392804097

        # Calculate the zoom level
        zoom_level = math.log2(initial_resolution / resolution)

        return int(zoom_level)

    if isinstance(bbox, list) and len(bbox) == 4:
        west, south, east, north = bbox
    else:
        raise ValueError(
            "bbox must be a list of 4 coordinates in the format of [xmin, ymin, xmax, ymax]"
        )

    if zoom is None and resolution is None:
        raise ValueError("Either zoom or resolution must be provided")
    elif zoom is not None and resolution is not None:
        raise ValueError("Only one of zoom or resolution can be provided")

    if resolution is not None:
        zoom = resolution_to_zoom_level(resolution)

    EARTH_EQUATORIAL_RADIUS = 6378137.0

    Image.MAX_IMAGE_PIXELS = None

    web_mercator = osr.SpatialReference()
    web_mercator.ImportFromEPSG(3857)

    WKT_3857 = web_mercator.ExportToWkt()

    def from4326_to3857(lat, lon):
        xtile = math.radians(lon) * EARTH_EQUATORIAL_RADIUS
        ytile = (
            math.log(math.tan(math.radians(45 + lat / 2.0))) * EARTH_EQUATORIAL_RADIUS
        )
        return (xtile, ytile)

    def deg2num(lat, lon, zoom):
        lat_r = math.radians(lat)
        n = 2**zoom
        xtile = (lon + 180) / 360 * n
        ytile = (1 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2 * n
        return (xtile, ytile)

    def is_empty(im):
        extrema = im.getextrema()
        if len(extrema) >= 3:
            if len(extrema) > 3 and extrema[-1] == (0, 0):
                return True
            for ext in extrema[:3]:
                if ext != (0, 0):
                    return False
            return True
        else:
            return extrema[0] == (0, 0)

    def paste_tile(bigim, base_size, tile, corner_xy, bbox):
        if tile is None:
            return bigim
        im = Image.open(io.BytesIO(tile))
        mode = "RGB" if im.mode == "RGB" else "RGBA"
        size = im.size
        if bigim is None:
            base_size[0] = size[0]
            base_size[1] = size[1]
            newim = Image.new(
                mode, (size[0] * (bbox[2] - bbox[0]), size[1] * (bbox[3] - bbox[1]))
            )
        else:
            newim = bigim

        dx = abs(corner_xy[0] - bbox[0])
        dy = abs(corner_xy[1] - bbox[1])
        xy0 = (size[0] * dx, size[1] * dy)
        if mode == "RGB":
            newim.paste(im, xy0)
        else:
            if im.mode != mode:
                im = im.convert(mode)
            if not is_empty(im):
                newim.paste(im, xy0)
        im.close()
        return newim

    def finish_picture(bigim, base_size, bbox, x0, y0, x1, y1):
        xfrac = x0 - bbox[0]
        yfrac = y0 - bbox[1]
        x2 = round(base_size[0] * xfrac)
        y2 = round(base_size[1] * yfrac)
        imgw = round(base_size[0] * (x1 - x0))
        imgh = round(base_size[1] * (y1 - y0))
        retim = bigim.crop((x2, y2, x2 + imgw, y2 + imgh))
        if retim.mode == "RGBA" and retim.getextrema()[3] == (255, 255):
            retim = retim.convert("RGB")
        bigim.close()
        return retim

    def get_tile(url):
        retry = 3
        while 1:
            try:
                r = SESSION.get(url, timeout=60)
                break
            except Exception:
                retry -= 1
                if not retry:
                    raise
        if r.status_code == 404:
            return None
        elif not r.content:
            return None
        r.raise_for_status()
        return r.content

    def draw_tile(
        source, lat0, lon0, lat1, lon1, zoom, filename, quiet=False, **kwargs
    ):
        x0, y0 = deg2num(lat0, lon0, zoom)
        x1, y1 = deg2num(lat1, lon1, zoom)
        x0, x1 = sorted([x0, x1])
        y0, y1 = sorted([y0, y1])
        corners = tuple(
            itertools.product(
                range(math.floor(x0), math.ceil(x1)),
                range(math.floor(y0), math.ceil(y1)),
            )
        )
        totalnum = len(corners)
        futures = []
        with concurrent.futures.ThreadPoolExecutor(5) as executor:
            for x, y in corners:
                futures.append(
                    executor.submit(get_tile, source.format(z=zoom, x=x, y=y))
                )
            bbox = (math.floor(x0), math.floor(y0), math.ceil(x1), math.ceil(y1))
            bigim = None
            base_size = [256, 256]
            for k, (fut, corner_xy) in enumerate(zip(futures, corners), 1):
                bigim = paste_tile(bigim, base_size, fut.result(), corner_xy, bbox)
                if not quiet:
                    print("Downloaded image %d/%d" % (k, totalnum))

        if not quiet:
            print("Saving GeoTIFF. Please wait...")
        img = finish_picture(bigim, base_size, bbox, x0, y0, x1, y1)
        imgbands = len(img.getbands())
        driver = gdal.GetDriverByName("GTiff")

        if "options" not in kwargs:
            kwargs["options"] = [
                "COMPRESS=DEFLATE",
                "PREDICTOR=2",
                "ZLEVEL=9",
                "TILED=YES",
            ]

        gtiff = driver.Create(
            filename,
            img.size[0],
            img.size[1],
            imgbands,
            gdal.GDT_Byte,
            **kwargs,
        )
        xp0, yp0 = from4326_to3857(lat0, lon0)
        xp1, yp1 = from4326_to3857(lat1, lon1)
        pwidth = abs(xp1 - xp0) / img.size[0]
        pheight = abs(yp1 - yp0) / img.size[1]
        gtiff.SetGeoTransform((min(xp0, xp1), pwidth, 0, max(yp0, yp1), 0, -pheight))
        gtiff.SetProjection(WKT_3857)
        for band in range(imgbands):
            array = numpy.array(img.getdata(band), dtype="u8")
            array = array.reshape((img.size[1], img.size[0]))
            band = gtiff.GetRasterBand(band + 1)
            band.WriteArray(array)
        gtiff.FlushCache()

        if not quiet:
            print(f"Image saved to {filename}")
        return img

    try:
        draw_tile(source, south, west, north, east, zoom, output, quiet, **kwargs)
        if crs.upper() != "EPSG:3857":
            reproject(output, output, crs, to_cog=to_cog)
        elif to_cog:
            image_to_cog(output, output)
    except Exception as e:
        raise Exception(e)


def tif_to_jp2(filename, output, creationOptions=None):
    """Converts a GeoTIFF to JPEG2000.

    Args:
        filename (str): The path to the GeoTIFF file.
        output (str): The path to the output JPEG2000 file.
        creationOptions (list): A list of creation options for the JPEG2000 file. See
            https://gdal.org/drivers/raster/jp2openjpeg.html. For example, to specify the compression
            ratio, use ``["QUALITY=20"]``. A value of 20 means the file will be 20% of the size in comparison
            to uncompressed data.

    """

    from osgeo import gdal

    gdal.UseExceptions()

    if not os.path.exists(filename):
        raise Exception(f"File {filename} does not exist")

    if not output.endswith(".jp2"):
        output += ".jp2"

    in_ds = gdal.Open(filename)
    gdal.Translate(output, in_ds, format="JP2OpenJPEG", creationOptions=creationOptions)
    in_ds = None


def ee_to_geotiff(
    ee_object,
    output,
    bbox=None,
    vis_params={},
    zoom=None,
    resolution=None,
    crs="EPSG:3857",
    to_cog=False,
    quiet=False,
    **kwargs,
):
    """Downloads an Earth Engine object as GeoTIFF.

    Args:
        ee_object (ee.Image | ee.FeatureCollection): The Earth Engine object to download.
        output (str): The output path for the GeoTIFF.
        bbox (str, optional): The bounding box in the format [xmin, ymin, xmax, ymax]. Defaults to None,
            which is the bounding box of the Earth Engine object.
        vis_params (dict, optional): Visualization parameters. Defaults to {}.
        zoom (int, optional): The zoom level to download the image at. Defaults to None.
        resolution (float, optional): The resolution in meters to download the image at. Defaults to None.
        crs (str, optional): The CRS of the output image. Defaults to "EPSG:3857".
        to_cog (bool, optional): Whether to convert the image to Cloud Optimized GeoTIFF. Defaults to False.
        quiet (bool, optional): Whether to hide the download progress bar. Defaults to False.

    """

    from box import Box

    image = None

    if (
        not isinstance(ee_object, ee.Image)
        and not isinstance(ee_object, ee.ImageCollection)
        and not isinstance(ee_object, ee.FeatureCollection)
        and not isinstance(ee_object, ee.Feature)
        and not isinstance(ee_object, ee.Geometry)
    ):
        err_str = "\n\nThe image argument in 'addLayer' function must be an instance of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
        raise AttributeError(err_str)

    if (
        isinstance(ee_object, ee.geometry.Geometry)
        or isinstance(ee_object, ee.feature.Feature)
        or isinstance(ee_object, ee.featurecollection.FeatureCollection)
    ):
        features = ee.FeatureCollection(ee_object)

        width = 2

        if "width" in vis_params:
            width = vis_params["width"]

        color = "000000"

        if "color" in vis_params:
            color = vis_params["color"]

        image_fill = features.style(**{"fillColor": color}).updateMask(
            ee.Image.constant(0.5)
        )
        image_outline = features.style(
            **{"color": color, "fillColor": "00000000", "width": width}
        )

        image = image_fill.blend(image_outline)
    elif isinstance(ee_object, ee.image.Image):
        image = ee_object
    elif isinstance(ee_object, ee.imagecollection.ImageCollection):
        image = ee_object.mosaic()

    if "palette" in vis_params:
        if isinstance(vis_params["palette"], Box):
            try:
                vis_params["palette"] = vis_params["palette"]["default"]
            except Exception as e:
                print("The provided palette is invalid.")
                raise Exception(e)
        elif isinstance(vis_params["palette"], str):
            vis_params["palette"] = check_cmap(vis_params["palette"])
        elif not isinstance(vis_params["palette"], list):
            raise ValueError(
                "The palette must be a list of colors or a string or a Box object."
            )

    map_id_dict = ee.Image(image).getMapId(vis_params)
    url = map_id_dict["tile_fetcher"].url_format

    if bbox is None:
        bbox = ee_to_bbox(image)

    if zoom is None and resolution is None:
        raise ValueError("Either zoom level or resolution must be specified.")

    tms_to_geotiff(output, bbox, zoom, resolution, url, crs, to_cog, quiet, **kwargs)


def create_grid(ee_object, scale, proj=None):
    """Create a grid covering an Earth Engine object.

    Args:
        ee_object (ee.Image | ee.Geometry | ee.FeatureCollection): The Earth Engine object.
        scale (float): The grid cell size.
        proj (str, optional): The projection. Defaults to None.


    Returns:
        ee.FeatureCollection: The grid as a feature collection.
    """

    if isinstance(ee_object, ee.FeatureCollection) or isinstance(ee_object, ee.Image):
        geometry = ee_object.geometry()
    elif isinstance(ee_object, ee.Geometry):
        geometry = ee_object
    else:
        raise ValueError(
            "ee_object must be an ee.FeatureCollection, ee.Image, or ee.Geometry"
        )

    if proj is None:
        proj = geometry.projection()

    grid = geometry.coveringGrid(proj, scale)

    return grid


def jslink_slider_label(slider, label):
    """Link a slider and a label.

    Args:
        slider (ipywidgets.IntSlider | ipywidgets.FloatSlider): The slider.
        label (ipywidgets.Label): The label.
    """

    def update_label(change):
        if change["name"]:
            label.value = str(change["new"])

    slider.observe(update_label, "value")


def check_basemap(basemap):
    """Check Google basemaps

    Args:
        basemap (str): The basemap name.

    Returns:
        str: The basemap name.
    """
    if isinstance(basemap, str):
        map_dict = {
            "ROADMAP": "Google Maps",
            "SATELLITE": "Google Satellite",
            "TERRAIN": "Google Terrain",
            "HYBRID": "Google Hybrid",
        }

        if basemap.upper() in map_dict.keys():
            return map_dict[basemap.upper()]
        else:
            return basemap
    else:
        return basemap


def get_ee_token():
    """Get Earth Engine token.

    Returns:
        dict: The Earth Engine token.
    """
    credential_file_path = os.path.expanduser("~/.config/earthengine/credentials")

    if os.path.exists(credential_file_path):
        with open(credential_file_path, "r") as f:
            credentials = json.load(f)
            return credentials
    else:
        print("Earth Engine credentials not found. Please run ee.Authenticate()")
        return None


def geotiff_to_image(image: str, output: str) -> None:
    """
    Converts a GeoTIFF file to a JPEG/PNG image.

    Args:
        image (str): The path to the input GeoTIFF file.
        output (str): The path to save the output JPEG/PNG file.

    Returns:
        None
    """

    import rasterio
    from PIL import Image

    # Open the GeoTIFF file
    with rasterio.open(image) as dataset:
        # Read the image data
        data = dataset.read()

        # Convert the image data to 8-bit format (assuming it's not already)
        if dataset.dtypes[0] != "uint8":
            data = (data / data.max() * 255).astype("uint8")

        # Convert the image data to RGB format if it's a single band image
        if dataset.count == 1:
            data = data.squeeze()
            data = data.reshape((1, data.shape[0], data.shape[1]))
            data = data.repeat(3, axis=0)

        # Create a PIL Image object from the image data
        image = Image.fromarray(data.transpose(1, 2, 0))

        # Save the image as a JPEG file
        image.save(output)


def xee_to_image(
    xds,
    filenames: Optional[Union[str, List[str]]] = None,
    out_dir: Optional[str] = None,
    crs: Optional[str] = None,
    nodata: Optional[float] = None,
    driver: str = "COG",
    time_unit: str = "D",
    quiet: bool = False,
    **kwargs,
) -> None:
    """
    Convert xarray Dataset to georeferenced images.

    Args:
        xds (xr.Dataset): The xarray Dataset to convert to images.
        filenames (Union[str, List[str]], optional): Output filenames for the images.
            If a single string is provided, it will be used as the filename for all images.
            If a list of strings is provided, the filenames will be used in order. Defaults to None.
        out_dir (str, optional): Output directory for the images. Defaults to current working directory.
        crs (str, optional): Coordinate reference system (CRS) of the output images.
            If not provided, the CRS is inferred from the Dataset's attributes ('crs' attribute) or set to 'EPSG:4326'.
        nodata (float, optional): The nodata value used for the output images. Defaults to None.
        driver (str, optional): Driver used for writing the output images, such as 'GTiff'. Defaults to "COG".
        time_unit (str, optional): Time unit used for generating default filenames. Defaults to 'D'.
        quiet (bool, optional): If True, suppresses progress messages. Defaults to False.
        **kwargs: Additional keyword arguments passed to rioxarray's `rio.to_raster()` function.

    Returns:
        None

    Raises:
        ValueError: If the number of filenames doesn't match the number of time steps in the Dataset.

    """
    import numpy as np

    try:
        import rioxarray
    except ImportError:
        install_package("rioxarray")
        import rioxarray

    if crs is None and "crs" in xds.attrs:
        crs = xds.attrs["crs"]
    if crs is None:
        crs = "EPSG:4326"

    if out_dir is None:
        out_dir = os.getcwd()

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if isinstance(filenames, str):
        filenames = [filenames]
    if isinstance(filenames, list):
        if len(filenames) != len(xds.time):
            raise ValueError(
                "The number of filenames must match the number of time steps"
            )

    coords = [coord for coord in xds.coords]
    x_dim = coords[1]
    y_dim = coords[2]

    for index, time in enumerate(xds.time.values):
        if nodata is not None:
            # Create a Boolean mask where all three variables are zero (nodata)
            mask = (xds == nodata).all(dim="time")
            # Set nodata values based on the mask for all variables
            xds = xds.where(~mask, other=np.nan)

        if not quiet:
            print(f"Processing {index + 1}/{len(xds.time.values)}: {time}")
        image = xds.sel(time=time)
        # transform the image to suit rioxarray format
        image = (
            image.rename({y_dim: "y", x_dim: "x"})
            .transpose("y", "x")
            .rio.write_crs(crs)
        )

        if filenames is None:
            date = np.datetime_as_string(time, unit=time_unit)
            filename = f"{date}.tif"
        else:
            filename = filenames.pop()

        output_path = os.path.join(out_dir, filename)
        image.rio.to_raster(output_path, driver=driver, **kwargs)


def array_to_memory_file(
    array,
    source: str = None,
    dtype: str = None,
    compress: str = "deflate",
    transpose: bool = True,
    cellsize: float = None,
    crs: str = None,
    transform: tuple = None,
    driver="COG",
    **kwargs,
):
    """Convert a NumPy array to a memory file.

    Args:
        array (numpy.ndarray): The input NumPy array.
        source (str, optional): Path to the source file to extract metadata from. Defaults to None.
        dtype (str, optional): The desired data type of the array. Defaults to None.
        compress (str, optional): The compression method for the output file. Defaults to "deflate".
        transpose (bool, optional): Whether to transpose the array from (bands, rows, columns) to (rows, columns, bands). Defaults to True.
        cellsize (float, optional): The cell size of the array if source is not provided. Defaults to None.
        crs (str, optional): The coordinate reference system of the array if source is not provided. Defaults to None.
        transform (tuple, optional): The affine transformation matrix if source is not provided. Defaults to None.
        driver (str, optional): The driver to use for creating the output file, such as 'GTiff'. Defaults to "COG".
        **kwargs: Additional keyword arguments to be passed to the rasterio.open() function.

    Returns:
        rasterio.DatasetReader: The rasterio dataset reader object for the converted array.
    """
    import rasterio
    import numpy as np
    import xarray as xr

    if isinstance(array, xr.DataArray):
        coords = [coord for coord in array.coords]
        if coords[0] == "time":
            x_dim = coords[1]
            y_dim = coords[2]
            if array.dims[0] == "time":
                array = array.isel(time=0)

            array = array.rename({y_dim: "y", x_dim: "x"}).transpose("y", "x")
        array = array.values

    if array.ndim == 3 and transpose:
        array = np.transpose(array, (1, 2, 0))

    if source is not None:
        with rasterio.open(source) as src:
            crs = src.crs
            transform = src.transform
            if compress is None:
                compress = src.compression
    else:
        if cellsize is None:
            raise ValueError("cellsize must be provided if source is not provided")
        if crs is None:
            raise ValueError(
                "crs must be provided if source is not provided, such as EPSG:3857"
            )

        if "transform" not in kwargs:
            # Define the geotransformation parameters
            xmin, ymin, xmax, ymax = (
                0,
                0,
                cellsize * array.shape[1],
                cellsize * array.shape[0],
            )
            # (west, south, east, north, width, height)
            transform = rasterio.transform.from_bounds(
                xmin, ymin, xmax, ymax, array.shape[1], array.shape[0]
            )
        else:
            transform = kwargs["transform"]

    if dtype is None:
        # Determine the minimum and maximum values in the array
        min_value = np.min(array)
        max_value = np.max(array)
        # Determine the best dtype for the array
        if min_value >= 0 and max_value <= 1:
            dtype = np.float32
        elif min_value >= 0 and max_value <= 255:
            dtype = np.uint8
        elif min_value >= -128 and max_value <= 127:
            dtype = np.int8
        elif min_value >= 0 and max_value <= 65535:
            dtype = np.uint16
        elif min_value >= -32768 and max_value <= 32767:
            dtype = np.int16
        else:
            dtype = np.float64

    # Convert the array to the best dtype
    array = array.astype(dtype)

    # Define the GeoTIFF metadata
    metadata = {
        "driver": driver,
        "height": array.shape[0],
        "width": array.shape[1],
        "dtype": array.dtype,
        "crs": crs,
        "transform": transform,
    }

    if array.ndim == 2:
        metadata["count"] = 1
    elif array.ndim == 3:
        metadata["count"] = array.shape[2]
    if compress is not None:
        metadata["compress"] = compress

    metadata.update(**kwargs)

    # Create a new memory file and write the array to it
    memory_file = rasterio.MemoryFile()
    dst = memory_file.open(**metadata)

    if array.ndim == 2:
        dst.write(array, 1)
    elif array.ndim == 3:
        for i in range(array.shape[2]):
            dst.write(array[:, :, i], i + 1)

    dst.close()

    # Read the dataset from memory
    dataset_reader = rasterio.open(dst.name, mode="r")

    return dataset_reader


def array_to_image(
    array,
    output: str = None,
    source: str = None,
    dtype: str = None,
    compress: str = "deflate",
    transpose: bool = True,
    cellsize: float = None,
    crs: str = None,
    driver: str = "COG",
    **kwargs,
) -> str:
    """Save a NumPy array as a GeoTIFF using the projection information from an existing GeoTIFF file.

    Args:
        array (np.ndarray): The NumPy array to be saved as a GeoTIFF.
        output (str): The path to the output image. If None, a temporary file will be created. Defaults to None.
        source (str, optional): The path to an existing GeoTIFF file with map projection information. Defaults to None.
        dtype (np.dtype, optional): The data type of the output array. Defaults to None.
        compress (str, optional): The compression method. Can be one of the following: "deflate", "lzw", "packbits", "jpeg". Defaults to "deflate".
        transpose (bool, optional): Whether to transpose the array from (bands, rows, columns) to (rows, columns, bands). Defaults to True.
        cellsize (float, optional): The resolution of the output image in meters. Defaults to None.
        crs (str, optional): The CRS of the output image. Defaults to None.
        driver (str, optional): The driver to use for creating the output file, such as 'GTiff'. Defaults to "COG".
        **kwargs: Additional keyword arguments to be passed to the rasterio.open() function.
    """

    import numpy as np
    import rasterio
    import xarray as xr

    if output is None:
        return array_to_memory_file(
            array, source, dtype, compress, transpose, cellsize, crs, driver, **kwargs
        )

    if isinstance(array, xr.DataArray):
        coords = [coord for coord in array.coords]
        if coords[0] == "time":
            x_dim = coords[1]
            y_dim = coords[2]
            if array.dims[0] == "time":
                array = array.isel(time=0)

            array = array.rename({y_dim: "y", x_dim: "x"}).transpose("y", "x")
        array = array.values

    if array.ndim == 3 and transpose:
        array = np.transpose(array, (1, 2, 0))

    out_dir = os.path.dirname(os.path.abspath(output))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not output.endswith(".tif"):
        output += ".tif"

    if source is not None:
        with rasterio.open(source) as src:
            crs = src.crs
            transform = src.transform
            if compress is None:
                compress = src.compression
    else:
        if cellsize is None:
            raise ValueError("resolution must be provided if source is not provided")
        if crs is None:
            raise ValueError(
                "crs must be provided if source is not provided, such as EPSG:3857"
            )

        if "transform" not in kwargs:
            # Define the geotransformation parameters
            xmin, ymin, xmax, ymax = (
                0,
                0,
                cellsize * array.shape[1],
                cellsize * array.shape[0],
            )
            transform = rasterio.transform.from_bounds(
                xmin, ymin, xmax, ymax, array.shape[1], array.shape[0]
            )
        else:
            transform = kwargs["transform"]

    if dtype is None:
        # Determine the minimum and maximum values in the array
        min_value = np.min(array)
        max_value = np.max(array)
        # Determine the best dtype for the array
        if min_value >= 0 and max_value <= 1:
            dtype = np.float32
        elif min_value >= 0 and max_value <= 255:
            dtype = np.uint8
        elif min_value >= -128 and max_value <= 127:
            dtype = np.int8
        elif min_value >= 0 and max_value <= 65535:
            dtype = np.uint16
        elif min_value >= -32768 and max_value <= 32767:
            dtype = np.int16
        else:
            dtype = np.float64

    # Convert the array to the best dtype
    array = array.astype(dtype)

    # Define the GeoTIFF metadata
    metadata = {
        "driver": driver,
        "height": array.shape[0],
        "width": array.shape[1],
        "dtype": array.dtype,
        "crs": crs,
        "transform": transform,
    }

    if array.ndim == 2:
        metadata["count"] = 1
    elif array.ndim == 3:
        metadata["count"] = array.shape[2]
    if compress is not None:
        metadata["compress"] = compress

    metadata.update(**kwargs)

    # Create a new GeoTIFF file and write the array to it
    with rasterio.open(output, "w", **metadata) as dst:
        if array.ndim == 2:
            dst.write(array, 1)
        elif array.ndim == 3:
            for i in range(array.shape[2]):
                dst.write(array[:, :, i], i + 1)


def is_studio_lab():
    """Check if the current notebook is running on Studio Lab.

    Returns:
        bool: True if the notebook is running on Studio Lab.
    """

    import psutil

    output = psutil.Process().parent().cmdline()

    on_studio_lab = False
    for item in output:
        if "studiolab/bin" in item:
            on_studio_lab = True
    return on_studio_lab


def is_on_aws():
    """Check if the current notebook is running on AWS.

    Returns:
        bool: True if the notebook is running on AWS.
    """

    import psutil

    output = psutil.Process().parent().cmdline()

    on_aws = False
    for item in output:
        if item.endswith(".aws") or "ec2-user" in item:
            on_aws = True
    return on_aws


def xarray_to_raster(dataset, filename: str, **kwargs: Dict[str, Any]) -> None:
    """Convert an xarray Dataset to a raster file.

    Args:
        dataset (xr.Dataset): The input xarray Dataset to be converted.
        filename (str): The output filename for the raster file.
        **kwargs (Dict[str, Any]): Additional keyword arguments passed to the `rio.to_raster()` method.
            See https://corteva.github.io/rioxarray/stable/examples/convert_to_raster.html for more info.

    Returns:
        None
    """
    import rioxarray

    dims = list(dataset.dims)

    new_names = {}

    if "lat" in dims:
        new_names["lat"] = "y"
        dims.remove("lat")
    if "lon" in dims:
        new_names["lon"] = "x"
        dims.remove("lon")
    if "lng" in dims:
        new_names["lng"] = "x"
        dims.remove("lng")
    if "latitude" in dims:
        new_names["latitude"] = "y"
        dims.remove("latitude")
    if "longitude" in dims:
        new_names["longitude"] = "x"
        dims.remove("longitude")

    dataset = dataset.rename(new_names)
    dataset.transpose(..., "y", "x").rio.to_raster(filename, **kwargs)


def hex_to_rgba(hex_color: str, opacity: float) -> str:
    """
    Converts a hex color code to an RGBA color string.

    Args:
        hex_color (str): The hex color code to convert. It can be in the format
            '#RRGGBB' or 'RRGGBB'.
        opacity (float): The opacity value for the RGBA color. It should be a
            float between 0.0 (completely transparent) and 1.0 (completely opaque).

    Returns:
        str: The RGBA color string in the format 'rgba(R, G, B, A)'.
    """
    hex_color = hex_color.lstrip("#")
    h_len = len(hex_color)
    r, g, b = (
        int(hex_color[i : i + h_len // 3], 16) for i in range(0, h_len, h_len // 3)
    )
    return f"rgba({r},{g},{b},{opacity})"


def replace_top_level_hyphens(d: Union[Dict, Any]) -> Union[Dict, Any]:
    """
    Replaces hyphens with underscores in top-level dictionary keys.

    Args:
        d (Union[Dict, Any]): The input dictionary or any other data type.

    Returns:
        Union[Dict, Any]: The modified dictionary with top-level keys having hyphens replaced with underscores,
        or the original input if it's not a dictionary.
    """
    if isinstance(d, dict):
        return {k.replace("-", "_"): v for k, v in d.items()}
    return d


def replace_hyphens_in_keys(d: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively replaces hyphens with underscores in dictionary keys.

    Args:
        d (Union[Dict, List, Any]): The input dictionary, list or any other data type.

    Returns:
        Union[Dict, List, Any]: The modified dictionary or list with keys having hyphens replaced with underscores,
        or the original input if it's not a dictionary or list.
    """
    if isinstance(d, dict):
        return {k.replace("-", "_"): replace_hyphens_in_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [replace_hyphens_in_keys(i) for i in d]
    else:
        return d


def remove_port_from_string(data: str) -> str:
    """
    Removes the port number from all URLs in the given string.

    Args::
        data (str): The input string containing URLs.

    Returns:
        str: The string with port numbers removed from all URLs.
    """
    import re

    # Regular expression to match URLs with port numbers
    url_with_port_pattern = re.compile(r"(http://[\d\w.]+):\d+")

    # Function to remove the port from the matched URLs
    def remove_port(match):
        return match.group(1)

    # Substitute the URLs with ports removed
    result = url_with_port_pattern.sub(remove_port, data)

    return result


def pmtiles_metadata(input_file: str) -> Dict[str, Union[str, int, List[str]]]:
    """
    Fetch the metadata from a local or remote .pmtiles file.

    This function retrieves metadata from a PMTiles file, whether it's local or hosted remotely.
    If it's remote, the function fetches the header to determine the range of bytes to download
    for obtaining the metadata. It then reads the metadata and extracts the layer names.

    Args:
        input_file (str): Path to the .pmtiles file, or its URL if the file is hosted remotely.

    Returns:
        dict: A dictionary containing the metadata information, including layer names.

    Raises:
        ImportError: If the pmtiles library is not installed.
        ValueError: If the input file is not a .pmtiles file or if it does not exist.

    Example:
        >>> metadata = pmtiles_metadata("https://example.com/path/to/tiles.pmtiles")
        >>> print(metadata["layer_names"])
        ['buildings', 'roads']

    Note:
        If fetching a remote PMTiles file, this function may perform multiple requests to minimize
        the amount of data downloaded.
    """

    import json
    import requests
    from urllib.parse import urlparse

    try:
        from pmtiles.reader import Reader, MmapSource, MemorySource
    except ImportError:
        print(
            "pmtiles is not installed. Please install it using `pip install pmtiles`."
        )
        return

    # ignore uri parameters when checking file suffix
    if not urlparse(input_file).path.endswith(".pmtiles"):
        raise ValueError("Input file must be a .pmtiles file.")

    header = pmtiles_header(input_file)
    metadata_offset = header["metadata_offset"]
    metadata_length = header["metadata_length"]

    if input_file.startswith("http"):
        headers = {"Range": f"bytes=0-{metadata_offset + metadata_length}"}
        response = requests.get(input_file, headers=headers)
        content = MemorySource(response.content)
        metadata = Reader(content).metadata()
    else:
        with open(input_file, "rb") as f:
            reader = Reader(MmapSource(f))
            metadata = reader.metadata()
            if "json" in metadata:
                metadata["vector_layers"] = json.loads(metadata["json"])[
                    "vector_layers"
                ]

    vector_layers = metadata["vector_layers"]
    layer_names = [layer["id"] for layer in vector_layers]

    if "tilestats" in metadata:
        geometries = [layer["geometry"] for layer in metadata["tilestats"]["layers"]]
        metadata["geometries"] = geometries

    metadata["layer_names"] = layer_names
    metadata["center"] = header["center"]
    metadata["bounds"] = header["bounds"]
    return metadata


def pmtiles_style(
    url: str,
    layers: Optional[Union[str, List[str]]] = None,
    cmap: str = "Set3",
    n_class: Optional[int] = None,
    opacity: float = 0.5,
    circle_radius: int = 5,
    line_width: int = 1,
    attribution: str = "PMTiles",
    **kwargs,
):
    """
    Generates a Mapbox style JSON for rendering PMTiles data.

    Args:
        url (str): The URL of the PMTiles file.
        layers (str or list[str], optional): The layers to include in the style. If None, all layers will be included.
            Defaults to None.
        cmap (str, optional): The color map to use for styling the layers. Defaults to "Set3".
        n_class (int, optional): The number of classes to use for styling. If None, the number of classes will be
            determined automatically based on the color map. Defaults to None.
        opacity (float, optional): The fill opacity for polygon layers. Defaults to 0.5.
        circle_radius (int, optional): The circle radius for point layers. Defaults to 5.
        line_width (int, optional): The line width for line layers. Defaults to 1.
        attribution (str, optional): The attribution text for the data source. Defaults to "PMTiles".

    Returns:
        dict: The Mapbox style JSON.

    Raises:
        ValueError: If the layers argument is not a string or a list.
        ValueError: If a layer specified in the layers argument does not exist in the PMTiles file.
    """

    if cmap == "Set3":
        palette = [
            "#8dd3c7",
            "#ffffb3",
            "#bebada",
            "#fb8072",
            "#80b1d3",
            "#fdb462",
            "#b3de69",
            "#fccde5",
            "#d9d9d9",
            "#bc80bd",
            "#ccebc5",
            "#ffed6f",
        ]
    elif isinstance(cmap, list):
        palette = cmap
    else:
        from .colormaps import get_palette

        palette = ["#" + c for c in get_palette(cmap, n_class)]

    n_class = len(palette)

    metadata = pmtiles_metadata(url)
    layer_names = metadata["layer_names"]

    style = {
        "version": 8,
        "sources": {
            "source": {
                "type": "vector",
                "url": "pmtiles://" + url,
                "attribution": attribution,
            }
        },
        "layers": [],
    }

    if layers is None:
        layers = layer_names
    elif isinstance(layers, str):
        layers = [layers]
    elif isinstance(layers, list):
        for layer in layers:
            if layer not in layer_names:
                raise ValueError(f"Layer {layer} does not exist in the PMTiles file.")
    else:
        raise ValueError("The layers argument must be a string or a list.")

    for i, layer_name in enumerate(layers):
        layer_point = {
            "id": f"{layer_name}_point",
            "source": "source",
            "source-layer": layer_name,
            "type": "circle",
            "paint": {
                "circle-color": palette[i % n_class],
                "circle-radius": circle_radius,
            },
            "filter": ["==", ["geometry-type"], "Point"],
        }

        layer_stroke = {
            "id": f"{layer_name}_stroke",
            "source": "source",
            "source-layer": layer_name,
            "type": "line",
            "paint": {
                "line-color": palette[i % n_class],
                "line-width": line_width,
            },
            "filter": ["==", ["geometry-type"], "LineString"],
        }

        layer_fill = {
            "id": f"{layer_name}_fill",
            "source": "source",
            "source-layer": layer_name,
            "type": "fill",
            "paint": {
                "fill-color": palette[i % n_class],
                "fill-opacity": opacity,
            },
            "filter": ["==", ["geometry-type"], "Polygon"],
        }

        style["layers"].extend([layer_point, layer_stroke, layer_fill])

    return style


def check_html_string(html_string):
    """Check if an HTML string contains local images and convert them to base64.

    Args:
        html_string (str): The HTML string.

    Returns:
        str: The HTML string with local images converted to base64.
    """
    import re
    import base64

    # Search for img tags with src attribute
    img_regex = r'<img[^>]+src\s*=\s*["\']([^"\':]+)["\'][^>]*>'

    for match in re.findall(img_regex, html_string):
        with open(match, "rb") as img_file:
            img_data = img_file.read()
            base64_data = base64.b64encode(img_data).decode("utf-8")
            html_string = html_string.replace(
                'src="{}"'.format(match),
                'src="data:image/png;base64,' + base64_data + '"',
            )

    return html_string
