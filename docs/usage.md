# Usage

Below is a list of some commonly used functions available in the **geemap** Python package. Please check the [API Reference](https://geemap.org/geemap) for a complete list of all available functions.

To create an ipyleaflet-based interactive map:

```python
import geemap
Map = geemap.Map(center=[40,-100], zoom=4)
Map
```

To create a folium-based interactive map:

```python
import geemap.foliumap as geemap
Map = geemap.Map(center=[40,-100], zoom=4)
Map
```

To add an Earth Engine data layer to the Map:

```python
Map.addLayer(ee_object, vis_params, name, shown, opacity)
```

To center the map view at a given coordinates with the given zoom level:

```python
Map.setCenter(lon, lat, zoom)
```

To center the map view around an Earth Engine object:

```python
Map.centerObject(ee_object, zoom)
```

To add LayerControl to a folium-based Map:

```python
Map.addLayerControl()
```

To add a minimap (overview) to an ipyleaflet-based Map:

```python
Map.add_minimap()
```

To add additional basemaps to the Map:

```python
Map.add_basemap('Esri.OceanBasemap')
Map.add_basemap('Esri.NatGeoWorldMap')
```

To add an XYZ tile layer to the Map:

```python
url = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
Map.add_tile_layer(url, name='Google Map', attribution='Google')
```

To add a WMS layer to the Map:

```python
naip_url = 'https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?'
Map.add_wms_layer(url=naip_url, layers='0', name='NAIP Imagery', format='image/png', shown=True)
```

To convert a shapefile to Earth Engine object and add it to the Map:

```python
ee_object = geemap.shp_to_ee(shp_file_path)
Map.addLayer(ee_object, {}, 'Layer name')
```

To convert a GeoJSON file to Earth Engine object and add it to the Map:

```python
ee_object = geemap.geojson_to_ee(geojson_file_path)
Map.addLayer(ee_object, {}, 'Layer name')
```

To download an ee.FeatureCollection as a shapefile:

```python
geemap.ee_to_csv(ee_object, filename, selectors)
```

To export an ee.FeatureCollection to other formats, including shp, csv, json, kml, and kmz:

```python
geemap.ee_export_vector(ee_object, filename, selectors)
```

To export an ee.Image as a GeoTIFF file:

```python
geemap.ee_export_image(ee_object, filename, scale, crs, region, file_per_band)
```

To export an ee.ImageCollection as GeoTIFF files:

```python
geemap.ee_export_image_collection(ee_object, output, scale, crs, region, file_per_band)
```

To extract pixels from an ee.Image into a 3D numpy array:

```python
geemap.ee_to_numpy(ee_object, bands, region, properties, default_value)
```

To calculate zonal statistics:

```python
geemap.zonal_stats(in_value_raster, in_zone_vector, out_file_path, stat_type='MEAN')
```

To calculate zonal statistics by group:

```python
geemap.zonal_stats_by_group(in_value_raster, in_zone_vector, out_file_path, stat_type='SUM')
```

To create a split-panel Map:

```python
Map.split_map(left_layer='HYBRID', right_layer='ESRI')
```

To add a marker cluster to the Map:

```python
Map.marker_cluster()
feature_collection = ee.FeatureCollection(Map.ee_markers)
```

To add a customized legend to the Map:

```python
legend_dict = {
    'one': (0, 0, 0),
    'two': (255,255,0),
    'three': (127, 0, 127)
}
Map.add_legend(legend_title='Legend', legend_dict=legend_dict, position='bottomright')
Map.add_legend(builtin_legend='NLCD')
```

To download a GIF from an Earth Engine ImageCollection:

```python
geemap.download_ee_video(tempCol, videoArgs, saved_gif)
```

To add animated text to an existing GIF image:

```python
geemap.add_text_to_gif(in_gif, out_gif, xy=('5%', '5%'), text_sequence=1984, font_size=30, font_color='#0000ff', duration=100)
```

To create a colorbar for an Earth Engine image:

```python
palette = ['blue', 'purple', 'cyan', 'green', 'yellow', 'red']
create_colorbar(width=250, height=30, palette=palette, vertical=False,add_labels=True, font_size=20, labels=[-40, 35])
```

To create a Landsat timelapse animation and add it to the Map:

```python
Map.add_landsat_ts_gif(label='Place name', start_year=1985, bands=['NIR', 'Red', 'Green'], frames_per_second=5)
```

To convert all GEE JavaScripts in a folder recursively to Python scripts:

```python
from geemap.conversion import *
js_to_python_dir(in_dir, out_dir)
```

To convert all GEE Python scripts in a folder recursively to Jupyter notebooks:

```python
from geemap.conversion import *
template_file = get_nb_template()
py_to_ipynb_dir(in_dir, template_file, out_dir)
```

To execute all Jupyter notebooks in a folder recursively and save output cells:

```python
from geemap.conversion import *
execute_notebook_dir(in_dir)
```

To search Earth Engine API documentation with Jupyter notebooks:

```python
import geemap
geemap.ee_search()
```

To publish an interactive GEE map with Jupyter notebooks:

```python
Map.publish(name, headline, visibility)
```

To add a local raster dataset to the map:

```python
Map.add_raster(image, bands, colormap, layer_name)
```

To get image basic properties:

```python
geemap.image_props(image).getInfo()
```

To get image descriptive statistics:

```python
geemap.image_stats(image, region, scale)
```

To remove all user-drawn geometries:

```python
geemap.remove_drawn_features()
```

To extract pixel values based on user-drawn geometries:

```python
geemap.extract_values_to_points(out_shp)
```
