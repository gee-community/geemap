# Changelog

## v0.8.16 - May 10, 2021

**New Features**:

-   Added csv_to_points GUI [#461](https://github.com/giswqs/geemap/issues/461)
-   Added GUI for creating transects [#454](https://github.com/giswqs/geemap/issues/454)
-   Added csv_to_ee and csv_to_makers [#461](https://github.com/giswqs/geemap/issues/461)
-   Added geopandas support [#455](https://github.com/giswqs/geemap/issues/455)

**Improvement**:

-   Improved geojson style [#459](https://github.com/giswqs/geemap/issues/459) [#460](https://github.com/giswqs/geemap/issues/460)
-   Improved vector support [#455](https://github.com/giswqs/geemap/issues/455)
-   Improved add_colorbar function [#450](https://github.com/giswqs/geemap/issues/450)
-   Improved add_raster function [#449](https://github.com/giswqs/geemap/pull/449)
-   Updated notebooks

## v0.8.15 - April 28, 2021

**Improvement**:

-   Improved shp_to_geojson function [#430](https://github.com/giswqs/geemap/discussions/430)
-   Improved add_styled_vector function [#432](https://github.com/giswqs/geemap/discussions/432)
-   Fixed map publish bug [#445](https://github.com/giswqs/geemap/issues/445)
-   Improved add_colorbar function [dc7e548](https://github.com/giswqs/geemap/commit/dc7e54856694a1994b6d4f4044385babe04bd086)

## v0.8.14 - April 20, 2021

**New Features**:

-   Added timelapse GUI [#359](https://github.com/giswqs/geemap/issues/359)
-   Added timeslider GUI [#359](https://github.com/giswqs/geemap/issues/359) [#387](https://github.com/giswqs/geemap/issues/387)

**Improvement**:

-   Improved add_geojson function [731e59e](https://github.com/giswqs/geemap/commit/731e59efc4a1f629db13f6b6cc4e9ef6b06cbe8f)
-   Added GeoPython workshop notebook [6efd5e](https://geemap.org/workshops/GeoPython_2021)
-   Improved cartoee colorbar [#413](https://github.com/giswqs/geemap/discussions/413)
-   Improved cartoee add_layer function [#368](https://github.com/giswqs/geemap/issues/368)

## v0.8.13 - March 22, 2021

**New Features**:

-   Added linked maps [#375](https://github.com/giswqs/geemap/issues/375)
-   Added cartoee legend [#343](https://github.com/giswqs/geemap/issues/343)
-   Added chart by feature property [#339](https://github.com/giswqs/geemap/issues/339)
-   Added tool gui template [#239](https://github.com/giswqs/geemap/issues/239)
-   Added GEE Toolbox GUI [#362](https://github.com/giswqs/geemap/issues/362)
-   Added support for multiple legends [#365](https://github.com/giswqs/geemap/discussions/365)

**Improvement**:

-   Improved dataset module to use GEE STAC [#346](https://github.com/giswqs/geemap/issues/346)
-   Improved training sample tool [#326](https://github.com/giswqs/geemap/issues/326)
-   Added netcdf_to_ee example [#285](https://github.com/giswqs/geemap/issues/285)
-   Improved to_html function [#361](https://github.com/giswqs/geemap/discussions/361)
-   Changed colorbar plotting backend [#372](https://github.com/giswqs/geemap/issues/372)
-   Improved get_colorbar function [#372](https://github.com/giswqs/geemap/issues/372)
-   Added vector styling example
-   Improved zonal statistics

## v0.8.12 - March 8, 2021

**New Features**:

-   Added a dataset module for accessing the Earth Engine Data Catalog via dot notation [#345](https://github.com/giswqs/geemap/issues/345)
-   Added a chart module for creating interactive charts for Earth Engine data [#343](https://github.com/giswqs/geemap/issues/343)
-   Added a time slider for visualizing Earth Engine time-series images [#335 ](https://github.com/giswqs/geemap/issues/335) [#344](https://github.com/giswqs/geemap/issues/344)
-   Added a `netcdf_to_ee` function [#342](https://github.com/giswqs/geemap/pull/342)
-   Added a `numpy_to_ee` function [#337](https://github.com/giswqs/geemap/pull/337)
-   Added vertical colorbar support [#322](https://github.com/giswqs/geemap/issues/322)
-   Added GUI for creating training samples [#326](https://github.com/giswqs/geemap/issues/326)

**Improvement**:

-   Added layer control by default to folium map [#323](https://github.com/giswqs/geemap/issues/323)
-   Added geemap matplotlib example [#319](https://github.com/giswqs/geemap/discussions/319)
-   Added lgtm continuous integration [#330](https://github.com/giswqs/geemap/issues/330)
-   Fixed layer palette bug [#334](https://github.com/giswqs/geemap/issues/334)
-   Fixed minimap zoom parameter [#329](https://github.com/giswqs/geemap/pull/329)
-   Fixed centerObject bug

## v0.8.11 - February 23, 2021

**New Features**:

-   Added a colormap module [#302](https://github.com/giswqs/geemap/issues/302)
-   Added a new cartoee scale bar function [#313](https://github.com/giswqs/geemap/pull/313)
-   Added extract pixel values funciton [#315](https://github.com/giswqs/geemap/issues/315)
-   Visualizing Earth Engine image with >200 matplotlib colormaps via dot notation ([example](https://geemap.org/notebooks/60_colormaps/))

**Improvement**:

-   Improved the basemap module accessible via dot notation [#302](https://github.com/giswqs/geemap/issues/302)
-   Added googledrivedownloader and python-box to requirements [#310](https://github.com/giswqs/geemap/discussions/310)
-   Fixed folium layer name bug [#314](https://github.com/giswqs/geemap/issues/314)

## v0.8.10 - February 16, 2021

**New Features**:

-   Added default basemap options when creating the Map [#293](https://github.com/giswqs/geemap/issues/293)
-   Added GUI for change basemaps [#294](https://github.com/giswqs/geemap/issues/294)
-   Added GUI for js2py conversion [#296](https://github.com/giswqs/geemap/issues/296)
-   Added geemap cheat sheet [#276](https://github.com/giswqs/geemap/issues/276)
-   Added `Map.zoomToObject()` method [#303](https://github.com/giswqs/geemap/issues/303)

**Improvement**:

-   Improved `Map.centerObject()` method [#303](https://github.com/giswqs/geemap/issues/303)

## v0.8.9 - February 4, 2021

**New Features**:

-   Added [whiteboxgui](https://github.com/giswqs/whiteboxgui) with 477 geoprocessing tools [#254](https://github.com/giswqs/geemap/issues/254)

**Improvement**:

-   Fixed file open encoding bug

## v0.8.8 - January 17, 2021

**New Features**:

-   Added support for converting Pandas/GeoPandas DataFrame to ee.FeatureCollection and vice versa [#268](https://github.com/giswqs/geemap/issues/268)
-   Added KML/KMZ support [#247](https://github.com/giswqs/geemap/issues/247)
-   Added Code of Conduct

**Improvement**:

-   Fixed CSV encoding bug [#267](https://github.com/giswqs/geemap/issues/267)
-   Improved downloading shp support [#263](https://github.com/giswqs/geemap/issues/263)
-   Fixed WMS bug [#250](https://github.com/giswqs/geemap/discussions/250)
-   Added cartoee subplots example [#238](https://github.com/giswqs/geemap/discussions/238)
-   Reformatted code using black formatter
-   Improved support for shp and geojson [#244](https://github.com/giswqs/geemap/issues/244)
-   Fixed layer control bug
-   Added cartoee blend tutorial [#241](https://github.com/giswqs/geemap/issues/241)
-   Improved drawing tools [#240](https://github.com/giswqs/geemap/issues/240)
-   Improved Inspector tool

## v0.8.7 - December 27, 2020

**New Features**:

-   Added toolbar GUI [#215](https://github.com/giswqs/geemap/issues/215)
-   Added layer vis [#215](https://github.com/giswqs/geemap/issues/215)
-   Added raster/vector colormap [#215](https://github.com/giswqs/geemap/issues/215)
-   Added support for linking legend with layer [#234](https://github.com/giswqs/geemap/issues/234)
-   Added styled vector function [#235](https://github.com/giswqs/geemap/issues/235)
-   Added mouse click observe to toolbar [#215](https://github.com/giswqs/geemap/issues/215)
-   Added new tool for opening local data [#239 ](https://github.com/giswqs/geemap/issues/239)

**Improvement**:

-   Fixed COG mosaic bug [#236](https://github.com/giswqs/geemap/issues/236) and [#237](https://github.com/giswqs/geemap/issues/237)

## v0.8.6 - December 22, 2020

**New Features**:

-   Added GUI for changing layer visualization interactively [#215](https://github.com/giswqs/geemap/issues/215)
-   Added a toolbar [#215](https://github.com/giswqs/geemap/issues/215)
-   Added color bar support [#223](https://github.com/giswqs/geemap/issues/223)
-   Added draggable legend to folium maps [#224](https://github.com/giswqs/geemap/issues/224)
-   Added `get_image_collection_gif()` function [#225](https://github.com/giswqs/geemap/issues/225)
-   Added `image_dates()` function [#216 ](https://github.com/giswqs/geemap/issues/216)

**Improvement**:

-   Added `max_zoom` parameter to `add_tile_layer()` [#227](https://github.com/giswqs/geemap/issues/227)
-   Added mouse latlon to insepctor tool [#229](https://github.com/giswqs/geemap/discussions/229)
-   Added download icon to notebooks [#202](https://github.com/giswqs/geemap/issues/202)
-   Added GitHub issue template [#202](https://github.com/giswqs/geemap/issues/202)
-   Added more tutorials (cartoee gif, legend, color bar, vis GUI, etc.)
-   Fixed remove control bug [#218](https://github.com/giswqs/geemap/discussions/218)
-   Fixed split-panel map bug
-   Improved Exception handling

## v0.8.5 - December 12, 2020

**New Features**:

-   Add toolbar [#6](https://github.com/giswqs/geemap/issues/6)
-   Add fuctions for downloading imgae thumbnails [#214](https://github.com/giswqs/geemap/issues/214)
-   Add func for getting image collection dates [#216](https://github.com/giswqs/geemap/issues/216)
-   Add cartoee scale bar and north arrow [#191](https://github.com/giswqs/geemap/issues/191)
-   Add support for COG mosaic [#200](https://github.com/giswqs/geemap/issues/200)

**Improvement**:

-   Improve support for locally trained models [#210](https://github.com/giswqs/geemap/issues/210)
-   Add verbose option of downloading functions [#197](https://github.com/giswqs/geemap/pull/197)
-   Improve Inspector tool for point geometry [#198](https://github.com/giswqs/geemap/issues/198)
-   Add tutorials (COG, STAC, local RF, image thumbnails)

## v0.8.4 - December 6, 2020

**New Features:**

-   Add support for Cloud Optimized GeoTIFF (COG) and SpatioTemporal Asset Catalog (STAC) #192
-   Add [Map.add_COG_layer()](https://geemap.org/geemap/#geemap.geemap.Map.add_COG_layer) and [Map.add_STAC_layer()](https://geemap.org/geemap/#geemap.geemap.Map.add_STAC_layer)
-   Add new COG functions, e.g., `get_COG_tile()`, `get_COG_bounds()`, `get_COG_center()`, `get_COG_bands()`
-   Add new STAC functions, e.g., `get_STAC_tile()`, `get_STAC_bounds()`, `get_STAC_center()`, `get_STAC_bands()`

**Improvements:**

-   Improve Google Colab support #193. Use `import geemap` rather than `import geemap.eefolium as geemap`
-   Add `Open in Colab` button to notebooks #194

## v0.8.3 - December 2, 2020

**New Features:**

-   Add button for removing user-drawn features #182
-   Add function for moving drawn layer to top
-   Add remove_last_drawn() function #130
-   Add support for QGIS Layer Style File #174
-   Add mouse click get coordinates example #173
-   Add cartoee colab example #157
-   Add notebooks to mkdocs

**Improvements:**

-   Improve ee_Initialize() #189 #190
-   Fix cartoee map orientation bug #177 #183
-   Fix problematic Date field in shapefile #176
-   Fix Windows unzip bug

## v0.8.2 - November 6, 2020

**Improvements**

-   Reorganize modules
-   Add a new module common.py
-   Add new domain geemap.org
-   Format code using black
-   Add more init options for Map class

## v0.8.1 - October 27, 2020

**New Features:**

-   Add machine learning module #124 #156
-   Add cartoee module #157 #161
-   Add more tutorials (e.g., timelapse, water app, ipywidgets)

**Improvements:**

-   Make ee_Initialize() optional for Map class

BIG THANK YOU to [Kel Markert](https://github.com/kmarkert) for adding the cartoee and ml modules!!

## v0.8.0 - October 10, 2020

**Improvements**

-   Add support for loading Cloud Optimized GeoTIFFs as ee.Image and ee.ImageCollection
-   Make fmask optional when creating Landsat timelapse
-   Add support for creating timelapse of spectral indices (e.g., NDWI, NDVI)
-   Add geemap Colab tutorial
-   Add timelapse download option for voila
-   Add pydeck tutorial for visualizing 3D terrain data
-   Add qualityMosaic() tutorial

**Fixes**

-   Fix Windows zipfile bug

## v0.7.13 - September 15, 2020

**Improvements**

-   Improve ee authentication in Colab #145
-   Improve non-interactive mode #138
-   Add Colab notebook example

**Fixes**

-   Fix automated testing error
-   Fix Windows ee_search() bug

## v0.7.12 - September 1, 2020

**Improvements**

-   Rebuild docs using mkdocs-material
-   Add Internet proxy function
-   Add support for exporting shp and geojson #63

**Fixes**

-   Fix heroko config bug
-   Fix landsat timelapse bug #99 #134
-   Fix js_py conversion bug #136

## v0.7.11 - August 16, 2020

**Improvements:**

-   Add function for removing drawn features #130
-   Add function for extracting pixel values #131
-   Add function for interactive region reduction #35
-   Add machine learning tutorials

**Fixes:**

-   [Fix js_py conversion bug](https://github.com/giswqs/geemap/commit/6c0ebe4006d60f9ebb4390d0914400fc276e2c7d)
-   Fix typos

## v0.7.10 - August 5, 2020

**Improvements:**

-   Add function for getting image properties
-   Add function for calculating descriptive statistics (i.e., min, max, mean, std, sum)
-   Add more utils functions

## v0.7.7 - August 5, 2020

**Improvements:**

-   Add support for publishing maps #109
-   Add `find_layer()` function
-   Add `layer_opacity()` function
-   Update Readthedocs

**Fixes:**

-   Fix duplicate layer bug

## v0.7.0 - May 22, 2020

## v0.6.0 - April 5, 2020

## v0.5.0 - March 23, 2020

## v0.4.0 - March 19, 2020

## v0.3.0 - March 18, 2020

## v0.2.0 - March 17, 2020

## v0.1.0 - March 8, 2020
