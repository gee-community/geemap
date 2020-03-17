// Array-based quality mosaic.

// Returns a mosaic built by sorting each stack of pixels by the first band
// in descending order, and taking the highest quality pixel.
function qualityMosaic(bands) {
  // Convert to an array, and declare names for the axes and indices along the
  // band axis.
  var array = bands.toArray();
  var imageAxis = 0;
  var bandAxis = 1;
  var qualityIndex = 0;
  var valuesIndex = 1;

  // Slice the quality and values off the main array, and sort the values by the
  // quality in descending order.
  var quality = array.arraySlice(bandAxis, qualityIndex, qualityIndex + 1);
  var values = array.arraySlice(bandAxis, valuesIndex);
  var valuesByQuality = values.arraySort(quality.multiply(-1));

  // Get an image where each pixel is the array of band values where the quality
  // band is greatest. Note that while the array is 2-D, the first axis is
  // length one.
  var best = valuesByQuality.arraySlice(imageAxis, 0, 1);

  // Project the best 2D array down to a single dimension, and convert it back
  // to a regular scalar image by naming each position along the axis. Note we
  // provide the original band names, but slice off the first band since the
  // quality band is not part of the result. Also note to get at the band names,
  // we have to do some kind of reduction, but it won't really calculate pixels
  // if we only access the band names.
  var bandNames = bands.min().bandNames().slice(1);
  return best.arrayProject([bandAxis]).arrayFlatten([bandNames]);
}

// Load the l7_l1t collection for the year 2000, and make sure the first band
// is our quality measure, in this case the normalized difference values.
var l7 = ee.ImageCollection('LANDSAT/LE07/C01/T1')
    .filterDate('2000-01-01', '2001-01-01');
var withNd = l7.map(function(image) {
  return image.normalizedDifference(['B4', 'B3']).addBands(image);
});

// Build a mosaic using the NDVI of bands 4 and 3, essentially showing the
// greenest pixels from the year 2000.
var greenest = qualityMosaic(withNd);

// Select out the color bands to visualize. An interesting artifact of this
// approach is that clouds are greener than water. So all the water is white.
var rgb = greenest.select(['B3', 'B2', 'B1']);

Map.addLayer(rgb, {gain: [1.4, 1.4, 1.1]}, 'Greenest');
Map.setCenter(-90.08789, 16.38339, 11);

