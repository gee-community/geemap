// This example demonstrates the use of the Landsat 4, 5, 7 Collection 2,
// Level 2 QA_PIXEL band (CFMask) to mask unwanted pixels.

function maskL457sr(image) {
    // Bit 0 - Fill
    // Bit 1 - Dilated Cloud
    // Bit 2 - Unused
    // Bit 3 - Cloud
    // Bit 4 - Cloud Shadow
    var qaMask = image.select('QA_PIXEL').bitwiseAnd(parseInt('11111', 2)).eq(0);
    var saturationMask = image.select('QA_RADSAT').eq(0);
  
    // Apply the scaling factors to the appropriate bands.
    var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
    var thermalBand = image.select('ST_B6').multiply(0.00341802).add(149.0);
  
    // Replace the original bands with the scaled ones and apply the masks.
    return image.addBands(opticalBands, null, true)
        .addBands(thermalBand, null, true)
        .updateMask(qaMask)
        .updateMask(saturationMask);
  }
  
  // Map the function over one year of data.
  var collection = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
                       .filterDate('2010-01-01', '2011-01-01')
                       .map(maskL457sr);
  
  var composite = collection.median();
  
  // Display the results.
  Map.setCenter(-4.52, 40.29, 7);  // Iberian Peninsula
  Map.addLayer(composite, {bands: ['SR_B3', 'SR_B2', 'SR_B1'], min: 0, max: 0.3});