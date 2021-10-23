# /*
# MIT License
#
# Copyright (c) [2018] [Xiao Yang]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Original Author:  Xiao Yang, UNC Chapel Hill, United States
# Contact: yangxiao@live.unc.edu
# Contributing Authors:
# Tamlin Pavelsky, UNC Chapel Hill, United States
# George Allen, Texas A&M, United States
# Genna Dontchyts, Deltares, NL
#
# NOTE: THIS IS A PRERELEASE VERSION (Edited on: 2019/02/18)
# */

# /* functions to extract river mask */
# GitHub: https://github.com/seanyx/RivWidthCloudPaper


import ee
import math
import numpy as np

from geemap.common import ee_initialize


def hitOrMiss(image, se1, se2):
    """perform hitOrMiss transform (adapted from [citation])"""
    e1 = image.reduceNeighborhood(ee.Reducer.min(), se1)
    e2 = image.Not().reduceNeighborhood(ee.Reducer.min(), se2)
    return e1.And(e2)


def splitKernel(kernel, value):
    """recalculate the kernel according to the given foreground value"""
    kernel = np.array(kernel)
    result = kernel
    r = 0
    while r < kernel.shape[0]:
        c = 0
        while c < kernel.shape[1]:
            if kernel[r][c] == value:
                result[r][c] = 1
            else:
                result[r][c] = 0
            c = c + 1
        r = r + 1
    return result.tolist()


def Skeletonize(image, iterations, method):
    """perform skeletonization"""

    se1w = [[2, 2, 2], [0, 1, 0], [1, 1, 1]]

    if method == 2:
        se1w = [[2, 2, 2], [0, 1, 0], [0, 1, 0]]

    se11 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 1))
    se12 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 2))

    se2w = [[2, 2, 0], [2, 1, 1], [0, 1, 0]]

    if method == 2:
        se2w = [[2, 2, 0], [2, 1, 1], [0, 1, 1]]

    se21 = ee.Kernel.fixed(3, 3, splitKernel(se2w, 1))
    se22 = ee.Kernel.fixed(3, 3, splitKernel(se2w, 2))

    result = image

    i = 0
    while i < iterations:
        j = 0
        while j < 4:
            result = result.subtract(hitOrMiss(result, se11, se12))
            se11 = se11.rotate(1)
            se12 = se12.rotate(1)
            result = result.subtract(hitOrMiss(result, se21, se22))
            se21 = se21.rotate(1)
            se22 = se22.rotate(1)
            j = j + 1
        i = i + 1

    return result.rename(["clRaw"])


def CalcDistanceMap(img, neighborhoodSize, scale):
    # // assign each river pixel with the distance (in meter) between itself and the closest non-river pixel
    imgD2 = img.focal_max(1.5, "circle", "pixels", 2)
    imgD1 = img.focal_max(1.5, "circle", "pixels", 1)
    outline = imgD2.subtract(imgD1)

    dpixel = outline.fastDistanceTransform(neighborhoodSize).sqrt()
    dmeters = dpixel.multiply(scale)  # // for a given scale
    DM = dmeters.mask(dpixel.lte(neighborhoodSize).And(imgD2))

    return DM


def CalcGradientMap(image, gradMethod, scale):
    ## Calculate the gradient
    if gradMethod == 1:  # GEE .gradient() method
        grad = image.gradient()
        dx = grad.select(["x"])
        dy = grad.select(["y"])
        g = dx.multiply(dx).add(dy.multiply(dy)).sqrt()

    if gradMethod == 2:  # Gena's method
        k_dx = ee.Kernel.fixed(
            3,
            3,
            [
                [1.0 / 8, 0.0, -1.0 / 8],
                [2.0 / 8, 0.0, -2.0 / 8],
                [1.0 / 8, 0.0, -1.0 / 8],
            ],
        )
        k_dy = ee.Kernel.fixed(
            3,
            3,
            [
                [-1.0 / 8, -2.0 / 8, -1.0 / 8],
                [0.0, 0.0, 0.0],
                [1.0 / 8, 2.0 / 8, 1.0 / 8],
            ],
        )
        dx = image.convolve(k_dx)
        dy = image.convolve(k_dy)
        g = dx.multiply(dx).add(dy.multiply(dy)).divide(scale.multiply(scale)).sqrt()

    if gradMethod == 3:  # RivWidth method
        k_dx = ee.Kernel.fixed(3, 1, [[-0.5, 0.0, 0.5]])
        k_dy = ee.Kernel.fixed(1, 3, [[0.5], [0.0], [-0.5]])
        dx = image.convolve(k_dx)
        dy = image.convolve(k_dy)
        g = dx.multiply(dx).add(dy.multiply(dy)).divide(scale.multiply(scale))

    return g


def CalcOnePixelWidthCenterline(img, GM, hGrad):
    # /***
    # calculate the 1px centerline from:
    # 1. fast distance transform of the river banks
    # 2. gradient of the distance transform, mask areas where gradient greater than a threshold hGrad
    # 3. apply skeletonization twice to get a 1px centerline
    # thresholding gradient map inspired by Pavelsky and Smith., 2008
    # ***/

    imgD2 = img.focal_max(1.5, "circle", "pixels", 2)
    cl = ee.Image(GM).mask(imgD2).lte(hGrad).And(img)
    # // apply skeletonization twice
    cl1px = Skeletonize(cl, 2, 1)
    return cl1px


def ExtractEndpoints(CL1px):
    """calculate end points in the one pixel centerline"""

    se1w = [[0, 0, 0], [2, 1, 2], [2, 2, 2]]

    se11 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 1))
    se12 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 2))

    result = CL1px

    # // the for loop removes the identified endpoints from the input image
    i = 0
    while i < 4:  # rotate kernels
        result = result.subtract(hitOrMiss(CL1px, se11, se12))
        se11 = se11.rotate(1)
        se12 = se12.rotate(1)
        i = i + 1
    endpoints = CL1px.subtract(result)
    return endpoints


def ExtractCorners(CL1px):
    """calculate corners in the one pixel centerline"""

    se1w = [[2, 2, 0], [2, 1, 1], [0, 1, 0]]

    se11 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 1))
    se12 = ee.Kernel.fixed(3, 3, splitKernel(se1w, 2))

    result = CL1px
    # // the for loop removes the identified corners from the input image

    i = 0
    while i < 4:  # rotate kernels

        result = result.subtract(hitOrMiss(result, se11, se12))

        se11 = se11.rotate(1)
        se12 = se12.rotate(1)

        i = i + 1

    cornerPoints = CL1px.subtract(result)
    return cornerPoints


def CleanCenterline(cl1px, maxBranchLengthToRemove, rmCorners):
    """clean the 1px centerline:
    1. remove branches
    2. remove corners to insure 1px width (optional)
    """

    ## find the number of connecting pixels (8-connectivity)
    nearbyPoints = cl1px.mask(cl1px).reduceNeighborhood(
        reducer=ee.Reducer.count(), kernel=ee.Kernel.circle(1.5), skipMasked=True
    )

    ## define ends
    endsByNeighbors = nearbyPoints.lte(2)

    ## define joint points
    joints = nearbyPoints.gte(4)

    costMap = (
        cl1px.mask(cl1px)
        .updateMask(joints.Not())
        .cumulativeCost(
            source=endsByNeighbors.mask(endsByNeighbors),
            maxDistance=maxBranchLengthToRemove,
            geodeticDistance=True,
        )
    )

    branchMask = costMap.gte(0).unmask(0)
    cl1Cleaned = cl1px.updateMask(branchMask.Not())  # mask short branches;
    ends = ExtractEndpoints(cl1Cleaned)
    cl1Cleaned = cl1Cleaned.updateMask(ends.Not())

    if rmCorners:
        corners = ExtractCorners(cl1Cleaned)
        cl1Cleaned = cl1Cleaned.updateMask(corners.Not())

    return cl1Cleaned


def CalculateAngle(clCleaned):
    """calculate the orthogonal direction of each pixel of the centerline"""

    w3 = ee.Kernel.fixed(
        9,
        9,
        [
            [135.0, 126.9, 116.6, 104.0, 90.0, 76.0, 63.4, 53.1, 45.0],
            [143.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 36.9],
            [153.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 26.6],
            [166.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 14.0],
            [180.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1e-5],
            [194.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 346.0],
            [206.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 333.4],
            [216.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 323.1],
            [225.0, 233.1, 243.4, 256.0, 270.0, 284.0, 296.6, 306.9, 315.0],
        ],
    )

    combinedReducer = ee.Reducer.sum().combine(ee.Reducer.count(), None, True)

    clAngle = (
        clCleaned.mask(clCleaned)
        .rename(["clCleaned"])
        .reduceNeighborhood(
            reducer=combinedReducer, kernel=w3, inputWeight="kernel", skipMasked=True
        )
    )

    ## mask calculating when there are more than two inputs into the angle calculation
    clAngleNorm = (
        clAngle.select("clCleaned_sum")
        .divide(clAngle.select("clCleaned_count"))
        .mask(clAngle.select("clCleaned_count").gt(2).Not())
    )

    ## if only one input into the angle calculation, rotate it by 90 degrees to get the orthogonal
    clAngleNorm = clAngleNorm.where(
        clAngle.select("clCleaned_count").eq(1), clAngleNorm.add(ee.Image(90))
    )

    return clAngleNorm.rename(["orthDegree"])


def GetWidth(clAngleNorm, segmentInfo, endInfo, DM, crs, bound, scale, sceneID, note):
    """calculate the width of the river at each centerline pixel, measured according to the orthgonal direction of the river"""

    def GetXsectionEnds(f):
        xc = ee.Number(f.get("x"))
        yc = ee.Number(f.get("y"))
        orthRad = ee.Number(f.get("angle")).divide(180).multiply(math.pi)

        width = ee.Number(f.get("toBankDistance")).multiply(1.5)
        cosRad = width.multiply(orthRad.cos())
        sinRad = width.multiply(orthRad.sin())
        p1 = ee.Geometry.Point([xc.add(cosRad), yc.add(sinRad)], crs)
        p2 = ee.Geometry.Point([xc.subtract(cosRad), yc.subtract(sinRad)], crs)

        xlEnds = ee.Feature(
            ee.Geometry.MultiPoint([p1, p2]).buffer(30),
            {
                "xc": xc,
                "yc": yc,
                "longitude": f.get("lon"),
                "latitude": f.get("lat"),
                "orthogonalDirection": orthRad,
                "MLength": width.multiply(2),
                "p1": p1,
                "p2": p2,
                "crs": crs,
                "image_id": sceneID,
                "note": note,
            },
        )

        return xlEnds

    def SwitchGeometry(f):
        return (
            f.setGeometry(
                ee.Geometry.LineString(
                    coords=[f.get("p1"), f.get("p2")], proj=crs, geodesic=False
                )
            )
            .set("p1", None)
            .set("p2", None)
        )  # remove p1 and p2

    ## convert centerline image to a list. prepare for map function
    clPoints = (
        clAngleNorm.rename(["angle"])
        .addBands(ee.Image.pixelCoordinates(crs))
        .addBands(ee.Image.pixelLonLat().rename(["lon", "lat"]))
        .addBands(DM.rename(["toBankDistance"]))
        .sample(region=bound, scale=scale, projection=None, factor=1, dropNulls=True)
    )

    ## calculate the cross-section lines, returning a featureCollection
    xsectionsEnds = clPoints.map(GetXsectionEnds)

    ## calculate the flags at the xsection line end points
    endStat = endInfo.reduceRegions(
        collection=xsectionsEnds,
        reducer=ee.Reducer.anyNonZero().combine(
            ee.Reducer.count(), None, True
        ),  # test endpoints type
        scale=scale,
        crs=crs,
    )

    ## calculate the width of the river and other flags along the xsection lines
    xsections1 = endStat.map(SwitchGeometry)
    combinedReducer = ee.Reducer.mean()
    xsections = segmentInfo.reduceRegions(
        collection=xsections1, reducer=combinedReducer, scale=scale, crs=crs
    )

    return xsections


def CalculateCenterline(imgIn):

    crs = imgIn.get("crs")
    scale = ee.Number(imgIn.get("scale"))
    riverMask = imgIn.select(["riverMask"])

    distM = CalcDistanceMap(riverMask, 256, scale)
    gradM = CalcGradientMap(distM, 2, scale)
    cl1 = CalcOnePixelWidthCenterline(riverMask, gradM, 0.9)
    cl1Cleaned1 = CleanCenterline(cl1, 300, True)
    cl1px = CleanCenterline(cl1Cleaned1, 300, False)

    imgOut = (
        imgIn.addBands(cl1px.rename(["cleanedCL"]))
        .addBands(cl1.rename(["rawCL"]))
        .addBands(gradM.rename(["gradientMap"]))
        .addBands(distM.rename(["distanceMap"]))
    )

    return imgOut


def CalculateOrthAngle(imgIn):
    cl1px = imgIn.select(["cleanedCL"])
    angle = CalculateAngle(cl1px)
    imgOut = imgIn.addBands(angle)
    return imgOut


def prepExport(f):
    f = f.set(
        {
            "width": ee.Number(f.get("MLength")).multiply(f.get("channelMask")),
            "endsInWater": ee.Number(f.get("any")).eq(1),
            "endsOverEdge": ee.Number(f.get("count")).lt(2),
        }
    )

    fOut = ee.Feature(
        ee.Geometry.Point([f.get("longitude"), f.get("latitude")]), {}
    ).copyProperties(f, None, ["any", "count", "MLength", "xc", "yc", "channelMask"])
    return fOut


def CalculateWidth(imgIn):
    crs = imgIn.get("crs")
    scale = imgIn.get("scale")
    imgId = imgIn.get("image_id")
    bound = imgIn.select(["riverMask"]).geometry()
    angle = imgIn.select(["orthDegree"])
    dem = ee.Image("users/eeProject/MERIT")
    infoEnds = imgIn.select(["riverMask"])
    infoExport = (
        imgIn.select("channelMask")
        .addBands(imgIn.select("^flag.*"))
        .addBands(dem.rename(["flag_elevation"]))
    )
    dm = imgIn.select(["distanceMap"])

    widths = GetWidth(
        angle, infoExport, infoEnds, dm, crs, bound, scale, imgId, ""
    ).map(prepExport)

    return widths


def merge_collections_std_bandnames_collection1tier1_sr():
    """merge landsat 5, 7, 8 collection 1 tier 1 SR imageCollections and standardize band names"""
    ## standardize band names
    bn8 = ["B1", "B2", "B3", "B4", "B6", "pixel_qa", "B5", "B7"]
    bn7 = ["B1", "B1", "B2", "B3", "B5", "pixel_qa", "B4", "B7"]
    bn5 = ["B1", "B1", "B2", "B3", "B5", "pixel_qa", "B4", "B7"]
    bns = ["uBlue", "Blue", "Green", "Red", "Swir1", "BQA", "Nir", "Swir2"]

    # create a merged collection from landsat 5, 7, and 8
    ls5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR").select(bn5, bns)

    ls7 = (
        ee.ImageCollection("LANDSAT/LE07/C01/T1_SR")
        .filterDate("1999-04-15", "2003-05-30")
        .select(bn7, bns)
    )

    ls8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR").select(bn8, bns)

    merged = ls5.merge(ls7).merge(ls8)

    return merged


def id2Img(id):
    return ee.Image(
        merge_collections_std_bandnames_collection1tier1_sr()
        .filterMetadata("LANDSAT_ID", "equals", id)
        .first()
    )


def Unpack(bitBand, startingBit, bitWidth):
    # unpacking bit bands
    # see: https://groups.google.com/forum/#!starred/google-earth-engine-developers/iSV4LwzIW7A
    return (
        ee.Image(bitBand)
        .rightShift(startingBit)
        .bitwiseAnd(ee.Number(2).pow(ee.Number(bitWidth)).subtract(ee.Number(1)).int())
    )


def UnpackAllSR(bitBand):
    # apply Unpack function for multiple pixel qualities
    bitInfoSR = {
        "Cloud": [5, 1],
        "CloudShadow": [3, 1],
        "SnowIce": [4, 1],
        "Water": [2, 1],
    }
    unpackedImage = ee.Image.cat(
        [
            Unpack(bitBand, bitInfoSR[key][0], bitInfoSR[key][1]).rename([key])
            for key in bitInfoSR
        ]
    )
    return unpackedImage


def AddFmaskSR(image):
    # // add fmask as a separate band to the input image
    temp = UnpackAllSR(image.select(["BQA"]))

    fmask = (
        temp.select(["Water"])
        .rename(["fmask"])
        .where(temp.select(["SnowIce"]), ee.Image(3))
        .where(temp.select(["CloudShadow"]), ee.Image(2))
        .where(temp.select(["Cloud"]), ee.Image(4))
        .mask(temp.select(["Cloud"]).gte(0))
    )

    return image.addBands(fmask)


def CalcHillShadowSR(image):
    dem = ee.Image("users/eeProject/MERIT").clip(image.geometry().buffer(9000).bounds())
    SOLAR_AZIMUTH_ANGLE = ee.Number(image.get("SOLAR_AZIMUTH_ANGLE"))
    SOLAR_ZENITH_ANGLE = ee.Number(image.get("SOLAR_ZENITH_ANGLE"))

    return (
        ee.Terrain.hillShadow(dem, SOLAR_AZIMUTH_ANGLE, SOLAR_ZENITH_ANGLE, 100, True)
        .reproject("EPSG:4326", None, 90)
        .rename(["hillshadow"])
    )


# /* functions to classify water (default) */
def ClassifyWater(imgIn, method="Jones2019"):

    if method == "Jones2019":

        return ClassifyWaterJones2019(imgIn)
    elif method == "Zou2018":

        return ClassifyWaterZou2018(imgIn)


# /* water function */
def CalculateWaterAddFlagsSR(imgIn, waterMethod="Jones2019"):
    # waterMethod = typeof waterMethod !== 'undefined' ? waterMethod : 'Jones2019';

    fmask = AddFmaskSR(imgIn).select(["fmask"])

    fmaskUnpacked = (
        fmask.eq(4)
        .rename("flag_cloud")
        .addBands(fmask.eq(2).rename("flag_cldShadow"))
        .addBands(fmask.eq(3).rename("flag_snowIce"))
        .addBands(fmask.eq(1).rename("flag_water"))
    )

    water = ClassifyWater(imgIn, waterMethod).where(fmask.gte(2), ee.Image.constant(0))
    hillshadow = CalcHillShadowSR(imgIn).Not().rename(["flag_hillshadow"])

    imgOut = ee.Image(
        water.addBands(fmask)
        .addBands(hillshadow)
        .addBands(fmaskUnpacked)
        .setMulti(
            {
                "image_id": imgIn.get("LANDSAT_ID"),
                "timestamp": imgIn.get("system:time_start"),
                "scale": imgIn.projection().nominalScale(),
                "crs": imgIn.projection().crs(),
            }
        )
    )

    return imgOut


def GetCenterline(clDataset, bound):
    # // filter the GRWL centerline based on area of interest
    cl = clDataset.filterBounds(bound)
    return cl


def ExtractChannel(image, centerline, maxDistance):
    # // extract the channel water bodies from the water mask, based on connectivity to the reference centerline.
    connectedToCl = (
        image.Not()
        .cumulativeCost(
            source=ee.Image()
            .toByte()
            .paint(centerline, 1)
            .And(image),  # // only use the centerline that overlaps with the water mask
            maxDistance=maxDistance,
            geodeticDistance=False,
        )
        .eq(0)
    )

    channel = (
        image.updateMask(connectedToCl)
        .unmask(0)
        .updateMask(image.gte(0))
        .rename(["channelMask"])
    )
    return channel


def RemoveIsland(channel, FILL_SIZE):
    # /* fill in island as water if the size (number of pixels) of the island is smaller than FILL_SIZE */
    fill = channel.Not().selfMask().connectedPixelCount(FILL_SIZE).lt(FILL_SIZE)
    river = channel.where(fill, ee.Image(1)).rename(["riverMask"])
    return river


def ExtractRiver(imgIn, clData, maxDist, minIslandRemoval):
    waterMask = imgIn.select(["waterMask"])
    bound = waterMask.geometry()
    cl = GetCenterline(clData, bound)
    channelMask = ExtractChannel(waterMask, cl, maxDist)
    riverMask = RemoveIsland(channelMask, minIslandRemoval)
    return imgIn.addBands(channelMask).addBands(riverMask)


def Mndwi(image):
    return image.normalizedDifference(["Green", "Swir1"]).rename("mndwi")


def Mbsrv(image):
    return image.select(["Green"]).add(image.select(["Red"])).rename("mbsrv")


def Mbsrn(image):
    return image.select(["Nir"]).add(image.select(["Swir1"])).rename("mbsrn")


def Ndvi(image):
    return image.normalizedDifference(["Nir", "Red"]).rename("ndvi")


def Awesh(image):
    return image.expression(
        "Blue + 2.5 * Green + (-1.5) * mbsrn + (-0.25) * Swir2",
        {
            "Blue": image.select(["Blue"]),
            "Green": image.select(["Green"]),
            "mbsrn": Mbsrn(image).select(["mbsrn"]),
            "Swir2": image.select(["Swir2"]),
        },
    )


def Evi(image):
    # calculate the enhanced vegetation index
    evi = image.expression(
        "2.5 * (Nir - Red) / (1 + Nir + 6 * Red - 7.5 * Blue)",
        {
            "Nir": image.select(["Nir"]),
            "Red": image.select(["Red"]),
            "Blue": image.select(["Blue"]),
        },
    )
    return evi.rename(["evi"])


def Dswe(i):
    mndwi = Mndwi(i)
    mbsrv = Mbsrv(i)
    mbsrn = Mbsrn(i)
    awesh = Awesh(i)
    swir1 = i.select(["Swir1"])
    nir = i.select(["Nir"])
    ndvi = Ndvi(i)
    blue = i.select(["Blue"])
    swir2 = i.select(["Swir2"])

    t1 = mndwi.gt(0.124)
    t2 = mbsrv.gt(mbsrn)
    t3 = awesh.gt(0)
    t4 = mndwi.gt(-0.44).And(swir1.lt(900)).And(nir.lt(1500)).And(ndvi.lt(0.7))
    t5 = (
        mndwi.gt(-0.5)
        .And(blue.lt(1000))
        .And(swir1.lt(3000))
        .And(swir2.lt(1000))
        .And(nir.lt(2500))
    )

    t = (
        t1.add(t2.multiply(10))
        .add(t3.multiply(100))
        .add(t4.multiply(1000))
        .add(t5.multiply(10000))
    )

    noWater = t.eq(0).Or(t.eq(1)).Or(t.eq(10)).Or(t.eq(100)).Or(t.eq(1000))
    hWater = (
        t.eq(1111)
        .Or(t.eq(10111))
        .Or(t.eq(11011))
        .Or(t.eq(11101))
        .Or(t.eq(11110))
        .Or(t.eq(11111))
    )
    mWater = (
        t.eq(111)
        .Or(t.eq(1011))
        .Or(t.eq(1101))
        .Or(t.eq(1110))
        .Or(t.eq(10011))
        .Or(t.eq(10101))
        .Or(t.eq(10110))
        .Or(t.eq(11001))
        .Or(t.eq(11010))
        .Or(t.eq(11100))
    )
    pWetland = t.eq(11000)
    lWater = (
        t.eq(11)
        .Or(t.eq(101))
        .Or(t.eq(110))
        .Or(t.eq(1001))
        .Or(t.eq(1010))
        .Or(t.eq(1100))
        .Or(t.eq(10000))
        .Or(t.eq(10001))
        .Or(t.eq(10010))
        .Or(t.eq(10100))
    )

    iDswe = (
        noWater.multiply(0)
        .add(hWater.multiply(1))
        .add(mWater.multiply(2))
        .add(pWetland.multiply(3))
        .add(lWater.multiply(4))
    )

    return iDswe.rename(["dswe"])


def ClassifyWaterJones2019(img):
    dswe = Dswe(img)
    waterMask = dswe.eq(1).Or(dswe.eq(2)).rename(["waterMask"])
    return waterMask


def ClassifyWaterZou2018(image):
    mndwi = Mndwi(image)
    ndvi = Ndvi(image)
    evi = Evi(image)

    water = (mndwi.gt(ndvi).Or(mndwi.gt(evi))).And(evi.lt(0.1))
    return water.rename(["waterMask"])


def rwGenSR(
    aoi=None,
    WATER_METHOD="Jones2019",
    MAXDISTANCE=4000,
    FILL_SIZE=333,
    MAXDISTANCE_BRANCH_REMOVAL=500,
):

    grwl = ee.FeatureCollection("users/eeProject/grwl")

    # // generate function based on user choice
    def tempFUN(image, aoi=aoi):
        aoi = ee.Algorithms.If(aoi, aoi, image.geometry())
        image = image.clip(aoi)

        # // derive water mask and masks for flags
        imgOut = CalculateWaterAddFlagsSR(image, WATER_METHOD)
        # // calculate river mask
        imgOut = ExtractRiver(imgOut, grwl, MAXDISTANCE, FILL_SIZE)
        # // calculate centerline
        imgOut = CalculateCenterline(imgOut)
        # // calculate orthogonal direction of the centerline
        imgOut = CalculateOrthAngle(imgOut)
        # // export widths
        width_fc = CalculateWidth(imgOut)

        return width_fc

    return tempFUN


def maximum_no_of_tasks(MaxNActive, waitingPeriod):
    """maintain a maximum number of active tasks"""
    import time
    import ee

    ee.Initialize()

    time.sleep(10)
    ## initialize submitting jobs
    ts = list(ee.batch.Task.list())

    NActive = 0
    for task in ts:
        if "RUNNING" in str(task) or "READY" in str(task):
            NActive += 1
    ## wait if the number of current active tasks reach the maximum number
    ## defined in MaxNActive
    while NActive >= MaxNActive:
        time.sleep(
            waitingPeriod
        )  # if reach or over maximum no. of active tasks, wait for 2min and check again
        ts = list(ee.batch.Task.list())
        NActive = 0
        for task in ts:
            if "RUNNING" in str(task) or "READY" in str(task):
                NActive += 1
    return ()


def str_to_ee(id):
    """Convert an image id to ee.Image.

    Args:
        id (str | ee.Image): A string representing an ee.Image, such as LC08_022034_20180303, LANDSAT/LC08/C01/T1_SR/LC08_022034_20180303, LC08_L1TP_022034_20180303_20180319_01_T1

    Raises:
        Exception: The image id is not recognized. It must be retrieved using either LANDSAT_ID, system:index, or system:id
        Exception: The image id is not recognized. It must be either ee.Image or a string retrieved using either LANDSAT_ID, system:index, or system:id

    Returns:
        ee.Image: An ee.Image.
    """
    if isinstance(id, str):
        if len(id) == 43 and "/" in id:
            id = ee.Image(id).get("LANDSAT_ID").getInfo()
            return ee.Image(
                merge_collections_std_bandnames_collection1tier1_sr()
                .filterMetadata("LANDSAT_ID", "equals", id)
                .first()
            )

        elif len(id) == 40:
            return ee.Image(
                merge_collections_std_bandnames_collection1tier1_sr()
                .filterMetadata("LANDSAT_ID", "equals", id)
                .first()
            )
        else:
            raise Exception(
                "The image id is not recognized. It must be retrieved using either LANDSAT_ID, system:index"
            )

    elif isinstance(id, ee.Image):
        id = id.get("LANDSAT_ID").getInfo()
        return ee.Image(
            merge_collections_std_bandnames_collection1tier1_sr()
            .filterMetadata("LANDSAT_ID", "equals", id)
            .first()
        )
    else:
        raise Exception(
            "The image id is not recognized. It must be either ee.Image or a string retrieved using either LANDSAT_ID, system:index, or system:id"
        )


def rwc(
    image,
    description=None,
    folder="",
    file_format="shp",
    aoi=None,
    water_method="Jones2019",
    max_dist=4000,
    fill_size=333,
    max_dist_branch_removal=500,
    return_fc=False,
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
        fill_size (int, optional): islands or bars smaller than this value (unit: pixels) will be removed before calculating centerline. Defaults to 333.
        max_dist_branch_removal (int, optional): length of pruning. Spurious branch of the initial centerline will be removed by this length (unit: pixels). Defaults to 500.
        return_fc(bool, optional): whether to return the result as an ee.FeatureColleciton. Defaults to False.
    """

    img = str_to_ee(image)
    if description is None:
        if isinstance(image, str):
            description = image
        else:
            description = img.get("LANDSAT_ID").getInfo()

    gen = rwGenSR(
        aoi=aoi,
        WATER_METHOD=water_method,
        MAXDISTANCE=max_dist,
        FILL_SIZE=fill_size,
        MAXDISTANCE_BRANCH_REMOVAL=max_dist_branch_removal,
    )

    width_fc = gen(img)

    if return_fc:
        return width_fc
    else:
        taskWidth = ee.batch.Export.table.toDrive(
            collection=width_fc,
            description=description,
            folder=folder,
            fileFormat=file_format,
        )
        taskWidth.start()
        print(description, "will be exported to", folder, "as", file_format, "file")


def rwc_batch(
    images,
    folder="",
    file_format="shp",
    aoi=None,
    water_method="Jones2019",
    max_dist=4000,
    fill_size=333,
    max_dist_branch_remove=500,
):
    """Calculate river centerlines and widths for multiple Landsat SR images.

    Args:
        images (str | list | ee.ImageCollection): An input csv file containing a list of Landsat IDs (e.g., LC08_L1TP_022034_20130422_20170310_01_T1)
        folder (str, optional): Folder name within Google Drive to save the exported file. Defaults to "", which is the root directory.
        file_format (str, optional): The supported file format include shp, csv, json, kml, kmz, and TFRecord. Defaults to 'shp'. Defaults to "shp".
        aoi (ee.Geometry.Polygon, optional): A polygon (or rectangle) geometry define the area of interest. Only widths and centerline from this area will be calculated. Defaults to None.
        water_method (str, optional): Water classification method ('Jones2019' or 'Zou2018'). Defaults to "Jones2019".
        max_dist (int, optional): Maximum distance (unit: meters) to check water pixel's connectivity to GRWL centerline. Defaults to 4000.
        fill_size (int, optional): islands or bars smaller than this value (unit: pixels) will be removed before calculating centerline. Defaults to 333.
        max_dist_branch_removal (int, optional): length of pruning. Spurious branch of the initial centerline will be removed by this length (unit: pixels). Defaults to 500.

    """
    import pandas as pd

    if isinstance(images, str):

        imageInfo = pd.read_csv(
            images, dtype={"Point_ID": np.unicode_, "LANDSAT_ID": np.unicode_}
        )
        sceneIDList = imageInfo["LANDSAT_ID"].values.tolist()
    elif isinstance(images, ee.ImageCollection):
        sceneIDList = images.aggregate_array("LANDSAT_ID").getInfo()
    elif isinstance(images, list):
        sceneIDList = images
    else:
        raise Exception("images must be a list of Landsat IDs or an ee.ImageCollection")

    for scene in sceneIDList:
        rwc(
            scene,
            scene,
            folder,
            file_format,
            aoi,
            water_method,
            max_dist,
            fill_size,
            max_dist_branch_remove,
        )
