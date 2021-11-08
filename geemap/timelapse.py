"""Module for creating timelapse from various Earth Engine ImageCollection.
"""
import datetime
import io
import os
import shutil

import ee

from .common import *


def add_overlay(
    collection, overlay_data, color="black", width=1, opacity=1.0, region=None
):
    """Adds an overlay to an image collection.

    Args:
        collection (ee.ImageCollection): The image collection to add the overlay to.
        overlay_data (str | ee.Geometry | ee.FeatureCollection): The overlay data to add to the image collection. It can be an HTTP URL to a GeoJSON file.
        color (str, optional): The color of the overlay. Defaults to 'black'.
        width (int, optional): The width of the overlay. Defaults to 1.
        opacity (float, optional): The opacity of the overlay. Defaults to 1.0.
        region (ee.Geometry | ee.FeatureCollection, optional): The region of interest to add the overlay to. Defaults to None.

    Returns:
        ee.ImageCollection: An ImageCollection with the overlay added.
    """

    # Some common administrative boundaries.
    public_assets = [
        "continents",
        "countries",
        "us_states",
        "chn_admin_level0",
        "chn_admin_level1",
        "chn_admin_level2",
    ]

    if not isinstance(collection, ee.ImageCollection):
        raise Exception("The collection must be an ee.ImageCollection.")

    if not isinstance(overlay_data, ee.FeatureCollection):
        if isinstance(overlay_data, str):
            try:
                if overlay_data.lower() in public_assets:
                    overlay_data = ee.FeatureCollection(
                        f"users/giswqs/public/{overlay_data.lower()}"
                    )
                elif overlay_data.startswith("http") and overlay_data.endswith(
                    ".geojson"
                ):
                    overlay_data = geojson_to_ee(overlay_data)
                else:
                    overlay_data = ee.FeatureCollection(overlay_data)

            except Exception as e:
                print(
                    "The overlay_data must be a valid ee.FeatureCollection, a valid ee.FeatureCollection asset id, or http url to a geojson file."
                )
                raise Exception(e)
        elif isinstance(overlay_data, ee.Feature):
            overlay_data = ee.FeatureCollection([overlay_data])
        elif isinstance(overlay_data, ee.Geometry):
            overlay_data = ee.FeatureCollection([ee.Feature(overlay_data)])
        else:
            raise Exception(
                "The overlay_data must be a valid ee.FeatureCollection or a valid ee.FeatureCollection asset id."
            )

    try:
        if region is not None:
            overlay_data = overlay_data.filterBounds(region)

        empty = ee.Image().byte()
        image = empty.paint(
            **{
                "featureCollection": overlay_data,
                "color": 1,
                "width": width,
            }
        ).visualize(**{"palette": check_color(color), "opacity": opacity})
        blend_col = collection.map(lambda img: img.blend(image))
        return blend_col
    except Exception as e:
        print("Error in add_overlay:")
        raise Exception(e)


def merge_gifs(in_gifs, out_gif):
    """Merge multiple gifs into one.

    Args:
        in_gifs (str | list): The input gifs as a list or a directory path.
        out_gif (str): The output gif.

    Raises:
        Exception:  Raise exception when gifsicle is not installed.
    """
    import glob

    try:
        if isinstance(in_gifs, str) and os.path.isdir(in_gifs):
            in_gifs = glob.glob(os.path.join(in_gifs, "*.gif"))
        elif not isinstance(in_gifs, list):
            raise Exception("in_gifs must be a list.")

        in_gifs = " ".join(in_gifs)

        cmd = f"gifsicle {in_gifs} > {out_gif}"
        os.system(cmd)

    except Exception as e:
        print(
            "gifsicle is not installed. Run 'sudo apt-get install -y gifsicle' to install it."
        )
        print(e)


def naip_timeseries(roi=None, start_year=2003, end_year=2021, RGBN=False):
    """Creates NAIP annual timeseries

    Args:
        roi (object, optional): An ee.Geometry representing the region of interest. Defaults to None.
        start_year (int, optional): Starting year for the timeseries. Defaults to 2003.
        end_year (int, optional): Ending year for the timeseries. Defaults to 2021.
        RGBN (bool, optional): Whether to retrieve 4-band NAIP imagery only.
    Returns:
        object: An ee.ImageCollection representing annual NAIP imagery.
    """
    try:

        def get_annual_NAIP(year):
            try:
                collection = ee.ImageCollection("USDA/NAIP/DOQQ")
                if roi is not None:
                    collection = collection.filterBounds(roi)
                start_date = ee.Date.fromYMD(year, 1, 1)
                end_date = ee.Date.fromYMD(year, 12, 31)
                naip = collection.filterDate(start_date, end_date)
                if RGBN:
                    naip = naip.filter(ee.Filter.listContains("system:band_names", "N"))
                naip = ee.Image(ee.ImageCollection(naip).mosaic())
                return naip
            except Exception as e:
                raise Exception(e)

        years = ee.List.sequence(start_year, end_year)
        collection = ee.ImageCollection(years.map(get_annual_NAIP))
        return collection

    except Exception as e:
        raise Exception(e)


def sentinel2_timeseries(
    roi=None,
    start_year=2015,
    end_year=2021,
    start_date="01-01",
    end_date="12-31",
    apply_fmask=True,
):
    """Generates an annual Sentinel 2 ImageCollection. This algorithm is adapted from https://gist.github.com/jdbcode/76b9ac49faf51627ebd3ff988e10adbc. A huge thank you to Justin Braaten for sharing his fantastic work.
       Images include both level 1C and level 2A imagery.
    Args:

        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 2015.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2021.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '01-01'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '12-31'.
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
    Returns:
        object: Returns an ImageCollection containing annual Sentinel 2 images.
    """
    ################################################################################

    ################################################################################
    # Input and output parameters.
    import re

    # import datetime

    if roi is None:
        # roi = ee.Geometry.Polygon(
        #     [[[-180, -80],
        #       [-180, 80],
        #         [180, 80],
        #         [180, -80],
        #         [-180, -80]]], None, False)
        roi = ee.Geometry.Polygon(
            [
                [
                    [-115.471773, 35.892718],
                    [-115.471773, 36.409454],
                    [-114.271283, 36.409454],
                    [-114.271283, 35.892718],
                    [-115.471773, 35.892718],
                ]
            ],
            None,
            False,
        )

    if not isinstance(roi, ee.Geometry):

        try:
            roi = roi.geometry()
        except Exception as e:
            print("Could not convert the provided roi to ee.Geometry")
            print(e)
            return

    # Adjusts longitudes less than -180 degrees or greater than 180 degrees.
    geojson = ee_to_geojson(roi)
    geojson = adjust_longitude(geojson)
    roi = ee.Geometry(geojson)

    ################################################################################
    # Setup vars to get dates.
    if isinstance(start_year, int) and (start_year >= 2015) and (start_year <= 2021):
        pass
    else:
        print("The start year must be an integer >= 2015.")
        return

    if isinstance(end_year, int) and (end_year >= 2015) and (end_year <= 2021):
        pass
    else:
        print("The end year must be an integer <= 2021.")
        return

    if re.match("[0-9]{2}\-[0-9]{2}", start_date) and re.match(
        "[0-9]{2}\-[0-9]{2}", end_date
    ):
        pass
    else:
        print("The start data and end date must be month-day, such as 06-10, 09-20")
        return

    try:
        datetime.datetime(int(start_year), int(start_date[:2]), int(start_date[3:5]))
        datetime.datetime(int(end_year), int(end_date[:2]), int(end_date[3:5]))
    except Exception as e:
        raise ValueError("The input dates are invalid.")

    try:
        start_test = datetime.datetime(
            int(start_year), int(start_date[:2]), int(start_date[3:5])
        )
        end_test = datetime.datetime(
            int(end_year), int(end_date[:2]), int(end_date[3:5])
        )
        if start_test > end_test:
            raise ValueError("Start date must be prior to end date")
    except Exception as e:
        raise Exception(e)

    def days_between(d1, d2):
        d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    n_days = days_between(
        str(start_year) + "-" + start_date, str(start_year) + "-" + end_date
    )
    start_month = int(start_date[:2])
    start_day = int(start_date[3:5])
    # start_date = str(start_year) + "-" + start_date
    # end_date = str(end_year) + "-" + end_date

    # # Define a collection filter by date, bounds, and quality.
    # def colFilter(col, aoi):  # , startDate, endDate):
    #     return(col.filterBounds(aoi))

    # Get Sentinel 2 collections, both Level-1C (top of atmophere) and Level-2A (surface reflectance)
    MSILCcol = ee.ImageCollection("COPERNICUS/S2")
    MSI2Acol = ee.ImageCollection("COPERNICUS/S2_SR")

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, roi, start_date, end_date):
        return col.filterBounds(roi).filterDate(start_date, end_date)
        # .filter('CLOUD_COVER < 5')
        # .filter('GEOMETRIC_RMSE_MODEL < 15')
        # .filter('IMAGE_QUALITY == 9 || IMAGE_QUALITY_OLI == 9'))

    # Function to get and rename bands of interest from MSI
    def renameMSI(img):
        return img.select(
            ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12", "QA60"],
            [
                "Blue",
                "Green",
                "Red",
                "Red Edge 1",
                "Red Edge 2",
                "Red Edge 3",
                "NIR",
                "Red Edge 4",
                "SWIR1",
                "SWIR2",
                "QA60",
            ],
        )

    # Add NBR for LandTrendr segmentation.

    def calcNbr(img):
        return img.addBands(
            img.normalizedDifference(["NIR", "SWIR2"]).multiply(-10000).rename("NBR")
        ).int16()

    # Define function to mask out clouds and cloud shadows in images.
    # Use CFmask band included in USGS Landsat SR image product.

    def fmask(img):
        cloudOpaqueBitMask = 1 << 10
        cloudCirrusBitMask = 1 << 11
        qa = img.select("QA60")
        mask = (
            qa.bitwiseAnd(cloudOpaqueBitMask)
            .eq(0)
            .And(qa.bitwiseAnd(cloudCirrusBitMask).eq(0))
        )
        return img.updateMask(mask)

    # Define function to prepare MSI images.
    def prepMSI(img):
        orig = img
        img = renameMSI(img)
        if apply_fmask:
            img = fmask(img)
        return ee.Image(img.copyProperties(orig, orig.propertyNames())).resample(
            "bicubic"
        )

    # Get annual median collection.
    def getAnnualComp(y):
        startDate = ee.Date.fromYMD(
            ee.Number(y), ee.Number(start_month), ee.Number(start_day)
        )
        endDate = startDate.advance(ee.Number(n_days), "day")

        # Filter collections and prepare them for merging.
        MSILCcoly = colFilter(MSILCcol, roi, startDate, endDate).map(prepMSI)
        MSI2Acoly = colFilter(MSI2Acol, roi, startDate, endDate).map(prepMSI)

        # Merge the collections.
        col = MSILCcoly.merge(MSI2Acoly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(nBands, yearImg, dummyImg))
        return calcNbr(yearImg).set(
            {"year": y, "system:time_start": startDate.millis(), "nBands": nBands}
        )

    ################################################################################

    # Make a dummy image for missing years.
    bandNames = ee.List(
        [
            "Blue",
            "Green",
            "Red",
            "Red Edge 1",
            "Red Edge 2",
            "Red Edge 3",
            "NIR",
            "Red Edge 4",
            "SWIR1",
            "SWIR2",
            "QA60",
        ]
    )
    fillerValues = ee.List.repeat(0, bandNames.size())
    dummyImg = ee.Image.constant(fillerValues).rename(bandNames).selfMask().int16()

    ################################################################################
    # Get a list of years
    years = ee.List.sequence(start_year, end_year)

    ################################################################################
    # Make list of annual image composites.
    imgList = years.map(getAnnualComp)

    # Convert image composite list to collection
    imgCol = ee.ImageCollection.fromImages(imgList)

    imgCol = imgCol.map(lambda img: img.clip(roi))

    return imgCol


def landsat_timeseries(
    roi=None,
    start_year=1984,
    end_year=2020,
    start_date="06-10",
    end_date="09-20",
    apply_fmask=True,
):
    """Generates an annual Landsat ImageCollection. This algorithm is adapted from https://gist.github.com/jdbcode/76b9ac49faf51627ebd3ff988e10adbc. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2020.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
    Returns:
        object: Returns an ImageCollection containing annual Landsat images.
    """

    ################################################################################
    # Input and output parameters.
    import re

    # import datetime

    if roi is None:
        roi = ee.Geometry.Polygon(
            [
                [
                    [-115.471773, 35.892718],
                    [-115.471773, 36.409454],
                    [-114.271283, 36.409454],
                    [-114.271283, 35.892718],
                    [-115.471773, 35.892718],
                ]
            ],
            None,
            False,
        )

    if not isinstance(roi, ee.Geometry):

        try:
            roi = roi.geometry()
        except Exception as e:
            print("Could not convert the provided roi to ee.Geometry")
            print(e)
            return

    ################################################################################

    # Setup vars to get dates.
    if isinstance(start_year, int) and (start_year >= 1984) and (start_year < 2021):
        pass
    else:
        print("The start year must be an integer >= 1984.")
        return

    if isinstance(end_year, int) and (end_year > 1984) and (end_year <= 2021):
        pass
    else:
        print("The end year must be an integer <= 2021.")
        return

    if re.match("[0-9]{2}\-[0-9]{2}", start_date) and re.match(
        "[0-9]{2}\-[0-9]{2}", end_date
    ):
        pass
    else:
        print("The start date and end date must be month-day, such as 06-10, 09-20")
        return

    try:
        datetime.datetime(int(start_year), int(start_date[:2]), int(start_date[3:5]))
        datetime.datetime(int(end_year), int(end_date[:2]), int(end_date[3:5]))
    except Exception as e:
        print("The input dates are invalid.")
        raise Exception(e)

    def days_between(d1, d2):
        d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    n_days = days_between(
        str(start_year) + "-" + start_date, str(start_year) + "-" + end_date
    )
    start_month = int(start_date[:2])
    start_day = int(start_date[3:5])
    # start_date = str(start_year) + "-" + start_date
    # end_date = str(end_year) + "-" + end_date

    # # Define a collection filter by date, bounds, and quality.
    # def colFilter(col, aoi):  # , startDate, endDate):
    #     return(col.filterBounds(aoi))

    # Landsat collection preprocessingEnabled
    # Get Landsat surface reflectance collections for OLI, ETM+ and TM sensors.
    LC08col = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR")
    LE07col = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR")
    LT05col = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR")
    LT04col = ee.ImageCollection("LANDSAT/LT04/C01/T1_SR")

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, roi, start_date, end_date):
        return col.filterBounds(roi).filterDate(start_date, end_date)
        # .filter('CLOUD_COVER < 5')
        # .filter('GEOMETRIC_RMSE_MODEL < 15')
        # .filter('IMAGE_QUALITY == 9 || IMAGE_QUALITY_OLI == 9'))

    # Function to get and rename bands of interest from OLI.
    def renameOli(img):
        return img.select(
            ["B2", "B3", "B4", "B5", "B6", "B7", "pixel_qa"],
            ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"],
        )

    # Function to get and rename bands of interest from ETM+.
    def renameEtm(img):
        return img.select(
            ["B1", "B2", "B3", "B4", "B5", "B7", "pixel_qa"],
            ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"],
        )

    # Add NBR for LandTrendr segmentation.
    def calcNbr(img):
        return img.addBands(
            img.normalizedDifference(["NIR", "SWIR2"]).multiply(-10000).rename("NBR")
        ).int16()

    # Define function to mask out clouds and cloud shadows in images.
    # Use CFmask band included in USGS Landsat SR image product.
    def fmask(img):
        cloudShadowBitMask = 1 << 3
        cloudsBitMask = 1 << 5
        qa = img.select("pixel_qa")
        mask = (
            qa.bitwiseAnd(cloudShadowBitMask)
            .eq(0)
            .And(qa.bitwiseAnd(cloudsBitMask).eq(0))
        )
        return img.updateMask(mask)

    # Define function to prepare OLI images.
    def prepOli(img):
        orig = img
        img = renameOli(img)
        if apply_fmask:
            img = fmask(img)
        return ee.Image(img.copyProperties(orig, orig.propertyNames())).resample(
            "bicubic"
        )

    # Define function to prepare ETM+ images.
    def prepEtm(img):
        orig = img
        img = renameEtm(img)
        if apply_fmask:
            img = fmask(img)
        return ee.Image(img.copyProperties(orig, orig.propertyNames())).resample(
            "bicubic"
        )

    # Get annual median collection.
    def getAnnualComp(y):
        startDate = ee.Date.fromYMD(
            ee.Number(y), ee.Number(start_month), ee.Number(start_day)
        )
        endDate = startDate.advance(ee.Number(n_days), "day")

        # Filter collections and prepare them for merging.
        LC08coly = colFilter(LC08col, roi, startDate, endDate).map(prepOli)
        LE07coly = colFilter(LE07col, roi, startDate, endDate).map(prepEtm)
        LT05coly = colFilter(LT05col, roi, startDate, endDate).map(prepEtm)
        LT04coly = colFilter(LT04col, roi, startDate, endDate).map(prepEtm)

        # Merge the collections.
        col = LC08coly.merge(LE07coly).merge(LT05coly).merge(LT04coly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(nBands, yearImg, dummyImg))
        return calcNbr(yearImg).set(
            {"year": y, "system:time_start": startDate.millis(), "nBands": nBands}
        )

    ################################################################################

    # Make a dummy image for missing years.
    bandNames = ee.List(["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"])
    fillerValues = ee.List.repeat(0, bandNames.size())
    dummyImg = ee.Image.constant(fillerValues).rename(bandNames).selfMask().int16()

    ################################################################################
    # Get a list of years
    years = ee.List.sequence(start_year, end_year)

    ################################################################################
    # Make list of annual image composites.
    imgList = years.map(getAnnualComp)

    # Convert image composite list to collection
    imgCol = ee.ImageCollection.fromImages(imgList)

    imgCol = imgCol.map(
        lambda img: img.clip(roi).set({"coordinates": roi.coordinates()})
    )

    return imgCol

    # ################################################################################
    # # Run LandTrendr.
    # lt = ee.Algorithms.TemporalSegmentation.LandTrendr(
    #     timeSeries=imgCol.select(['NBR', 'SWIR1', 'NIR', 'Green']),
    #     maxSegments=10,
    #     spikeThreshold=0.7,
    #     vertexCountOvershoot=3,
    #     preventOneYearRecovery=True,
    #     recoveryThreshold=0.5,
    #     pvalThreshold=0.05,
    #     bestModelProportion=0.75,
    #     minObservationsNeeded=6)

    # ################################################################################
    # # Get fitted imagery. This starts export tasks.
    # def getYearStr(year):
    #     return(ee.String('yr_').cat(ee.Algorithms.String(year).slice(0,4)))

    # yearsStr = years.map(getYearStr)

    # r = lt.select(['SWIR1_fit']).arrayFlatten([yearsStr]).toShort()
    # g = lt.select(['NIR_fit']).arrayFlatten([yearsStr]).toShort()
    # b = lt.select(['Green_fit']).arrayFlatten([yearsStr]).toShort()

    # for i, c in zip([r, g, b], ['r', 'g', 'b']):
    #     descr = 'mamore-river-'+c
    #     name = 'users/user/'+descr
    #     print(name)
    #     task = ee.batch.Export.image.toAsset(
    #     image=i,
    #     region=roi.getInfo()['coordinates'],
    #     assetId=name,
    #     description=descr,
    #     scale=30,
    #     crs='EPSG:3857',
    #     maxPixels=1e13)
    #     task.start()


def modis_timeseries(
    asset_id="MODIS/006/MOD13A2",
    band_name=None,
    roi=None,
    start_year=2001,
    end_year=2021,
    start_date="01-01",
    end_date="12-31",
):
    """Generates a Monthly MODIS ImageCollection.
    Args:
        asset_id (str, optional): The asset id the MODIS ImageCollection.
        band_name (str, optional): The band name of the image to use.
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2020.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
    Returns:
        object: Returns an ImageCollection containing month MODIS images.
    """

    try:
        collection = ee.ImageCollection(asset_id)
        if band_name is None:
            band_name = collection.first().bandNames().getInfo()[0]
        collection = collection.select(band_name)
        if roi is not None:
            if isinstance(roi, ee.Geometry):
                collection = ee.ImageCollection(
                    collection.map(lambda img: img.clip(roi))
                )
            elif isinstance(roi, ee.FeatureCollection):
                collection = ee.ImageCollection(
                    collection.map(lambda img: img.clipToCollection(roi))
                )

        start = str(start_year) + "-" + start_date
        end = str(end_year) + "-" + end_date

        seq = date_sequence(start, end, "month")

        def monthly_modis(start_d):

            end_d = ee.Date(start_d).advance(1, "month")
            return ee.Image(collection.filterDate(start_d, end_d).mean())

        images = ee.ImageCollection(seq.map(monthly_modis))
        return images

    except Exception as e:
        raise Exception(e)


def landsat_timelapse(
    roi=None,
    out_gif=None,
    start_year=1984,
    end_year=2021,
    start_date="06-10",
    end_date="09-20",
    bands=["NIR", "Red", "Green"],
    vis_params=None,
    dimensions=768,
    frames_per_second=10,
    apply_fmask=True,
    nd_bands=None,
    nd_threshold=0,
    nd_palette=["black", "blue"],
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
):
    """Generates a Landsat timelapse GIF image. This function is adapted from https://emaprlab.users.earthengine.app/view/lt-gee-time-series-animator. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        out_gif (str, optional): File path to the output animated GIF. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2021.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        bands (list, optional): Three bands selected from ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']. Defaults to ['NIR', 'Red', 'Green'].
        vis_params (dict, optional): Visualization parameters. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
        nd_bands (list, optional): A list of names specifying the bands to use, e.g., ['Green', 'SWIR1']. The normalized difference is computed as (first − second) / (first + second). Note that negative input values are forced to 0 so that the result is confined to the range (-1, 1).
        nd_threshold (float, optional): The threshold for extacting pixels from the normalized difference band.
        nd_palette (list, optional): The color palette to use for displaying the normalized difference band.
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Line width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.

    Returns:
        str: File path to the output GIF image.
    """

    # ee_initialize()

    if roi is None:
        roi = ee.Geometry.Polygon(
            [
                [
                    [-115.471773, 35.892718],
                    [-115.471773, 36.409454],
                    [-114.271283, 36.409454],
                    [-114.271283, 35.892718],
                    [-115.471773, 35.892718],
                ]
            ],
            None,
            False,
        )
    elif isinstance(roi, ee.Feature) or isinstance(roi, ee.FeatureCollection):
        roi = roi.geometry()
    elif isinstance(roi, ee.Geometry):
        pass
    else:
        print("The provided roi is invalid. It must be an ee.Geometry")
        return

    if out_gif is None:
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = "landsat_ts_" + random_string() + ".gif"
        out_gif = os.path.join(out_dir, filename)
    elif not out_gif.endswith(".gif"):
        print("The output file must end with .gif")
        return
    # elif not os.path.isfile(out_gif):
    #     print('The output file must be a file')
    #     return
    else:
        out_gif = os.path.abspath(out_gif)
        out_dir = os.path.dirname(out_gif)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    allowed_bands = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2", "pixel_qa"]

    if len(bands) == 3 and all(x in allowed_bands for x in bands):
        pass
    else:
        raise Exception(
            "You can only select 3 bands from the following: {}".format(
                ", ".join(allowed_bands)
            )
        )

    if nd_bands is not None:
        if len(nd_bands) == 2 and all(x in allowed_bands[:-1] for x in nd_bands):
            pass
        else:
            raise Exception(
                "You can only select two bands from the following: {}".format(
                    ", ".join(allowed_bands[:-1])
                )
            )

    try:

        if vis_params is None:
            vis_params = {}
            vis_params["bands"] = bands
            vis_params["min"] = 0
            vis_params["max"] = 4000
            vis_params["gamma"] = [1, 1, 1]
        col = landsat_timeseries(
            roi, start_year, end_year, start_date, end_date, apply_fmask
        )
        # col = col.select(bands)
        col = col.select(bands).map(lambda img: img.visualize(**vis_params))
        if overlay_data is not None:
            col = add_overlay(
                col, overlay_data, overlay_color, overlay_width, overlay_opacity
            )

        video_args = vis_params.copy()
        video_args["dimensions"] = dimensions
        video_args["region"] = roi
        video_args["framesPerSecond"] = frames_per_second
        video_args["crs"] = "EPSG:3857"
        video_args["bands"] = ["vis-red", "vis-green", "vis-blue"]
        video_args["min"] = 0
        video_args["max"] = 255

        # if "bands" not in video_args.keys():
        #     video_args["bands"] = bands

        # if "min" not in video_args.keys():
        #     video_args["min"] = 0

        # if "max" not in video_args.keys():
        #     video_args["max"] = 4000

        # if "gamma" not in video_args.keys():
        #     video_args["gamma"] = [1, 1, 1]

        download_ee_video(col, video_args, out_gif)

        if nd_bands is not None:
            nd_images = landsat_ts_norm_diff(
                col, bands=nd_bands, threshold=nd_threshold
            )
            out_nd_gif = out_gif.replace(".gif", "_nd.gif")
            landsat_ts_norm_diff_gif(
                nd_images,
                out_gif=out_nd_gif,
                vis_params=None,
                palette=nd_palette,
                dimensions=dimensions,
                frames_per_second=frames_per_second,
            )

        return out_gif

    except Exception as e:
        print(e)


def sentinel2_timelapse(
    roi=None,
    out_gif=None,
    start_year=2015,
    end_year=2021,
    start_date="06-10",
    end_date="09-20",
    bands=["NIR", "Red", "Green"],
    vis_params=None,
    dimensions=768,
    frames_per_second=10,
    apply_fmask=True,
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
):
    """Generates a Sentinel-2 timelapse GIF image. This function is adapted from https://emaprlab.users.earthengine.app/view/lt-gee-time-series-animator. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        out_gif (str, optional): File path to the output animated GIF. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 2015.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2021.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        bands (list, optional): Three bands selected from ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'Red Edge 1', 'Red Edge 2', 'Red Edge 3', 'Red Edge 4']. Defaults to ['NIR', 'Red', 'Green'].
        vis_params (dict, optional): Visualization parameters. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        apply_fmask (bool, optional): Whether to apply Fmask (Function of mask) for automated clouds, cloud shadows, snow, and water masking.
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Line width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.

    Returns:
        str: File path to the output GIF image.
    """

    # ee_initialize()

    if roi is None:
        roi = ee.Geometry.Polygon(
            [
                [
                    [-115.471773, 35.892718],
                    [-115.471773, 36.409454],
                    [-114.271283, 36.409454],
                    [-114.271283, 35.892718],
                    [-115.471773, 35.892718],
                ]
            ],
            None,
            False,
        )
    elif isinstance(roi, ee.Feature) or isinstance(roi, ee.FeatureCollection):
        roi = roi.geometry()
    elif isinstance(roi, ee.Geometry):
        pass
    else:
        print("The provided roi is invalid. It must be an ee.Geometry")
        return

    if out_gif is None:
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = "s2_ts_" + random_string() + ".gif"
        out_gif = os.path.join(out_dir, filename)
    elif not out_gif.endswith(".gif"):
        print("The output file must end with .gif")
        return
    # elif not os.path.isfile(out_gif):
    #     print('The output file must be a file')
    #     return
    else:
        out_gif = os.path.abspath(out_gif)
        out_dir = os.path.dirname(out_gif)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    allowed_bands = [
        "Blue",
        "Green",
        "Red",
        "Red Edge 1",
        "Red Edge 2",
        "Red Edge 3",
        "NIR",
        "Red Edge 4",
        "SWIR1",
        "SWIR2",
        "QA60",
    ]

    if len(bands) == 3 and all(x in allowed_bands for x in bands):
        pass
    else:
        raise Exception(
            "You can only select 3 bands from the following: {}".format(
                ", ".join(allowed_bands)
            )
        )

    # if nd_bands is not None:
    #     if len(nd_bands) == 2 and all(x in allowed_bands[:-1] for x in nd_bands):
    #         pass
    #     else:
    #         raise Exception(
    #             "You can only select two bands from the following: {}".format(
    #                 ", ".join(allowed_bands[:-1])
    #             )
    #         )

    try:

        if vis_params is None:
            vis_params = {}
            vis_params["bands"] = bands
            vis_params["min"] = 0
            vis_params["max"] = 4000
            vis_params["gamma"] = [1, 1, 1]
        col = sentinel2_timeseries(
            roi, start_year, end_year, start_date, end_date, apply_fmask
        )
        # col = col.select(bands)
        col = col.select(bands).map(lambda img: img.visualize(**vis_params))
        if overlay_data is not None:
            col = add_overlay(
                col, overlay_data, overlay_color, overlay_width, overlay_opacity
            )

        video_args = vis_params.copy()
        video_args["dimensions"] = dimensions
        video_args["region"] = roi
        video_args["framesPerSecond"] = frames_per_second
        video_args["crs"] = "EPSG:3857"
        video_args["bands"] = ["vis-red", "vis-green", "vis-blue"]
        video_args["min"] = 0
        video_args["max"] = 255

        # if "bands" not in video_args.keys():
        #     video_args["bands"] = bands

        # if "min" not in video_args.keys():
        #     video_args["min"] = 0

        # if "max" not in video_args.keys():
        #     video_args["max"] = 4000

        # if "gamma" not in video_args.keys():
        #     video_args["gamma"] = [1, 1, 1]

        download_ee_video(col, video_args, out_gif)

        # if nd_bands is not None:
        #     nd_images = landsat_ts_norm_diff(
        #         col, bands=nd_bands, threshold=nd_threshold
        #     )
        #     out_nd_gif = out_gif.replace(".gif", "_nd.gif")
        #     landsat_ts_norm_diff_gif(
        #         nd_images,
        #         out_gif=out_nd_gif,
        #         vis_params=None,
        #         palette=nd_palette,
        #         dimensions=dimensions,
        #         frames_per_second=frames_per_second,
        #     )

        return out_gif

    except Exception as e:
        print(e)


def add_text_to_gif(
    in_gif,
    out_gif,
    xy=None,
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#000000",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    duration=100,
    loop=0,
):
    """Adds animated text to a GIF image.

    Args:
        in_gif (str): The file path to the input GIF image.
        out_gif (str): The file path to the output GIF image.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        duration (int, optional): controls how long each frame will be displayed for, in milliseconds. It is the inverse of the frame rate. Setting it to 100 milliseconds gives 10 frames per second. You can decrease the duration to give a smoother animation.. Defaults to 100.
        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.

    """
    # import io
    import warnings

    import pkg_resources
    from PIL import Image, ImageDraw, ImageFont, ImageSequence

    warnings.simplefilter("ignore")
    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    default_font = os.path.join(pkg_dir, "data/fonts/arial.ttf")

    in_gif = os.path.abspath(in_gif)
    out_gif = os.path.abspath(out_gif)

    if not os.path.exists(in_gif):
        print("The input gif file does not exist.")
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

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

    color = check_color(font_color)
    progress_bar_color = check_color(progress_bar_color)

    try:
        image = Image.open(in_gif)
    except Exception as e:
        print("An error occurred while opening the gif.")
        print(e)
        return

    count = image.n_frames
    W, H = image.size
    progress_bar_widths = [i * 1.0 / count * W for i in range(1, count + 1)]
    progress_bar_shapes = [
        [(0, H - progress_bar_height), (x, H)] for x in progress_bar_widths
    ]

    if xy is None:
        # default text location is 5% width and 5% height of the image.
        xy = (int(0.05 * W), int(0.05 * H))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        print("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")
        return
    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < W) and (y > 0) and (y < H):
            pass
        else:
            print(
                f"xy is out of bounds. x must be within [0, {W}], and y must be within [0, {H}]"
            )
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ("%" in x) and ("%" in y):
            try:
                x = int(float(x.replace("%", "")) / 100.0 * W)
                y = int(float(y.replace("%", "")) / 100.0 * H)
                xy = (x, y)
            except Exception:
                raise Exception(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')"
                )
    else:
        print(
            "The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')"
        )
        return

    if text_sequence is None:
        text = [str(x) for x in range(1, count + 1)]
    elif isinstance(text_sequence, int):
        text = [str(x) for x in range(text_sequence, text_sequence + count + 1)]
    elif isinstance(text_sequence, str):
        try:
            text_sequence = int(text_sequence)
            text = [str(x) for x in range(text_sequence, text_sequence + count + 1)]
        except Exception:
            text = [text_sequence] * count
    elif isinstance(text_sequence, list) and len(text_sequence) != count:
        print(
            f"The length of the text sequence must be equal to the number ({count}) of frames in the gif."
        )
        return
    else:
        text = [str(x) for x in text_sequence]

    try:

        frames = []
        # Loop over each frame in the animated image
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            # Draw the text on the frame
            frame = frame.convert("RGB")
            draw = ImageDraw.Draw(frame)
            # w, h = draw.textsize(text[index])
            draw.text(xy, text[index], font=font, fill=color)
            if add_progress_bar:
                draw.rectangle(progress_bar_shapes[index], fill=progress_bar_color)
            del draw

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)

            frames.append(frame)
        # https://www.pythoninformer.com/python-libraries/pillow/creating-animated-gif/
        # Save the frames as a new image

        frames[0].save(
            out_gif,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=loop,
            optimize=True,
        )
    except Exception as e:
        print(e)


def add_image_to_gif(
    in_gif, out_gif, in_image, xy=None, image_size=(80, 80), circle_mask=False
):
    """Adds an image logo to a GIF image.

    Args:
        in_gif (str): Input file path to the GIF image.
        out_gif (str): Output file path to the GIF image.
        in_image (str): Input file path to the image.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        image_size (tuple, optional): Resize image. Defaults to (80, 80).
        circle_mask (bool, optional): Whether to apply a circle mask to the image. This only works with non-png images. Defaults to False.
    """
    # import io
    import warnings

    from PIL import Image, ImageDraw, ImageSequence

    warnings.simplefilter("ignore")

    in_gif = os.path.abspath(in_gif)

    is_url = False
    if in_image.startswith("http"):
        is_url = True

    if not os.path.exists(in_gif):
        print("The input gif file does not exist.")
        return

    if (not is_url) and (not os.path.exists(in_image)):
        print("The provided logo file does not exist.")
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    try:
        image = Image.open(in_gif)
    except Exception as e:
        print("An error occurred while opening the image.")
        print(e)
        return

    logo_raw_image = None
    try:
        if in_image.startswith("http"):
            logo_raw_image = open_image_from_url(in_image)
        else:
            in_image = os.path.abspath(in_image)
            logo_raw_image = Image.open(in_image)
    except Exception as e:
        print(e)

    logo_raw_size = logo_raw_image.size
    image_size = min(logo_raw_size[0], image_size[0]), min(
        logo_raw_size[1], image_size[1]
    )

    logo_image = logo_raw_image.convert("RGBA")
    logo_image.thumbnail(image_size, Image.ANTIALIAS)

    W, H = image.size
    mask_im = None

    if circle_mask:
        mask_im = Image.new("L", image_size, 0)
        draw = ImageDraw.Draw(mask_im)
        draw.ellipse((0, 0, image_size[0], image_size[1]), fill=255)

    if has_transparency(logo_raw_image):
        mask_im = logo_image.copy()

    if xy is None:
        # default logo location is 5% width and 5% height of the image.
        xy = (int(0.05 * W), int(0.05 * H))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        print("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")
        return
    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < W) and (y > 0) and (y < H):
            pass
        else:
            print(
                "xy is out of bounds. x must be within [0, {}], and y must be within [0, {}]".format(
                    W, H
                )
            )
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ("%" in x) and ("%" in y):
            try:
                x = int(float(x.replace("%", "")) / 100.0 * W)
                y = int(float(y.replace("%", "")) / 100.0 * H)
                xy = (x, y)
            except Exception:
                raise Exception(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')"
                )

    else:
        raise Exception(
            "The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')"
        )

    try:

        frames = []
        for _, frame in enumerate(ImageSequence.Iterator(image)):
            frame = frame.convert("RGBA")
            frame.paste(logo_image, xy, mask_im)

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)
            frames.append(frame)

        frames[0].save(out_gif, save_all=True, append_images=frames[1:])
    except Exception as e:
        print(e)


def reduce_gif_size(in_gif, out_gif=None):
    """Reduces a GIF image using ffmpeg.

    Args:
        in_gif (str): The input file path to the GIF image.
        out_gif (str, optional): The output file path to the GIF image. Defaults to None.
    """
    import ffmpeg
    import warnings

    warnings.filterwarnings("ignore")

    if not is_tool("ffmpeg"):
        print("ffmpeg is not installed on your computer.")
        return

    if not os.path.exists(in_gif):
        print("The input gif file does not exist.")
        return

    if out_gif is None:
        out_gif = in_gif
    elif not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if in_gif == out_gif:
        tmp_gif = in_gif.replace(".gif", "_tmp.gif")
        shutil.copyfile(in_gif, tmp_gif)
        stream = ffmpeg.input(tmp_gif)
        stream = ffmpeg.output(stream, in_gif).overwrite_output()
        ffmpeg.run(stream)
        os.remove(tmp_gif)

    else:
        stream = ffmpeg.input(in_gif)
        stream = ffmpeg.output(stream, out_gif).overwrite_output()
        ffmpeg.run(stream)


def landsat_ts_norm_diff(collection, bands=["Green", "SWIR1"], threshold=0):
    """Computes a normalized difference index based on a Landsat timeseries.

    Args:
        collection (ee.ImageCollection): A Landsat timeseries.
        bands (list, optional): The bands to use for computing normalized difference. Defaults to ['Green', 'SWIR1'].
        threshold (float, optional): The threshold to extract features. Defaults to 0.

    Returns:
        ee.ImageCollection: An ImageCollection containing images with values greater than the specified threshold.
    """
    nd_images = collection.map(
        lambda img: img.normalizedDifference(bands)
        .gt(threshold)
        .copyProperties(img, img.propertyNames())
    )
    return nd_images


def landsat_ts_norm_diff_gif(
    collection,
    out_gif=None,
    vis_params=None,
    palette=["black", "blue"],
    dimensions=768,
    frames_per_second=10,
):
    """[summary]

    Args:
        collection (ee.ImageCollection): The normalized difference Landsat timeseires.
        out_gif (str, optional): File path to the output animated GIF. Defaults to None.
        vis_params (dict, optional): Visualization parameters. Defaults to None.
        palette (list, optional): The palette to use for visualizing the timelapse. Defaults to ['black', 'blue']. The first color in the list is the background color.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.

    Returns:
        str: File path to the output animated GIF.
    """
    coordinates = ee.Image(collection.first()).get("coordinates")
    roi = ee.Geometry.Polygon(coordinates, None, False)

    if out_gif is None:
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = "landsat_ts_nd_" + random_string() + ".gif"
        out_gif = os.path.join(out_dir, filename)
    elif not out_gif.endswith(".gif"):
        raise Exception("The output file must end with .gif")

    bands = ["nd"]
    if vis_params is None:
        vis_params = {}
        vis_params["bands"] = bands
        vis_params["palette"] = palette

    video_args = vis_params.copy()
    video_args["dimensions"] = dimensions
    video_args["region"] = roi
    video_args["framesPerSecond"] = frames_per_second
    video_args["crs"] = "EPSG:3857"

    if "bands" not in video_args.keys():
        video_args["bands"] = bands

    download_ee_video(collection, video_args, out_gif)

    return out_gif


def goes_timeseries(
    start_date="2021-10-24T14:00:00",
    end_date="2021-10-25T01:00:00",
    data="GOES-17",
    scan="full_disk",
    region=None,
):

    """Create a time series of GOES data. The code is adapted from Justin Braaten's code: https://code.earthengine.google.com/57245f2d3d04233765c42fb5ef19c1f4.
    Credits to Justin Braaten. See also https://jstnbraaten.medium.com/goes-in-earth-engine-53fbc8783c16

    Args:
        start_date (str, optional): The start date of the time series. Defaults to "2021-10-24T14:00:00".
        end_date (str, optional): The end date of the time series. Defaults to "2021-10-25T01:00:00".
        data (str, optional): The GOES satellite data to use. Defaults to "GOES-17".
        scan (str, optional): The GOES scan to use. Defaults to "full_disk".
        region (ee.Geometry, optional): The region of interest. Defaults to None.

    Raises:
        ValueError: The data must be either GOES-16 or GOES-17.
        ValueError: The scan must be either full_disk, conus, or mesoscale.

    Returns:
        ee.ImageCollection: GOES timeseries.
    """

    if data not in ["GOES-16", "GOES-17"]:
        raise ValueError("The data must be either GOES-16 or GOES-17.")

    if scan.lower() not in ["full_disk", "conus", "mesoscale"]:
        raise ValueError("The scan must be either full_disk, conus, or mesoscale.")

    scan_types = {
        "full_disk": "MCMIPF",
        "conus": "MCMIPC",
        "mesoscale": "MCMIPM",
    }

    col = ee.ImageCollection(f"NOAA/GOES/{data[-2:]}/{scan_types[scan.lower()]}")

    if region is None:
        region = ee.Geometry.Polygon(
            [
                [
                    [-159.5954379282731, 60.40883060191719],
                    [-159.5954379282731, 24.517881970830725],
                    [-114.2438754282731, 24.517881970830725],
                    [-114.2438754282731, 60.40883060191719],
                ]
            ],
            None,
            False,
        )

    # Applies scaling factors.
    def applyScaleAndOffset(img):
        def getFactorImg(factorNames):
            factorList = img.toDictionary().select(factorNames).values()
            return ee.Image.constant(factorList)

        scaleImg = getFactorImg(["CMI_C.._scale"])
        offsetImg = getFactorImg(["CMI_C.._offset"])
        scaled = img.select("CMI_C..").multiply(scaleImg).add(offsetImg)
        return img.addBands(**{"srcImg": scaled, "overwrite": True})

    # Adds a synthetic green band.
    def addGreenBand(img):
        green = img.expression(
            "CMI_GREEN = 0.45 * red + 0.10 * nir + 0.45 * blue",
            {
                "blue": img.select("CMI_C01"),
                "red": img.select("CMI_C02"),
                "nir": img.select("CMI_C03"),
            },
        )
        return img.addBands(green)

    # Scales select bands for visualization.
    def scaleForVis(img):
        return (
            img.select(["CMI_C01", "CMI_GREEN", "CMI_C02", "CMI_C03", "CMI_C05"])
            .resample("bicubic")
            .log10()
            .interpolate([-1.6, 0.176], [0, 1], "clamp")
            .unmask(0)
            .set("system:time_start", img.get("system:time_start"))
        )

    # Wraps previous functions.
    def processForVis(img):

        return scaleForVis(addGreenBand(applyScaleAndOffset(img)))

    return col.filterDate(start_date, end_date).map(processForVis)


def goes_fire_timeseries(
    start_date="2020-09-05T15:00",
    end_date="2020-09-06T02:00",
    data="GOES-17",
    scan="full_disk",
    region=None,
    merge=True,
):

    """Create a time series of GOES Fire data. The code is adapted from Justin Braaten's code: https://code.earthengine.google.com/8a083a7fb13b95ad4ba148ed9b65475e.
    Credits to Justin Braaten. See also https://jstnbraaten.medium.com/goes-in-earth-engine-53fbc8783c16

    Args:
        start_date (str, optional): The start date of the time series. Defaults to "2020-09-05T15:00".
        end_date (str, optional): The end date of the time series. Defaults to "2020-09-06T02:00".
        data (str, optional): The GOES satellite data to use. Defaults to "GOES-17".
        scan (str, optional): The GOES scan to use. Defaults to "full_disk".
        region (ee.Geometry, optional): The region of interest. Defaults to None.
        merge (bool, optional): Whether to merge the fire timeseries with GOES CMI timeseries. Defaults to True.

    Raises:
        ValueError: The data must be either GOES-16 or GOES-17.
        ValueError: The scan must be either full_disk or conus.

    Returns:
        ee.ImageCollection: GOES fire timeseries.
    """

    if data not in ["GOES-16", "GOES-17"]:
        raise ValueError("The data must be either GOES-16 or GOES-17.")

    if scan.lower() not in ["full_disk", "conus"]:
        raise ValueError("The scan must be either full_disk or conus.")

    scan_types = {
        "full_disk": "FDCF",
        "conus": "FDCC",
    }

    if region is None:
        region = ee.Geometry.BBox(-123.17, 36.56, -118.22, 40.03)

    # Get the fire/hotspot characterization dataset.
    col = ee.ImageCollection(f"NOAA/GOES/{data[-2:]}/{scan_types[scan.lower()]}")
    fdcCol = col.filterDate(start_date, end_date)

    # Identify fire-detected pixels of medium to high confidence.
    fireMaskCodes = [10, 30, 11, 31, 12, 32, 13, 33, 14, 34, 15, 35]
    confVals = [1.0, 1.0, 0.9, 0.9, 0.8, 0.8, 0.5, 0.5, 0.3, 0.3, 0.1, 0.1]
    defaultConfVal = 0

    def fdcVis(img):
        confImg = img.remap(fireMaskCodes, confVals, defaultConfVal, "Mask")
        return (
            confImg.gte(0.3)
            .selfMask()
            .set("system:time_start", img.get("system:time_start"))
        )

    fdcVisCol = fdcCol.map(fdcVis)
    if not merge:
        return fdcVisCol
    else:
        geosVisCol = goes_timeseries(start_date, end_date, data, scan, region)
        # Join the fire collection to the CMI collection.
        joinFilter = ee.Filter.equals(
            **{"leftField": "system:time_start", "rightField": "system:time_start"}
        )
        joinedCol = ee.Join.saveFirst("match").apply(geosVisCol, fdcVisCol, joinFilter)

        def overlayVis(img):
            cmi = ee.Image(img).visualize(
                **{
                    "bands": ["CMI_C02", "CMI_GREEN", "CMI_C01"],
                    "min": 0,
                    "max": 0.8,
                    "gamma": 0.8,
                }
            )
            fdc = ee.Image(img.get("match")).visualize(
                **{"palette": ["ff5349"], "min": 0, "max": 1, "opacity": 0.7}
            )
            return cmi.blend(fdc).set("system:time_start", img.get("system:time_start"))

        cmiFdcVisCol = ee.ImageCollection(joinedCol.map(overlayVis))
        return cmiFdcVisCol


def goes_timelapse(
    out_gif,
    start_date="2021-10-24T14:00:00",
    end_date="2021-10-25T01:00:00",
    data="GOES-17",
    scan="full_disk",
    region=None,
    dimensions=768,
    framesPerSecond=10,
    date_format="YYYY-MM-dd HH:mm",
    xy=("3%", "3%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#ffffff",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    crs=None,
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    **kwargs,
):
    """Create a timelapse of GOES data. The code is adapted from Justin Braaten's code: https://code.earthengine.google.com/57245f2d3d04233765c42fb5ef19c1f4.
    Credits to Justin Braaten. See also https://jstnbraaten.medium.com/goes-in-earth-engine-53fbc8783c16

    Args:
        out_gif (str): The file path to save the gif.
        start_date (str, optional): The start date of the time series. Defaults to "2021-10-24T14:00:00".
        end_date (str, optional): The end date of the time series. Defaults to "2021-10-25T01:00:00".
        data (str, optional): The GOES satellite data to use. Defaults to "GOES-17".
        scan (str, optional): The GOES scan to use. Defaults to "full_disk".
        region (ee.Geometry, optional): The region of interest. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        date_format (str, optional): The date format to use. Defaults to "YYYY-MM-dd HH:mm".
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        crs (str, optional): The coordinate reference system to use, e.g., "EPSG:3857". Defaults to None.
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Line width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.
    Raises:
        Exception: Raise exception.
    """

    try:

        bands = ["CMI_C02", "CMI_GREEN", "CMI_C01"]
        visParams = {
            "bands": bands,
            "min": 0,
            "max": 0.8,
        }
        col = goes_timeseries(start_date, end_date, data, scan, region)
        col = col.select(bands).map(lambda img: img.visualize(**visParams))
        if overlay_data is not None:
            col = add_overlay(
                col, overlay_data, overlay_color, overlay_width, overlay_opacity
            )

        if region is None:
            region = ee.Geometry.Polygon(
                [
                    [
                        [-159.5954, 60.4088],
                        [-159.5954, 24.5178],
                        [-114.2438, 24.5178],
                        [-114.2438, 60.4088],
                    ]
                ],
                None,
                False,
            )

        if crs is None:
            crs = col.first().projection()

        videoParams = {
            "bands": ["vis-red", "vis-green", "vis-blue"],
            "min": 0,
            "max": 255,
            "dimensions": dimensions,
            "framesPerSecond": framesPerSecond,
            "region": region,
            "crs": crs,
        }

        if text_sequence is None:
            text_sequence = image_dates(col, date_format=date_format).getInfo()

        download_ee_video(col, videoParams, out_gif)

        if os.path.exists(out_gif):

            add_text_to_gif(
                out_gif,
                out_gif,
                xy,
                text_sequence,
                font_type,
                font_size,
                font_color,
                add_progress_bar,
                progress_bar_color,
                progress_bar_height,
                duration=1000 / framesPerSecond,
                loop=loop,
            )

            try:
                reduce_gif_size(out_gif)
            except Exception as _:
                pass

    except Exception as e:
        raise Exception(e)


def goes_fire_timelapse(
    out_gif,
    start_date="2020-09-05T15:00",
    end_date="2020-09-06T02:00",
    data="GOES-17",
    scan="full_disk",
    region=None,
    dimensions=768,
    framesPerSecond=10,
    date_format="YYYY-MM-dd HH:mm",
    xy=("3%", "3%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#ffffff",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    crs=None,
    overlay_data=None,
    overlay_color="#000000",
    overlay_width=1,
    overlay_opacity=1.0,
    **kwargs,
):
    """Create a timelapse of GOES fire data. The code is adapted from Justin Braaten's code: https://code.earthengine.google.com/8a083a7fb13b95ad4ba148ed9b65475e.
    Credits to Justin Braaten. See also https://jstnbraaten.medium.com/goes-in-earth-engine-53fbc8783c16

    Args:
        out_gif (str): The file path to save the gif.
        start_date (str, optional): The start date of the time series. Defaults to "2021-10-24T14:00:00".
        end_date (str, optional): The end date of the time series. Defaults to "2021-10-25T01:00:00".
        data (str, optional): The GOES satellite data to use. Defaults to "GOES-17".
        scan (str, optional): The GOES scan to use. Defaults to "full_disk".
        region (ee.Geometry, optional): The region of interest. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        date_format (str, optional): The date format to use. Defaults to "YYYY-MM-dd HH:mm".
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        crs (str, optional): The coordinate reference system to use, e.g., "EPSG:3857". Defaults to None.
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.

    Raises:
        Exception: Raise exception.
    """

    try:

        if region is None:
            region = ee.Geometry.BBox(-123.17, 36.56, -118.22, 40.03)

        col = goes_fire_timeseries(start_date, end_date, data, scan, region)
        if overlay_data is not None:
            col = add_overlay(
                col, overlay_data, overlay_color, overlay_width, overlay_opacity
            )

        # visParams = {
        #     "bands": ["CMI_C02", "CMI_GREEN", "CMI_C01"],
        #     "min": 0,
        #     "max": 0.8,
        #     "dimensions": dimensions,
        #     "framesPerSecond": framesPerSecond,
        #     "region": region,
        #     "crs": col.first().projection(),
        # }

        if crs is None:
            crs = col.first().projection()

        cmiFdcVisParams = {
            "dimensions": dimensions,
            "framesPerSecond": framesPerSecond,
            "region": region,
            "crs": crs,
        }

        if text_sequence is None:
            text_sequence = image_dates(col, date_format=date_format).getInfo()

        download_ee_video(col, cmiFdcVisParams, out_gif)

        if os.path.exists(out_gif):

            add_text_to_gif(
                out_gif,
                out_gif,
                xy,
                text_sequence,
                font_type,
                font_size,
                font_color,
                add_progress_bar,
                progress_bar_color,
                progress_bar_height,
                duration=1000 / framesPerSecond,
                loop=loop,
            )

            try:
                reduce_gif_size(out_gif)
            except Exception as _:
                pass

    except Exception as e:
        raise Exception(e)


def modis_ndvi_doy_ts(
    data="Terra", band="NDVI", start_date=None, end_date=None, region=None
):
    """Create MODIS NDVI timeseries. The source code is adapted from https://developers.google.com/earth-engine/tutorials/community/modis-ndvi-time-series-animation.

    Args:
        data (str, optional): Either "Terra" or "Aqua". Defaults to "Terra".
        band (str, optional): Either the "NDVI" or "EVI" band. Defaults to "NDVI".
        start_date (str, optional): The start date used to filter the image collection, e.g., "2013-01-01". Defaults to None.
        end_date (str, optional): The end date used to filter the image collection. Defaults to None.
        region (ee.Geometry, optional): The geometry used to filter the image collection. Defaults to None.

    Returns:
        ee.ImageCollection: The MODIS NDVI time series.
    """
    if data not in ["Terra", "Aqua"]:
        raise Exception("data must be 'Terra' or 'Aqua'.")

    if band not in ["NDVI", "EVI"]:
        raise Exception("band must be 'NDVI' or 'EVI'.")

    if region is not None:
        if isinstance(region, ee.Geometry) or isinstance(region, ee.FeatureCollection):
            pass
        else:
            raise Exception("region must be an ee.Geometry or ee.FeatureCollection.")

    if data == "Terra":
        col = ee.ImageCollection("MODIS/006/MOD13A2").select(band)
    else:
        col = ee.ImageCollection("MODIS/006/MYD13A2").select(band)

    if (start_date is not None) and (end_date is not None):
        col = col.filterDate(start_date, end_date)

    def set_doy(img):
        doy = ee.Date(img.get("system:time_start")).getRelative("day", "year")
        return img.set("doy", doy)

    col = col.map(set_doy)

    # Get a collection of distinct images by 'doy'.
    distinctDOY = col.filterDate("2013-01-01", "2014-01-01")

    # Define a filter that identifies which images from the complete
    # collection match the DOY from the distinct DOY collection.
    filter = ee.Filter.equals(**{"leftField": "doy", "rightField": "doy"})

    # Define a join.
    join = ee.Join.saveAll("doy_matches")

    # Apply the join and convert the resulting FeatureCollection to an
    # ImageCollection.
    joinCol = ee.ImageCollection(join.apply(distinctDOY, col, filter))

    # Apply median reduction among matching DOY collections.

    def match_doy(img):
        doyCol = ee.ImageCollection.fromImages(img.get("doy_matches"))
        return doyCol.reduce(ee.Reducer.median())

    comp = joinCol.map(match_doy)

    if region is not None:
        return comp.map(lambda img: img.clip(region))
    else:
        return comp


def modis_ndvi_timelapse(
    out_gif,
    data="Terra",
    band="NDVI",
    start_date=None,
    end_date=None,
    region=None,
    dimensions=768,
    framesPerSecond=10,
    crs="EPSG:3857",
    xy=("3%", "3%"),
    text_sequence=None,
    font_type="arial.ttf",
    font_size=20,
    font_color="#ffffff",
    add_progress_bar=True,
    progress_bar_color="white",
    progress_bar_height=5,
    loop=0,
    overlay_data=None,
    overlay_color="black",
    overlay_width=1,
    overlay_opacity=1.0,
    **kwargs,
):
    """Create MODIS NDVI timelapse. The source code is adapted from https://developers.google.com/earth-engine/tutorials/community/modis-ndvi-time-series-animation.

    Args:
        data (str, optional): Either "Terra" or "Aqua". Defaults to "Terra".
        band (str, optional): Either the "NDVI" or "EVI" band. Defaults to "NDVI".
        start_date (str, optional): The start date used to filter the image collection, e.g., "2013-01-01". Defaults to None.
        end_date (str, optional): The end date used to filter the image collection. Defaults to None.
        region (ee.Geometry, optional): The geometry used to filter the image collection. Defaults to None.
        crs (str, optional): The coordinate reference system to use. Defaults to "EPSG:3857".
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.
        overlay_data (int, str, list, optional): Administrative boundary to be drawn on the timelapse. Defaults to None.
        overlay_color (str, optional): Color for the overlay data. Can be any color name or hex color code. Defaults to 'black'.
        overlay_width (int, optional): Width of the overlay. Defaults to 1.
        overlay_opacity (float, optional): Opacity of the overlay. Defaults to 1.0.

    """

    if region is None:
        region = ee.Geometry.Polygon(
            [
                [
                    [-18.6983, 38.1446],
                    [-18.6983, -36.1630],
                    [52.2293, -36.1630],
                    [52.2293, 38.1446],
                ]
            ],
            None,
            False,
        )

    try:
        col = modis_ndvi_doy_ts(data, band, start_date, end_date, region)

        # Define RGB visualization parameters.
        visParams = {
            "min": 0.0,
            "max": 9000.0,
            "palette": [
                "FFFFFF",
                "CE7E45",
                "DF923D",
                "F1B555",
                "FCD163",
                "99B718",
                "74A901",
                "66A000",
                "529400",
                "3E8601",
                "207401",
                "056201",
                "004C00",
                "023B01",
                "012E01",
                "011D01",
                "011301",
            ],
        }

        # Create RGB visualization images for use as animation frames.
        rgbVis = col.map(lambda img: img.visualize(**visParams).clip(region))

        if overlay_data is not None:
            rgbVis = add_overlay(
                rgbVis,
                overlay_data,
                overlay_color,
                overlay_width,
                overlay_opacity,
                region,
            )

        # Define GIF visualization arguments.
        videoArgs = {
            "region": region,
            "dimensions": dimensions,
            "crs": crs,
            "framesPerSecond": framesPerSecond,
        }

        download_ee_video(rgbVis, videoArgs, out_gif)

        if text_sequence is None:
            text = rgbVis.aggregate_array("system:index").getInfo()
            text_sequence = [d.replace("_", "-")[5:] for d in text]

        if os.path.exists(out_gif):

            add_text_to_gif(
                out_gif,
                out_gif,
                xy,
                text_sequence,
                font_type,
                font_size,
                font_color,
                add_progress_bar,
                progress_bar_color,
                progress_bar_height,
                duration=1000 / framesPerSecond,
                loop=loop,
            )

            try:
                reduce_gif_size(out_gif)
            except Exception as _:
                pass

    except Exception as e:
        raise Exception(e)
