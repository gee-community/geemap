// Extract MODIS QA information from the "state_1km" QA band
// and use it to mask out cloudy and deep ocean areas.
//
// QA Band information is available at:
// https://lpdaac.usgs.gov/products/modis_products_table/mod09ga
// Table 1: 1-kilometer State QA Descriptions (16-bit)


/**
 * Returns an image containing just the specified QA bits.
 *
 * Args:
 *   image - The QA Image to get bits from.
 *   start - The first bit position, 0-based.
 *   end   - The last bit position, inclusive.
 *   name  - A name for the output image.
 */
var getQABits = function(image, start, end, newName) {
    // Compute the bits we need to extract.
    var pattern = 0;
    for (var i = start; i <= end; i++) {
       pattern += Math.pow(2, i);
    }
    return image.select([0], [newName])
                  .bitwiseAnd(pattern)
                  .rightShift(start);
};

// Reference a single MODIS MOD09GA image.
var image = ee.Image('MODIS/006/MOD09GA/2012_10_11');

// Select the QA band
var QA = image.select('state_1km');

// Get the cloud_state bits and find cloudy areas.
var cloud = getQABits(QA, 0, 1, 'cloud_state')
                    .expression("b(0) == 1 || b(0) == 2");

// Get the land_water_flag bits.
var landWaterFlag = getQABits(QA, 3, 5, 'land_water_flag');

// Create a mask that filters out deep ocean and cloudy areas.
var mask = landWaterFlag.neq(7).and(cloud.not());

// Add a map layer with the deep ocean and clouds areas masked out.
Map.addLayer(image.updateMask(mask),
  {
    bands: ['sur_refl_b01', 'sur_refl_b04', 'sur_refl_b03'],
    min: -100,
    max: 2000
  }, 'MOD09GA 143'
);

// Add a semi-transparent map layer that displays the clouds.
Map.addLayer(
    cloud.updateMask(cloud),
    {palette: 'FFFFFF', opacity: 0.8},
    'clouds'
);
