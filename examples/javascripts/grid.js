/*

A sample Earth Engine JavaScript library.
The script is adapted from https://code.earthengine.google.com/2bca4e5f36d5a2d642475a98fa421fa9
Credits to Gennadii Donchyts.

*/

var generateRasterGrid= function(origin, dx, dy, proj) {
    var coords = origin.transform(proj).coordinates();
    origin = ee.Image.constant(coords.get(0)).addBands(ee.Image.constant(coords.get(1)));

    var pixelCoords = ee.Image.pixelCoordinates(proj);

    var grid = pixelCoords
       .subtract(origin)
       .divide([dx, dy]).floor()
       .toInt().reduce(ee.Reducer.sum()).bitwiseAnd(1).rename('grid');

    var xy = pixelCoords.reproject(proj.translate(coords.get(0), coords.get(1)).scale(dx, dy));

    var id = xy.multiply(ee.Image.constant([1, 1000000])).reduce(ee.Reducer.sum()).rename('id');

    return grid
      .addBands(id)
      .addBands(xy);
  }


/***
 * Generates a regular grid using given bounds, specified as geometry.
 */
var generateGrid = function(xmin, ymin, xmax, ymax, dx, dy, marginx, marginy, opt_proj) {
    var proj = opt_proj || 'EPSG:4326';

    dx = ee.Number(dx);
    dy = ee.Number(dy);

    var xx = ee.List.sequence(xmin, ee.Number(xmax).subtract(ee.Number(dx).multiply(0.1)), dx);
    var yy = ee.List.sequence(ymin, ee.Number(ymax).subtract(ee.Number(dy).multiply(0.1)), dy);

    var cells = xx.map(function(x) {
      return yy.map(function(y) {
        var x1 = ee.Number(x).subtract(marginx);
        var x2 = ee.Number(x).add(ee.Number(dx)).add(marginx);
        var y1 = ee.Number(y).subtract(marginy);
        var y2 = ee.Number(y).add(ee.Number(dy)).add(marginy);

        var coords = ee.List([x1, y1, x2, y2]);
        var rect = ee.Algorithms.GeometryConstructors.Rectangle(coords, proj, false);

        var nx = x1.add(dx.multiply(0.5)).subtract(xmin).divide(dx).floor();
        var ny = y1.add(dy.multiply(0.5)).subtract(ymin).divide(dy).floor();

        return ee.Feature(rect)
          .set({
            nx: nx.format('%d'),
            ny: ny.format('%d'),
          });
          // .set({cell_id: x1.format('%.3f').cat('_').cat(y1.format('%.3f')) })
      });
    }).flatten();

    return ee.FeatureCollection(cells);
  };


var grid_test = function() {

    var gridRaster = generateRasterGrid(ee.Geometry.Point(0, 0), 10, 10, ee.Projection('EPSG:4326'));
    Map.addLayer(gridRaster.select('id').randomVisualizer(), {}, 'Grid raster', true, 0.5);

    var gridVector = generateGrid(-180, -70, 180, 70, 10, 10, 0, 0);
    style = {'fillColor': '00000000'};
    Map.addLayer(gridVector.style(style), {}, 'Grid vector');

}

exports.generateGrid = generateGrid;
exports.generateRasterGrid = generateRasterGrid;
exports.grid_test = grid_test;
