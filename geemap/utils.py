
"""Module of various Earth Engine utility functions.
"""
import os
import ee


def ee_initialize(token_name='EARTHENGINE_TOKEN'):
    """Authenticates Earth Engine and initialize an Earth Engine session

    """
    try:
        ee_token = os.environ.get(token_name)
        if ee_token is not None:
            credential = '{"refresh_token":"%s"}' % ee_token
            credential_file_path = os.path.expanduser("~/.config/earthengine/")
            os.makedirs(credential_file_path, exist_ok=True)
            with open(credential_file_path + 'credentials', 'w') as file:
                file.write(credential)

        ee.Initialize()
    except:
        ee.Authenticate()
        ee.Initialize()


def vec_area(fc):
    """Calculate the area (m2) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({'area_m2': f.area(1).round()}))


def vec_area_km2(fc):
    """Calculate the area (km2) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({'area_km2': f.area(1).divide(1e6).round()}))


def vec_area_mi2(fc):
    """Calculate the area (square mile) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({'area_mi2': f.area(1).divide(2.59e6).round()}))


def vec_area_ha(fc):
    """Calculate the area (hectare) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({'area_ha': f.area(1).divide(1e4).round()}))


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
    scale = ee.Algorithms.If(scales.distinct().size().gt(1), ee.Dictionary.fromLists(bands.getInfo(), scales), scales.get(0))
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


def image_date(img, date_format='YYYY-MM-dd'):
    """Retrieves the image acquisition date.

    Args:
        img (object): ee.Image
        date_format (str, optional): The date format to use. Defaults to 'YYYY-MM-dd'.

    Returns:
        str: A string representing the acquisition of the image.
    """
    return ee.Date(img.get('system:time_start')).format(date_format)


def image_area(img, region=None, scale=None, denominator=1.0):
    """Calculates the the area of an image.

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

    pixel_area = img.unmask().neq(ee.Image(0)).multiply(
        ee.Image.pixelArea()).divide(denominator)
    img_area = pixel_area.reduceRegion(**{
        'geometry': region,
        'reducer': ee.Reducer.sum(),
        'scale': scale,
        'maxPixels': 1e12
    })
    return img_area


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

    max_value = img.reduceRegion(**{
        'reducer': ee.Reducer.max(),
        'geometry': region,
        'scale': scale,
        'maxPixels': 1e12
    })
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

    min_value = img.reduceRegion(**{
        'reducer': ee.Reducer.min(),
        'geometry': region,
        'scale': scale,
        'maxPixels': 1e12
    })
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

    mean_value = img.reduceRegion(**{
        'reducer': ee.Reducer.mean(),
        'geometry': region,
        'scale': scale,
        'maxPixels': 1e12
    })
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

    std_value = img.reduceRegion(**{
        'reducer': ee.Reducer.stdDev(),
        'geometry': region,
        'scale': scale,
        'maxPixels': 1e12
    })
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

    sum_value = img.reduceRegion(**{
        'reducer': ee.Reducer.sum(),
        'geometry': region,
        'scale': scale,
        'maxPixels': 1e12
    })
    return sum_value


def extract_values_to_points(in_points, img, label, scale=None):
    """Extracts image values to points.

    Args:
        in_points (object): ee.FeatureCollection
        img (object): ee.Image
        label (str): The column name to keep.
        scale (float, optional): The image resolution to use. Defaults to None.

    Returns:
        object: ee.FeatureCollection
    """
    if scale is None:
        scale = image_scale(img)

    out_fc = img.sampleRegions(**{
        'collection': in_points,
        'properties': [label],
        'scale': scale
    })

    return out_fc


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
    image = img.reduceNeighborhood(**{
        'reducer': reducer,
        'kernel': kernel,
    })
    return image


def rename_bands(img, in_band_names, out_band_names):
    """Renames image bands.

    Args:
        img (object): The image to be renamed.
        in_band_names (list): The list of of input band names.
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
    collection = ee.ImageCollection(
        img.bandNames().map(lambda b: img.select([b])))
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
            collection = landsat_col.filter(ee.Filter.eq('WRS_PATH', path_num)) \
                .filter(ee.Filter.eq('WRS_ROW', row_num))
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
        collection = ee.ImageCollection('USDA/NAIP/DOQQ')
        start_date = str(year) + '-01-01'
        end_date = str(year) + '-12-31'
        naip = collection.filterDate(start_date, end_date)
        if RGBN:
            naip = naip.filter(ee.Filter.listContains(
                "system:band_names", "N"))
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
                collection = ee.ImageCollection('USDA/NAIP/DOQQ')
                start_date = ee.Date.fromYMD(year, 1, 1)
                end_date = ee.Date.fromYMD(year, 12, 31)
                naip = collection.filterDate(start_date, end_date) \
                    .filter(ee.Filter.listContains("system:band_names", "N"))
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
    collection = ee.ImageCollection('USDA/NAIP/DOQQ') \
        .filterDate(start_date, end_date) \
        .filterBounds(region)

    time_start = ee.Date(
        ee.List(collection.aggregate_array('system:time_start')).sort().get(0))
    time_end = ee.Date(
        ee.List(collection.aggregate_array('system:time_end')).sort().get(-1))
    image = ee.Image(collection.mosaic().clip(region))
    NDWI = ee.Image(image).normalizedDifference(
        ['G', 'N']).select(['nd'], ['ndwi'])
    NDVI = ee.Image(image).normalizedDifference(
        ['N', 'R']).select(['nd'], ['ndvi'])
    image = image.addBands(NDWI)
    image = image.addBands(NDVI)
    return image.set({'system:time_start': time_start, 'system:time_end': time_end})


def find_NAIP(region, add_NDVI=True, add_NDWI=True):
    """Create annual NAIP mosaic for a given region.

    Args:
        region (object): ee.Geometry
        add_NDVI (bool, optional): Whether to add the NDVI band. Defaults to True.
        add_NDWI (bool, optional): Whether to add the NDWI band. Defaults to True.

    Returns:
        object: ee.ImageCollection
    """

    init_collection = ee.ImageCollection('USDA/NAIP/DOQQ') \
        .filterBounds(region) \
        .filterDate('2009-01-01', '2019-12-31') \
        .filter(ee.Filter.listContains("system:band_names", "N"))

    yearList = ee.List(init_collection.distinct(
        ['system:time_start']).aggregate_array('system:time_start'))
    init_years = yearList.map(lambda y: ee.Date(y).get('year'))

    # remove duplicates
    init_years = ee.Dictionary(init_years.reduce(
        ee.Reducer.frequencyHistogram())).keys()
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
            ee.List(collection.aggregate_array('system:time_start')).sort().get(0)).format('YYYY-MM-dd')
        time_end = ee.Date(
            ee.List(collection.aggregate_array('system:time_end')).sort().get(-1)).format('YYYY-MM-dd')
        col_size = collection.size()
        image = ee.Image(collection.mosaic().clip(region))

        if add_NDVI:
            NDVI = ee.Image(image).normalizedDifference(
                ['N', 'R']).select(['nd'], ['ndvi'])
            image = image.addBands(NDVI)

        if add_NDWI:
            NDWI = ee.Image(image).normalizedDifference(
                ['G', 'N']).select(['nd'], ['ndwi'])
            image = image.addBands(NDWI)

        return image.set({'system:time_start': time_start, 'system:time_end': time_end, 'tiles': col_size})

    # remove years with incomplete coverage
    naip = ee.ImageCollection(years.map(NAIPAnnual))
    mean_size = ee.Number(naip.aggregate_mean('tiles'))
    total_sd = ee.Number(naip.aggregate_total_sd('tiles'))
    threshold = mean_size.subtract(total_sd.multiply(1))
    naip = naip.filter(ee.Filter.Or(ee.Filter.gte(
        'tiles', threshold), ee.Filter.gte('tiles', 15)))
    naip = naip.filter(ee.Filter.gte('tiles', 7))

    naip_count = naip.size()
    naip_seq = ee.List.sequence(0, naip_count.subtract(1))

    def set_index(index):
        img = ee.Image(naip.toList(naip_count).get(index))
        return img.set({'system:uid': ee.Number(index).toUint8()})

    naip = naip_seq.map(set_index)

    return ee.ImageCollection(naip)


def filter_NWI(HUC08_Id, region, exclude_riverine=True):
    """Retrives NWI dataset for a given HUC8 watershed.

    Args:
        HUC08_Id (str): The HUC8 watershed id.
        region (object): ee.Geometry
        exclude_riverine (bool, optional): Whether to exclude riverine wetlands. Defaults to True.

    Returns:
        object: ee.FeatureCollection
    """
    nwi_asset_prefix = 'users/wqs/NWI-HU8/HU8_'
    nwi_asset_suffix = '_Wetlands'
    nwi_asset_path = nwi_asset_prefix + HUC08_Id + nwi_asset_suffix
    nwi_huc = ee.FeatureCollection(nwi_asset_path).filterBounds(region)

    if exclude_riverine:
        nwi_huc = nwi_huc.filter(ee.Filter.notEquals(
            **{'leftField': 'WETLAND_TY', 'rightValue': 'Riverine'}))
    return nwi_huc


def filter_HUC08(region):
    """Filters HUC08 watersheds intersecting a given region.

    Args:
        region (object): ee.Geometry

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC08 = ee.FeatureCollection('USGS/WBD/2017/HUC08')   # Subbasins
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

    USGS_HUC10 = ee.FeatureCollection('USGS/WBD/2017/HUC10')   # Watersheds
    HUC10 = USGS_HUC10.filterBounds(region)
    return HUC10


def find_HUC08(HUC08_Id):
    """Finds a HUC08 watershed based on a given HUC08 ID

    Args:
        HUC08_Id (str): The HUC08 ID.

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC08 = ee.FeatureCollection('USGS/WBD/2017/HUC08')   # Subbasins
    HUC08 = USGS_HUC08.filter(ee.Filter.eq('huc8', HUC08_Id))
    return HUC08


def find_HUC10(HUC10_Id):
    """Finds a HUC10 watershed based on a given HUC08 ID

    Args:
        HUC10_Id (str): The HUC10 ID.

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC10 = ee.FeatureCollection('USGS/WBD/2017/HUC10')   # Watersheds
    HUC10 = USGS_HUC10.filter(ee.Filter.eq('huc10', HUC10_Id))
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

    nwi_asset_prefix = 'users/wqs/NWI-HU8/HU8_'
    nwi_asset_suffix = '_Wetlands'
    nwi_asset_path = nwi_asset_prefix + HUC08_Id + nwi_asset_suffix
    nwi_huc = ee.FeatureCollection(nwi_asset_path)
    if exclude_riverine:
        nwi_huc = nwi_huc.filter(ee.Filter.notEquals(
            **{'leftField': 'WETLAND_TY', 'rightValue': 'Riverine'}))
    return nwi_huc


def nwi_add_color(fc):
    """Converts NWI vector dataset to image and add color to it.

    Args:
        fc (object): ee.FeatureCollection

    Returns:
        object: ee.Image
    """
    emergent = ee.FeatureCollection(
        fc.filter(ee.Filter.eq('WETLAND_TY', 'Freshwater Emergent Wetland')))
    emergent = emergent.map(lambda f: f.set(
        'R', 127).set('G', 195).set('B', 28))
    # print(emergent.first())

    forested = fc.filter(ee.Filter.eq(
        'WETLAND_TY', 'Freshwater Forested/Shrub Wetland'))
    forested = forested.map(lambda f: f.set('R', 0).set('G', 136).set('B', 55))

    pond = fc.filter(ee.Filter.eq('WETLAND_TY', 'Freshwater Pond'))
    pond = pond.map(lambda f: f.set('R', 104).set('G', 140).set('B', 192))

    lake = fc.filter(ee.Filter.eq('WETLAND_TY', 'Lake'))
    lake = lake.map(lambda f: f.set('R', 19).set('G', 0).set('B', 124))

    riverine = fc.filter(ee.Filter.eq('WETLAND_TY', 'Riverine'))
    riverine = riverine.map(lambda f: f.set(
        'R', 1).set('G', 144).set('B', 191))

    fc = ee.FeatureCollection(emergent.merge(
        forested).merge(pond).merge(lake).merge(riverine))

#   base = ee.Image(0).mask(0).toInt8()
    base = ee.Image().byte()
    img = base.paint(fc, 'R') \
        .addBands(base.paint(fc, 'G')
                  .addBands(base.paint(fc, 'B')))

    return img


def nwi_rename(names):

    name_dict = ee.Dictionary({
        'Freshwater Emergent Wetland': 'Emergent',
        'Freshwater Forested/Shrub Wetland': 'Forested',
        'Estuarine and Marine Wetland': 'Estuarine',
        'Freshwater Pond': 'Pond',
        'Lake': 'Lake',
        'Riverine': 'Riverine',
        'Estuarine and Marine Deepwater': 'Deepwater',
        'Other': 'Other'
    })

    new_names = ee.List(names).map(lambda name: name_dict.get(name))
    return new_names


def summarize_by_group(collection, column, group, group_name, stats_type, return_dict=True):
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
    allowed_stats = ['min', 'max', 'mean',
                     'median', 'sum', 'stdDev', 'variance']
    if stats_type not in allowed_stats:
        print('The stats type must be one of the following: {}'.format(
            ','.join(allowed_stats)))
        return

    stats_dict = {
        'min': ee.Reducer.min(),
        'max': ee.Reducer.max(),
        'mean': ee.Reducer.mean(),
        'median': ee.Reducer.median(),
        'sum': ee.Reducer.sum(),
        'stdDev': ee.Reducer.stdDev(),
        'variance': ee.Reducer.variance()
    }

    selectors = [column, group]
    stats = collection.reduceColumns(**{
        'selectors': selectors,
        'reducer': stats_dict[stats_type].group(**{
            'groupField': 1,
            'groupName': group_name
        })
    })
    results = ee.List(ee.Dictionary(stats).get('groups'))
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
    return eval(str(stats)).get('values')


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
    allowed_stats = ['min', 'max', 'mean',
                     'median', 'sum', 'stdDev', 'variance']
    if stats_type not in allowed_stats:
        print('The stats type must be one of the following: {}'.format(
            ','.join(allowed_stats)))
        return

    stats_dict = {
        'min': ee.Reducer.min(),
        'max': ee.Reducer.max(),
        'mean': ee.Reducer.mean(),
        'median': ee.Reducer.median(),
        'sum': ee.Reducer.sum(),
        'stdDev': ee.Reducer.stdDev(),
        'variance': ee.Reducer.variance()
    }

    selectors = [column]
    stats = collection.reduceColumns(**{
        'selectors': selectors,
        'reducer': stats_dict[stats_type]
    })

    return stats


def ee_num_round(num, decimal=2):
    """Rounds a number to a specified number of decimal places.

    Args:
        num (ee.Number): The number to round.
        decimal (int, optional): The number of decimal places to round. Defaults to 2.

    Returns:
        ee.Number: The number with the specified decimal places rounded.
    """
    format_str = '%.{}f'.format(decimal)
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


def dict_to_csv(data_dict, out_csv, by_row=False):
    """Downloads an ee.Dictionary as a CSV file.

    Args:
        data_dict (ee.Dictionary): The input ee.Dictionary.
        out_csv (str): The output file path to the CSV file.
        by_row (bool, optional): Whether to use by row or by column. Defaults to False.
    """
    import geemap

    out_dir = os.path.dirname(out_csv)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not by_row:
        csv_feature = ee.Feature(None, data_dict)
        csv_feat_col = ee.FeatureCollection([csv_feature])
    else:
        keys = data_dict.keys()
        data = keys.map(lambda k: ee.Dictionary({'name': k, 'value': data_dict.get(k)}))
        csv_feature = data.map(lambda f: ee.Feature(None, f))
        csv_feat_col = ee.FeatureCollection(csv_feature)

    geemap.ee_export_vector(csv_feat_col, out_csv)
  
        
