"""
This module defines here-map-widget-for-jupyter as backend for geemap library.
For more details about Here Map Widget for Jupyter
please check: https://github.com/heremaps/here-map-widget-for-jupyter
"""
import ee
import os
import json
import random
import requests
import ipywidgets as widgets
from box import Box
from .basemaps import xyz_to_heremap
from .common import *
from . import examples

try:
    import here_map_widget
except ImportError:
    raise ImportError(
        'This module requires the hermap package. Please install it using "pip install here-map-widget-for-jupyter".'
    )


from here_map_widget import (
    FullscreenControl,
    MeasurementControl,
    ScaleBar,
    ZoomControl,
    ImageTileProvider,
    MapSettingsControl,
    TileLayer,
    GeoJSON,
    WidgetControl,
    LayersControl,
)


basemaps = Box(xyz_to_heremap(), frozen_box=True)


class Map(here_map_widget.Map):
    """
    The Map class inherits here_map_widget.Map. The arguments you can pass to the Map can be found
    at https://here-map-widget-for-jupyter.readthedocs.io/en/latest/api_reference/map.html.

    Returns:
        object: here_map_widget map object.
    """

    def __init__(self, api_key=None, **kwargs):

        # Authenticates Earth Engine and initializes an Earth Engine session
        if "ee_initialize" not in kwargs.keys():
            kwargs["ee_initialize"] = True

        if kwargs["ee_initialize"]:
            ee_initialize()

        kwargs.pop("ee_initialize")

        if api_key is None:
            api_key = os.environ.get("HEREMAPS_API_KEY")
            if api_key is None:
                raise ValueError(
                    "Please provide an api_key or set the HEREMAPS_API_KEY environment variable."
                )

        if "center" not in kwargs:
            kwargs["center"] = [20, 0]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 2

        if "basemap" in kwargs:
            kwargs["basemap"] = basemaps[kwargs["basemap"]]

        super().__init__(api_key=api_key, **kwargs)
        self.baseclass = "here_map_widget"

        if "height" not in kwargs:
            self.layout.height = "600px"
        else:
            self.layout.height = kwargs["height"]

        if "width" in kwargs:
            self.layout.width = kwargs["width"]

        if kwargs.get("layers_control"):
            self.add_control(LayersControl(alignment="RIGHT_TOP"))

        if "zoom_control" not in kwargs:
            kwargs["zoom_control"] = True

        if kwargs["zoom_control"]:
            self.add_control(ZoomControl(alignment="LEFT_TOP"))
        if "fullscreen_control" not in kwargs:
            kwargs["fullscreen_control"] = True
        if kwargs["fullscreen_control"]:
            self.add_control(FullscreenControl(alignment="LEFT_TOP"))

        if kwargs.get("measure_control"):
            self.add_control(MeasurementControl(alignment="LEFT_TOP"))
        if "scale_control" not in kwargs:
            kwargs["scale_control"] = True
        if kwargs["scale_control"]:
            self.add_control(ScaleBar(alignment="LEFT_BOTTOM"))

    def set_center(self, lon, lat, zoom=None):
        """Centers the map view at a given coordinates with the given zoom level.

        Args:
            lon (float): The longitude of the center, in degrees.
            lat (float): The latitude of the center, in degrees.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to None.
        """
        self.center = (lat, lon)
        if zoom is not None:
            self.zoom = zoom

    def zoom_to_bounds(self, bounds):
        """Zooms to a bounding box in the form of [south, west, north, east].

        Args:
            bounds (list | tuple): A list/tuple containing south, west, north, east values for the bounds.
        """
        self.bounds = tuple(bounds)

    def zoom_to_gdf(self, gdf):
        """Zooms to the bounding box of a GeoPandas GeoDataFrame.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
        """
        bounds = gdf.total_bounds
        self.zoom_to_bounds(bounds)

    def add_basemap(self, basemap="HYBRID"):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from basemaps. Defaults to 'HYBRID'.
        """
        import xyzservices

        try:
            if isinstance(basemap, xyzservices.TileProvider):
                name = basemap.name
                url = basemap.build_url()
                attribution = basemap.attribution
                if "max_zoom" in basemap.keys():
                    max_zoom = basemap["max_zoom"]
                else:
                    max_zoom = 22
                layer = here_map_widget.TileLayer(
                    provider=here_map_widget.ImageTileProvider(
                        url=url, attribution=attribution, name=name, max_zoom=max_zoom
                    )
                )
                self.basemap = layer
            elif basemap in basemaps and basemaps[basemap] not in self.layers:
                self.basemap = basemaps[basemap]
        except Exception:
            raise ValueError(
                "Basemap can only be one of the following:\n  {}".format(
                    "\n  ".join(basemaps.keys())
                )
            )

    def add_tile_layer(
        self,
        url,
        name,
        attribution,
        opacity=1.0,
        **kwargs,
    ):
        """Adds a TileLayer to the map.

        Args:
            url (str): The URL of the tile layer.
            name (str): The layer name to use for the layer.
            attribution (str): The attribution to use.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
        """
        try:
            if "style" in kwargs:
                style = kwargs.pop("style")
            else:
                style = {}
            provider = ImageTileProvider(
                url=url, opacity=opacity, attribution=attribution, **kwargs
            )
            tile_layer = TileLayer(provider=provider, name=name, style=style)
            self.add_layer(tile_layer)
        except Exception as e:
            print("Failed to add the specified TileLayer.")
            raise Exception(e)

    def add_ee_layer(
        self, ee_object, vis_params={}, name=None, shown=True, opacity=1.0, **kwargs
    ):
        """Adds a given EE object to the map as a layer.

        Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to {}.
            name (str, optional): The name of the layer. Defaults to 'Layer N'.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """
        from box import Box

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
            err_str = "\n\nThe image argument in 'addLayer' function must be an instance of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
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
            if isinstance(vis_params["palette"], Box):
                try:
                    vis_params["palette"] = vis_params["palette"]["default"]
                except Exception as e:
                    print("The provided palette is invalid.")
                    raise Exception(e)
            elif isinstance(vis_params["palette"], str):
                vis_params["palette"] = check_cmap(vis_params["palette"])
            elif not isinstance(vis_params["palette"], list):
                raise ValueError(
                    "The palette must be a list of colors or a string or a Box object."
                )

        map_id_dict = ee.Image(image).getMapId(vis_params)
        url = map_id_dict["tile_fetcher"].url_format
        self.add_tile_layer(
            url, name=name, attribution="Google Earth Engine", opacity=opacity, **kwargs
        )

    addLayer = add_ee_layer

    def add_layer_control(self, **kwargs):
        """Adds a layer control to the map.

        Args:
            **kwargs: Arbitrary keyword arguments.
        """
        layers = [{"label": layer.name, "layer": layer} for layer in self.layers]
        settings = MapSettingsControl(layers=layers, **kwargs)
        self.add_control(settings)

    addLayerControl = add_layer_control

    def add_geojson(
        self,
        in_geojson,
        layer_name="Untitled",
        style=None,
        hover_style=None,
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
        point_style=None,
        default_popup=False,
    ):
        """Adds a GeoJSON file to the map.

        Args:
            in_geojson (str | dict): The file path or http URL to the input GeoJSON or a dictionary containing the geojson.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            point_style (dict, optional): style dictionary for Points in GeoJSON. If not provided default Markers will be shown.
            default_popup: If set to True this will disable info_mode and default popup will be shown on clicking the feature.
        Raises:
            FileNotFoundError: The provided GeoJSON file could not be found.
        """

        try:
            if isinstance(in_geojson, str):
                if in_geojson.startswith("http"):
                    data = requests.get(in_geojson).json()
                else:
                    in_geojson = os.path.abspath(in_geojson)
                    if not os.path.exists(in_geojson):
                        raise FileNotFoundError(
                            "The provided GeoJSON file could not be found."
                        )

                    with open(in_geojson, encoding="utf-8") as f:
                        data = json.load(f)
            elif isinstance(in_geojson, dict):
                data = in_geojson
            else:
                raise TypeError("The input geojson must be a type of str or dict.")
        except Exception as e:
            raise Exception(e)

        if not style:
            style = {
                "strokeColor": "black",
                "lineWidth": 1,
            }
        else:
            style.setdefault("lineWidth", 1)

        if not hover_style:
            hover_style = {
                "fillColor": random.choice(fill_colors)
                if fill_colors
                else ["rgba(0,0,0,0.5)"],
                "strokeColor": "black",
                "lineWidth": style["lineWidth"] + 1,
            }

        toolbar_button = widgets.ToggleButton(
            value=True,
            tooltip="Toolbar",
            icon="info",
            layout=widgets.Layout(
                width="28px", height="28px", padding="0px 0px 0px 4px"
            ),
        )

        close_button = widgets.ToggleButton(
            value=False,
            tooltip="Close the tool",
            icon="times",
            # button_style="primary",
            layout=widgets.Layout(
                height="28px", width="28px", padding="0px 0px 0px 4px"
            ),
        )

        html = widgets.HTML()
        html.layout.margin = "0px 10px 0px 10px"
        html.layout.max_height = "250px"
        html.layout.max_width = "250px"

        output_widget = widgets.VBox(
            [widgets.HBox([toolbar_button, close_button]), html]
        )
        info_control = WidgetControl(widget=output_widget, position="bottomright")

        if not default_popup and info_mode in ["on_hover", "on_click"]:
            self.add_control(info_control)

        def _toolbar_btn_click(change):
            if change["new"]:
                close_button.value = False
                output_widget.children = [
                    widgets.VBox([widgets.HBox([toolbar_button, close_button]), html])
                ]
            else:
                output_widget.children = [widgets.HBox([toolbar_button, close_button])]

        toolbar_button.observe(_toolbar_btn_click, "value")

        def _close_btn_click(change):
            if change["new"]:
                toolbar_button.value = False
                if info_control in self.controls:
                    self.remove_control(info_control)
                output_widget.close()

        close_button.observe(_close_btn_click, "value")

        def _update_html(feature, **_):

            value = [
                "<h5><b>{}: </b>{}</h5>".format(prop, feature["properties"][prop])
                for prop in feature["properties"].keys()
            ][:-1]

            value = """{}""".format("".join(value))
            html.value = value

        geojson = GeoJSON(
            data=data,
            style=style if style else {},
            hover_style=hover_style if hover_style else {},
            style_callback=style_callback,
            name=layer_name,
            point_style=point_style if point_style else {},
            show_bubble=default_popup,
        )

        if not default_popup:
            if info_mode == "on_hover":
                geojson.on_hover(_update_html)
            elif info_mode == "on_click":
                geojson.on_click(_update_html)

        self.add_layer(geojson)

    def add_shp(
        self,
        in_shp,
        layer_name="Untitled",
        style=None,
        hover_style=None,
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
        point_style=None,
        default_popup=False,
    ):
        """Adds a shapefile to the map.

        Args:
            in_shp (str): The input file path to the shapefile.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            point_style (dict, optional): style dictionary for Points in GeoJSON. If not provided default Markers will be shown.
            default_popup: If set to True this will disable info_mode and default popup will be shown on clicking the feature.

        Raises:
            FileNotFoundError: The provided shapefile could not be found.
        """
        in_shp = os.path.abspath(in_shp)
        if not os.path.exists(in_shp):
            raise FileNotFoundError("The provided shapefile could not be found.")

        geojson = shp_to_geojson(in_shp)
        self.add_geojson(
            in_geojson=geojson,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
            point_style=point_style,
            default_popup=default_popup,
        )

    def add_gdf(
        self,
        gdf,
        layer_name="Untitled",
        style=None,
        hover_style=None,
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
        zoom_to_layer=True,
        point_style=None,
        default_popup=False,
    ):
        """Adds a GeoJSON file to the map.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            zoom_to_layer (bool, optional): Whether to zoom to the layer.
            point_style (dict, optional): style dictionary for Points in GeoJSON. If not provided default Markers will be shown.
            default_popup: If set to True this will disable info_mode and default popup will be shown on clicking the feature.
        """
        data = gdf_to_geojson(gdf, epsg="4326")
        self.add_geojson(
            in_geojson=data,
            layer_name=layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
            point_style=point_style,
            default_popup=default_popup,
        )
        if zoom_to_layer:
            import numpy as np

            bounds = gdf.to_crs(epsg="4326").bounds
            west = np.min(bounds["minx"])
            south = np.min(bounds["miny"])
            east = np.max(bounds["maxx"])
            north = np.max(bounds["maxy"])
            print((south, west, north, east))
            self.bounds = (south, west, north, east)

    def add_kml(
        self,
        in_kml,
        layer_name="Untitled",
        style=None,
        hover_style=None,
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
        point_style=None,
        default_popup=False,
    ):
        """Adds a GeoJSON file to the map.

        Args:
            in_kml (str): The input file path to the KML.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            point_style (dict, optional): style dictionary for Points in GeoJSON. If not provided default Markers will be shown.
            default_popup: If set to True this will disable info_mode and default popup will be shown on clicking the feature.

        Raises:
            FileNotFoundError: The provided KML file could not be found.
        """

        in_kml = os.path.abspath(in_kml)
        if not os.path.exists(in_kml):
            raise FileNotFoundError("The provided KML file could not be found.")
        self.add_vector(
            in_kml,
            layer_name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            info_mode=info_mode,
            point_style=point_style,
            default_popup=default_popup,
        )

    def add_vector(
        self,
        filename,
        layer_name="Untitled",
        bbox=None,
        mask=None,
        rows=None,
        style=None,
        hover_style=None,
        style_callback=None,
        fill_colors=None,
        info_mode="on_hover",
        point_style=None,
        default_popup=False,
        **kwargs,
    ):
        """Adds any geopandas-supported vector dataset to the map.

        Args:
            filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
            layer_name (str, optional): The layer name to use. Defaults to "Untitled".
            bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
            mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter for features that intersect with the given dict-like geojson geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox. Defaults to None.
            rows (int or slice, optional): Load in specific rows by passing an integer (first n rows) or a slice() object.. Defaults to None.
            style (dict, optional): A dictionary specifying the style to be used. Defaults to {}.
            hover_style (dict, optional): Hover style dictionary. Defaults to {}.
            style_callback (function, optional): Styling function that is called for each feature, and should return the feature style. This styling function takes the feature as argument. Defaults to None.
            fill_colors (list, optional): The random colors to use for filling polygons. Defaults to ["black"].
            info_mode (str, optional): Displays the attributes by either on_hover or on_click. Any value other than "on_hover" or "on_click" will be treated as None. Defaults to "on_hover".
            point_style (dict, optional): style dictionary for Points in GeoJSON. If not provided default Markers will be shown.
            default_popup: If set to True this will disable info_mode and default popup will be shown on clicking the feature.

        """
        if not filename.startswith("http"):
            filename = os.path.abspath(filename)

        ext = os.path.splitext(filename)[1].lower()
        if ext == ".shp":
            self.add_shp(
                filename,
                layer_name,
                style,
                hover_style,
                style_callback,
                fill_colors,
                info_mode,
                point_style,
                default_popup,
            )
        elif ext in [".json", ".geojson"]:
            self.add_geojson(
                in_geojson=filename,
                layer_name=layer_name,
                style=style,
                hover_style=hover_style,
                style_callback=style_callback,
                fill_colors=fill_colors,
                info_mode=info_mode,
                point_style=point_style,
                default_popup=default_popup,
            )
        else:
            geojson = vector_to_geojson(
                filename,
                bbox=bbox,
                mask=mask,
                rows=rows,
                epsg="4326",
                **kwargs,
            )

            self.add_geojson(
                in_geojson=geojson,
                layer_name=layer_name,
                style=style,
                hover_style=hover_style,
                style_callback=style_callback,
                fill_colors=fill_colors,
                info_mode=info_mode,
                point_style=point_style,
                default_popup=default_popup,
            )

    def to_html(
        self,
        filename=None,
        title="My Map",
        width="100%",
        height="880px",
        **kwargs,
    ):
        """Saves the map as an HTML file.

        Args:
            filename (str, optional): The output file path to the HTML file.
            title (str, optional): The title of the HTML file. Defaults to 'My Map'.
            width (str, optional): The width of the map in pixels or percentage. Defaults to '100%'.
            height (str, optional): The height of the map in pixels. Defaults to '880px'.

        """
        try:
            from ipywidgets.embed import embed_minimal_html

            save = True
            if filename is not None:
                if not filename.endswith(".html"):
                    raise ValueError("The output file extension must be html.")
                filename = os.path.abspath(filename)
                out_dir = os.path.dirname(filename)
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
            else:
                filename = os.path.abspath(random_string() + ".html")
                save = False

            before_width = self.layout.width
            before_height = self.layout.height

            if not isinstance(width, str):
                print("width must be a string.")
                return
            elif width.endswith("px") or width.endswith("%"):
                pass
            else:
                print("width must end with px or %")
                return

            if not isinstance(height, str):
                print("height must be a string.")
                return
            elif not height.endswith("px"):
                print("height must end with px")
                return

            self.layout.width = width
            self.layout.height = height

            embed_minimal_html(filename, views=[self], title=title, **kwargs)

            self.layout.width = before_width
            self.layout.height = before_height

            if not save:
                out_html = ""
                with open(filename) as f:
                    lines = f.readlines()
                    out_html = "".join(lines)
                os.remove(filename)
                return out_html

        except Exception as e:
            raise Exception(e)

    def to_streamlit(
        self, width=700, height=500, responsive=True, scrolling=False, **kwargs
    ):
        """Renders map figure in a Streamlit app.

        Args:
            width (int, optional): Width of the map. Defaults to 700.
            height (int, optional): Height of the map. Defaults to 500.
            responsive (bool, optional): If True, the map will be responsive. Defaults to True.
            scrolling (bool, optional): If True, show a scrollbar when the content is larger than the iframe. Otherwise, do not show a scrollbar. Defaults to False.

        Returns:
            streamlit.components: components.html object.
        """

        try:
            import streamlit as st
            import streamlit.components.v1 as components

            if responsive:
                make_map_responsive = """
                <style>
                [title~="st.iframe"] { width: 100%}
                </style>
                """
                st.markdown(make_map_responsive, unsafe_allow_html=True)
            return components.html(
                self.to_html(), width=width, height=height, scrolling=scrolling
            )

        except Exception as e:
            raise Exception(e)
