# geemap cheat sheet

## Installation

### Install from PyPI

```console
pip install geemap
```

### Install from conda-forge

```console
conda install geemap -c conda-forge
```

### Create a new conda env

```console
conda create -n gee python=3.9
conda activate gee
conda install geemap -c conda-forge
```

## Upgrade

### Upgrade from PyPI

```console
pip install -U geemap
```

### Upgrade from conda-forge

```console
conda update geemap -c conda-forge
```

### Upgrade from GitHub

```console
import geemap
geemap.update_package()
```

## Map

### Create an interactive map

```python
Map = geemap.Map(center=(lat, lon), zoom=4)
Map
```

### Change the default basemap

```python
Map = geemap.Map(basemap='HYBRID')
```

### Add basemaps

```python
Map.add_basemap('OpenTopoMap')
```

### Add XYZ layers

```python
url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'
Map.add_tile_layer(url, name='Google Satellite', attribution='Google')
```

### Add WMS layers

```python
url = 'https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?'
Map.add_wms_layer(url=url, layers='0', name='NAIP Imagery', format='image/png', shown=True)
```

### Add Earth Engine layers

```python
image = ee.Image('USGS/SRTMGL1_003')
vis_params = {
  'min': 0,
  'max': 4000,
  'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']
  }
Map.addLayer(image, vis_params, 'SRTM DEM', True, 0.5)
```

### Set map center

```python
Map.setCenter(lon, lat, zoom)
```

### Center map around an object

```python
Map.centerObject(ee_object, zoom)
```

### Add built-in legends

```python
Map.add_legend(builtin_legend='NLCD')
```

### Add custom legends

```python
Map.add_legend(legend_title, legend_dict, layer_name)
```

## Export data

### Export vector to local

```python
geemap.ee_to_shp(ee_object, filename)
geemap.ee_export_geojson(ee_object, filename)
geemap.ee_export_vector(ee_object, filename)
```

### Export vector to Google Drive

```python
ee_export_vector_to_drive(ee_object, description, folder, file_format='shp', selectors=None)
```

### Export image to local

```python
ee_export_image(ee_object, filename, scale=None, crs=None, region=None, file_per_band=False)
```

### Export image collection to local

```python
ee_export_image_collection(ee_object, out_dir, scale=None, crs=None, region=None, file_per_band=False)
```

### Export image to Google Drive

```python
ee_export_image_to_drive(ee_object, description, folder=None, region=None, scale=None, crs=None, file_format='GeoTIFF')
```

### Export image collection to Google Drive

```python
ee_export_image_collection_to_drive(ee_object, descriptions=None, folder=None, region=None, scale=None, crs=None, file_format='GeoTIFF')
```
