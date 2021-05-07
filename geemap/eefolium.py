""" This module extends the folium Map class. It is designed to be used in Google Colab, as Google Colab currently does not support ipyleaflet.
"""
import os
import ee
import folium
from folium import plugins
from .common import *
from .conversion import *
from .legends import builtin_legends


# More WMS basemaps can be found at https://viewer.nationalmap.gov/services/
ee_basemaps = {
    "ROADMAP": folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Maps",
        overlay=True,
        control=True,
    ),
    "SATELLITE": folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        overlay=True,
        control=True,
    ),
    "TERRAIN": folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Terrain",
        overlay=True,
        control=True,
    ),
    "HYBRID": folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        overlay=True,
        control=True,
    ),
    "ESRI": folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Satellite",
        overlay=True,
        control=True,
    ),
    "Esri Ocean": folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Ocean",
        overlay=True,
        control=True,
    ),
    "Esri Satellite": folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Satellite",
        overlay=True,
        control=True,
    ),
    "Esri Standard": folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Standard",
        overlay=True,
        control=True,
    ),
    "Esri Terrain": folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Terrain",
        overlay=True,
        control=True,
    ),
    "Esri Transportation": folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Transportation",
        overlay=True,
        control=True,
    ),
    "Esri Topo World": folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Topo World",
        overlay=True,
        control=True,
    ),
    "Esri National Geographic": folium.TileLayer(
        tiles="http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri National Geographic",
        overlay=True,
        control=True,
    ),
    "Esri Shaded Relief": folium.TileLayer(
        tiles="https://services.arcgisonline.com/arcgis/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Shaded Relief",
        overlay=True,
        control=True,
    ),
    "Esri Physical Map": folium.TileLayer(
        tiles="https://services.arcgisonline.com/arcgis/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Esri Physical Map",
        overlay=True,
        control=True,
    ),
    "Bing VirtualEarth": folium.TileLayer(
        tiles="http://ecn.t3.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1",
        attr="Microsoft",
        name="Bing VirtualEarth",
        overlay=True,
        control=True,
    ),
    "3DEP Elevation": folium.WmsTileLayer(
        url="https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WMSServer?",
        layers="3DEPElevation:None",
        attr="USGS",
        name="3DEP Elevation",
        overlay=True,
        control=True,
    ),
    "NAIP Imagery": folium.WmsTileLayer(
        url="https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?",
        layers="0",
        attr="USGS",
        name="NAIP Imagery",
        overlay=True,
        control=True,
    ),
}


class Map(folium.Map):
    """The Map class inherits from folium.Map. By default, the Map will add Google Maps as the basemap. Set add_google_map = False to use OpenStreetMap as the basemap.

    Returns:
        object: folium map object.
    """

    def __init__(self, **kwargs):

        import logging

        logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

        if "ee_initialize" not in kwargs.keys():
            kwargs["ee_initialize"] = True

        if kwargs["ee_initialize"]:
            ee_initialize()

        # Default map center location and zoom level
        latlon = [40, -100]
        zoom = 4

        # Interchangeable parameters between ipyleaflet and folium
        if "center" in kwargs.keys():
            kwargs["location"] = kwargs["center"]
            kwargs.pop("center")
        if "location" in kwargs.keys():
            latlon = kwargs["location"]
        else:
            kwargs["location"] = latlon

        if "zoom" in kwargs.keys():
            kwargs["zoom_start"] = kwargs["zoom"]
            kwargs.pop("zoom")
        if "zoom_start" in kwargs.keys():
            zoom = kwargs["zoom_start"]
        else:
            kwargs["zoom_start"] = zoom

        if "add_google_map" not in kwargs.keys() and "basemap" not in kwargs.keys():
            kwargs["add_google_map"] = True
        if "plugin_LatLngPopup" not in kwargs.keys():
            kwargs["plugin_LatLngPopup"] = True
        if "plugin_Fullscreen" not in kwargs.keys():
            kwargs["plugin_Fullscreen"] = True
        if "plugin_Draw" not in kwargs.keys():
            kwargs["plugin_Draw"] = False
        if "Draw_export" not in kwargs.keys():
            kwargs["Draw_export"] = True
        if "plugin_MiniMap" not in kwargs.keys():
            kwargs["plugin_MiniMap"] = False
        if "plugin_LayerControl" not in kwargs.keys():
            kwargs["plugin_LayerControl"] = False

        super().__init__(**kwargs)
        self.baseclass = "folium"

        if kwargs.get("add_google_map"):
            ee_basemaps["ROADMAP"].add_to(self)
        if kwargs.get("basemap"):
            ee_basemaps[kwargs.get("basemap")].add_to(self)
        if kwargs.get("plugin_LatLngPopup"):
            folium.LatLngPopup().add_to(self)
        if kwargs.get("plugin_Fullscreen"):
            plugins.Fullscreen().add_to(self)
        if kwargs.get("plugin_Draw"):
            plugins.Draw(export=kwargs.get("Draw_export")).add_to(self)
        if kwargs.get("plugin_MiniMap"):
            plugins.MiniMap().add_to(self)
        if kwargs.get("plugin_LayerControl"):
            folium.LayerControl().add_to(self)

        self.fit_bounds([latlon, latlon], max_zoom=zoom)

    def setOptions(self, mapTypeId="HYBRID", styles={}, types=[]):
        """Adds Google basemap to the map.

        Args:
            mapTypeId (str, optional): A mapTypeId to set the basemap to. Can be one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN" to select one of the standard Google Maps API map types. Defaults to 'HYBRID'.
            styles ([type], optional): A dictionary of custom MapTypeStyle objects keyed with a name that will appear in the map's Map Type Controls. Defaults to None.
            types ([type], optional): A list of mapTypeIds to make available. If omitted, but opt_styles is specified, appends all of the style keys to the standard Google Maps API map types.. Defaults to None.
        """
        try:
            ee_basemaps[mapTypeId].add_to(self)
        except Exception:
            raise Exception(
                "Basemap can only be one of the following: {}".format(
                    ", ".join(ee_basemaps.keys())
                )
            )

    set_options = setOptions

    def add_basemap(self, basemap="HYBRID"):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from ee_basemaps. Defaults to 'HYBRID'.
        """
        try:
            ee_basemaps[basemap].add_to(self)
        except Exception:
            raise Exception(
                "Basemap can only be one of the following: {}".format(
                    ", ".join(ee_basemaps.keys())
                )
            )

    def add_layer(
        self,
        ee_object,
        vis_params={},
        name="Layer untitled",
        shown=True,
        opacity=1.0,
        **kwargs,
    ):
        """Adds a given EE object to the map as a layer.

        Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to {}.
            name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """

        from box import Box

        image = None

        if (
            not isinstance(ee_object, ee.Image)
            and not isinstance(ee_object, ee.ImageCollection)
            and not isinstance(ee_object, ee.FeatureCollection)
            and not isinstance(ee_object, ee.Feature)
            and not isinstance(ee_object, ee.Geometry)
        ):
            err_str = "\n\nThe image argument in 'addLayer' function must be an instace of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
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

        if "palette" in vis_params and isinstance(vis_params["palette"], Box):
            try:
                vis_params["palette"] = vis_params["palette"]["default"]
            except Exception as e:
                print("The provided palette is invalid.")
                raise Exception(e)

        map_id_dict = ee.Image(image).getMapId(vis_params)

        # if a layer starts with a number, add "Layer" to name.
        if name[0].isdigit():
            name = "Layer " + name

        folium.raster_layers.TileLayer(
            tiles=map_id_dict["tile_fetcher"].url_format,
            attr="Google Earth Engine",
            name=name,
            overlay=True,
            control=True,
            show=shown,
            opacity=opacity,
            **kwargs,
        ).add_to(self)

    addLayer = add_layer

    def _repr_mimebundle_(self, include, exclude, **kwargs):
        """Adds Layer control to the map. Referece: https://ipython.readthedocs.io/en/stable/config/integrating.html#MyObject._repr_mimebundle_

        Args:
            include ([type]): [description]
            exclude ([type]): [description]
        """
        self.add_layer_control()

    def set_center(self, lon, lat, zoom=10):
        """Centers the map view at a given coordinates with the given zoom level.

        Args:
            lon (float): The longitude of the center, in degrees.
            lat (float): The latitude of the center, in degrees.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to 10.
        """
        self.fit_bounds([[lat, lon], [lat, lon]], max_zoom=zoom)

    setCenter = set_center

    def center_object(self, ee_object, zoom=10):
        """Centers the map view on a given object.

        Args:
            ee_object (Element|Geometry): An Earth Engine object to center on - a geometry, image or feature.
            zoom (int, optional): The zoom level, from 1 to 24. Defaults to 10.
        """
        lat = 0
        lon = 0

        if isinstance(ee_object, ee.geometry.Geometry):
            centroid = ee_object.centroid()
            lon, lat = centroid.getInfo()["coordinates"]
            bounds = [[lat, lon], [lat, lon]]
        elif isinstance(ee_object, ee.featurecollection.FeatureCollection):
            centroid = ee_object.geometry().centroid()
            lon, lat = centroid.getInfo()["coordinates"]
            bounds = [[lat, lon], [lat, lon]]
        elif isinstance(ee_object, ee.image.Image):
            geometry = ee_object.geometry()
            coordinates = geometry.getInfo()["coordinates"][0]
            bounds = [coordinates[0][::-1], coordinates[2][::-1]]
        elif isinstance(ee_object, ee.imagecollection.ImageCollection):
            geometry = ee_object.geometry()
            coordinates = geometry.getInfo()["coordinates"][0]
            bounds = [coordinates[0][::-1], coordinates[2][::-1]]
        else:
            bounds = [[0, 0], [0, 0]]

        self.fit_bounds(bounds, max_zoom=zoom)

    centerObject = center_object

    def set_control_visibility(
        self, layerControl=True, fullscreenControl=True, latLngPopup=True
    ):
        """Sets the visibility of the controls on the map.

        Args:
            layerControl (bool, optional): Whether to show the control that allows the user to toggle layers on/off. Defaults to True.
            fullscreenControl (bool, optional): Whether to show the control that allows the user to make the map full-screen. Defaults to True.
            latLngPopup (bool, optional): Whether to show the control that pops up the Lat/lon when the user clicks on the map. Defaults to True.
        """
        if layerControl:
            folium.LayerControl().add_to(self)
        if fullscreenControl:
            plugins.Fullscreen().add_to(self)
        if latLngPopup:
            folium.LatLngPopup().add_to(self)

    setControlVisibility = set_control_visibility

    def add_layer_control(self):
        """Adds layer control to the map."""
        layer_ctrl = False
        for item in self.to_dict()["children"]:
            if item.startswith("layer_control"):
                layer_ctrl = True
                break
        if not layer_ctrl:
            folium.LayerControl().add_to(self)

    addLayerControl = add_layer_control

    def add_wms_layer(
        self,
        url,
        layers,
        name=None,
        attribution="",
        overlay=True,
        control=True,
        shown=True,
        format="image/png",
        transparent=False,
        version="1.1.1",
        styles="",
        **kwargs,
    ):

        """Add a WMS layer to the map.

        Args:
            url (str): The URL of the WMS web service.
            layers (str): Comma-separated list of WMS layers to show.
            name (str, optional): The layer name to use on the layer control. Defaults to None.
            attribution (str, optional): The attribution of the data layer. Defaults to ''.
            overlay (str, optional): Allows overlay. Defaults to True.
            control (str, optional): Adds the layer to the layer control. Defaults to True.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            format (str, optional): WMS image format (use ‘image/png’ for layers with transparency). Defaults to 'image/png'.
            transparent (bool, optional): Whether the layer shall allow transparency. Defaults to False.
            version (str, optional): Version of the WMS service to use. Defaults to "1.1.1".
            styles (str, optional): Comma-separated list of WMS styles. Defaults to "".
        """
        try:
            folium.raster_layers.WmsTileLayer(
                url=url,
                layers=layers,
                name=name,
                attr=attribution,
                overlay=overlay,
                control=control,
                show=shown,
                styles=styles,
                fmt=format,
                transparent=transparent,
                version=version,
                **kwargs,
            ).add_to(self)
        except Exception:
            raise Exception("Failed to add the specified WMS TileLayer.")

    def add_tile_layer(
        self,
        tiles="OpenStreetMap",
        name="Untitled",
        attribution=".",
        overlay=True,
        control=True,
        shown=True,
        opacity=1.0,
        API_key=None,
        **kwargs,
    ):
        """Add a XYZ tile layer to the map.

        Args:
            tiles (str): The URL of the XYZ tile service.
            name (str, optional): The layer name to use on the layer control. Defaults to 'Untitled'.
            attribution (str, optional): The attribution of the data layer. Defaults to '.'.
            overlay (str, optional): Allows overlay. Defaults to True.
            control (str, optional): Adds the layer to the layer control. Defaults to True.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): Sets the opacity for the layer.
            API_key (str, optional): – API key for Cloudmade or Mapbox tiles. Defaults to True.
        """

        try:
            folium.raster_layers.TileLayer(
                tiles=tiles,
                name=name,
                attr=attribution,
                overlay=overlay,
                control=control,
                show=shown,
                opacity=opacity,
                API_key=API_key,
                **kwargs,
            ).add_to(self)
        except Exception:
            raise Exception("Failed to add the specified TileLayer.")

    def add_COG_layer(
        self,
        url,
        name="Untitled",
        attribution=".",
        opacity=1.0,
        shown=True,
        titiler_endpoint="https://api.cogeo.xyz/",
        **kwargs,
    ):
        """Adds a COG TileLayer to the map.

        Args:
            url (str): The URL of the COG tile layer.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to '.'.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".
        """
        tile_url = get_COG_tile(url, titiler_endpoint, **kwargs)
        center = get_COG_center(url, titiler_endpoint)  # (lon, lat)
        self.add_tile_layer(
            tiles=tile_url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            shown=shown,
        )
        self.set_center(lon=center[0], lat=center[1], zoom=10)

    def add_COG_mosaic(
        self,
        links,
        name="Untitled",
        attribution=".",
        opacity=1.0,
        shown=True,
        titiler_endpoint="https://api.cogeo.xyz/",
        username="anonymous",
        overwrite=False,
        show_footprints=False,
        verbose=True,
        **kwargs,
    ):
        """Add a virtual mosaic of COGs to the map.

        Args:
            links (list): A list of links pointing to COGs.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to '.'.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".
            username (str, optional): The username to create mosaic using the titiler endpoint. Defaults to 'anonymous'.
            overwrite (bool, optional): Whether or not to replace existing layer with the same layer name. Defaults to False.
            show_footprints (bool, optional): Whether or not to show footprints of COGs. Defaults to False.
            verbose (bool, optional): Whether or not to print descriptions. Defaults to True.
        """
        layername = name.replace(" ", "_")
        tile = get_COG_mosaic(
            links,
            titiler_endpoint=titiler_endpoint,
            username=username,
            layername=layername,
            overwrite=overwrite,
            verbose=verbose,
        )
        self.add_tile_layer(tile, name, attribution, opacity, shown)

        if show_footprints:
            if verbose:
                print(
                    f"Generating footprints of {len(links)} COGs. This might take a while ..."
                )
            coords = []
            for link in links:
                coord = get_COG_bounds(link)
                if coord is not None:
                    coords.append(coord)
            fc = coords_to_geojson(coords)

            # style_function = lambda x: {'opacity': 1, 'dashArray': '1', 'fillOpacity': 0, 'weight': 1}

            folium.GeoJson(
                data=fc,
                # style_function=style_function,
                name="Footprints",
            ).add_to(self)

            center = get_center(fc)
            if verbose:
                print("The footprint layer has been added.")
        else:
            center = get_COG_center(links[0], titiler_endpoint)

        self.set_center(center[0], center[1], zoom=6)

    def add_STAC_layer(
        self,
        url,
        bands=None,
        name="Untitled",
        attribution=".",
        opacity=1.0,
        shown=True,
        titiler_endpoint="https://api.cogeo.xyz/",
        **kwargs,
    ):
        """Adds a STAC TileLayer to the map.

        Args:
            url (str): The URL of the COG tile layer.
            name (str, optional): The layer name to use for the layer. Defaults to 'Untitled'.
            attribution (str, optional): The attribution to use. Defaults to '.'.
            opacity (float, optional): The opacity of the layer. Defaults to 1.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://api.cogeo.xyz/".
        """
        tile_url = get_STAC_tile(url, bands, titiler_endpoint, **kwargs)
        center = get_STAC_center(url, titiler_endpoint)
        self.add_tile_layer(
            tiles=tile_url,
            name=name,
            attribution=attribution,
            opacity=opacity,
            shown=shown,
        )
        self.set_center(lon=center[0], lat=center[1], zoom=10)

    def add_legend(
        self,
        title="Legend",
        colors=None,
        labels=None,
        legend_dict=None,
        builtin_legend=None,
        opacity=1.0,
        **kwargs,
    ):
        """Adds a customized basemap to the map. Reference: https://bit.ly/3oV6vnH

        Args:
            title (str, optional): Title of the legend. Defaults to 'Legend'. Defaults to "Legend".
            colors ([type], optional): A list of legend colors. Defaults to None.
            labels ([type], optional): A list of legend labels. Defaults to None.
            legend_dict ([type], optional): A dictionary containing legend items as keys and color as values. If provided, legend_keys and legend_colors will be ignored. Defaults to None.
            builtin_legend ([type], optional): Name of the builtin legend to add to the map. Defaults to None.
            opacity (float, optional): The opacity of the legend. Defaults to 1.0.

        """

        import pkg_resources
        from branca.element import Template, MacroElement

        pkg_dir = os.path.dirname(
            pkg_resources.resource_filename("geemap", "geemap.py")
        )
        legend_template = os.path.join(pkg_dir, "data/template/legend.txt")

        if not os.path.exists(legend_template):
            raise FileNotFoundError("The legend template does not exist.")

        if labels is not None:
            if not isinstance(labels, list):
                raise ValueError("The legend labels must be a list.")
        else:
            labels = ["One", "Two", "Three", "Four", "ect"]

        if colors is not None:
            if not isinstance(colors, list):
                raise ValueError("The legend colors must be a list.")
            elif all(isinstance(item, tuple) for item in colors):
                try:
                    colors = ["#" + rgb_to_hex(x) for x in colors]
                except Exception as e:
                    raise Exception(e)
            elif all((item.startswith("#") and len(item) == 7) for item in colors):
                pass
            elif all((len(item) == 6) for item in colors):
                pass
            else:
                raise ValueError("The legend colors must be a list of tuples.")
        else:
            colors = ["#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072", "#80B1D3"]

        if len(labels) != len(colors):
            raise ValueError("The legend keys and values must be the same length.")

        allowed_builtin_legends = builtin_legends.keys()
        if builtin_legend is not None:
            if builtin_legend not in allowed_builtin_legends:
                raise ValueError(
                    "The builtin legend must be one of the following: {}".format(
                        ", ".join(allowed_builtin_legends)
                    )
                )
            else:
                legend_dict = builtin_legends[builtin_legend]
                labels = list(legend_dict.keys())
                colors = list(legend_dict.values())
                if all(isinstance(item, tuple) for item in colors):
                    try:
                        colors = [rgb_to_hex(x) for x in colors]
                    except Exception as e:
                        raise Exception(e)
                elif all(isinstance(item, str) for item in colors):
                    colors = ["#" + color for color in colors]

        if legend_dict is not None:
            if not isinstance(legend_dict, dict):
                raise ValueError("The legend dict must be a dictionary.")
            else:
                labels = list(legend_dict.keys())
                colors = list(legend_dict.values())

                if all(isinstance(item, tuple) for item in colors):
                    try:
                        colors = [rgb_to_hex(x) for x in colors]
                    except Exception as e:
                        raise Exception(e)
                elif all(isinstance(item, str) for item in colors):
                    colors = ["#" + color for color in colors]

        content = []

        with open(legend_template) as f:
            lines = f.readlines()
            for index, line in enumerate(lines):
                if index < 36:
                    content.append(line)
                elif index == 36:
                    line = lines[index].replace("Legend", title)
                    content.append(line)
                elif index < 39:
                    content.append(line)
                elif index == 39:
                    for i, color in enumerate(colors):
                        item = f"    <li><span style='background:{check_color(color)};opacity:{opacity};'></span>{labels[i]}</li>\n"
                        content.append(item)
                elif index > 41:
                    content.append(line)

        template = "".join(content)
        macro = MacroElement()
        macro._template = Template(template)

        self.get_root().add_child(macro)

    def add_colorbar(
        self,
        colors,
        vmin=0,
        vmax=1.0,
        index=None,
        caption="",
        categorical=False,
        step=None,
        **kwargs,
    ):
        """Add a colorbar to the map.

        Args:
            colors (list): The set of colors to be used for interpolation. Colors can be provided in the form: * tuples of RGBA ints between 0 and 255 (e.g: (255, 255, 0) or (255, 255, 0, 255)) * tuples of RGBA floats between 0. and 1. (e.g: (1.,1.,0.) or (1., 1., 0., 1.)) * HTML-like string (e.g: “#ffff00) * a color name or shortcut (e.g: “y” or “yellow”)
            vmin (int, optional): The minimal value for the colormap. Values lower than vmin will be bound directly to colors[0].. Defaults to 0.
            vmax (float, optional): The maximal value for the colormap. Values higher than vmax will be bound directly to colors[-1]. Defaults to 1.0.
            index (list, optional):The values corresponding to each color. It has to be sorted, and have the same length as colors. If None, a regular grid between vmin and vmax is created.. Defaults to None.
            caption (str, optional): The caption for the colormap. Defaults to "".
            categorical (bool, optional): Whether or not to create a categorical colormap. Defaults to False.
            step (int, optional): The step to split the LinearColormap into a StepColormap. Defaults to None.
        """
        from box import Box
        from branca.colormap import LinearColormap

        if isinstance(colors, Box):
            try:
                colors = list(colors["default"])
            except Exception as e:
                print("The provided color list is invalid.")
                raise Exception(e)

        if all(len(color) == 6 for color in colors):
            colors = ["#" + color for color in colors]

        colormap = LinearColormap(
            colors=colors, index=index, vmin=vmin, vmax=vmax, caption=caption
        )

        if categorical:
            if step is not None:
                colormap = colormap.to_step(step)
            elif index is not None:
                colormap = colormap.to_step(len(index) - 1)
            else:
                colormap = colormap.to_step(3)

        self.add_child(colormap)

    def add_styled_vector(
        self, ee_object, column, palette, layer_name="Untitled", **kwargs
    ):
        """Adds a styled vector to the map.

        Args:
            ee_object (object): An ee.FeatureCollection.
            column (str): The column name to use for styling.
            palette (list | dict): The palette (e.g., list of colors or a dict containing label and color pairs) to use for styling.
            layer_name (str, optional): The name to be used for the new layer. Defaults to "Untitled".
        """
        styled_vector = vector_styling(ee_object, column, palette, **kwargs)
        self.addLayer(styled_vector.style(**{"styleProperty": "style"}), {}, layer_name)

    def add_shapefile(self, in_shp, layer_name="Untitled", **kwargs):
        """Adds a shapefile to the map. See https://python-visualization.github.io/folium/modules.html#folium.features.GeoJson for more info about setting style.

        Args:
            in_shp (str): The input file path to the shapefile.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".

        Raises:
            FileNotFoundError: The provided shapefile could not be found.
        """
        in_shp = os.path.abspath(in_shp)
        if not os.path.exists(in_shp):
            raise FileNotFoundError("The provided shapefile could not be found.")

        data = shp_to_geojson(in_shp)

        geo_json = folium.GeoJson(data=data, name=layer_name, **kwargs)
        geo_json.add_to(self)

    def add_geojson(self, in_geojson, layer_name="Untitled", **kwargs):
        """Adds a GeoJSON file to the map.

        Args:
            in_geojson (str): The input file path to the GeoJSON.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".

        Raises:
            FileNotFoundError: The provided GeoJSON file could not be found.
        """
        import json
        import requests

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

                    with open(in_geojson) as f:
                        data = json.load(f)
            elif isinstance(in_geojson, dict):
                data = in_geojson
            else:
                raise TypeError("The input geojson must be a type of str or dict.")
        except Exception as e:
            raise Exception(e)

        geo_json = folium.GeoJson(data=data, name=layer_name, **kwargs)
        geo_json.add_to(self)

    def add_kml(self, in_kml, layer_name="Untitled", **kwargs):
        """Adds a KML file to the map.

        Args:
            in_kml (str): The input file path to the KML.
            layer_name (str, optional): The layer name to be used. Defaults to "Untitled".

        Raises:
            FileNotFoundError: The provided KML file could not be found.
        """
        # import json

        in_kml = os.path.abspath(in_kml)
        if not os.path.exists(in_kml):
            raise FileNotFoundError("The provided KML file could not be found.")

        # out_json = os.path.join(os.getcwd(), "tmp.geojson")

        data = kml_to_geojson(in_kml)

        # with open(out_json) as f:
        #     data = json.load(f)

        geo_json = folium.GeoJson(data=data, name=layer_name, **kwargs)
        geo_json.add_to(self)
        # os.remove(out_json)

    def publish(
        self,
        name="Folium Map",
        description="",
        source_url="",
        visibility="PUBLIC",
        open=True,
        tags=None,
        **kwargs,
    ):
        """Publish the map to datapane.com

        Args:
            name (str, optional): The document name - can include spaces, caps, symbols, etc., e.g. "Profit & Loss 2020". Defaults to "Folium Map".
            description (str, optional): A high-level description for the document, this is displayed in searches and thumbnails. Defaults to ''.
            source_url (str, optional): A URL pointing to the source code for the document, e.g. a GitHub repo or a Colab notebook. Defaults to ''.
            visibility (str, optional): Visibility of the map. It can be one of the following: PUBLIC, PRIVATE. Defaults to 'PUBLIC'.
            open (bool, optional): Whether to open the map. Defaults to True.
            tags (bool, optional): A list of tags (as strings) used to categorise your document. Defaults to None.
        """
        import webbrowser

        try:
            import datapane as dp
        except Exception:
            webbrowser.open_new_tab("https://docs.datapane.com/tut-getting-started")
            raise ImportError(
                "The datapane Python package is not installed. You need to install and authenticate datapane first."
            )

        try:

            visibility = visibility.upper()

            if visibility not in ["PUBLIC", "PRIVATE"]:
                raise ValueError(
                    "The visibility argument must be either PUBLIC or PRIVATE."
                )

            if visibility == "PUBLIC":
                visibility = dp.Visibility.PUBLIC
            else:
                visibility = dp.Visibility.PRIVATE

            dp.Report(dp.Plot(self)).publish(
                name=name,
                description=description,
                source_url=source_url,
                visibility=visibility,
                open=open,
                tags=tags,
            )

        except Exception as e:
            raise Exception(e)


def delete_dp_report(name):
    """Deletes a datapane report.

    Args:
        name (str): Name of the report to delete.
    """
    try:
        import datapane as dp

        reports = dp.Report.list()
        items = list(reports)
        names = list(map(lambda item: item["name"], items))
        if name in names:
            report = dp.Report.get(name)
            url = report.blocks[0]["url"]
            # print('Deleting {}...'.format(url))
            dp.Report.delete(dp.Report.by_id(url))
    except Exception as e:
        print(e)
        return


def delete_dp_reports():
    """Deletes all datapane reports."""
    try:
        import datapane as dp

        reports = dp.Report.list()
        for item in reports:
            print(item["name"])
            report = dp.Report.get(item["name"])
            url = report.blocks[0]["url"]
            print("Deleting {}...".format(url))
            dp.Report.delete(dp.Report.by_id(url))
    except Exception as e:
        print(e)
        return
