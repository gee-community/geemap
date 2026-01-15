"""Module for creating interactive maps with plotly."""

# *******************************************************************************#
# This module contains extra features of the geemap package.                     #
# The geemap community will maintain the extra features.                         #
# *******************************************************************************#

import json
import os
import shutil

import box
import ipywidgets as widgets
import numpy as np
import pandas as pd

from .basemaps import xyz_to_plotly
from .common import *
from . import coreutils
from . import examples


try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    raise ImportError(
        "This module requires the plotly package. "
        "Please install it using 'pip install plotly'."
    )

basemaps = xyz_to_plotly()


class Canvas:
    """The widgets.HBox containing the map and a toolbar."""

    def __init__(
        self,
        map,
        map_min_width: str = "90%",
        map_max_width: str = "98%",
        map_refresh: bool = False,
        **kwargs,
    ):
        """Initialize the Canvas.

        Args:
            map (go.FigureWidget): The map to display.
            map_min_width: The minimum width of the map. Defaults to '90%'.
            map_max_width: The maximum width of the map. Defaults to '98%'.
            map_refresh: Whether to refresh the map when the map is resized. Defaults to
              False.
        """
        from .toolbar import plotly_toolbar

        map_widget = widgets.Output(layout=widgets.Layout(width=map_max_width))
        with map_widget:
            display(map)

        self.map = map
        self.map_min_width = map_min_width
        self.map_max_width = map_max_width
        self.map_refresh = map_refresh
        self.map_widget = map_widget

        container_widget = widgets.VBox()
        self.container_widget = container_widget

        toolbar_widget = plotly_toolbar(self)
        sidebar_widget = widgets.VBox([toolbar_widget, container_widget])
        canvas = widgets.HBox([map_widget, sidebar_widget])

        self.canvas = canvas
        self.toolbar_widget = toolbar_widget

    def toolbar_reset(self):
        """Reset the toolbar so that no tool is selected."""
        if hasattr(self, "_toolbar"):
            toolbar_grid = self._toolbar
            for tool in toolbar_grid.children:
                tool.value = False


class Map(go.FigureWidget):
    """The Map class inherits the Plotly FigureWidget class.

    More info at https://plotly.com/python/figurewidget.
    """

    def __init__(
        self,
        center: tuple[int, int] = (20, 0),
        zoom: int = 1,
        basemap: str = "open-street-map",
        height: int = 600,
        **kwargs,
    ):
        """Initializes a map.

        More info at https://plotly.com/python/mapbox-layers/.

        Args:
            center: Center of the map. Defaults to (20, 0).
            zoom: Zoom level of the map. Defaults to 1.
            basemap: Can be one of string from "open-street-map", "carto-positron",
                "carto-darkmatter", "stamen-terrain", "stamen-toner" or
                "stamen-watercolor". Defaults to 'open-street-map'.
            height: Height of the map. Defaults to 600.
        """
        # Authenticates Earth Engine and initializes an Earth Engine session.
        if "ee_initialize" not in kwargs.keys():
            kwargs["ee_initialize"] = True

        if kwargs["ee_initialize"]:
            coreutils.ee_initialize()

        kwargs.pop("ee_initialize")

        super().__init__(**kwargs)
        self.add_scattermapbox()
        self.update_layout(
            {
                "mapbox": {
                    "style": basemap,
                    "center": {"lat": center[0], "lon": center[1]},
                    "zoom": zoom,
                },
                "margin": {"r": 0, "t": 0, "l": 0, "b": 0},
                "height": height,
            }
        )

    def show(
        self,
        toolbar: bool = True,
        map_min_width: str = "91%",
        map_max_width: str = "98%",
        refresh: bool = False,
        **kwargs,
    ):
        """Shows the map.

        Args:
            toolbar: Whether to show the toolbar. Defaults to True.
            map_min_width: The minimum width of the map. Defaults to '91%'.
            map_max_width: The maximum width of the map. Defaults to '98%'.
            refresh: Whether to refresh the map when the map is resized. Defaults to
                False.

        Returns:
            Canvas: [description]
        """
        if not toolbar:
            super().show(**kwargs)
        else:
            canvas = Canvas(
                self,
                map_min_width=map_min_width,
                map_max_width=map_max_width,
                map_refresh=refresh,
            )
            return canvas.canvas

    def clear_controls(self) -> None:
        """Removes all controls from the map."""
        config = {
            "scrollZoom": True,
            "displayModeBar": False,
            "editable": True,
            "showLink": False,
            "displaylogo": False,
        }
        self.show(toolbar=False, config=config)

    def add_controls(self, controls) -> None:
        """Adds controls to the map.

        Args:
            controls (list): List of controls to add, e.g., ['drawline', 'drawopenpath',
                'drawclosedpath', 'drawcircle', 'drawrect', 'eraseshape'] See
                https://bit.ly/33Tmqxr
        """
        if isinstance(controls, str):
            controls = [controls]
        elif not isinstance(controls, list):
            raise ValueError(
                "Controls must be a string or a list of strings. See https://bit.ly/33Tmqxr"
            )

        self.update_layout(modebar_add=controls)

    def remove_controls(self, controls) -> None:
        """Removes controls to the map.

        Args:
            controls (list): List of controls to remove, e.g., ["zoomin", "zoomout",
                "toimage", "pan", "resetview"]. See https://bit.ly/3Jk7wkb
        """
        if isinstance(controls, str):
            controls = [controls]
        elif not isinstance(controls, list):
            raise ValueError(
                "Controls must be a string or a list of strings. "
                "See https://bit.ly/3Jk7wkb"
            )

        self.update_layout(modebar_remove=controls)

    def set_center(self, lat: float, lon: float, zoom: int | None = None) -> None:
        """Sets the center of the map.

        Args:
            lat: Latitude.
            lon: Longitude.
            zoom: Zoom level of the map. Defaults to None.
        """
        self.update_layout(
            mapbox=dict(
                center=dict(lat=lat, lon=lon),
                zoom=zoom if zoom is not None else self.layout.mapbox.zoom,
            )
        )

    def add_basemap(self, basemap: str = "ROADMAP") -> None:
        """Adds a basemap to the map.

        Args:
            basemap: Can be one of string from basemaps. Defaults to 'ROADMAP'.
        """
        if basemap not in basemaps:
            raise ValueError(
                f"Basemap {basemap} not found. Choose from {','.join(basemaps.keys())}"
            )

        if basemap in self.get_tile_layers():
            self.remove_basemap(basemap)
        layers = list(self.layout.mapbox.layers) + [basemaps[basemap]]
        self.update_layout(mapbox_layers=layers)

    def remove_basemap(self, name: str) -> None:
        """Removes a basemap from the map.

        Args:
            name: Name of the basemap to remove.
        """
        layers = list(self.layout.mapbox.layers)
        layers = [layer for layer in layers if layer["name"] != name]
        self.layout.mapbox.layers = layers

    def add_mapbox_layer(self, style, access_token=None):
        """Adds a mapbox layer to the map.

        Args:
            layer (str | dict): Layer to add. Can be "basic", "streets", "outdoors",
                "light", "dark", "satellite", or "satellite-streets". See
                https://plotly.com/python/mapbox-layers/ and
                https://docs.mapbox.com/mapbox-gl-js/style-spec/
            access_token (str, optional): The Mapbox Access token. It can be set as an
                environment variable "MAPBOX_TOKEN". Defaults to None.
        """

        if access_token is None:
            access_token = os.environ.get("MAPBOX_TOKEN")

        self.update_layout(
            mapbox_style=style, mapbox_layers=[], mapbox_accesstoken=access_token
        )

    def add_layer(self, layer, name: str | None = None, **kwargs) -> None:
        """Adds a layer to the map.

        Args:
            layer (plotly.graph_objects): Layer to add.
            name: Name of the layer. Defaults to None.
        """
        if isinstance(name, str):
            layer.name = name
        self.add_trace(layer, **kwargs)

    def remove_layer(self, name: str) -> None:
        """Removes a layer from the map.

        Args:
            name: Name of the layer to remove.
        """
        if name in self.get_data_layers():
            self.data = [layer for layer in self.data if layer.name != name]
        elif name in self.get_tile_layers():
            self.layout.mapbox.layers = [
                layer for layer in self.layout.mapbox.layers if layer["name"] != name
            ]

    def clear_layers(self, clear_basemap: bool = False) -> None:
        """Clears all layers from the map.

        Args:
            clear_basemap: If True, clears the basemap. Defaults to False.
        """
        if clear_basemap:
            self.data = []
        else:
            if len(self.data) > 1:
                self.data = self.data[:1]

    def get_layers(self):
        """Returns a dictionary of all layers in the map."""
        layers = {}

        for layer in self.layout.mapbox.layers:
            if layer["name"] is not None:
                layers[layer["name"]] = layer

        for layer in self.data:
            if layer.name is not None and layer.name != "trace 0":
                layers[layer.name] = layer

        return layers

    def get_tile_layers(self):
        """Returns a dictionary of tile layers in the map."""
        layers = {}

        for layer in self.layout.mapbox.layers:
            if layer["name"] is not None:
                layers[layer["name"]] = layer

        return layers

    def get_data_layers(self):
        """Returns a dictionary of data layers in the map."""

        layers = {}

        for layer in self.data:
            if layer.name is not None and layer.name != "trace 0":
                layers[layer.name] = layer

        return layers

    def find_layer_index(self, name: str) -> int | None:
        """Finds the index of a layer.

        Args:
            name: Name of the layer to find.

        Returns:
            Index of the layer.
        """
        for i, layer in enumerate(self.data):
            if layer.name == name:
                return i

        for i, layer in enumerate(self.layout.mapbox.layers):
            if layer["name"] == name:
                return i

        return None

    def set_layer_visibility(self, name: str, show: bool = True) -> None:
        """Sets the visibility of a layer.

        Args:
            name: Name of the layer to set.
            show: If True, shows the layer. Defaults to True.
        """

        if name in self.get_tile_layers():
            index = self.find_layer_index(name)
            self.layout.mapbox.layers[index].visible = show
        elif name in self.get_data_layers():
            index = self.find_layer_index(name)
            self.data[index].visible = show
        else:
            print(f"Layer {name} not found.")

    def set_layer_opacity(self, name: str, opacity: float = 1.0) -> None:
        """Sets the visibility of a layer.

        Args:
            name: Name of the layer to set.
            opacity: Opacity of the layer. Defaults to 1.0.
        """

        if name in self.get_tile_layers():
            index = self.find_layer_index(name)
            self.layout.mapbox.layers[index].opacity = opacity
        elif name in self.get_data_layers():
            index = self.find_layer_index(name)
            layer = self.data[index]
            if hasattr(layer, "opacity"):
                layer.opacity = opacity
            elif hasattr(layer, "marker"):
                layer.marker.opacity = opacity
        else:
            print(f"Layer {name} not found.")

    def add_tile_layer(
        self,
        url: str,
        name: str = "TileLayer",
        attribution: str = "",
        opacity: float = 1.0,
        **kwargs,
    ) -> None:
        """Adds a TileLayer to the map.

        Args:
            url: The URL of the tile layer.
            name: Name of the layer. Defaults to 'TileLayer'.
            attribution: The attribution to use. Defaults to "".
            opacity: The opacity of the layer. Defaults to 1.
        """
        layer = {
            "below": "traces",
            "sourcetype": "raster",
            "sourceattribution": attribution,
            "source": [url],
            "opacity": opacity,
            "name": name,
        }
        layers = list(self.layout.mapbox.layers) + [layer]
        self.update_layout(mapbox_layers=layers)

    def add_ee_layer(
        self,
        ee_object,
        vis_params={},
        name: str | None = None,
        shown: bool = True,
        opacity: float = 1.0,
        **kwargs,
    ):
        """Adds a given EE object to the map as a layer.

        Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to {}.
            name: The name of the layer. Defaults to 'Layer N'.
            shown: A flag indicating whether the layer should be on by default. Defaults to True.
            opacity: The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """
        image = None

        if vis_params is None:
            vis_params = {}

        if name is None:
            layer_count = len(self.layout.mapbox.layers)
            name = "Layer " + str(layer_count + 1)

        if (
            not isinstance(ee_object, ee.Image)
            and not isinstance(ee_object, ee.ImageCollection)
            and not isinstance(ee_object, ee.FeatureCollection)
            and not isinstance(ee_object, ee.Feature)
            and not isinstance(ee_object, ee.Geometry)
        ):
            err_str = (
                "The image argument in 'addLayer' function must be an instance of "
                "one of ee.Image, ee.Geometry, ee.Feature, or ee.FeatureCollection."
            )
            raise AttributeError(err_str)

        if (
            isinstance(ee_object, ee.geometry.Geometry)
            or isinstance(ee_object, ee.feature.Feature)
            or isinstance(ee_object, ee.featurecollection.FeatureCollection)
        ):
            features = ee.FeatureCollection(ee_object)

            width = 2

            if "width" in vis_params:
                width = vis_params["width"]

            color = "000000"

            if "color" in vis_params:
                color = vis_params["color"]

            image_fill = features.style(**{"fillColor": color}).updateMask(
                ee.Image.constant(0.5)
            )
            image_outline = features.style(
                **{"color": color, "fillColor": "00000000", "width": width}
            )

            image = image_fill.blend(image_outline)
        elif isinstance(ee_object, ee.image.Image):
            image = ee_object
        elif isinstance(ee_object, ee.imagecollection.ImageCollection):
            image = ee_object.mosaic()

        if "palette" in vis_params:
            if isinstance(vis_params["palette"], tuple):
                vis_params["palette"] = list(vis_params["palette"])
            if isinstance(vis_params["palette"], box.Box):
                try:
                    vis_params["palette"] = vis_params["palette"]["default"]
                except Exception as e:
                    print("The provided palette is invalid.")
                    raise Exception(e)
            elif isinstance(vis_params["palette"], str):
                vis_params["palette"] = coreutils.check_cmap(vis_params["palette"])
            elif not isinstance(vis_params["palette"], list):
                raise ValueError(
                    "The palette must be a list of colors or a string or a Box object."
                )

        map_id_dict = ee.Image(image).getMapId(vis_params)
        url = map_id_dict["tile_fetcher"].url_format
        self.add_tile_layer(
            url, name=name, attribution="Google Earth Engine", opacity=opacity, **kwargs
        )
        self.set_layer_visibility(name=name, show=shown)

    addLayer = add_ee_layer

    def add_cog_layer(
        self,
        url: str,
        name: str = "Untitled",
        attribution: str = "",
        opacity: float = 1.0,
        bands=None,
        titiler_endpoint: str | None = None,
        **kwargs,
    ):
        """Adds a COG TileLayer to the map.

        Args:
            url: The URL of the COG tile layer, e.g.,
                https://github.com/opengeos/data/releases/download/raster/Libya-2023-07-01.tif
            name: The layer name to use for the layer. Defaults to 'Untitled'.
            attribution: The attribution to use. Defaults to ''.
            opacity: The opacity of the layer. Defaults to 1.
            bands (list, optional): The bands to use. Defaults to None.
            titiler_endpoint: Titiler endpoint. Defaults to
                https://giswqs-titiler-endpoint.hf.space.
            **kwargs: Arbitrary keyword arguments, including bidx, expression, nodata,
              unscale, resampling, rescale, color_formula, colormap, colormap_name,
              return_mask. See https://developmentseed.org/titiler/endpoints/cog/ and
              https://cogeotiff.github.io/rio-tiler/colormap/. To select a certain
              bands, use bidx=[1, 2, 3]
        """
        tile_url = cog_tile(url, bands, titiler_endpoint, **kwargs)
        center = cog_center(url, titiler_endpoint)  # (lon, lat)
        self.add_tile_layer(tile_url, name, attribution, opacity)
        self.set_center(lon=center[0], lat=center[1], zoom=10)

    def add_stac_layer(
        self,
        url: str | None = None,
        collection: str | None = None,
        item: str | None = None,
        assets=None,
        bands=None,
        titiler_endpoint: str | None = None,
        name: str = "STAC Layer",
        attribution: str = "",
        opacity: float = 1.0,
        **kwargs,
    ):
        """Adds a STAC TileLayer to the map.

        Args:
            url: HTTP URL to a STAC item, e.g.,
                https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
            collection: The Microsoft Planetary Computer STAC collection ID, e.g.,
                landsat-8-c2-l2.
            item: The Microsoft Planetary Computer STAC item ID, e.g.,
                LC08_L2SP_047027_20201204_02_T1.
            assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g.,
                ["SR_B7", "SR_B5", "SR_B4"].
            bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
            titiler_endpoint: Titiler endpoint, e.g.,
                "https://giswqs-titiler-endpoint.hf.space", "planetary-computer",
                "pc". Defaults to None.
            name: The layer name to use for the layer. Defaults to 'STAC Layer'.
            attribution: The attribution to use. Defaults to ''.
            opacity: The opacity of the layer. Defaults to 1.
        """
        tile_url = stac_tile(
            url, collection, item, assets, bands, titiler_endpoint, **kwargs
        )
        center = stac_center(url, collection, item, titiler_endpoint)
        self.add_tile_layer(tile_url, name, attribution, opacity)
        self.set_center(lon=center[0], lat=center[1], zoom=10)

    def add_planet_by_month(
        self,
        year: int = 2016,
        month: int = 1,
        api_key: str | None = None,
        token_name: str = "PLANET_API_KEY",
        name: str | None = None,
        attribution: str = "",
        opacity: float = 1.0,
    ) -> None:
        """Adds Planet global mosaic by month to the map.

        To get a Planet API key, see https://developers.planet.com/quickstart/apis/

        Args:
            year: The year of Planet global mosaic, must be >=2016. Defaults to 2016.
            month: The month of Planet global mosaic, must be 1-12. Defaults to 1.
            api_key: The Planet API key. Defaults to None.
            token_name: The environment variable name of the API key. Defaults to
                "PLANET_API_KEY".
            name: Name of the layer. Defaults to 'TileLayer'.
            attribution: The attribution to use. Defaults to "".
            opacity: The opacity of the layer. Defaults to 1.
        """
        if name is None:
            name = str(year) + "-" + str(month).zfill(2)
        tile_url = planet_by_month(year, month, api_key, token_name)
        self.add_tile_layer(
            tile_url, name=name, attribution=attribution, opacity=opacity
        )

    def add_planet_by_quarter(
        self,
        year: int = 2016,
        quarter: int = 1,
        api_key: str | None = None,
        token_name: str = "PLANET_API_KEY",
        name: str | None = None,
        attribution: str = "",
        opacity: float = 1.0,
    ) -> None:
        """Adds Planet global mosaic by month to the map.

        To get a Planet API key, see https://developers.planet.com/quickstart/apis/

        Args:
            year: The year of Planet global mosaic, must be >=2016. Defaults to 2016.
            quarter: The quarter of Planet global mosaic, must be 1-4. Defaults to 1.
            api_key: The Planet API key. Defaults to None.
            token_name: The environment variable name of the API key. Defaults to
                "PLANET_API_KEY".
            name: Name of the layer. Defaults to 'TileLayer'.
            attribution: The attribution to use. Defaults to "".
            opacity: The opacity of the layer. Defaults to 1.
        """
        if name is None:
            name = str(year) + "-" + "q" + str(quarter)
        tile_url = planet_by_quarter(year, quarter, api_key, token_name)
        self.add_tile_layer(
            tile_url, name=name, attribution=attribution, opacity=opacity
        )

    def save(
        self,
        file: str,
        format: str | None = None,
        width: int | None = None,
        height: int | None = None,
        scale: int | None = None,
        **kwargs,
    ) -> None:
        """Convert a map to a static image and write it to a file or writeable object.

        Args:
            file: A string representing a local file path or a writeable object (e.g. a
                pathlib.Path object or an open file descriptor)
            format: The desired image format. One of png, jpg, jpeg, webp, svg, pdf,
                eps. Defaults to None.
            width: The width of the exported image in layout pixels. If the `scale`
                property is 1.0, this will also be the width of the exported image in
                physical pixels. Defaults to None.
            height: The height of the exported image in layout pixels. If the `scale`
                property is 1.0, this will also be the height of the exported image in
                physical pixels. Defaults to None.
            scale: The scale factor to use when exporting the figure. A scale factor
                larger than 1.0 will increase the image resolution with respect to the
                figure's layout pixel dimensions. Whereas as scale factor of less than
                1.0 will decrease the image resolution. Defaults to None.
        """
        self.write_image(
            file, format=format, width=width, height=height, scale=scale, **kwargs
        )

    def add_choropleth_map(
        self,
        data: str,
        name: str | None = None,
        z: str | None = None,
        colorscale: str = "Viridis",
        **kwargs,
    ) -> None:
        """Adds a choropleth map to the map.

        Args:
            data: File path to vector data, e.g.,
                https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/countries.geojson
            name: Name of the layer. Defaults to None.
            z: Z value of the data. Defaults to None.
            colorscale: Color scale of the data. Defaults to "Viridis".
        """
        import geopandas as gpd

        gdf = gpd.read_file(data).to_crs(epsg=4326)
        geojson = json.loads(gdf.to_json())

        self.add_choroplethmapbox(
            geojson=geojson,
            locations=gdf.index,
            z=gdf[z],
            name=name,
            colorscale=colorscale,
            **kwargs,
        )

    def add_scatter_plot_demo(self, **kwargs) -> None:
        """Adds a scatter plot to the map."""
        lons = np.random.random(1000) * 360.0
        lats = np.random.random(1000) * 180.0 - 90.0
        z = np.random.random(1000) * 50.0
        self.add_scattermapbox(
            lon=lons, lat=lats, marker={"color": z}, name="Random points", **kwargs
        )

    def add_heatmap(
        self,
        data,
        latitude: str = "latitude",
        longitude: str = "longitude",
        z: str = "value",
        radius: int = 10,
        colorscale: str | None = None,
        name: str = "Heat map",
        **kwargs,
    ) -> None:
        """Adds a heat map to the map.

        Reference: https://plotly.com/python/mapbox-density-heatmaps

        Args:
            data (str | pd.DataFrame): File path or HTTP URL to the input file or a '.'
                For example,
                https://raw.githubusercontent.com/plotly/datasets/master/earthquakes-23k.csv
            latitude: The column name of latitude. Defaults to "latitude".
            longitude: The column name of longitude. Defaults to "longitude".
            z: The column name of z values. Defaults to "value".
            radius: Radius of each “point” of the heatmap. Defaults to 10.
            colorscale: Color scale of the data, e.g., Viridis. See
                https://plotly.com/python/builtin-colorscales. Defaults to None.
            name: Layer name to use. Defaults to "Heat map".
        """
        if isinstance(data, str):
            df = pd.read_csv(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("data must be a DataFrame or a file path.")

        heatmap = go.Densitymapbox(
            lat=df[latitude],
            lon=df[longitude],
            z=df[z],
            radius=radius,
            colorscale=colorscale,
            name=name,
            **kwargs,
        )
        self.add_trace(heatmap)

    def add_heatmap_demo(self, **kwargs) -> None:
        """Adds a heatmap to the map."""
        quakes = pd.read_csv(
            "https://raw.githubusercontent.com/"
            "plotly/datasets/master/earthquakes-23k.csv"
        )
        heatmap = go.Densitymapbox(
            lat=quakes.Latitude,
            lon=quakes.Longitude,
            z=quakes.Magnitude,
            radius=10,
            name="Earthquake",
            **kwargs,
        )

        self.add_basemap("Esri.WorldTopoMap")
        self.add_trace(heatmap)

    def add_gdf(
        self,
        gdf,
        label_col: str | None = None,
        color_col: str | None = None,
        labels=None,
        opacity: float = 1.0,
        zoom=None,
        color_continuous_scale: str = "Viridis",
        **kwargs,
    ) -> None:
        """Adds a GeoDataFrame to the map.

        Args:
            gdf (GeoDataFrame): A GeoDataFrame.
            label_col: The column name of locations. Defaults to None.
            color_col: The column name of color. Defaults to None.
            labels: TODO
            opacity: TODO
            zoom: TODO
            color_continuous_scale: TODO
        """
        import geopandas as gpd

        if isinstance(gdf, str):
            gdf = gpd.read_file(gdf)

        if not isinstance(gdf, gpd.GeoDataFrame):
            raise ValueError("gdf must be a GeoDataFrame.")

        gdf = gdf.to_crs(epsg=4326)
        # geom_type = gdf_geom_type(gdf)
        center_lon, center_lat = gdf_centroid(gdf)

        if isinstance(label_col, str):
            gdf = gdf.set_index(label_col)
            if label_col == color_col:
                gdf[label_col] = gdf.index
            label_col = gdf.index
        elif label_col is None:
            label_col = gdf.index

        if isinstance(color_col, str):
            if color_col not in gdf.columns:
                raise ValueError(
                    f"color must be a column name in the GeoDataFrame. Can be one of {','.join(gdf.columns)} "
                )
        fig = px.choropleth_mapbox(
            gdf,
            geojson=gdf.geometry,
            locations=label_col,
            color=color_col,
            color_continuous_scale=color_continuous_scale,
            opacity=opacity,
            labels=labels,
            # mapbox_style="carto-positron",
            **kwargs,
        )

        self.add_traces(fig.data)
        self.set_center(center_lat, center_lon, zoom)


def fix_widget_error() -> None:
    """Fix FigureWidget - 'mapbox._derived' Value Error.

    Adopted from: https://github.com/plotly/plotly.py/issues/2570#issuecomment-738735816
    """
    basedatatypesPath = os.path.join(
        os.path.dirname(os.__file__), "site-packages", "plotly", "basedatatypes.py"
    )

    backup_file = basedatatypesPath.replace(".py", "_bk.py")
    shutil.copyfile(basedatatypesPath, backup_file)

    # Read basedatatypes.py.
    with open(basedatatypesPath) as f:
        lines = f.read()

    find = "if not BaseFigure._is_key_path_compatible(key_path_str, self.layout):"

    replace = """if not BaseFigure._is_key_path_compatible(key_path_str, self.layout):
                if key_path_str == "mapbox._derived":
                    return"""

    # Add new text.
    lines = lines.replace(find, replace)

    # Overwrite old 'basedatatypes.py'.
    with open(basedatatypesPath, "w") as f:
        f.write(lines)
