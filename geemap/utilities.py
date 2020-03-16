import ee

# Compute area in square meters

def vecArea(f):
    # Compute area in square meters.  Convert to hectares.
    areaSqm = f.area()
    # A new property called 'area' will be set on each feature.
    return f.set({'area': areaSqm})


def vecAreaSqkm(f):
    areaSqkm = f.area().divide(1000 * 1000)
    return f.set({'area': areaSqkm})


def vecAreaHa(f):
    # Compute area in square meters.  Convert to hectares.
    areaHa = f.area(1).divide(100 * 100)

    # A new property called 'area' will be set on each feature.
    return f.set({'area': areaHa})


def getYear(date):
    return ee.Date(date).get('year')


# Convert string to number
def stringToNumber(str):
    return ee.Number.parse(str)


# Calculate array sum
def arraySum(arr):
    return ee.Array(arr).accum(0).get([-1])


# Calculate array mean
def arrayMean(arr):
    sum = ee.Array(arr).accum(0).get([-1])
    size = arr.length()
    return ee.Number(sum.divide(size))


# Create NAIP mosaic for a specified year
def annualNAIP(year, geometry):
    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = ee.Date.fromYMD(year, 12, 31)
    collection = ee.ImageCollection('USDA/NAIP/DOQQ') \
        .filterDate(start_date, end_date) \
        .filterBounds(geometry)

    time_start = ee.Date(
        ee.List(collection.aggregate_array('system:time_start')).sort().get(0))
    time_end = ee.Date(
        ee.List(collection.aggregate_array('system:time_end')).sort().get(-1))
    image = ee.Image(collection.mosaic().clip(geometry))
    NDWI = ee.Image(image).normalizedDifference(
        ['G', 'N']).select(['nd'], ['ndwi'])
    NDVI = ee.Image(image).normalizedDifference(
        ['N', 'R']).select(['nd'], ['ndvi'])
    image = image.addBands(NDWI)
    image = image.addBands(NDVI)
    return image.set({'system:time_start': time_start, 'system:time_end': time_end})


# Find all available NAIP images for a geometry
def findNAIP(geometry, add_NDVI=True, add_NDWI=True):
    init_collection = ee.ImageCollection('USDA/NAIP/DOQQ') \
        .filterBounds(geometry) \
        .filterDate('2009-01-01', '2018-12-31') \
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
            ee.List(collection.aggregate_array('system:time_start')).sort().get(0))
        time_end = ee.Date(
            ee.List(collection.aggregate_array('system:time_end')).sort().get(-1))
        col_size = collection.size()
        image = ee.Image(collection.mosaic().clip(geometry))

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


# Get NWI by HUC
def filterNWI(HUC08_Id, geometry):
    nwi_asset_prefix = 'users/wqs/NWI-HU8/HU8_'
    nwi_asset_suffix = '_Wetlands'
    nwi_asset_path = nwi_asset_prefix + HUC08_Id + nwi_asset_suffix
    nwi_huc = ee.FeatureCollection(nwi_asset_path).filterBounds(geometry) \
        .filter(ee.Filter.notEquals(**{'leftField': 'WETLAND_TY', 'rightValue': 'Riverine'}))
    return nwi_huc


# Find HUC08 intersecting a geometry
def filterHUC08(geometry):
    USGS_HUC08 = ee.FeatureCollection('USGS/WBD/2017/HUC08')   # Subbasins
    HUC08 = USGS_HUC08.filterBounds(geometry)
    return HUC08


# Find HUC10 intersecting a geometry
def filterHUC10(geometry):
    USGS_HUC10 = ee.FeatureCollection('USGS/WBD/2017/HUC10')   # Watersheds
    HUC10 = USGS_HUC10.filterBounds(geometry)
    return HUC10

    # Find HUC08 by HUC ID


def findHUC08(HUC08_Id):
    USGS_HUC08 = ee.FeatureCollection('USGS/WBD/2017/HUC08')   # Subbasins
    HUC08 = USGS_HUC08.filter(ee.Filter.eq('huc8', HUC08_Id))
    return HUC08


# Find HUC10 by HUC ID
def findHUC10(HUC10_Id):
    USGS_HUC10 = ee.FeatureCollection('USGS/WBD/2017/HUC10')   # Watersheds
    HUC10 = USGS_HUC10.filter(ee.Filter.eq('huc10', HUC10_Id))
    return HUC10


# find NWI by HUC08
def findNWI(HUC08_Id):
    nwi_asset_prefix = 'users/wqs/NWI-HU8/HU8_'
    nwi_asset_suffix = '_Wetlands'
    nwi_asset_path = nwi_asset_prefix + HUC08_Id + nwi_asset_suffix
    nwi_huc = ee.FeatureCollection(nwi_asset_path) \
        .filter(ee.Filter.notEquals(**{'leftField': 'WETLAND_TY', 'rightValue': 'Riverine'}))
    return nwi_huc


# Extract NWI by providing a geometry
def extractNWI(geometry):

    HUC08 = filterHUC08(geometry)
    HUC_list = ee.List(HUC08.aggregate_array('huc8')).getInfo()
    # print('Intersecting HUC08 IDs:', HUC_list)
    nwi = ee.FeatureCollection(HUC_list.map(findNWI)).flatten()
    return nwi.filterBounds(geometry)

# NWI legend: https://www.fws.gov/wetlands/Data/Mapper-Wetlands-Legend.html


def nwi_add_color(fc):
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


# calculate total image area (unit: m2)
def imageArea(img, geometry, scale):
    pixelArea = img.Add(ee.Image(1)).multiply(
        ee.Image.pixelArea())
    imgArea = pixelArea.reduceRegion(**{
        'geometry': geometry,
        'reducer': ee.Reducer.sum(),
        'scale': scale,
        'maxPixels': 1e9
    })
    return imgArea


# calculate total image area (unit: ha)
def imageAreaHa(img, geometry, scale):
    pixelArea = img.Add(ee.Image(1)).multiply(
        ee.Image.pixelArea()).divide(10000)
    imgArea = pixelArea.reduceRegion(**{
        'geometry': geometry,
        'reducer': ee.Reducer.sum(),
        'scale': scale,
        'maxPixels': 1e9
    })
    return imgArea


# get highest value
def maxValue(img, scale=30):
    max_value = img.reduceRegion(**{
        'reducer': ee.Reducer.max(),
        'geometry': img.geometry(),
        'scale': scale,
        'maxPixels': 1e9
    })
    return max_value


# get lowest value
def minValue(img, scale=30):
    min_value = img.reduceRegion(**{
        'reducer': ee.Reducer.min(),
        'geometry': img.geometry(),
        'scale': scale,
        'maxPixels': 1e9
    })
    return min_value


# get mean value
def meanValue(img, scale=30):
    mean_value = img.reduceRegion(**{
        'reducer': ee.Reducer.mean(),
        'geometry': img.geometry(),
        'scale': scale,
        'maxPixels': 1e9
    })
    return mean_value


# get standard deviation
def stdValue(img, scale=30):
    std_value = img.reduceRegion(**{
        'reducer': ee.Reducer.stdDev(),
        'geometry': img.geometry(),
        'scale': scale,
        'maxPixels': 1e9
    })
    return std_value
