"""The maplibregl module provides the Map class for creating interactive maps using the maplibre.ipywidget module.
"""

import os
import requests
import xyzservices
import geopandas as gpd
import ipyvuetify as v
from box import Box
from maplibre.basemaps import background
from maplibre.basemaps import construct_carto_basemap_url
from maplibre.ipywidget import MapWidget
from maplibre import Layer, LayerType, MapOptions
from maplibre.sources import GeoJSONSource, RasterTileSource
from maplibre.utils import get_bounds
from maplibre.controls import (
    ScaleControl,
    FullscreenControl,
    GeolocateControl,
    NavigationControl,
    AttributionControl,
    Marker,
)

from .basemaps import (
    xyz_to_leaflet,
    get_xyz_dict,
    get_google_maps_api_key,
    get_google_map_tile_providers,
)
from .common import *
from typing import Tuple, Dict, Any, Optional

basemaps = Box(xyz_to_leaflet(), frozen_box=True)


class Map(MapWidget):
    """The Map class inherits from the MapWidget class of the maplibre.ipywidget module."""

    _BASEMAP_ALIASES: Dict[str, List[str]] = {
        "DEFAULT": ["Google.Roadmap", "OpenStreetMap.Mapnik"],
        "ROADMAP": ["Google.Roadmap", "Esri.WorldStreetMap"],
        "SATELLITE": ["Google.Satellite", "Esri.WorldImagery"],
        "TERRAIN": ["Google.Terrain", "Esri.WorldTopoMap"],
        "HYBRID": ["Google.Hybrid", "Esri.WorldImagery"],
    }

    def __init__(
        self,
        center: Tuple[float, float] = (0, 20),
        zoom: float = 1,
        pitch: float = 0,
        bearing: float = 0,
        style: str = "dark-matter",
        height: str = "600px",
        controls: Dict[str, str] = {
            "navigation": "top-right",
            "fullscreen": "top-right",
            "scale": "bottom-left",
        },
        **kwargs: Any,
    ) -> None:
        """
        Create a Map object.

        Args:
            center (tuple, optional): The center of the map (lon, lat). Defaults
                to (0, 20).
            zoom (float, optional): The zoom level of the map. Defaults to 1.
            pitch (float, optional): The pitch of the map. Measured in degrees
                away from the plane of the screen (0-85) Defaults to 0.
            bearing (float, optional): The bearing of the map. Measured in degrees
                counter-clockwise from north. Defaults to 0.
            style (str, optional): The style of the map. It can be a string or a URL.
                If it is a string, it must be one of the following: "dark-matter",
                "positron", "voyager", "positron-nolabels", "dark-matter-nolabels",
                "voyager-nolabels", or "demotiles". If a MapTiler API key is set,
                you can also use any of the MapTiler styles, such as aquarelle,
                backdrop, basic, bright, dataviz, landscape, ocean, openstreetmap, outdoor,
                satellite, streets, toner, topo, winter, etc. If it is a URL, it must point to
                a MapLibre style JSON. Defaults to "dark-matter".
            height (str, optional): The height of the map. Defaults to "600px".
            controls (dict, optional): The controls and their positions on the
                map. Defaults to {"fullscreen": "top-right", "scale": "bottom-left"}.
            **kwargs: Additional keyword arguments that are passed to the MapOptions class.
                See https://maplibre.org/maplibre-gl-js/docs/API/type-aliases/MapOptions/
                for more information.

        Returns:
            None
        """
        carto_basemaps = [
            "dark-matter",
            "positron",
            "voyager",
            "positron-nolabels",
            "dark-matter-nolabels",
            "voyager-nolabels",
        ]
        if isinstance(style, str):

            if style.startswith("https"):
                response = requests.get(style)
                if response.status_code != 200:
                    print(
                        "The provided style URL is invalid. Falling back to 'dark-matter'."
                    )
                    style = "dark-matter"
            elif style.startswith("3d-"):
                style = maptiler_3d_style(
                    style=style.replace("3d-", "").lower(),
                    exaggeration=kwargs.pop("exaggeration", 1),
                    tile_size=kwargs.pop("tile_size", 512),
                    hillshade=kwargs.pop("hillshade", True),
                )

            elif style.lower() in carto_basemaps:
                style = construct_carto_basemap_url(style.lower())
            elif style == "demotiles":
                style = "https://demotiles.maplibre.org/style.json"
            elif "background-" in style:
                color = style.split("-")[1]
                style = background(color)
            else:
                style = construct_maptiler_style(style)

            if style in carto_basemaps:
                style = construct_carto_basemap_url(style)

        if style is not None:
            kwargs["style"] = style

        if len(controls) == 0:
            kwargs["attribution_control"] = False

        map_options = MapOptions(
            center=center, zoom=zoom, pitch=pitch, bearing=bearing, **kwargs
        )

        super().__init__(map_options, height=height)
        super().use_message_queue()

        for control, position in controls.items():
            self.add_control(control, position)

        self.layer_dict = {}
        self.layer_dict["background"] = {
            "layer": Layer(id="background", type=LayerType.BACKGROUND),
            "opacity": 1.0,
            "visible": True,
            "type": "background",
            "color": None,
        }
        self._style = style
        self.style_dict = {}
        for layer in self.get_style_layers():
            self.style_dict[layer["id"]] = layer
        self.source_dict = {}

    def _get_available_basemaps(self) -> Dict[str, Any]:
        """Convert xyz tile services to a dictionary of basemaps."""
        tile_providers = list(get_xyz_dict().values())
        if get_google_maps_api_key():
            tile_providers = tile_providers + list(
                get_google_map_tile_providers().values()
            )

        ret_dict = {}
        for tile_info in tile_providers:
            tile_info["url"] = tile_info.build_url()
            ret_dict[tile_info["name"]] = tile_info

        # Each alias needs to point to a single map. For each alias, pick the
        # first aliased map in `self._BASEMAP_ALIASES`.
        aliased_maps = {}
        for alias, maps in self._BASEMAP_ALIASES.items():
            for map_name in maps:
                if provider := ret_dict.get(map_name):
                    aliased_maps[alias] = provider
                    break
        return {**aliased_maps, **ret_dict}

    def _get_preferred_basemap_name(self, basemap_name: str) -> str:
        """Returns the aliased basemap name."""
        reverse_aliases = {}
        for alias, maps in self._BASEMAP_ALIASES.items():
            for map_name in maps:
                if map_name not in reverse_aliases:
                    reverse_aliases[map_name] = alias
        return reverse_aliases.get(basemap_name, basemap_name)

    def show(self) -> None:
        """Displays the map."""
        return Container(self)

    def _repr_html_(self, **kwargs):
        """Displays the map."""

        filename = os.environ.get("MAPLIBRE_OUTPUT", None)
        replace_key = os.environ.get("MAPTILER_REPLACE_KEY", False)
        if filename is not None:
            self.to_html(filename, replace_key=replace_key)

    def add_layer(
        self,
        layer: "Layer",
        before_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Adds a layer to the map.

        This method adds a layer to the map. If a name is provided, it is used
            as the key to store the layer in the layer dictionary. Otherwise,
            the layer's ID is used as the key. If a before_id is provided, the
            layer is inserted before the layer with that ID.

        Args:
            layer (Layer): The layer object to add to the map.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            name (str, optional): The name to use as the key to store the layer
                in the layer dictionary. If None, the layer's ID is used as the key.

        Returns:
            None
        """
        if isinstance(layer, dict):
            if "minzoom" in layer:
                layer["min-zoom"] = layer.pop("minzoom")
            if "maxzoom" in layer:
                layer["max-zoom"] = layer.pop("maxzoom")
            layer = replace_top_level_hyphens(layer)
            layer = Layer(**layer)

        if name is None:
            name = layer.id

        if (
            "paint" in layer.to_dict()
            and f"{layer.type}-color" in layer.paint
            and isinstance(layer.paint[f"{layer.type}-color"], str)
        ):
            color = check_color(layer.paint[f"{layer.type}-color"])
        else:
            color = None

        self.layer_dict[name] = {
            "layer": layer,
            "opacity": 1.0,
            "visible": True,
            "type": layer.type,
            "color": color,
        }
        super().add_layer(layer, before_id=before_id)

    def remove_layer(self, name: str) -> None:
        """
        Removes a layer from the map.

        This method removes a layer from the map using the layer's name.

        Args:
            name (str): The name of the layer to remove.

        Returns:
            None
        """

        super().add_call("removeLayer", name)
        if name in self.layer_dict:
            self.layer_dict.pop(name)

    def add_control(
        self, control: Union[str, Any], position: str = "top-right", **kwargs: Any
    ) -> None:
        """
        Adds a control to the map.

        This method adds a control to the map. The control can be one of the
            following: 'scale', 'fullscreen', 'geolocate', 'navigation', "attribution",
            and "draw". If the control is a string, it is converted to the
            corresponding control object. If the control is not a string, it is
            assumed to be a control object.

        Args:
            control (str or object): The control to add to the map. Can be one
                of the following: 'scale', 'fullscreen', 'geolocate', 'navigation',
                 "attribution", and "draw".
            position (str, optional): The position of the control. Defaults to "top-right".
            **kwargs: Additional keyword arguments that are passed to the control object.

        Returns:
            None

        Raises:
            ValueError: If the control is a string and is not one of the
                following: 'scale', 'fullscreen', 'geolocate', 'navigation', "attribution".
        """

        if isinstance(control, str):
            control = control.lower()
            if control == "scale":
                control = ScaleControl(**kwargs)
            elif control == "fullscreen":
                control = FullscreenControl(**kwargs)
            elif control == "geolocate":
                control = GeolocateControl(**kwargs)
            elif control == "navigation":
                control = NavigationControl(**kwargs)
            elif control == "attribution":
                control = AttributionControl(**kwargs)
            elif control == "draw":
                self.add_draw_control(position=position, **kwargs)
            elif control == "layers":
                self.add_layer_control(position=position, **kwargs)
                return
            else:
                print(
                    "Control can only be one of the following: 'scale', 'fullscreen', 'geolocate', 'navigation', and 'draw'."
                )
                return

        super().add_control(control, position)

    def add_draw_control(
        self,
        options: Optional[Dict[str, Any]] = None,
        position: str = "top-left",
        geojson: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Adds a drawing control to the map.

        This method enables users to add interactive drawing controls to the map,
        allowing for the creation, editing, and deletion of geometric shapes on
        the map. The options, position, and initial GeoJSON can be customized.

        Args:
            options (Optional[Dict[str, Any]]): Configuration options for the
                drawing control. Defaults to None.
            position (str): The position of the control on the map. Defaults
                to "top-left".
            geojson (Optional[Dict[str, Any]]): Initial GeoJSON data to load
                into the drawing control. Defaults to None.
            **kwargs (Any): Additional keyword arguments to be passed to the
                drawing control.

        Returns:
            None
        """

        super().add_mapbox_draw(
            options=options, position=position, geojson=geojson, **kwargs
        )

    def save_draw_features(self, filepath: str, indent=4, **kwargs) -> None:
        """
        Saves the drawn features to a file.

        This method saves all features created with the drawing control to a
        specified file in GeoJSON format. If there are no features to save, the
        file will not be created.

        Args:
            filepath (str): The path to the file where the GeoJSON data will be saved.
            **kwargs (Any): Additional keyword arguments to be passed to
            json.dump for custom serialization.

        Returns:
            None

        Raises:
            ValueError: If the feature collection is empty.
        """

        if len(self.draw_feature_collection_all) > 0:
            with open(filepath, "w") as f:
                json.dump(self.draw_feature_collection_all, f, indent=indent, **kwargs)
        else:
            print("There are no features to save.")

    def add_source(self, id: str, source: Union[str, Dict]) -> None:
        """
        Adds a source to the map.

        Args:
            id (str): The ID of the source.
            source (str or dict): The source data. .

        Returns:
            None
        """
        super().add_source(id, source)
        self.source_dict[id] = source

    def set_center(self, lon: float, lat: float, zoom: Optional[int] = None) -> None:
        """
        Sets the center of the map.

        This method sets the center of the map to the specified longitude and latitude.
        If a zoom level is provided, it also sets the zoom level of the map.

        Args:
            lon (float): The longitude of the center of the map.
            lat (float): The latitude of the center of the map.
            zoom (int, optional): The zoom level of the map. If None, the zoom
                level is not changed.

        Returns:
            None
        """
        center = [lon, lat]
        self.add_call("setCenter", center)

        if zoom is not None:
            self.add_call("setZoom", zoom)

    def set_zoom(self, zoom: Optional[int] = None) -> None:
        """
        Sets the zoom level of the map.

        This method sets the zoom level of the map to the specified value.

        Args:
            zoom (int): The zoom level of the map.

        Returns:
            None
        """
        self.add_call("setZoom", zoom)

    def fit_bounds(self, bounds: List[Tuple[float, float]]) -> None:
        """
        Adjusts the viewport of the map to fit the specified geographical bounds
            in the format of [[lon_min, lat_min], [lon_max, lat_max]] or
            [lon_min, lat_min, lon_max, lat_max].

        This method adjusts the viewport of the map so that the specified geographical bounds
        are visible in the viewport. The bounds are specified as a list of two points,
        where each point is a list of two numbers representing the longitude and latitude.

        Args:
            bounds (list): A list of two points representing the geographical bounds that
                        should be visible in the viewport. Each point is a list of two
                        numbers representing the longitude and latitude. For example,
                        [[32.958984, -5.353521],[43.50585, 5.615985]]

        Returns:
            None
        """

        if isinstance(bounds, list):
            if len(bounds) == 4 and all(isinstance(i, (int, float)) for i in bounds):
                bounds = [[bounds[0], bounds[1]], [bounds[2], bounds[3]]]

        self.add_call("fitBounds", bounds)

    def add_basemap(
        self,
        basemap: Union[str, xyzservices.TileProvider] = None,
        opacity: float = 1.0,
        visible: bool = True,
        attribution: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Adds a basemap to the map.

        This method adds a basemap to the map. The basemap can be a string from
        predefined basemaps, an instance of xyzservices.TileProvider, or a key
        from the basemaps dictionary.

        Args:
            basemap (str or TileProvider, optional): The basemap to add. Can be
                one of the predefined strings, an instance of xyzservices.TileProvider,
                or a key from the basemaps dictionary. Defaults to None, which adds
                the basemap widget.
            opacity (float, optional): The opacity of the basemap. Defaults to 1.0.
            visible (bool, optional): Whether the basemap is visible or not.
                Defaults to True.
            attribution (str, optional): The attribution text to display for the
                basemap. If None, the attribution text is taken from the basemap
                or the TileProvider. Defaults to None.
            **kwargs: Additional keyword arguments that are passed to the
                RasterTileSource class. See https://bit.ly/4erD2MQ for more information.

        Returns:
            None

        Raises:
            ValueError: If the basemap is not one of the predefined strings,
                not an instance of TileProvider, and not a key from the basemaps dictionary.
        """
        import xyzservices

        if basemap is None:
            return self._basemap_widget()

        self._available_basemaps = self._get_available_basemaps()

        name = basemap
        url = None
        max_zoom = 30
        min_zoom = 0

        if isinstance(basemap, str):
            for map_name, tile_provider in self._available_basemaps.items():
                if basemap.upper() == map_name.upper():
                    basemap = tile_provider
                    break

        if isinstance(basemap, xyzservices.TileProvider):
            name = basemap.name
            url = basemap.build_url()
            if attribution is None:
                attribution = basemap.attribution
            if "max_zoom" in basemap.keys():
                max_zoom = basemap["max_zoom"]
            if "min_zoom" in basemap.keys():
                min_zoom = basemap["min_zoom"]

        elif basemap in basemaps:
            url = basemaps[basemap]["url"]
            if attribution is None:
                attribution = basemaps[basemap]["attribution"]
            if "max_zoom" in basemaps[basemap]:
                max_zoom = basemaps[basemap]["max_zoom"]
            if "min_zoom" in basemaps[basemap]:
                min_zoom = basemaps[basemap]["min_zoom"]
        else:
            print(
                "Basemap can only be one of the following:\n  {}".format(
                    "\n  ".join(basemaps.keys())
                )
            )
            return

        raster_source = RasterTileSource(
            tiles=[url],
            attribution=attribution,
            max_zoom=max_zoom,
            min_zoom=min_zoom,
            tile_size=256,
            **kwargs,
        )
        layer = Layer(id=name, source=raster_source, type=LayerType.RASTER)
        self.add_layer(layer)
        self.set_opacity(name, opacity)
        self.set_visibility(name, visible)

    def add_geojson(
        self,
        data: Union[str, Dict],
        layer_type: Optional[str] = None,
        filter: Optional[Dict] = None,
        paint: Optional[Dict] = None,
        name: Optional[str] = None,
        fit_bounds: bool = True,
        visible: bool = True,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ) -> None:
        """
        Adds a GeoJSON layer to the map.

        This method adds a GeoJSON layer to the map. The GeoJSON data can be a
        URL to a GeoJSON file or a GeoJSON dictionary. If a name is provided, it
        is used as the key to store the layer in the layer dictionary. Otherwise,
        a random name is generated.

        Args:
            data (str | dict): The GeoJSON data. This can be a URL to a GeoJSON
                file or a GeoJSON dictionary.
            layer_type (str, optional): The type of the layer. It can be one of
                the following: 'circle', 'fill', 'fill-extrusion', 'line', 'symbol',
                'raster', 'background', 'heatmap', 'hillshade'. If None, the type
                is inferred from the GeoJSON data.
            filter (dict, optional): The filter to apply to the layer. If None,
                no filter is applied.
            paint (dict, optional): The paint properties to apply to the layer.
                If None, no paint properties are applied.
            name (str, optional): The name of the layer. If None, a random name
                is generated.
            fit_bounds (bool, optional): Whether to adjust the viewport of the
                map to fit the bounds of the GeoJSON data. Defaults to True.
            visible (bool, optional): Whether the layer is visible or not.
                Defaults to True.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            source_args (dict, optional): Additional keyword arguments that are
                passed to the GeoJSONSource class.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://maplibre.org/maplibre-style-spec/layers/ for more info.

        Returns:
            None

        Raises:
            ValueError: If the data is not a URL or a GeoJSON dictionary.
        """

        import os

        bounds = None
        geom_type = None

        if isinstance(data, str):
            if os.path.isfile(data) or data.startswith("http"):
                data = gpd.read_file(data).__geo_interface__
                bounds = get_bounds(data)
                source = GeoJSONSource(data=data, **source_args)
            else:
                raise ValueError("The data must be a URL or a GeoJSON dictionary.")
        elif isinstance(data, dict):
            source = GeoJSONSource(data=data, **source_args)

            bounds = get_bounds(data)
        else:
            raise ValueError("The data must be a URL or a GeoJSON dictionary.")

        if name is None:
            name = "geojson"

        if filter is not None:
            kwargs["filter"] = filter
        if paint is None:
            if "features" in data:
                geom_type = data["features"][0]["geometry"]["type"]
            elif "geometry" in data:
                geom_type = data["geometry"]["type"]
            if geom_type in ["Point", "MultiPoint"]:
                if layer_type is None:
                    layer_type = "circle"
                    paint = {
                        "circle-radius": 5,
                        "circle-color": "#3388ff",
                        "circle-stroke-color": "#ffffff",
                        "circle-stroke-width": 1,
                    }
            elif geom_type in ["LineString", "MultiLineString"]:
                if layer_type is None:
                    layer_type = "line"
                    paint = {"line-color": "#3388ff", "line-width": 2}
            elif geom_type in ["Polygon", "MultiPolygon"]:
                if layer_type is None:
                    layer_type = "fill"
                    paint = {
                        "fill-color": "#3388ff",
                        "fill-opacity": 0.8,
                        "fill-outline-color": "#ffffff",
                    }

        if paint is not None:
            kwargs["paint"] = paint

        layer = Layer(
            id=name,
            type=layer_type,
            source=source,
            **kwargs,
        )
        self.add_layer(layer, before_id=before_id, name=name)
        self.add_popup(name)
        if fit_bounds and bounds is not None:
            self.fit_bounds(bounds)
        self.set_visibility(name, visible)

        if isinstance(paint, dict) and f"{layer_type}-opacity" in paint:
            self.set_opacity(name, paint[f"{layer_type}-opacity"])
        else:
            self.set_opacity(name, 1.0)

    def add_vector(
        self,
        data: Union[str, Dict],
        layer_type: Optional[str] = None,
        filter: Optional[Dict] = None,
        paint: Optional[Dict] = None,
        name: Optional[str] = None,
        fit_bounds: bool = True,
        visible: bool = True,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ) -> None:
        """
        Adds a vector layer to the map.

        This method adds a vector layer to the map. The vector data can be a
        URL or local file path to a vector file. If a name is provided, it
        is used as the key to store the layer in the layer dictionary. Otherwise,
        a random name is generated.

        Args:
            data (str | dict): The vector data. This can be a URL or local file
                path to a vector file.
            layer_type (str, optional): The type of the layer. If None, the type
                is inferred from the GeoJSON data.
            filter (dict, optional): The filter to apply to the layer. If None,
                no filter is applied.
            paint (dict, optional): The paint properties to apply to the layer.
                If None, no paint properties are applied.
            name (str, optional): The name of the layer. If None, a random name
                is generated.
            fit_bounds (bool, optional): Whether to adjust the viewport of the
                map to fit the bounds of the GeoJSON data. Defaults to True.
            visible (bool, optional): Whether the layer is visible or not.
                Defaults to True.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            source_args (dict, optional): Additional keyword arguments that are
                passed to the GeoJSONSource class.
            **kwargs: Additional keyword arguments that are passed to the Layer class.

        Returns:
            None

        Raises:
            ValueError: If the data is not a URL or a GeoJSON dictionary.
        """

        if not isinstance(data, gpd.GeoDataFrame):
            data = gpd.read_file(data).__geo_interface__
        else:
            data = data.__geo_interface__

        self.add_geojson(
            data,
            layer_type=layer_type,
            filter=filter,
            paint=paint,
            name=name,
            fit_bounds=fit_bounds,
            visible=visible,
            before_id=before_id,
            source_args=source_args,
            **kwargs,
        )

    def add_gdf(
        self,
        gdf: gpd.GeoDataFrame,
        layer_type: Optional[str] = None,
        filter: Optional[Dict] = None,
        paint: Optional[Dict] = None,
        name: Optional[str] = None,
        fit_bounds: bool = True,
        visible: bool = True,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ) -> None:
        """
        Adds a vector layer to the map.

        This method adds a GeoDataFrame to the map as a vector layer.

        Args:
            gdf (gpd.GeoDataFrame): The GeoDataFrame to add to the map.
            layer_type (str, optional): The type of the layer. If None, the type
                is inferred from the GeoJSON data.
            filter (dict, optional): The filter to apply to the layer. If None,
                no filter is applied.
            paint (dict, optional): The paint properties to apply to the layer.
                If None, no paint properties are applied.
            name (str, optional): The name of the layer. If None, a random name
                is generated.
            fit_bounds (bool, optional): Whether to adjust the viewport of the
                map to fit the bounds of the GeoJSON data. Defaults to True.
            visible (bool, optional): Whether the layer is visible or not.
                Defaults to True.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            source_args (dict, optional): Additional keyword arguments that are
                passed to the GeoJSONSource class.
            **kwargs: Additional keyword arguments that are passed to the Layer class.

        Returns:
            None

        Raises:
            ValueError: If the data is not a URL or a GeoJSON dictionary.
        """
        if not isinstance(gdf, gpd.GeoDataFrame):
            raise ValueError("The data must be a GeoDataFrame.")
        geojson = gdf.__geo_interface__
        self.add_geojson(
            geojson,
            layer_type=layer_type,
            filter=filter,
            paint=paint,
            name=name,
            fit_bounds=fit_bounds,
            visible=visible,
            before_id=before_id,
            source_args=source_args,
            **kwargs,
        )

    def add_tile_layer(
        self,
        url: str,
        name: str = "Tile Layer",
        attribution: str = "",
        opacity: float = 1.0,
        visible: bool = True,
        tile_size: int = 256,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ) -> None:
        """
        Adds a TileLayer to the map.

        This method adds a TileLayer to the map. The TileLayer is created from
            the specified URL, and it is added to the map with the specified
            name, attribution, visibility, and tile size.

        Args:
            url (str): The URL of the tile layer.
            name (str, optional): The name to use for the layer. Defaults to '
                Tile Layer'.
            attribution (str, optional): The attribution to use for the layer.
                Defaults to ''.
            visible (bool, optional): Whether the layer should be visible by
                default. Defaults to True.
            tile_size (int, optional): The size of the tiles in the layer.
                Defaults to 256.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            source_args (dict, optional): Additional keyword arguments that are
                passed to the RasterTileSource class.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://eodagmbh.github.io/py-maplibregl/api/layer/ for more information.

        Returns:
            None
        """

        raster_source = RasterTileSource(
            tiles=[url.strip()],
            attribution=attribution,
            tile_size=tile_size,
            **source_args,
        )
        layer = Layer(id=name, source=raster_source, type=LayerType.RASTER, **kwargs)
        self.add_layer(layer, before_id=before_id, name=name)
        self.set_visibility(name, visible)
        self.set_opacity(name, opacity)

    def add_wms_layer(
        self,
        url: str,
        layers: str,
        format: str = "image/png",
        name: str = "WMS Layer",
        attribution: str = "",
        opacity: float = 1.0,
        visible: bool = True,
        tile_size: int = 256,
        before_id: Optional[str] = None,
        source_args: Dict = {},
        **kwargs: Any,
    ) -> None:
        """
        Adds a WMS layer to the map.

        This method adds a WMS layer to the map. The WMS  is created from
            the specified URL, and it is added to the map with the specified
            name, attribution, visibility, and tile size.

        Args:
            url (str): The URL of the tile layer.
            layers (str): The layers to include in the WMS request.
            format (str, optional): The format of the tiles in the layer.
            name (str, optional): The name to use for the layer. Defaults to
                'WMS Layer'.
            attribution (str, optional): The attribution to use for the layer.
                Defaults to ''.
            visible (bool, optional): Whether the layer should be visible by
                default. Defaults to True.
            tile_size (int, optional): The size of the tiles in the layer.
                Defaults to 256.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            source_args (dict, optional): Additional keyword arguments that are
                passed to the RasterTileSource class.
            **kwargs: Additional keyword arguments that are passed to the Layer class.
                See https://eodagmbh.github.io/py-maplibregl/api/layer/ for more information.

        Returns:
            None
        """

        url = f"{url.strip()}?service=WMS&request=GetMap&layers={layers}&styles=&format={format.replace('/', '%2F')}&transparent=true&version=1.1.1&height=256&width=256&srs=EPSG%3A3857&bbox={{bbox-epsg-3857}}"

        self.add_tile_layer(
            url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            visible=visible,
            tile_size=tile_size,
            before_id=before_id,
            source_args=source_args,
            **kwargs,
        )

    def add_ee_layer(
        self,
        ee_object=None,
        vis_params={},
        asset_id: str = None,
        name: str = None,
        opacity: float = 1.0,
        attribution: str = "Google Earth Engine",
        visible: bool = True,
        before_id: Optional[str] = None,
        ee_initialize: bool = False,
        **kwargs,
    ) -> None:
        """
        Adds a Google Earth Engine tile layer to the map based on the tile layer URL from
            https://github.com/opengeos/ee-tile-layers/blob/main/datasets.tsv.

        Args:
            ee_object (object): The Earth Engine object to display.
            vis_params (dict): Visualization parameters. For example, {'min': 0, 'max': 100}.
            asset_id (str): The ID of the Earth Engine asset.
            name (str, optional): The name of the tile layer. If not provided,
                the asset ID will be used. Default is None.
            opacity (float, optional): The opacity of the tile layer (0 to 1).
                Default is 1.
            attribution (str, optional): The attribution text to be displayed.
                Default is "Google Earth Engine".
            visible (bool, optional): Whether the tile layer should be shown on
                the map. Default is True.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            ee_initialize (bool, optional): Whether to initialize the Earth Engine
            **kwargs: Additional keyword arguments to be passed to the underlying
                `add_tile_layer` method.

        Returns:
            None
        """
        import pandas as pd

        if isinstance(asset_id, str):
            df = pd.read_csv(
                "https://raw.githubusercontent.com/opengeos/ee-tile-layers/main/datasets.tsv",
                sep="\t",
            )

            asset_id = asset_id.strip()
            if name is None:
                name = asset_id

            if asset_id in df["id"].values:
                url = df.loc[df["id"] == asset_id, "url"].values[0]
                self.add_tile_layer(
                    url,
                    name,
                    attribution=attribution,
                    opacity=opacity,
                    visible=visible,
                    before_id=before_id,
                    **kwargs,
                )
            else:
                print(f"The provided EE tile layer {asset_id} does not exist.")
        elif ee_object is not None:
            try:
                import geemap
                from geemap.ee_tile_layers import _get_tile_url_format

                if ee_initialize:
                    geemap.ee_initialize()
                url = _get_tile_url_format(ee_object, vis_params)
                if name is None:
                    name = "EE Layer"
                self.add_tile_layer(
                    url,
                    name,
                    attribution=attribution,
                    opacity=opacity,
                    visible=visible,
                    before_id=before_id,
                    **kwargs,
                )
            except Exception as e:
                print(e)
                print(
                    "Please install the `geemap` package to use the `add_ee_layer` function."
                )
                return

    def add_cog_layer(
        self,
        url: str,
        name: Optional[str] = None,
        attribution: str = "",
        opacity: float = 1.0,
        visible: bool = True,
        bands: Optional[List[int]] = None,
        nodata: Optional[Union[int, float]] = 0,
        titiler_endpoint: str = None,
        fit_bounds: bool = True,
        before_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Adds a Cloud Optimized Geotiff (COG) TileLayer to the map.

        This method adds a COG TileLayer to the map. The COG TileLayer is created
        from the specified URL, and it is added to the map with the specified name,
        attribution, opacity, visibility, and bands.

        Args:
            url (str): The URL of the COG tile layer.
            name (str, optional): The name to use for the layer. If None, a
                random name is generated. Defaults to None.
            attribution (str, optional): The attribution to use for the layer.
                Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            visible (bool, optional): Whether the layer should be visible by default.
                Defaults to True.
            bands (list, optional): A list of bands to use for the layer.
                Defaults to None.
            nodata (float, optional): The nodata value to use for the layer.
            titiler_endpoint (str, optional): The endpoint of the titiler service.
                Defaults to "https://titiler.xyz".
            fit_bounds (bool, optional): Whether to adjust the viewport of
                the map to fit the bounds of the layer. Defaults to True.
            **kwargs: Arbitrary keyword arguments, including bidx, expression,
                nodata, unscale, resampling, rescale, color_formula, colormap,
                    colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/.
                    To select a certain bands, use bidx=[1, 2, 3]. apply a
                        rescaling to multiple bands, use something like
                        `rescale=["164,223","130,211","99,212"]`.
        Returns:
            None
        """

        if name is None:
            name = "COG_" + random_string()

        tile_url = cog_tile(url, bands, titiler_endpoint, nodata=nodata, **kwargs)
        bounds = cog_bounds(url, titiler_endpoint)
        self.add_tile_layer(
            tile_url, name, attribution, opacity, visible, before_id=before_id
        )
        if fit_bounds:
            self.fit_bounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])

    def add_stac_layer(
        self,
        url: Optional[str] = None,
        collection: Optional[str] = None,
        item: Optional[str] = None,
        assets: Optional[Union[str, List[str]]] = None,
        bands: Optional[List[str]] = None,
        nodata: Optional[Union[int, float]] = 0,
        titiler_endpoint: Optional[str] = None,
        name: str = "STAC Layer",
        attribution: str = "",
        opacity: float = 1.0,
        visible: bool = True,
        fit_bounds: bool = True,
        before_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Adds a STAC TileLayer to the map.

        This method adds a STAC TileLayer to the map. The STAC TileLayer is
        created from the specified URL, collection, item, assets, and bands, and
        it is added to the map with the specified name, attribution, opacity,
        visibility, and fit bounds.

        Args:
            url (str, optional): HTTP URL to a STAC item, e.g., https://bit.ly/3VlttGm.
                Defaults to None.
            collection (str, optional): The Microsoft Planetary Computer STAC
                collection ID, e.g., landsat-8-c2-l2. Defaults to None.
            item (str, optional): The Microsoft Planetary Computer STAC item ID, e.g.,
                LC08_L2SP_047027_20201204_02_T1. Defaults to None.
            assets (str | list, optional): The Microsoft Planetary Computer STAC asset ID,
                e.g., ["SR_B7", "SR_B5", "SR_B4"]. Defaults to None.
            bands (list, optional): A list of band names, e.g.,
                ["SR_B7", "SR_B5", "SR_B4"]. Defaults to None.
            no_data (int | float, optional): The nodata value to use for the layer.
            titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz",
                "https://planetarycomputer.microsoft.com/api/data/v1",
                "planetary-computer", "pc". Defaults to None.
            name (str, optional): The layer name to use for the layer. Defaults to 'STAC Layer'.
            attribution (str, optional): The attribution to use. Defaults to ''.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            visible (bool, optional): A flag indicating whether the layer should
                be on by default. Defaults to True.
            fit_bounds (bool, optional): A flag indicating whether the map should
                be zoomed to the layer extent. Defaults to True.
            before_id (str, optional): The ID of an existing layer before which
                the new layer should be inserted.
            **kwargs: Arbitrary keyword arguments, including bidx, expression,
                nodata, unscale, resampling, rescale, color_formula, colormap,
                colormap_name, return_mask. See https://developmentseed.org/titiler/endpoints/cog/
                and https://cogeotiff.github.io/rio-tiler/colormap/. To select
                a certain bands, use bidx=[1, 2, 3]. apply a rescaling to multiple
                bands, use something like `rescale=["164,223","130,211","99,212"]`.

        Returns:
            None
        """

        if "colormap_name" in kwargs and kwargs["colormap_name"] is None:
            kwargs.pop("colormap_name")

        tile_url = stac_tile(
            url,
            collection,
            item,
            assets,
            bands,
            titiler_endpoint,
            nodata=nodata,
            **kwargs,
        )
        bounds = stac_bounds(url, collection, item, titiler_endpoint)
        self.add_tile_layer(
            tile_url, name, attribution, opacity, visible, before_id=before_id
        )
        if fit_bounds:
            self.fit_bounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])

    def add_raster(
        self,
        source,
        indexes=None,
        colormap=None,
        vmin=None,
        vmax=None,
        nodata=None,
        attribution="Localtileserver",
        name="Raster",
        before_id=None,
        fit_bounds=True,
        visible=True,
        opacity=1.0,
        array_args={},
        client_args={"cors_all": True},
        **kwargs,
    ):
        """Add a local raster dataset to the map.
            If you are using this function in JupyterHub on a remote server
            (e.g., Binder, Microsoft Planetary Computer) and if the raster
            does not render properly, try installing jupyter-server-proxy using
            `pip install jupyter-server-proxy`, then running the following code
            before calling this function. For more info, see https://bit.ly/3JbmF93.

            import os
            os.environ['LOCALTILESERVER_CLIENT_PREFIX'] = 'proxy/{port}'

        Args:
            source (str): The path to the GeoTIFF file or the URL of the Cloud
                Optimized GeoTIFF.
            indexes (int, optional): The band(s) to use. Band indexing starts
                at 1. Defaults to None.
            colormap (str, optional): The name of the colormap from `matplotlib`
                to use when plotting a single band.
                See https://matplotlib.org/stable/gallery/color/colormap_reference.html.
                Default is greyscale.
            vmin (float, optional): The minimum value to use when colormapping
                the palette when plotting a single band. Defaults to None.
            vmax (float, optional): The maximum value to use when colormapping
                the palette when plotting a single band. Defaults to None.
            nodata (float, optional): The value from the band to use to interpret
                as not valid data. Defaults to None.
            attribution (str, optional): Attribution for the source raster. This
                defaults to a message about it being a local file.. Defaults to None.
            layer_name (str, optional): The layer name to use. Defaults to 'Raster'.
            layer_index (int, optional): The index of the layer. Defaults to None.
            zoom_to_layer (bool, optional): Whether to zoom to the extent of the
                layer. Defaults to True.
            visible (bool, optional): Whether the layer is visible. Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            array_args (dict, optional): Additional arguments to pass to
                `array_to_memory_file` when reading the raster. Defaults to {}.
            client_args (dict, optional): Additional arguments to pass to
                localtileserver.TileClient. Defaults to { "cors_all": False }.
        """
        import numpy as np
        import xarray as xr

        if isinstance(source, np.ndarray) or isinstance(source, xr.DataArray):
            source = array_to_image(source, **array_args)

        tile_layer, tile_client = get_local_tile_layer(
            source,
            indexes=indexes,
            colormap=colormap,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            opacity=opacity,
            attribution=attribution,
            layer_name=name,
            client_args=client_args,
            return_client=True,
            **kwargs,
        )

        self.add_tile_layer(
            tile_layer.url,
            name=name,
            opacity=opacity,
            visible=visible,
            attribution=attribution,
            before_id=before_id,
        )

        bounds = tile_client.bounds()  # [ymin, ymax, xmin, xmax]
        bounds = [[bounds[2], bounds[0]], [bounds[3], bounds[1]]]
        # [minx, miny, maxx, maxy]
        if fit_bounds:
            self.fit_bounds(bounds)

    def to_html(
        self,
        output: str = None,
        title: str = "My Awesome Map",
        width: str = "100%",
        height: str = "100%",
        replace_key: bool = False,
        remove_port: bool = True,
        preview: bool = False,
        overwrite: bool = False,
        **kwargs,
    ):
        """Render the map to an HTML page.

        Args:
            output (str, optional): The output HTML file. If None, the HTML content
                is returned as a string. Defaults
            title (str, optional): The title of the HTML page. Defaults to 'My Awesome Map'.
            width (str, optional): The width of the map. Defaults to '100%'.
            height (str, optional): The height of the map. Defaults to '100%'.
            replace_key (bool, optional): Whether to replace the API key in the HTML.
                If True, the API key is replaced with the public API key.
                The API key is read from the environment variable `MAPTILER_KEY`.
                The public API key is read from the environment variable `MAPTILER_KEY_PUBLIC`.
                Defaults to False.
            remove_port (bool, optional): Whether to remove the port number from the HTML.
            preview (bool, optional): Whether to preview the HTML file in a web browser.
                Defaults to False.
            overwrite (bool, optional): Whether to overwrite the output file if it already exists.
            **kwargs: Additional keyword arguments that are passed to the
                `maplibre.ipywidget.MapWidget.to_html()` method.

        Returns:
            str: The HTML content of the map.
        """
        if isinstance(height, int):
            height = f"{height}px"
        if isinstance(width, int):
            width = f"{width}px"

        if "style" not in kwargs:
            kwargs["style"] = f"width: {width}; height: {height};"
        else:
            kwargs["style"] += f"width: {width}; height: {height};"
        html = super().to_html(title=title, **kwargs)

        if isinstance(height, str) and ("%" in height):
            style_before = """</style>\n"""
            style_after = (
                """html, body {height: 100%; margin: 0; padding: 0;} #pymaplibregl {width: 100%; height: """
                + height
                + """;}\n</style>\n"""
            )
            html = html.replace(style_before, style_after)

            div_before = f"""<div id="pymaplibregl" style="width: 100%; height: {height};"></div>"""
            div_after = f"""<div id="pymaplibregl"></div>"""
            html = html.replace(div_before, div_after)

            div_before = f"""<div id="pymaplibregl" style="height: {height};"></div>"""
            html = html.replace(div_before, div_after)

        if replace_key or (os.getenv("MAPTILER_REPLACE_KEY") is not None):
            key_before = get_env_var("MAPTILER_KEY")
            key_after = get_env_var("MAPTILER_KEY_PUBLIC")
            if key_after is not None:
                html = html.replace(key_before, key_after)

        if remove_port:
            html = remove_port_from_string(html)

        if output is None:
            output = os.getenv("MAPLIBRE_OUTPUT", None)

        if output:

            if not overwrite and os.path.exists(output):
                import glob

                num = len(glob.glob(output.replace(".html", "*.html")))
                output = output.replace(".html", f"_{num}.html")

            with open(output, "w") as f:
                f.write(html)
            if preview:
                import webbrowser

                webbrowser.open(output)
        else:
            return html

    def set_paint_property(self, name: str, prop: str, value: Any) -> None:
        """
        Set the opacity of a layer.

        This method sets the opacity of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            opacity (float): The opacity value to set.

        Returns:
            None
        """
        super().set_paint_property(name, prop, value)

        if "opacity" in prop and name in self.layer_dict:
            self.layer_dict[name]["opacity"] = value
        elif name in self.style_dict:
            layer = self.style_dict[name]
            if "paint" in layer:
                layer["paint"][prop] = value

    def set_layout_property(self, name: str, prop: str, value: Any) -> None:
        """
        Set the layout property of a layer.

        This method sets the layout property of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            prop (str): The layout property to set.
            value (Any): The value to set.

        Returns:
            None
        """
        super().set_layout_property(name, prop, value)

        if name in self.style_dict:
            layer = self.style_dict[name]
            if "layout" in layer:
                layer["layout"][prop] = value

    def set_color(self, name: str, color: str) -> None:
        """
        Set the color of a layer.

        This method sets the color of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            color (str): The color value to set.

        Returns:
            None
        """
        color = check_color(color)
        super().set_paint_property(
            name, f"{self.layer_dict[name]['layer'].type}-color", color
        )
        self.layer_dict[name]["color"] = color

    def set_opacity(self, name: str, opacity: float) -> None:
        """
        Set the opacity of a layer.

        This method sets the opacity of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            opacity (float): The opacity value to set.

        Returns:
            None
        """

        if name in self.layer_dict:
            layer_type = self.layer_dict[name]["layer"].to_dict()["type"]
            prop_name = f"{layer_type}-opacity"
            self.layer_dict[name]["opacity"] = opacity
        elif name in self.style_dict:
            layer = self.style_dict[name]
            layer_type = layer.get("type")
            prop_name = f"{layer_type}-opacity"
            if "paint" in layer:
                layer["paint"][prop_name] = opacity
        super().set_paint_property(name, prop_name, opacity)

    def set_visibility(self, name: str, visible: bool) -> None:
        """
        Set the visibility of a layer.

        This method sets the visibility of the specified layer to the specified value.

        Args:
            name (str): The name of the layer.
            visible (bool): The visibility value to set.

        Returns:
            None
        """
        super().set_visibility(name, visible)
        self.layer_dict[name]["visible"] = visible

    def layer_interact(self, name=None):
        """Create a layer widget for changing the visibility and opacity of a layer.

        Args:
            name (str): The name of the layer.

        Returns:
            ipywidgets.Widget: The layer widget.
        """

        import ipywidgets as widgets

        layer_names = list(self.layer_dict.keys())
        if name is None:
            name = layer_names[-1]
        elif name not in layer_names:
            raise ValueError(f"Layer {name} not found.")

        style = {"description_width": "initial"}
        dropdown = widgets.Dropdown(
            options=layer_names,
            value=name,
            description="Layer",
            style=style,
        )
        checkbox = widgets.Checkbox(
            description="Visible",
            value=self.layer_dict[name]["visible"],
            style=style,
            layout=widgets.Layout(width="120px"),
        )
        opacity_slider = widgets.FloatSlider(
            description="Opacity",
            min=0,
            max=1,
            step=0.01,
            value=self.layer_dict[name]["opacity"],
            style=style,
        )

        color_picker = widgets.ColorPicker(
            concise=True,
            value="white",
            style=style,
        )

        if self.layer_dict[name]["color"] is not None:
            color_picker.value = self.layer_dict[name]["color"]
            color_picker.disabled = False
        else:
            color_picker.value = "white"
            color_picker.disabled = True

        def color_picker_event(change):
            if self.layer_dict[dropdown.value]["color"] is not None:
                self.set_color(dropdown.value, change.new)

        color_picker.observe(color_picker_event, "value")

        hbox = widgets.HBox(
            [dropdown, checkbox, opacity_slider, color_picker],
            layout=widgets.Layout(width="750px"),
        )

        def dropdown_event(change):
            name = change.new
            checkbox.value = self.layer_dict[dropdown.value]["visible"]
            opacity_slider.value = self.layer_dict[dropdown.value]["opacity"]
            if self.layer_dict[dropdown.value]["color"] is not None:
                color_picker.value = self.layer_dict[dropdown.value]["color"]
                color_picker.disabled = False
            else:
                color_picker.value = "white"
                color_picker.disabled = True

        dropdown.observe(dropdown_event, "value")

        def update_layer(change):
            self.set_visibility(dropdown.value, checkbox.value)
            self.set_opacity(dropdown.value, opacity_slider.value)

        checkbox.observe(update_layer, "value")
        opacity_slider.observe(update_layer, "value")

        return hbox

    def style_layer_interact(self, id=None):
        """Create a layer widget for changing the visibility and opacity of a style layer.

        Args:
            id (str): The is of the layer.

        Returns:
            ipywidgets.Widget: The layer widget.
        """

        import ipywidgets as widgets

        layer_ids = list(self.style_dict.keys())
        layer_ids.sort()
        if id is None:
            id = layer_ids[0]
        elif id not in layer_ids:
            raise ValueError(f"Layer {id} not found.")

        layer = self.style_dict[id]
        layer_type = layer.get("type")
        style = {"description_width": "initial"}
        dropdown = widgets.Dropdown(
            options=layer_ids,
            value=id,
            description="Layer",
            style=style,
        )

        visibility = layer.get("layout", {}).get("visibility", "visible")
        if visibility == "visible":
            visibility = True
        else:
            visibility = False

        checkbox = widgets.Checkbox(
            description="Visible",
            value=visibility,
            style=style,
            layout=widgets.Layout(width="120px"),
        )

        opacity = layer.get("paint", {}).get(f"{layer_type}-opacity", 1.0)
        opacity_slider = widgets.FloatSlider(
            description="Opacity",
            min=0,
            max=1,
            step=0.01,
            value=opacity,
            style=style,
        )

        def extract_rgb(rgba_string):
            import re

            # Extracting the RGB values using regex
            rgb_tuple = tuple(map(int, re.findall(r"\d+", rgba_string)[:3]))
            return rgb_tuple

        color = layer.get("paint", {}).get(f"{layer_type}-color", "white")
        if color.startswith("rgba"):
            color = extract_rgb(color)
        color = check_color(color)
        color_picker = widgets.ColorPicker(
            concise=True,
            value=color,
            style=style,
        )

        def color_picker_event(change):
            self.set_paint_property(dropdown.value, f"{layer_type}-color", change.new)

        color_picker.observe(color_picker_event, "value")

        hbox = widgets.HBox(
            [dropdown, checkbox, opacity_slider, color_picker],
            layout=widgets.Layout(width="750px"),
        )

        def dropdown_event(change):
            name = change.new
            layer = self.style_dict[name]
            layer_type = layer.get("type")

            visibility = layer.get("layout", {}).get("visibility", "visible")
            if visibility == "visible":
                visibility = True
            else:
                visibility = False

            checkbox.value = visibility
            opacity = layer.get("paint", {}).get(f"{layer_type}-opacity", 1.0)
            opacity_slider.value = opacity

            color = layer.get("paint", {}).get(f"{layer_type}-color", "white")
            if color.startswith("rgba"):
                color = extract_rgb(color)
            color = check_color(color)

            if color:
                color_picker.value = color
                color_picker.disabled = False
            else:
                color_picker.value = "white"
                color_picker.disabled = True

        dropdown.observe(dropdown_event, "value")

        def update_layer(change):
            self.set_layout_property(
                dropdown.value, "visibility", "visible" if checkbox.value else "none"
            )
            self.set_paint_property(
                dropdown.value, f"{layer_type}-opacity", opacity_slider.value
            )

        checkbox.observe(update_layer, "value")
        opacity_slider.observe(update_layer, "value")

        return hbox

    def _basemap_widget(self, name=None):
        """Create a layer widget for changing the visibility and opacity of a layer.

        Args:
            name (str): The name of the layer.

        Returns:
            ipywidgets.Widget: The layer widget.
        """

        import ipywidgets as widgets

        layer_names = [
            basemaps[basemap]["name"]
            for basemap in basemaps.keys()
            if "layers" not in basemaps[basemap]
        ][1:]
        if name is None:
            name = layer_names[0]
        elif name not in layer_names:
            raise ValueError(f"Layer {name} not found.")

        tile = basemaps[name]
        raster_source = RasterTileSource(
            tiles=[tile["url"]],
            attribution=tile["attribution"],
            tile_size=256,
        )
        layer = Layer(id=name, source=raster_source, type=LayerType.RASTER)
        self.add_layer(layer)
        self.set_opacity(name, 1.0)
        self.set_visibility(name, True)

        style = {"description_width": "initial"}
        dropdown = widgets.Dropdown(
            options=layer_names,
            value=name,
            description="Basemap",
            style=style,
        )
        checkbox = widgets.Checkbox(
            description="Visible",
            value=self.layer_dict[name]["visible"],
            style=style,
            layout=widgets.Layout(width="120px"),
        )
        opacity_slider = widgets.FloatSlider(
            description="Opacity",
            min=0,
            max=1,
            step=0.01,
            value=self.layer_dict[name]["opacity"],
            style=style,
        )
        hbox = widgets.HBox(
            [dropdown, checkbox, opacity_slider], layout=widgets.Layout(width="600px")
        )

        def dropdown_event(change):
            old = change["old"]
            name = change.new
            self.remove_layer(old)

            tile = basemaps[name]
            raster_source = RasterTileSource(
                tiles=[tile["url"]],
                attribution=tile["attribution"],
                tile_size=256,
            )
            layer = Layer(id=name, source=raster_source, type=LayerType.RASTER)
            self.add_layer(layer)
            self.set_opacity(name, 1.0)
            self.set_visibility(name, True)

            checkbox.value = self.layer_dict[dropdown.value]["visible"]
            opacity_slider.value = self.layer_dict[dropdown.value]["opacity"]

        dropdown.observe(dropdown_event, "value")

        def update_layer(change):
            self.set_visibility(dropdown.value, checkbox.value)
            self.set_opacity(dropdown.value, opacity_slider.value)

        checkbox.observe(update_layer, "value")
        opacity_slider.observe(update_layer, "value")

        return hbox

    def add_pmtiles(
        self,
        url: str,
        style: Optional[Dict] = None,
        visible: bool = True,
        opacity: float = 1.0,
        exclude_mask: bool = False,
        tooltip: bool = True,
        properties: Optional[Dict] = None,
        template: Optional[str] = None,
        attribution: str = "PMTiles",
        fit_bounds: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Adds a PMTiles layer to the map.

        Args:
            url (str): The URL of the PMTiles file.
            style (dict, optional): The CSS style to apply to the layer. Defaults to None.
                See https://docs.mapbox.com/style-spec/reference/layers/ for more info.
            visible (bool, optional): Whether the layer should be shown initially. Defaults to True.
            opacity (float, optional): The opacity of the layer. Defaults to 1.0.
            exclude_mask (bool, optional): Whether to exclude the mask layer. Defaults to False.
            tooltip (bool, optional): Whether to show tooltips on the layer. Defaults to True.
            properties (dict, optional): The properties to use for the tooltips. Defaults to None.
            template (str, optional): The template to use for the tooltips. Defaults to None.
            attribution (str, optional): The attribution to use for the layer. Defaults to 'PMTiles'.
            fit_bounds (bool, optional): Whether to zoom to the layer extent. Defaults to True.
            **kwargs: Additional keyword arguments to pass to the PMTilesLayer constructor.

        Returns:
            None
        """

        try:

            if "sources" in kwargs:
                del kwargs["sources"]

            if "version" in kwargs:
                del kwargs["version"]

            pmtiles_source = {
                "type": "vector",
                "url": f"pmtiles://{url}",
                "attribution": attribution,
            }

            if style is None:
                style = pmtiles_style(url)

            if "sources" in style:
                source_name = list(style["sources"].keys())[0]
            elif "layers" in style:
                source_name = style["layers"][0]["source"]
            else:
                source_name = "source"

            self.add_source(source_name, pmtiles_source)

            style = replace_hyphens_in_keys(style)

            for params in style["layers"]:

                if exclude_mask and params.get("source_layer") == "mask":
                    continue

                layer = Layer(**params)
                self.add_layer(layer)
                self.set_visibility(params["id"], visible)
                self.set_opacity(params["id"], opacity)

                if tooltip:
                    self.add_tooltip(params["id"], properties, template)

            if fit_bounds:
                metadata = pmtiles_metadata(url)
                bounds = metadata["bounds"]  # [minx, miny, maxx, maxy]
                self.fit_bounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]])

        except Exception as e:
            print(e)

    def add_marker(
        self,
        marker: Marker = None,
        lng_lat: List[Union[float, float]] = [],
        popup: Optional[Dict] = {},
        options: Optional[Dict] = {},
    ) -> None:
        """
        Adds a marker to the map.

        Args:
            marker (Marker, optional): A Marker object. Defaults to None.
            lng_lat (List[Union[float, float]]): A list of two floats
                representing the longitude and latitude of the marker.
            popup (Optional[str], optional): The text to display in a popup when
                the marker is clicked. Defaults to None.
            options (Optional[Dict], optional): A dictionary of options to
                customize the marker. Defaults to None.

        Returns:
            None
        """

        if marker is None:
            marker = Marker(lng_lat=lng_lat, popup=popup, options=options)
        super().add_marker(marker)

    def fly_to(
        self,
        lon: float,
        lat: float,
        zoom: Optional[float] = None,
        speed: Optional[float] = None,
        essential: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Makes the map fly to a specified location.

        Args:
            lon (float): The longitude of the location to fly to.
            lat (float): The latitude of the location to fly to.
            zoom (Optional[float], optional): The zoom level to use when flying
                to the location. Defaults to None.
            speed (Optional[float], optional): The speed of the fly animation.
                Defaults to None.
            essential (bool, optional): Whether the flyTo animation is considered
                essential and not affected by prefers-reduced-motion. Defaults to True.
            **kwargs: Additional keyword arguments to pass to the flyTo function.

        Returns:
            None
        """

        center = [lon, lat]
        kwargs["center"] = center
        if zoom is not None:
            kwargs["zoom"] = zoom
        if speed is not None:
            kwargs["speed"] = speed
        if essential:
            kwargs["essential"] = essential

        super().add_call("flyTo", kwargs)

    def _read_image(self, image: str) -> Dict[str, Union[int, List[int]]]:
        """
        Reads an image from a URL or a local file path and returns a dictionary
            with the image data.

        Args:
            image (str): The URL or local file path to the image.

        Returns:
            Dict[str, Union[int, List[int]]]: A dictionary with the image width,
                height, and flattened data.

        Raises:
            ValueError: If the image argument is not a string representing a URL
                or a local file path.
        """

        import os
        from PIL import Image
        import numpy as np

        if isinstance(image, str):
            try:
                if image.startswith("http"):
                    image = download_file(
                        image, temp_file_path(image.split(".")[-1]), quiet=True
                    )
                if os.path.exists(image):
                    img = Image.open(image)
                else:
                    raise ValueError("The image file does not exist.")

                width, height = img.size
                # Convert image to numpy array and then flatten it
                img_data = np.array(img, dtype="uint8")
                if len(img_data.shape) == 3 and img_data.shape[2] == 2:
                    # Split the grayscale and alpha channels
                    gray_channel = img_data[:, :, 0]
                    alpha_channel = img_data[:, :, 1]

                    # Create the R, G, and B channels by duplicating the grayscale channel
                    R_channel = gray_channel
                    G_channel = gray_channel
                    B_channel = gray_channel

                    # Combine the channels into an RGBA image
                    RGBA_image_data = np.stack(
                        (R_channel, G_channel, B_channel, alpha_channel), axis=-1
                    )

                    # Update img_data to the new RGBA image data
                    img_data = RGBA_image_data

                flat_img_data = img_data.flatten()

                # Create the image dictionary with the flattened data
                image_dict = {
                    "width": width,
                    "height": height,
                    "data": flat_img_data.tolist(),  # Convert to list if necessary
                }

                return image_dict
            except Exception as e:
                print(e)
                return None
        else:
            raise ValueError("The image must be a URL or a local file path.")

    def add_image(
        self,
        id: str = None,
        image: Union[str, Dict] = None,
        width: int = None,
        height: int = None,
        coordinates: List[float] = None,
        position: str = None,
        icon_size: float = 1.0,
        **kwargs: Any,
    ) -> None:
        """Add an image to the map.

        Args:
            id (str): The layer ID of the image.
            image (Union[str, Dict, np.ndarray]): The URL or local file path to
                the image, or a dictionary containing image data, or a numpy
                array representing the image.
            width (int, optional): The width of the image. Defaults to None.
            height (int, optional): The height of the image. Defaults to None.
            coordinates (List[float], optional): The longitude and latitude
                coordinates to place the image.
            position (str, optional): The position of the image. Defaults to None.
                Can be one of 'top-right', 'top-left', 'bottom-right', 'bottom-left'.
            icon_size (float, optional): The size of the icon. Defaults to 1.0.

        Returns:
            None
        """
        import numpy as np

        if id is None:
            id = "image"

        style = ""
        if isinstance(width, int):
            style += f"width: {width}px; "
        elif isinstance(width, str) and width.endswith("px"):
            style += f"width: {width}; "
        if isinstance(height, int):
            style += f"height: {height}px; "
        elif isinstance(height, str) and height.endswith("px"):
            style += f"height: {height}; "

        if position is not None:
            if style == "":
                html = f'<img src="{image}">'
            else:
                html = f'<img src="{image}" style="{style}">'
            self.add_html(html, position=position, **kwargs)
        else:
            if isinstance(image, str):
                image_dict = self._read_image(image)
            elif isinstance(image, dict):
                image_dict = image
            elif isinstance(image, np.ndarray):
                image_dict = {
                    "width": width,
                    "height": height,
                    "data": image.flatten().tolist(),
                }
            else:
                raise ValueError(
                    "The image must be a URL, a local file path, or a numpy array."
                )
            super().add_call("addImage", id, image_dict)

            if coordinates is not None:

                source = {
                    "type": "geojson",
                    "data": {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": coordinates,
                                },
                            }
                        ],
                    },
                }

                self.add_source("image_point", source)

                kwargs["id"] = "image_points"
                kwargs["type"] = "symbol"
                kwargs["source"] = "image_point"
                if "layout" not in kwargs:
                    kwargs["layout"] = {}
                kwargs["layout"]["icon-image"] = id
                kwargs["layout"]["icon-size"] = icon_size
                self.add_layer(kwargs)

    def to_streamlit(
        self,
        width: Optional[int] = None,
        height: Optional[int] = 600,
        scrolling: Optional[bool] = False,
        **kwargs: Any,
    ) -> Any:
        """
        Convert the map to a Streamlit component.

        This function converts the map to a Streamlit component by encoding the
        HTML representation of the map as base64 and embedding it in an iframe.
        The width, height, and scrolling parameters control the appearance of
        the iframe.

        Args:
            width (Optional[int]): The width of the iframe. If None, the width
                will be determined by Streamlit.
            height (Optional[int]): The height of the iframe. Default is 600.
            scrolling (Optional[bool]): Whether the iframe should be scrollable.
                Default is False.
            **kwargs (Any): Additional arguments to pass to the Streamlit iframe
                function.

        Returns:
            Any: The Streamlit component.

        Raises:
            Exception: If there is an error in creating the Streamlit component.
        """
        try:
            import streamlit.components.v1 as components
            import base64

            raw_html = self.to_html().encode("utf-8")
            raw_html = base64.b64encode(raw_html).decode()
            return components.iframe(
                f"data:text/html;base64,{raw_html}",
                width=width,
                height=height,
                scrolling=scrolling,
                **kwargs,
            )

        except Exception as e:
            raise Exception(e)

    def rotate_to(
        self, bearing: float, options: Dict[str, Any] = {}, **kwargs: Any
    ) -> None:
        """
        Rotate the map to a specified bearing.

        This function rotates the map to a specified bearing. The bearing is specified in degrees
        counter-clockwise from true north. If the bearing is not specified, the map will rotate to
        true north. Additional options and keyword arguments can be provided to control the rotation.
        For more information, see https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#rotateto

        Args:
            bearing (float): The bearing to rotate to, in degrees counter-clockwise from true north.
            options (Dict[str, Any], optional): Additional options to control the rotation. Defaults to {}.
            **kwargs (Any): Additional keyword arguments to control the rotation.

        Returns:
            None
        """
        super().add_call("rotateTo", bearing, options, **kwargs)

    def open_geojson(self, **kwargs: Any) -> "widgets.FileUpload":
        """
        Creates a file uploader widget to upload a GeoJSON file. When a file is
        uploaded, it is written to a temporary file and added to the map.

        Args:
            **kwargs: Additional keyword arguments to pass to the add_geojson method.

        Returns:
            widgets.FileUpload: The file uploader widget.
        """

        import ipywidgets as widgets

        uploader = widgets.FileUpload(
            accept=".geojson",  # Accept GeoJSON files
            multiple=False,  # Only single file upload
            description="Open GeoJSON",
        )

        def on_upload(change):
            content = uploader.value[0]["content"]
            temp_file = temp_file_path(extension=".geojson")
            with open(temp_file, "wb") as f:
                f.write(content)
            self.add_geojson(temp_file, **kwargs)

        uploader.observe(on_upload, names="value")

        return uploader

    def pan_to(
        self,
        lnglat: List[float],
        options: Dict[str, Any] = {},
        **kwargs: Any,
    ) -> None:
        """
        Pans the map to a specified location.

        This function pans the map to the specified longitude and latitude coordinates.
        Additional options and keyword arguments can be provided to control the panning.
        For more information, see https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#panto

        Args:
            lnglat (List[float, float]): The longitude and latitude coordinates to pan to.
            options (Dict[str, Any], optional): Additional options to control the panning. Defaults to {}.
            **kwargs (Any): Additional keyword arguments to control the panning.

        Returns:
            None
        """
        super().add_call("panTo", lnglat, options, **kwargs)

    def set_pitch(self, pitch: float, **kwargs: Any) -> None:
        """
        Sets the pitch of the map.

        This function sets the pitch of the map to the specified value. The pitch is the
        angle of the camera measured in degrees where 0 is looking straight down, and 60 is
        looking towards the horizon. Additional keyword arguments can be provided to control
        the pitch. For more information, see https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#setpitch

        Args:
            pitch (float): The pitch value to set.
            **kwargs (Any): Additional keyword arguments to control the pitch.

        Returns:
            None
        """
        super().add_call("setPitch", pitch, **kwargs)

    def jump_to(self, options: Dict[str, Any] = {}, **kwargs: Any) -> None:
        """
        Jumps the map to a specified location.

        This function jumps the map to the specified location with the specified options.
        Additional keyword arguments can be provided to control the jump. For more information,
        see https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#jumpto

        Args:
            options (Dict[str, Any], optional): Additional options to control the jump. Defaults to {}.
            **kwargs (Any): Additional keyword arguments to control the jump.

        Returns:
            None
        """
        super().add_call("jumpTo", options, **kwargs)

    def _get_3d_terrain_style(
        self,
        satellite=True,
        exaggeration: float = 1,
        token: str = "MAPTILER_KEY",
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the 3D terrain style for the map.

        This function generates a style dictionary for the map that includes 3D terrain features.
        The terrain exaggeration and API key can be specified. If the API key is not provided,
        it will be retrieved using the specified token.

        Args:
            exaggeration (float, optional): The terrain exaggeration. Defaults to 1.
            token (str, optional): The token to use to retrieve the API key. Defaults to "MAPTILER_KEY".
            api_key (Optional[str], optional): The API key. If not provided, it will be retrieved using the token.

        Returns:
            Dict[str, Any]: The style dictionary for the map.

        Raises:
            ValueError: If the API key is not provided and cannot be retrieved using the token.
        """

        if api_key is None:
            api_key = get_env_var(token)

        if api_key is None:
            print("An API key is required to use the 3D terrain feature.")
            return "dark-matter"

        layers = []

        if satellite:
            layers.append({"id": "satellite", "type": "raster", "source": "satellite"})

        layers.append(
            {
                "id": "hills",
                "type": "hillshade",
                "source": "hillshadeSource",
                "layout": {"visibility": "visible"},
                "paint": {"hillshade-shadow-color": "#473B24"},
            }
        )

        style = {
            "version": 8,
            "sources": {
                "satellite": {
                    "type": "raster",
                    "tiles": [
                        "https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key="
                        + api_key
                    ],
                    "tileSize": 256,
                    "attribution": "&copy; MapTiler",
                    "maxzoom": 19,
                },
                "terrainSource": {
                    "type": "raster-dem",
                    "url": f"https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key={api_key}",
                    "tileSize": 256,
                },
                "hillshadeSource": {
                    "type": "raster-dem",
                    "url": f"https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key={api_key}",
                    "tileSize": 256,
                },
            },
            "layers": layers,
            "terrain": {"source": "terrainSource", "exaggeration": exaggeration},
        }

        return style

    def get_style(self):
        """
        Get the style of the map.

        Returns:
            Dict: The style of the map.
        """
        if self._style is not None:
            if isinstance(self._style, str):
                response = requests.get(self._style)
                style = response.json()
            elif isinstance(self._style, dict):
                style = self._style
            return style
        else:
            return {}

    def get_style_layers(self, return_ids=False, sorted=True) -> List[str]:
        """
        Get the names of the basemap layers.

        Returns:
            List[str]: The names of the basemap layers.
        """
        style = self.get_style()
        if "layers" in style:
            layers = style["layers"]
            if return_ids:
                ids = [layer["id"] for layer in layers]
                if sorted:
                    ids.sort()

                return ids
            else:
                return layers
        else:
            return []

    def find_style_layer(self, id: str) -> Optional[Dict]:
        """
        Searches for a style layer in the map's current style by its ID and returns it if found.

        Args:
            id (str): The ID of the style layer to find.

        Returns:
            Optional[Dict]: The style layer as a dictionary if found, otherwise None.
        """
        layers = self.get_style_layers()
        for layer in layers:
            if layer["id"] == id:
                return layer
        return None

    def zoom_to(self, zoom: float, options: Dict[str, Any] = {}, **kwargs: Any) -> None:
        """
        Zooms the map to a specified zoom level.

        This function zooms the map to the specified zoom level. Additional options and keyword
        arguments can be provided to control the zoom. For more information, see
        https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#zoomto

        Args:
            zoom (float): The zoom level to zoom to.
            options (Dict[str, Any], optional): Additional options to control the zoom. Defaults to {}.
            **kwargs (Any): Additional keyword arguments to control the zoom.

        Returns:
            None
        """
        super().add_call("zoomTo", zoom, options, **kwargs)

    def find_first_symbol_layer(self) -> Optional[Dict]:
        """
        Find the first symbol layer in the map's current style.

        Returns:
            Optional[Dict]: The first symbol layer as a dictionary if found, otherwise None.
        """
        layers = self.get_style_layers()
        for layer in layers:
            if layer["type"] == "symbol":
                return layer
        return None

    def add_text(
        self,
        text: str,
        fontsize: int = 20,
        fontcolor: str = "black",
        bold: bool = False,
        padding: str = "5px",
        bg_color: str = "white",
        border_radius: str = "5px",
        position: str = "bottom-right",
        **kwargs: Any,
    ) -> None:
        """
        Adds text to the map with customizable styling.

        This method allows adding a text widget to the map with various styling options such as font size, color,
        background color, and more. The text's appearance can be further customized using additional CSS properties
        passed through kwargs.

        Args:
            text (str): The text to add to the map.
            fontsize (int, optional): The font size of the text. Defaults to 20.
            fontcolor (str, optional): The color of the text. Defaults to "black".
            bold (bool, optional): If True, the text will be bold. Defaults to False.
            padding (str, optional): The padding around the text. Defaults to "5px".
            bg_color (str, optional): The background color of the text widget. Defaults to "white".
                To make the background transparent, set this to "transparent".
                To make the background half transparent, set this to "rgba(255, 255, 255, 0.5)".
            border_radius (str, optional): The border radius of the text widget. Defaults to "5px".
            position (str, optional): The position of the text widget on the map. Defaults to "bottom-right".
            **kwargs (Any): Additional CSS properties to apply to the text widget.

        Returns:
            None
        """
        from maplibre.controls import InfoBoxControl

        if bg_color == "transparent" and "box-shadow" not in kwargs:
            kwargs["box-shadow"] = "none"

        css_text = f"""font-size: {fontsize}px; color: {fontcolor};
        font-weight: {'bold' if bold else 'normal'}; padding: {padding};
        background-color: {bg_color}; border-radius: {border_radius};"""

        for key, value in kwargs.items():
            css_text += f" {key.replace('_', '-')}: {value};"

        control = InfoBoxControl(content=text, css_text=css_text)
        self.add_control(control, position=position)

    def add_html(
        self,
        html: str,
        bg_color: str = "white",
        position: str = "bottom-right",
        **kwargs: Union[str, int, float],
    ) -> None:
        """
        Add HTML content to the map.

        This method allows for the addition of arbitrary HTML content to the map, which can be used to display
        custom information or controls. The background color and position of the HTML content can be customized.

        Args:
            html (str): The HTML content to add.
            bg_color (str, optional): The background color of the HTML content. Defaults to "white".
                To make the background transparent, set this to "transparent".
                To make the background half transparent, set this to "rgba(255, 255, 255, 0.5)".
            position (str, optional): The position of the HTML content on the map. Can be one of "top-left",
                "top-right", "bottom-left", "bottom-right". Defaults to "bottom-right".
            **kwargs: Additional keyword arguments for future use.

        Returns:
            None
        """
        # Check if an HTML string contains local images and convert them to base64.
        html = check_html_string(html)
        self.add_text(html, position=position, bg_color=bg_color, **kwargs)

    def add_legend(
        self,
        title: str = "Legend",
        legend_dict: Optional[Dict[str, str]] = None,
        labels: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        fontsize: int = 15,
        bg_color: str = "white",
        position: str = "bottom-right",
        builtin_legend: Optional[str] = None,
        **kwargs: Union[str, int, float],
    ) -> None:
        """
        Adds a legend to the map.

        This method allows for the addition of a legend to the map. The legend can be customized with a title,
        labels, colors, and more. A built-in legend can also be specified.

        Args:
            title (str, optional): The title of the legend. Defaults to "Legend".
            legend_dict (Optional[Dict[str, str]], optional): A dictionary with legend items as keys and colors as values.
                If provided, `labels` and `colors` will be ignored. Defaults to None.
            labels (Optional[List[str]], optional): A list of legend labels. Defaults to None.
            colors (Optional[List[str]], optional): A list of colors corresponding to the labels. Defaults to None.
            fontsize (int, optional): The font size of the legend text. Defaults to 15.
            bg_color (str, optional): The background color of the legend. Defaults to "white".
                To make the background transparent, set this to "transparent".
                To make the background half transparent, set this to "rgba(255, 255, 255, 0.5)".
            position (str, optional): The position of the legend on the map. Can be one of "top-left",
                "top-right", "bottom-left", "bottom-right". Defaults to "bottom-right".
            builtin_legend (Optional[str], optional): The name of a built-in legend to use. Defaults to None.
            **kwargs: Additional keyword arguments for future use.

        Returns:
            None
        """
        import pkg_resources
        from .legends import builtin_legends

        pkg_dir = os.path.dirname(
            pkg_resources.resource_filename("geemap", "geemap.py")
        )
        legend_template = os.path.join(pkg_dir, "data/template/legend.html")

        if not os.path.exists(legend_template):
            print("The legend template does not exist.")
            return

        if labels is not None:
            if not isinstance(labels, list):
                print("The legend keys must be a list.")
                return
        else:
            labels = ["One", "Two", "Three", "Four", "etc"]

        if colors is not None:
            if not isinstance(colors, list):
                print("The legend colors must be a list.")
                return
            elif all(isinstance(item, tuple) for item in colors):
                try:
                    colors = [rgb_to_hex(x) for x in colors]
                except Exception as e:
                    print(e)
            elif all((item.startswith("#") and len(item) == 7) for item in colors):
                pass
            elif all((len(item) == 6) for item in colors):
                pass
            else:
                print("The legend colors must be a list of tuples.")
                return
        else:
            colors = [
                "#8DD3C7",
                "#FFFFB3",
                "#BEBADA",
                "#FB8072",
                "#80B1D3",
            ]

        if len(labels) != len(colors):
            print("The legend keys and values must be the same length.")
            return

        allowed_builtin_legends = builtin_legends.keys()
        if builtin_legend is not None:
            if builtin_legend not in allowed_builtin_legends:
                print(
                    "The builtin legend must be one of the following: {}".format(
                        ", ".join(allowed_builtin_legends)
                    )
                )
                return
            else:
                legend_dict = builtin_legends[builtin_legend]
                labels = list(legend_dict.keys())
                colors = list(legend_dict.values())

        if legend_dict is not None:
            if not isinstance(legend_dict, dict):
                print("The legend dict must be a dictionary.")
                return
            else:
                labels = list(legend_dict.keys())
                colors = list(legend_dict.values())
                if all(isinstance(item, tuple) for item in colors):
                    try:
                        colors = [rgb_to_hex(x) for x in colors]
                    except Exception as e:
                        print(e)

        allowed_positions = [
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
        ]
        if position not in allowed_positions:
            print(
                "The position must be one of the following: {}".format(
                    ", ".join(allowed_positions)
                )
            )
            return

        header = []
        content = []
        footer = []

        with open(legend_template) as f:
            lines = f.readlines()
            lines[3] = lines[3].replace("Legend", title)
            header = lines[:6]
            footer = lines[11:]

        for index, key in enumerate(labels):
            color = colors[index]
            if not color.startswith("#"):
                color = "#" + color
            item = "      <li><span style='background:{};'></span>{}</li>\n".format(
                color, key
            )
            content.append(item)

        legend_html = header + content + footer
        legend_text = "".join(legend_html)

        self.add_html(
            legend_text,
            fontsize=fontsize,
            bg_color=bg_color,
            position=position,
            **kwargs,
        )

    def add_colorbar(
        self,
        width: Optional[float] = 3.0,
        height: Optional[float] = 0.2,
        vmin: Optional[float] = 0,
        vmax: Optional[float] = 1.0,
        palette: Optional[List[str]] = None,
        vis_params: Optional[Dict[str, Union[str, float, int]]] = None,
        cmap: Optional[str] = "gray",
        discrete: Optional[bool] = False,
        label: Optional[str] = None,
        label_size: Optional[int] = 10,
        label_weight: Optional[str] = "normal",
        tick_size: Optional[int] = 8,
        bg_color: Optional[str] = "white",
        orientation: Optional[str] = "horizontal",
        dpi: Optional[Union[str, float]] = "figure",
        transparent: Optional[bool] = False,
        position: str = "bottom-right",
        **kwargs,
    ) -> str:
        """
        Add a colorbar to the map.

        This function uses matplotlib to generate a colorbar, saves it as a PNG file, and adds it to the map using
        the Map.add_html() method. The colorbar can be customized in various ways including its size, color palette,
        label, and orientation.

        Args:
            width (Optional[float]): Width of the colorbar in inches. Defaults to 3.0.
            height (Optional[float]): Height of the colorbar in inches. Defaults to 0.2.
            vmin (Optional[float]): Minimum value of the colorbar. Defaults to 0.
            vmax (Optional[float]): Maximum value of the colorbar. Defaults to 1.0.
            palette (Optional[List[str]]): List of colors or a colormap name for the colorbar. Defaults to None.
            vis_params (Optional[Dict[str, Union[str, float, int]]]): Visualization parameters as a dictionary.
            cmap (Optional[str]): Matplotlib colormap name. Defaults to "gray".
            discrete (Optional[bool]): Whether to create a discrete colorbar. Defaults to False.
            label (Optional[str]): Label for the colorbar. Defaults to None.
            label_size (Optional[int]): Font size for the colorbar label. Defaults to 10.
            label_weight (Optional[str]): Font weight for the colorbar label. Defaults to "normal".
            tick_size (Optional[int]): Font size for the colorbar tick labels. Defaults to 8.
            bg_color (Optional[str]): Background color for the colorbar. Defaults to "white".
            orientation (Optional[str]): Orientation of the colorbar ("vertical" or "horizontal"). Defaults to "horizontal".
            dpi (Optional[Union[str, float]]): Resolution in dots per inch. If 'figure', uses the figure's dpi value. Defaults to "figure".
            transparent (Optional[bool]): Whether the background is transparent. Defaults to False.
            position (str): Position of the colorbar on the map. Defaults to "bottom-right".
            **kwargs: Additional keyword arguments passed to matplotlib.pyplot.savefig().

        Returns:
            str: Path to the generated colorbar image.
        """

        if transparent:
            bg_color = "transparent"

        colorbar = save_colorbar(
            None,
            width,
            height,
            vmin,
            vmax,
            palette,
            vis_params,
            cmap,
            discrete,
            label,
            label_size,
            label_weight,
            tick_size,
            bg_color,
            orientation,
            dpi,
            transparent,
            show_colorbar=False,
        )

        html = f'<img src="{colorbar}">'

        self.add_html(html, bg_color=bg_color, position=position, **kwargs)

    def add_layer_control(
        self,
        layer_ids: Optional[List[str]] = None,
        theme: str = "default",
        css_text: Optional[str] = None,
        position: str = "top-left",
        bg_layers: Optional[Union[bool, List[str]]] = False,
    ) -> None:
        """
        Adds a layer control to the map.

        This function creates and adds a layer switcher control to the map, allowing users to toggle the visibility
        of specified layers. The appearance and functionality of the layer control can be customized with parameters
        such as theme, CSS styling, and position on the map.

        Args:
            layer_ids (Optional[List[str]]): A list of layer IDs to include in the control. If None, all layers
                in the map will be included. Defaults to None.
            theme (str): The theme for the layer switcher control. Can be "default" or other custom themes. Defaults to "default".
            css_text (Optional[str]): Custom CSS text for styling the layer control. If None, a default style will be applied.
                Defaults to None.
            position (str): The position of the layer control on the map. Can be "top-left", "top-right", "bottom-left",
                or "bottom-right". Defaults to "top-left".
            bg_layers (bool): If True, background layers will be included in the control. Defaults to False.

        Returns:
            None
        """
        from maplibre.controls import LayerSwitcherControl

        if layer_ids is None:
            layer_ids = list(self.layer_dict.keys())
            if layer_ids[0] == "background":
                layer_ids = layer_ids[1:]

        if isinstance(bg_layers, list):
            layer_ids = bg_layers + layer_ids
        elif bg_layers:
            background_ids = list(self.style_dict.keys())
            layer_ids = background_ids + layer_ids

        if css_text is None:
            css_text = "padding: 5px; border: 1px solid darkgrey; border-radius: 4px;"

        if len(layer_ids) > 0:

            control = LayerSwitcherControl(
                layer_ids=layer_ids,
                theme=theme,
                css_text=css_text,
            )
            self.add_control(control, position=position)

    def add_3d_buildings(
        self,
        name: str = "buildings",
        min_zoom: int = 15,
        values: List[int] = [0, 200, 400],
        colors: List[str] = ["lightgray", "royalblue", "lightblue"],
    ) -> None:
        """
        Adds a 3D buildings layer to the map.

        This function creates and adds a 3D buildings layer to the map using fill-extrusion. The buildings' heights
        are determined by the 'render_height' property, and their colors are interpolated based on specified values.
        The layer is only visible from a certain zoom level, specified by the 'min_zoom' parameter.

        Args:
            name (str): The name of the 3D buildings layer. Defaults to "buildings".
            min_zoom (int): The minimum zoom level at which the 3D buildings will start to be visible. Defaults to 15.
            values (List[int]): A list of height values (in meters) used for color interpolation. Defaults to [0, 200, 400].
            colors (List[str]): A list of colors corresponding to the 'values' list. Each color is applied to the
                building height range defined by the 'values'. Defaults to ["lightgray", "royalblue", "lightblue"].

        Raises:
            ValueError: If the lengths of 'values' and 'colors' lists do not match.

        Returns:
            None
        """

        MAPTILER_KEY = get_env_var("MAPTILER_KEY")
        source = {
            "url": f"https://api.maptiler.com/tiles/v3/tiles.json?key={MAPTILER_KEY}",
            "type": "vector",
        }

        if len(values) != len(colors):
            raise ValueError("The values and colors must have the same length.")

        value_color_pairs = []
        for i, value in enumerate(values):
            value_color_pairs.append(value)
            value_color_pairs.append(colors[i])

        layer = {
            "id": name,
            "source": "openmaptiles",
            "source-layer": "building",
            "type": "fill-extrusion",
            "min-zoom": min_zoom,
            "paint": {
                "fill-extrusion-color": [
                    "interpolate",
                    ["linear"],
                    ["get", "render_height"],
                ]
                + value_color_pairs,
                "fill-extrusion-height": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    15,
                    0,
                    16,
                    ["get", "render_height"],
                ],
                "fill-extrusion-base": [
                    "case",
                    [">=", ["get", "zoom"], 16],
                    ["get", "render_min_height"],
                    0,
                ],
            },
        }
        self.add_source("openmaptiles", source)
        self.add_layer(layer)

    def add_video(
        self,
        urls: Union[str, List[str]],
        coordinates: List[List[float]],
        layer_id: str = "video",
        before_id: Optional[str] = None,
    ) -> None:
        """
        Adds a video layer to the map.

        This method allows embedding a video into the map by specifying the video URLs and the geographical coordinates
        that the video should cover. The video will be stretched and fitted into the specified coordinates.

        Args:
            urls (Union[str, List[str]]): A single video URL or a list of video URLs. These URLs must be accessible
                from the client's location.
            coordinates (List[List[float]]): A list of four coordinates in [longitude, latitude] format, specifying
                the corners of the video. The coordinates order should be top-left, top-right, bottom-right, bottom-left.
            layer_id (str): The ID for the video layer. Defaults to "video".
            before_id (Optional[str]): The ID of an existing layer to insert the new layer before. If None, the layer
                will be added on top. Defaults to None.

        Returns:
            None
        """

        if isinstance(urls, str):
            urls = [urls]
        source = {
            "type": "video",
            "urls": urls,
            "coordinates": coordinates,
        }
        self.add_source("video_source", source)
        layer = {
            "id": layer_id,
            "type": "raster",
            "source": "video_source",
        }
        self.add_layer(layer, before_id=before_id)


class Container(v.Container):

    def __init__(self, host_map=None, *args, **kwargs):

        # Create the left column with the map
        left_col_layout = v.Col(
            cols=11, children=[], class_="pa-1"  # padding for consistent spacing
        )
        if host_map is not None:
            left_col_layout.children = [host_map]

        # Create the right column with some output
        right_col_layout = v.Col(
            cols=1,
            children=[v.Card(children=[v.CardText(children=["Output Content"])])],
            class_="pa-1",  # padding for consistent spacing
        )

        # Create a toggle button with an icon
        btn = v.Btn(
            children=[
                v.Icon(left=False, children=["mdi-layers"]),
            ],
            # class_='ma-1',
            v_model=False,
        )

        # Create the button toggle
        toggle = v.BtnToggle(v_model="toggle_exclusive", children=[btn])

        # Function to change column widths
        def change_column_widths(*args, **kwargs):
            if toggle.v_model == 0:
                left_col_layout.cols = 10
                right_col_layout.cols = 2
            else:
                left_col_layout.cols = 11
                right_col_layout.cols = 1

        # Observe changes in the v_model of the toggle button
        toggle.on_event("change", change_column_widths)

        # Update the right column to include the toggle button
        right_col_layout.children = [toggle]
        row = v.Row(
            class_="d-flex flex-wrap",
            children=[left_col_layout, right_col_layout],
            *args,
            **kwargs,
        )
        super().__init__(fluid=True, children=[row])


def construct_maptiler_style(style: str, api_key: Optional[str] = None) -> str:
    """
    Constructs a URL for a MapTiler style with an optional API key.

    This function generates a URL for accessing a specific MapTiler map style. If an API key is not provided,
    it attempts to retrieve one using a predefined method. If the request to MapTiler fails, it defaults to
    a "dark-matter" style.

    Args:
        style (str): The name of the MapTiler style to be accessed. It can be one of the following:
            aquarelle, backdrop, basic, bright, dataviz, landscape, ocean, openstreetmap, outdoor,
            satellite, streets, toner, topo, winter, etc.
        api_key (Optional[str]): An optional API key for accessing MapTiler services. If None, the function
            attempts to retrieve the API key using a predefined method. Defaults to None.

    Returns:
        str: The URL for the requested MapTiler style. If the request fails, returns a URL for the "dark-matter" style.

    Raises:
        requests.exceptions.RequestException: If the request to the MapTiler API fails.
    """

    if api_key is None:
        api_key = get_env_var("MAPTILER_KEY")

    url = f"https://api.maptiler.com/maps/{style}/style.json?key={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        print(
            "Failed to retrieve the MapTiler style. Defaulting to 'dark-matter' style."
        )
        url = "dark-matter"

    return url


def maptiler_3d_style(
    style="satellite",
    exaggeration: float = 1,
    tile_size: int = 512,
    tile_type: str = None,
    max_zoom: int = 24,
    hillshade: bool = True,
    token: str = "MAPTILER_KEY",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get the 3D terrain style for the map.

    This function generates a style dictionary for the map that includes 3D terrain features.
    The terrain exaggeration and API key can be specified. If the API key is not provided,
    it will be retrieved using the specified token.

    Args:
        style (str): The name of the MapTiler style to be accessed. It can be one of the following:
            aquarelle, backdrop, basic, bright, dataviz, hillshade, landscape, ocean, openstreetmap, outdoor,
            satellite, streets, toner, topo, winter, etc.
        exaggeration (float, optional): The terrain exaggeration. Defaults to 1.
        tile_size (int, optional): The size of the tiles. Defaults to 512.
        tile_type (str, optional): The type of the tiles. It can be one of the following:
            webp, png, jpg. Defaults to None.
        max_zoom (int, optional): The maximum zoom level. Defaults to 24.
        hillshade (bool, optional): Whether to include hillshade. Defaults to True.
        token (str, optional): The token to use to retrieve the API key. Defaults to "MAPTILER_KEY".
        api_key (Optional[str], optional): The API key. If not provided, it will be retrieved using the token.

    Returns:
        Dict[str, Any]: The style dictionary for the map.

    Raises:
        ValueError: If the API key is not provided and cannot be retrieved using the token.
    """

    if api_key is None:
        api_key = get_env_var(token)

    if api_key is None:
        print("An API key is required to use the 3D terrain feature.")
        return "dark-matter"

    if style == "terrain":
        style = "satellite"
    elif style == "hillshade":
        style = None

    if tile_type is None:

        image_types = {
            "aquarelle": "webp",
            "backdrop": "png",
            "basic": "png",
            "basic-v2": "png",
            "bright": "png",
            "bright-v2": "png",
            "dataviz": "png",
            "hybrid": "jpg",
            "landscape": "png",
            "ocean": "png",
            "openstreetmap": "jpg",
            "outdoor": "png",
            "outdoor-v2": "png",
            "satellite": "jpg",
            "toner": "png",
            "toner-v2": "png",
            "topo": "png",
            "topo-v2": "png",
            "winter": "png",
            "winter-v2": "png",
        }
        if style in image_types:
            tile_type = image_types[style]
        else:
            tile_type = "png"

    layers = []

    if isinstance(style, str):
        layers.append({"id": style, "type": "raster", "source": style})

    if hillshade:
        layers.append(
            {
                "id": "hillshade",
                "type": "hillshade",
                "source": "hillshadeSource",
                "layout": {"visibility": "visible"},
                "paint": {"hillshade-shadow-color": "#473B24"},
            }
        )

    if style == "ocean":
        sources = {
            "terrainSource": {
                "type": "raster-dem",
                "url": f"https://api.maptiler.com/tiles/ocean-rgb/tiles.json?key={api_key}",
                "tileSize": tile_size,
            },
            "hillshadeSource": {
                "type": "raster-dem",
                "url": f"https://api.maptiler.com/tiles/ocean-rgb/tiles.json?key={api_key}",
                "tileSize": tile_size,
            },
        }
    else:
        sources = {
            "terrainSource": {
                "type": "raster-dem",
                "url": f"https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key={api_key}",
                "tileSize": tile_size,
            },
            "hillshadeSource": {
                "type": "raster-dem",
                "url": f"https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key={api_key}",
                "tileSize": tile_size,
            },
        }
    if isinstance(style, str):
        sources[style] = {
            "type": "raster",
            "tiles": [
                "https://api.maptiler.com/maps/"
                + style
                + "/{z}/{x}/{y}."
                + tile_type
                + "?key="
                + api_key
            ],
            "tileSize": tile_size,
            "attribution": "&copy; MapTiler",
            "maxzoom": max_zoom,
        }

    style = {
        "version": 8,
        "sources": sources,
        "layers": layers,
        "terrain": {"source": "terrainSource", "exaggeration": exaggeration},
    }

    return style
