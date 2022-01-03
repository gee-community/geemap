from typing import Optional, Union

import ee
from ee_extra.Algorithms import river


def rwc(
    image: Union[str, ee.Image],
    description: Optional[str] = None,
    folder: str = "",
    file_format: str = "shp",
    aoi: Optional[ee.Geometry.Polygon] = None,
    water_method: Optional[str] = "Jones2019",
    max_dist: Optional[int] = 4000,
    fill_size: Optional[int] = 333,
    max_dist_branch_removal: Optional[int] = 500,
    return_fc: Optional[bool] = False,
):
    """Calculate river centerlines and widths for one Landsat SR image.

    Args:
        image (str | ee.Image): LANDSAT_ID for any Landsat 5, 7, and 8 SR scene. For example, LC08_L1TP_022034_20130422_20170310_01_T1.
        description (str, optional): File name of the output file. Defaults to None.
        folder (str, optional): Folder name within Google Drive to save the exported file. Defaults to "", which is the root directory.
        file_format (str, optional): The supported file format include shp, csv, json, kml, kmz, and TFRecord. Defaults to 'shp'. Defaults to "shp".
        aoi (ee.Geometry.Polygon, optional): A polygon (or rectangle) geometry define the area of interest. Only widths and centerline from this area will be calculated. Defaults to None.
        water_method (str, optional): Water classification method ('Jones2019' or 'Zou2018'). Defaults to "Jones2019".
        max_dist (int, optional): Maximum distance (unit: meters) to check water pixel's connectivity to GRWL centerline. Defaults to 4000.
        fill_size (int, optional): Islands or bars smaller than this value (unit: pixels) will be removed before calculating centerline. Defaults to 333.
        max_dist_branch_removal (int, optional): Length of pruning. Spurious branch of the initial centerline will be removed by this length (unit: pixels). Defaults to 500.
        return_fc (Optional[bool], optional): Whether to return the result as an ee.FeatureColleciton. Defaults to False.

    Returns:
        If return_fc is True, return an ee.FeatureCollection. Otherwise, return True.

    Examples:
        >>> import ee
        >>> from ee_extra.Algorithms import river
        >>> ee.Initialize()
        >>> # Find an image by ROI.
        >>> point = ee.Geometry.Point([-88.08, 37.47])
        >>> image = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR") \
        >>>           .filterBounds(point) \
        >>>           .sort("CLOUD_COVER") \
        >>>           .first()
        >>> # Extract river width for a single image.
        >>> ## Export to drive
        >>> river.rwc(image, folder="export", water_method='Jones2019')
        >>> ## Return a ee.FeatureCollection
        >>> river.rwc(image, water_method='Jones2019', return_fc=True)
    """
    return river.rwc(
        image=image,
        description=description,
        folder=folder,
        file_format=file_format,
        aoi=aoi,
        water_method=water_method,
        max_dist=max_dist,
        fill_size=fill_size,
        max_dist_branch_removal=max_dist_branch_removal,
        return_fc=return_fc,
    )


def rwc_batch(
    images: Union[str, list, ee.ImageCollection],
    folder: Optional[str] = "",
    file_format: Optional[str] = "shp",
    aoi: Optional[ee.Geometry.Polygon] = None,
    water_method: Optional[str] = "Jones2019",
    max_dist: Optional[int] = 4000,
    fill_size: Optional[int] = 333,
    max_dist_branch_remove: Optional[int] = 500,
):
    """Calculate river centerlines and widths for multiple Landsat SR images.

    Args:
        images (Union[str, list, ee.ImageCollection]): An input csv file containing a list of Landsat IDs (e.g., LC08_L1TP_022034_20130422_20170310_01_T1).
        folder (Optional[str], optional): Folder name within Google Drive to save the exported file. Defaults to "", which is the root directory.
        file_format (Optional[str], optional): The supported file format include shp, csv, json, kml, kmz, and TFRecord. Defaults to 'shp'.
        aoi (Optional[ee.Geometry.Polygon], optional): A polygon (or rectangle) geometry define the area of interest. Only widths and centerline from this area will be calculated. Defaults to None.
        water_method (Optional[str], optional): Water classification method ('Jones2019' or 'Zou2018'). Defaults to "Jones2019".
        max_dist (Optional[int], optional): Maximum distance (unit: meters) to check water pixel's connectivity to GRWL centerline. Defaults to 4000.
        fill_size (Optional[int], optional): Islands or bars smaller than this value (unit: pixels) will be removed before calculating centerline. Defaults to 333.
        max_dist_branch_remove (Optional[int], optional): Length of pruning. Spurious branch of the initial centerline will be removed by this length (unit: pixels). Defaults to 500.

    Returns:
        Return True.

    Examples:
        >>> import ee
        >>> from ee_extra.Algorithms import river
        >>> ee.Initialize()
        >>> # Find an image by ROI.
        >>> point = ee.Geometry.Point([-88.08, 37.47])
        >>> image = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR") \
        >>>           .filterBounds(point) \
        >>>           .sort("CLOUD_COVER")
        >>> ic = ee.ImageCollection(ic.toList(2))
        >>> # Extract river width iteratively.
        >>> river.rwc_batch(ic, folder="export2", water_method='Jones2019')
    """
    return river.rwc_batch(
        images=images,
        folder=folder,
        file_format=file_format,
        aoi=aoi,
        water_method=water_method,
        max_dist=max_dist,
        fill_size=fill_size,
        max_dist_branch_remove=max_dist_branch_remove,
    )
