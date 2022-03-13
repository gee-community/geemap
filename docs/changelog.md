# Changelog

## v0.11.8 - Mar 12, 2022

**New Features**:

-   Added split map for folium and streamlit [#970](https://github.com/giswqs/geemap/pull/970)
-   Updated Landsat timelapse to Collection 2 [#974](https://github.com/giswqs/geemap/pull/974)

**Improvement**:

-   Fixed typos and broken links [#971](https://github.com/giswqs/geemap/issues/971)
-   Updated netCDF notebook
## v0.11.7 - Mar 8, 2022

**New Features**:

-   Added blend function for creating shaded relief maps blended with hillshade

**Improvement**:

-   Added mode reducer to zonal stats [#960](https://github.com/giswqs/geemap/issues/960)
## v0.11.6 - Mar 3, 2022

**New Features**:

-   Added support for visualizing LiDAR data in 3D [#957](https://github.com/giswqs/geemap/pull/957)
-   Added date option for gdf_to_ee [#950](https://github.com/giswqs/geemap/issues/950)

**Improvement**:

-   Improved chart histogram [#953](https://github.com/giswqs/geemap/pull/953)
-   Fixed LGTM false alarm [#939](https://github.com/giswqs/geemap/pull/939)

## v0.11.5 - Feb 22, 2022

**New Features**:

-   Added numpy to COG [#945](https://github.com/giswqs/geemap/pull/945)
-   Added gdf_bounds [#939](https://github.com/giswqs/geemap/pull/939)
-   Added [Landsat 9 notebook](https://geemap.org/notebooks/99_landsat_9)
-   Added ESRI Global Land Cover legend

**Improvement**:

-   Fixed stac tile bug [#944](https://github.com/giswqs/geemap/pull/944)
-   Added None to vis_params as optional [#943](https://github.com/giswqs/geemap/pull/943)
-   Reformatted code using black
## v0.11.4 - Feb 14, 2022

**New Features**:

-   Added timelapse fading effect [#925](https://github.com/giswqs/geemap/pull/925)

## v0.11.3 - Feb 7, 2022

**New Features**:

-   Added support for joining attribute tables `ee_join_table()` [#916](https://github.com/giswqs/geemap/issues/916)
-   Added `gdf_to_df()` and `geojson_to_df()` functions

## v0.11.2 - Feb 4, 2022

**New Features**:

-   Added remove_colorbars function [#881](https://github.com/giswqs/geemap/discussions/881)
-   Added remove_legends function [#881](https://github.com/giswqs/geemap/discussions/881)

**Improvement**:

-   Update get_image_collection_gif() [#905](https://github.com/giswqs/geemap/pull/905)
-   Fixed timelapse ND bug [#904](https://github.com/giswqs/geemap/issues/904)
-   Improved open raster [#902](https://github.com/giswqs/geemap/issues/902)
-   Fixed zonal stats bug [#899](https://github.com/giswqs/geemap/issues/899)
-   Fixed Landsat timelapse bug [#885](https://github.com/giswqs/geemap/issues/885)

## v0.11.1 - January 24, 2022

**New Features**:

-   Added ee_extra to algorithms [#868](https://github.com/giswqs/geemap/pull/868)
-   Added COG creation [bc83fdf](https://github.com/giswqs/geemap/commit/bc83fdf959dd91bdeb40de6af41fea79933c57c2)
-   Added heremap plotting backend [#382](https://github.com/giswqs/geemap/issues/382)
-   Added COG Inspector GUI [#841](https://github.com/giswqs/geemap/issues/841)

**Improvement**:

-   Improved GitHub workflows [#879](https://github.com/giswqs/geemap/pull/879)
-   Fixed ee_stac_list bug [#873](https://github.com/giswqs/geemap/issues/873)
-   Fixed js py conversion [ce7fee0](https://github.com/giswqs/geemap/commit/ce7fee0e87ab2a35069e45d141fb2c84333f392b)
-   Updated notebook 07 [#871](https://github.com/giswqs/geemap/pull/871)
-   Added IR band to goes_timelapse [#870](https://github.com/giswqs/geemap/pull/870)
-   Updated ee_basemaps [#869](https://github.com/giswqs/geemap/pull/869)
-   Removed COG mosaic
-   Fixed cartoee legend bug
-   Updated installation instructions

## v0.11.0 - January 7, 2022

**New Features**:

-   Added support for plotly [#842](https://github.com/giswqs/geemap/issues/842)
-   Added colorbar to timelapse [#846](https://github.com/giswqs/geemap/issues/846)
-   Added save_colorbar function [#846](https://github.com/giswqs/geemap/issues/846)
-   Added ocean color timelapse [#845](https://github.com/giswqs/geemap/issues/845)
-   Added support for xyzservices basemaps [#795](https://github.com/giswqs/geemap/issues/795)
-   Added labeling gdf shp geojson [#815](https://github.com/giswqs/geemap/issues/815)
-   Added remove_labels [#815](https://github.com/giswqs/geemap/issues/815)
-   Added Planetary Computer STAC support
-   Added bbox_to_gdf function

**Improvement**:

-   Fixed cartoee projection bug [#843](https://github.com/giswqs/geemap/discussions/843)
-   Improved COG visualization [#844](https://github.com/giswqs/geemap/issues/844)
-   Updated STAC notebook example [#841](https://github.com/giswqs/geemap/issues/841)
-   Improved stac tile functions [#839](https://github.com/giswqs/geemap/pull/839)
-   Removed pangeo broken binder links

## v0.10.2 - Dec 23, 2021

**New Features**:

-   Add locate control to folium [#809](https://github.com/giswqs/geemap/issues/809)
-   Added add_points_from_xy function [#812](https://github.com/giswqs/geemap/issues/812)
-   Added heatmap function
-   Added add_labels function [#815](https://github.com/giswqs/geemap/issues/815)
-   Added NAIP timelapse [#789](https://github.com/giswqs/geemap/issues/789)

**Improvement**:

-   Improved js_to_py function [#805](https://github.com/giswqs/geemap/discussions/805)
-   Renamed popups to popup [#812](https://github.com/giswqs/geemap/issues/812)
-   Changed default map view [#821](https://github.com/giswqs/geemap/issues/821)
-   Fixed centerObject bug [#823](https://github.com/giswqs/geemap/issues/823)
-   Fixed typo [#824](https://github.com/giswqs/geemap/pull/824)

## v0.10.1 - Dec 6, 2021

**Improvement**:

-   A temporary fix for ipyleaflet basemap error [#795](https://github.com/giswqs/geemap/issues/795)

## v0.10.0 - Nov 28, 2021

**New Features**:

-   Added remove_legend function [#761](https://github.com/giswqs/geemap/issues/761)
-   Added add_marker function [#765](https://github.com/giswqs/geemap/pull/765)
-   Added support for local tile and raster GUI [#758](https://github.com/giswqs/geemap/issues/758), [#769](https://github.com/giswqs/geemap/pull/769)
-   Added a new osm module [#770](https://github.com/giswqs/geemap/issues/770) [#772](https://github.com/giswqs/geemap/pull/772)
-   Added support for PostGIS [#771](https://github.com/giswqs/geemap/issues/771) [#772](https://github.com/giswqs/geemap/pull/772)
-   Added ImageOverlay from local files [#773](https://github.com/giswqs/geemap/issues/773)

## v0.9.5 - Nov 22, 2021

**New Features**:

-   Added timelapse module
-   Added quarter and monthly timelapse [#746](https://github.com/giswqs/geemap/issues/746)
-   Improved create timeseries [#736](https://github.com/giswqs/geemap/issues/736)
-   Added Sentinel-2 timelapse [#733](https://github.com/giswqs/geemap/issues/733) [#736](https://github.com/giswqs/geemap/issues/736)
-   Added MODIS NDVI timelapse [#728](https://github.com/giswqs/geemap/issues/728)
-   Added GOES timelapse [#717](https://github.com/giswqs/geemap/issues/717)
-   Added time slider opacity param [#720](https://github.com/giswqs/geemap/discussions/720)
-   Added contour function [#688](https://github.com/giswqs/geemap/issues/688)
-   Added more gif functions
-   Added make_gif and gif_to_mp4 functions
-   Improved date sequence
-   Added Alibaba font type
-   Added ESA Land Cover legend
-   Added zoom to bounds function
-   Added streamlit download button

**Improvement**:

-   Fixed encoding bug [#747](https://github.com/giswqs/geemap/issues/747)

## v0.9.4 - Oct 23, 2021

**New Features**:

-   Made streamlit map width responsive [#713](https://github.com/giswqs/geemap/issues/713)
-   Added function read file from url

**Improvement**:

-   Fixed map width bug [#712](https://github.com/giswqs/geemap/issues/712)
-   Fixed algorithms module bug
-   Updated environment.yml

## v0.9.3 - Oct 23, 2021

**New Features**:

-   Added streamlit support [#697](https://github.com/giswqs/geemap/issues/697)
-   Added point layer function [#702](https://github.com/giswqs/geemap/issues/702)
-   Added river width module [#682](https://github.com/giswqs/geemap/issues/682)
-   Added census data and xyzservices
-   Added nlcd notebook
-   Added river width module notebook
-   Added GEE workshop notebook

**Improvement**:

-   Fixed geojson style callback bug [#692](https://github.com/giswqs/geemap/issues/692)
-   Fixed open vector bug [#124](https://github.com/giswqs/geemap/issues/124)
-   Removed py36 due to xyzservices

## v0.9.2 - Oct 1, 2021

**New Features**:

-   Added RivWidthCloud module [#682](https://github.com/giswqs/geemap/issues/682)
-   Added RivWidthCloud notebook [#682](https://github.com/giswqs/geemap/issues/682)
-   Added [NLCD notebook](https://geemap.org/notebooks/nlcd_app/)
-   Added a close button to timeseries inspector

**Improvement**:

-   Fixed hover countries notebook [#686](https://github.com/giswqs/geemap/pull/686)
-   Improved cartoee colorbar with custom label size [#681](https://github.com/giswqs/geemap/discussions/681)

## v0.9.1 - Sep 17, 2021

**New Features**:

-   Added `sandbox_path` option allowing users to restrict Voila app access to system directories [#673](https://github.com/giswqs/geemap/issues/673)

## v0.9.0 - Sep 10, 2021

**New Features**:

-   Get current device latlon [#618](https://github.com/giswqs/geemap/issues/618)

**Improvement**:

-   Improved Colab support [#661](https://github.com/giswqs/geemap/issues/661)
-   Improved folium colorbar [#586](https://github.com/giswqs/geemap/issues/586)
-   Fixed broken link [#653](https://github.com/giswqs/geemap/issues/653)
-   Fixed extract pixel values bug [#610](https://github.com/giswqs/geemap/issues/610)
-   Fixed color palette bug [#605](https://github.com/giswqs/geemap/pull/605)
-   Fixed typos [#589](https://github.com/giswqs/geemap/pull/589)

## v0.8.18 - Jul 8, 2021

**New Features**:

-   Added pandas_to_geojson [#557](https://github.com/giswqs/geemap/discussions/557)
-   Added feature_histogram function to chart module [#553](https://github.com/giswqs/geemap/pull/553)
-   Added feature_groups function to chart module [#539](https://github.com/giswqs/geemap/pull/539)
-   Added random forest probability output [#550](https://github.com/giswqs/geemap/pull/550)

**Improvement**:

-   Renamed eefolium module to foliumap
-   Changed COG and STAC to lowercase
-   Changed .format() to fstring [#561](https://github.com/giswqs/geemap/pull/561)
-   Fixed random forest string to label bug [#545](https://github.com/giswqs/geemap/pull/545)
-   Improved split-panel map [#543](https://github.com/giswqs/geemap/discussions/543)
-   Updated otsu example [#535](https://github.com/giswqs/geemap/discussions/535)

## v0.8.17 - Jun 20, 2021

**New Features**:

-   Added Planet global mosaic [#527](https://github.com/giswqs/geemap/issues/527)
-   Add LCMS dataset option for sankee [#517](https://github.com/giswqs/geemap/issues/517)
-   Added add_osm function [#503](https://github.com/giswqs/geemap/discussions/503)

**Improvement**:

-   Added otsu example [#535](https://github.com/giswqs/geemap/discussions/535)
-   Fixed timeseries plotting bug [#513](https://github.com/giswqs/geemap/discussions/513)
-   Fixed shp deletion bug [#509](https://github.com/giswqs/geemap/discussions/509)
-   Fixed csv_to_points bug [#490](https://github.com/giswqs/geemap/discussions/490)
-   Improved ee_to_geojson [#486](https://github.com/giswqs/geemap/pull/486)
-   Improved random sampling notebook [#479](https://github.com/giswqs/geemap/discussions/479)
-   Fixed link bug [#480](https://github.com/giswqs/geemap/issues/480)
-   Improved sankee notebook [#471](https://github.com/giswqs/geemap/issues/471)
-   Updated installation docs
-   Added binder env

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

## v0.8.15 - Apr 28, 2021

**Improvement**:

-   Improved shp_to_geojson function [#430](https://github.com/giswqs/geemap/discussions/430)
-   Improved add_styled_vector function [#432](https://github.com/giswqs/geemap/discussions/432)
-   Fixed map publish bug [#445](https://github.com/giswqs/geemap/issues/445)
-   Improved add_colorbar function [dc7e548](https://github.com/giswqs/geemap/commit/dc7e54856694a1994b6d4f4044385babe04bd086)

## v0.8.14 - Apr 20, 2021

**New Features**:

-   Added timelapse GUI [#359](https://github.com/giswqs/geemap/issues/359)
-   Added timeslider GUI [#359](https://github.com/giswqs/geemap/issues/359) [#387](https://github.com/giswqs/geemap/issues/387)

**Improvement**:

-   Improved add_geojson function [731e59e](https://github.com/giswqs/geemap/commit/731e59efc4a1f629db13f6b6cc4e9ef6b06cbe8f)
-   Added GeoPython workshop notebook [6efd5e](https://geemap.org/workshops/GeoPython_2021)
-   Improved cartoee colorbar [#413](https://github.com/giswqs/geemap/discussions/413)
-   Improved cartoee add_layer function [#368](https://github.com/giswqs/geemap/issues/368)

## v0.8.13 - Mar 22, 2021

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

## v0.8.12 - Mar 8, 2021

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

## v0.8.11 - Feb 23, 2021

**New Features**:

-   Added a colormap module [#302](https://github.com/giswqs/geemap/issues/302)
-   Added a new cartoee scale bar function [#313](https://github.com/giswqs/geemap/pull/313)
-   Added extract pixel values function [#315](https://github.com/giswqs/geemap/issues/315)
-   Visualizing Earth Engine image with >200 matplotlib colormaps via dot notation ([example](https://geemap.org/notebooks/60_colormaps/))

**Improvement**:

-   Improved the basemap module accessible via dot notation [#302](https://github.com/giswqs/geemap/issues/302)
-   Added googledrivedownloader and python-box to requirements [#310](https://github.com/giswqs/geemap/discussions/310)
-   Fixed folium layer name bug [#314](https://github.com/giswqs/geemap/issues/314)

## v0.8.10 - Feb 16, 2021

**New Features**:

-   Added default basemap options when creating the Map [#293](https://github.com/giswqs/geemap/issues/293)
-   Added GUI for change basemaps [#294](https://github.com/giswqs/geemap/issues/294)
-   Added GUI for js2py conversion [#296](https://github.com/giswqs/geemap/issues/296)
-   Added geemap cheat sheet [#276](https://github.com/giswqs/geemap/issues/276)
-   Added `Map.zoomToObject()` method [#303](https://github.com/giswqs/geemap/issues/303)

**Improvement**:

-   Improved `Map.centerObject()` method [#303](https://github.com/giswqs/geemap/issues/303)

## v0.8.9 - Feb 4, 2021

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

## v0.8.7 - Dec 27, 2020

**New Features**:

-   Added toolbar GUI [#215](https://github.com/giswqs/geemap/issues/215)
-   Added layer vis [#215](https://github.com/giswqs/geemap/issues/215)
-   Added raster/vector colormap [#215](https://github.com/giswqs/geemap/issues/215)
-   Added support for linking legend with layer [#234](https://github.com/giswqs/geemap/issues/234)
-   Added styled vector function [#235](https://github.com/giswqs/geemap/issues/235)
-   Added mouse click observe to toolbar [#215](https://github.com/giswqs/geemap/issues/215)
-   Added new tool for opening local data [#239](https://github.com/giswqs/geemap/issues/239)

**Improvement**:

-   Fixed COG mosaic bug [#236](https://github.com/giswqs/geemap/issues/236) and [#237](https://github.com/giswqs/geemap/issues/237)

## v0.8.6 - Dec 22, 2020

**New Features**:

-   Added GUI for changing layer visualization interactively [#215](https://github.com/giswqs/geemap/issues/215)
-   Added a toolbar [#215](https://github.com/giswqs/geemap/issues/215)
-   Added color bar support [#223](https://github.com/giswqs/geemap/issues/223)
-   Added draggable legend to folium maps [#224](https://github.com/giswqs/geemap/issues/224)
-   Added `get_image_collection_gif()` function [#225](https://github.com/giswqs/geemap/issues/225)
-   Added `image_dates()` function [#216](https://github.com/giswqs/geemap/issues/216)

**Improvement**:

-   Added `max_zoom` parameter to `add_tile_layer()` [#227](https://github.com/giswqs/geemap/issues/227)
-   Added mouse latlon to insepctor tool [#229](https://github.com/giswqs/geemap/discussions/229)
-   Added download icon to notebooks [#202](https://github.com/giswqs/geemap/issues/202)
-   Added GitHub issue template [#202](https://github.com/giswqs/geemap/issues/202)
-   Added more tutorials (cartoee gif, legend, color bar, vis GUI, etc.)
-   Fixed remove control bug [#218](https://github.com/giswqs/geemap/discussions/218)
-   Fixed split-panel map bug
-   Improved Exception handling

## v0.8.5 - Dec 12, 2020

**New Features**:

-   Add toolbar [#6](https://github.com/giswqs/geemap/issues/6)
-   Add functions for downloading imgae thumbnails [#214](https://github.com/giswqs/geemap/issues/214)
-   Add func for getting image collection dates [#216](https://github.com/giswqs/geemap/issues/216)
-   Add cartoee scale bar and north arrow [#191](https://github.com/giswqs/geemap/issues/191)
-   Add support for COG mosaic [#200](https://github.com/giswqs/geemap/issues/200)

**Improvement**:

-   Improve support for locally trained models [#210](https://github.com/giswqs/geemap/issues/210)
-   Add verbose option of downloading functions [#197](https://github.com/giswqs/geemap/pull/197)
-   Improve Inspector tool for point geometry [#198](https://github.com/giswqs/geemap/issues/198)
-   Add tutorials (COG, STAC, local RF, image thumbnails)

## v0.8.4 - Dec 6, 2020

**New Features:**

-   Add support for Cloud Optimized GeoTIFF (COG) and SpatioTemporal Asset Catalog (STAC) #192
-   Add [Map.add_cog_layer()](https://geemap.org/geemap/#geemap.geemap.Map.add_cog_layer) and [Map.add_stac_layer()](https://geemap.org/geemap/#geemap.geemap.Map.add_stac_layer)
-   Add new COG functions, e.g., `cog_tile()`, `cog_bounds()`, `cog_center()`, `cog_bands()`
-   Add new STAC functions, e.g., `stac_tile()`, `stac_bounds()`, `stac_center()`, `stac_bands()`

**Improvements:**

-   Improve Google Colab support #193. Use `import geemap` rather than `import geemap.foliumap as geemap`
-   Add `Open in Colab` button to notebooks #194

## v0.8.3 - Dec 2, 2020

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

## v0.8.2 - Nov 6, 2020

**Improvements**

-   Reorganize modules
-   Add a new module common.py
-   Add new domain geemap.org
-   Format code using black
-   Add more init options for Map class

## v0.8.1 - Oct 27, 2020

**New Features:**

-   Add machine learning module #124 #156
-   Add cartoee module #157 #161
-   Add more tutorials (e.g., timelapse, water app, ipywidgets)

**Improvements:**

-   Make ee_Initialize() optional for Map class

BIG THANK YOU to [Kel Markert](https://github.com/kmarkert) for adding the cartoee and ml modules!!

## v0.8.0 - Oct 10, 2020

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

## v0.7.13 - Sep 15, 2020

**Improvements**

-   Improve ee authentication in Colab #145
-   Improve non-interactive mode #138
-   Add Colab notebook example

**Fixes**

-   Fix automated testing error
-   Fix Windows ee_search() bug

## v0.7.12 - Sep 1, 2020

**Improvements**

-   Rebuild docs using mkdocs-material
-   Add Internet proxy function
-   Add support for exporting shp and geojson #63

**Fixes**

-   Fix heroko config bug
-   Fix landsat timelapse bug #99 #134
-   Fix js_py conversion bug #136

## v0.7.11 - Aug 16, 2020

**Improvements:**

-   Add function for removing drawn features #130
-   Add function for extracting pixel values #131
-   Add function for interactive region reduction #35
-   Add machine learning tutorials

**Fixes:**

-   [Fix js_py conversion bug](https://github.com/giswqs/geemap/commit/6c0ebe4006d60f9ebb4390d0914400fc276e2c7d)
-   Fix typos

## v0.7.10 - Aug 5, 2020

**Improvements:**

-   Add function for getting image properties
-   Add function for calculating descriptive statistics (i.e., min, max, mean, std, sum)
-   Add more utils functions

## v0.7.7 - Aug 5, 2020

**Improvements:**

-   Add support for publishing maps #109
-   Add `find_layer()` function
-   Add `layer_opacity()` function
-   Update Readthedocs

**Fixes:**

-   Fix duplicate layer bug

## v0.7.0 - May 22, 2020

## v0.6.0 - Apr 5, 2020

## v0.5.0 - Mar 23, 2020

## v0.4.0 - Mar 19, 2020

## v0.3.0 - Mar 18, 2020

## v0.2.0 - Mar 17, 2020

## v0.1.0 - Mar 8, 2020
