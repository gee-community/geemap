import os
from .common import *
from .osm import *
from .geemap import basemaps
from . import examples

try:
    import pydeck as pdk

except ImportError:
    raise ImportError(
        "pydeck needs to be installed to use this module. Use 'pip install pydeck' to install the package. See https://deckgl.readthedocs.io/en/latest/installation.html for more details."
    )


class Layer(pdk.Layer):
    """Configures a deck.gl layer for rendering on a map. Parameters passed here will be specific to the particular deck.gl layer that you are choosing to use.
    Please see the deck.gl Layer catalog (https://deck.gl/docs/api-reference/layers) to determine the particular parameters of your layer.
    You are highly encouraged to look at the examples in the pydeck documentation.
    """

    def __init__(self, type, data=None, id=None, use_binary_transport=None, **kwargs):
        """Initialize a Layer object.

        Args:
            type (str):  Type of layer to render, e.g., HexagonLayer. See deck.gl Layer catalog (https://deck.gl/docs/api-reference/layers)
            data (str, optional): Unique name for layer. Defaults to None.
            id (str | dict | pandas.DataFrame, optional): Either a URL of data to load in or an array of data. Defaults to None.
            use_binary_transport (bool, optional): Boolean indicating binary data. Defaults to None.
        """
        super().__init__(type, data, id, use_binary_transport, **kwargs)


class Map(pdk.Deck):
    """The Map class inherits pydeck.Deck.

    Returns:
        object: pydeck.Deck object.
    """

    def __init__(self, center=(20, 0), zoom=1.2, height=800, width=None, **kwargs):
        """Initialize a Map object.

        Args:
            center (tuple, optional): Center of the map in the format of (lat, lon). Defaults to (20, 0).
            zoom (int, optional): The map zoom level. Defaults to 1.2.
            height (int, optional): The map height. Note that the height has no effect in Jupyter notebook. Only works for streamlit. Defaults to 800.
            width (int, optional): The map width. Note that the height has no effect in Jupyter notebook. Only works for streamlit. Defaults to None.
        """
        # Authenticates Earth Engine and initializes an Earth Engine session
        if "ee_initialize" not in kwargs.keys():
            kwargs["ee_initialize"] = True

        if kwargs["ee_initialize"]:
            ee_initialize()

        kwargs.pop("ee_initialize")

        if "initial_view_state" not in kwargs:
            kwargs["initial_view_state"] = pdk.ViewState(
                latitude=center[0],
                longitude=center[1],
                zoom=zoom,
                height=height,
                width=width,
            )

        if "map_style" not in kwargs:
            kwargs["map_style"] = "light"

        super().__init__(**kwargs)

    def add_layer(self, layer, layer_name=None, **kwargs):
        """Add a layer to the map.

        Args:
            layer (pydeck.Layer): A pydeck Layer object.
        """

        try:

            if isinstance(layer, str) and layer.startswith("http"):
                pdk.settings.custom_libraries = [
                    {
                        "libraryName": "MyTileLayerLibrary",
                        "resourceUri": "https://cdn.jsdelivr.net/gh/giswqs/pydeck_myTileLayer@master/dist/bundle.js",
                    }
                ]
                layer = pdk.Layer("MyTileLayer", layer, id=layer_name)

            self.layers.append(layer)
        except Exception as e:
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
        import ee
        from box import Box

        image = None

        if vis_params is None:
            vis_params = {}

        if name is None:
            layer_count = len(self.layers)
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
        self.add_layer(url, layer_name=name, **kwargs)

    addLayer = add_ee_layer

    def add_basemap(self, basemap="HYBRID"):
        """Adds a basemap to the map.

        Args:
            basemap (str): Can be one of string from pydeck_basemaps. Defaults to 'HYBRID'.
        """
        import xyzservices

        try:
            if isinstance(basemap, xyzservices.TileProvider):
                name = basemap.name
                url = basemap.build_url()
                self.add_layer(url, name)

            elif basemap in basemaps:

                pdk.settings.custom_libraries = [
                    {
                        "libraryName": "MyTileLayerLibrary",
                        "resourceUri": "https://cdn.jsdelivr.net/gh/giswqs/pydeck_myTileLayer@master/dist/bundle.js",
                    }
                ]
                layer = pdk.Layer("MyTileLayer", basemaps[basemap].url, basemap)

                self.add_layer(layer)

            else:
                print(
                    "Basemap can only be one of the following:\n  {}".format(
                        "\n  ".join(basemaps.keys())
                    )
                )

        except Exception:
            raise ValueError(
                "Basemap can only be one of the following:\n  {}".format(
                    "\n  ".join(basemaps.keys())
                )
            )

    def add_gdf(self, gdf, layer_name=None, random_color_column=None, **kwargs):
        """Adds a GeoPandas GeoDataFrame to the map.

        Args:
            gdf (GeoPandas.GeoDataFrame): The GeoPandas GeoDataFrame to add to the map.
            layer_name (str, optional): The layer name to be used. Defaults to None.
            random_color_column (str, optional): The column name to use for random color. Defaults to None.

        Raises:
            TypeError: gdf must be a GeoPandas GeoDataFrame.
        """

        try:
            import geopandas as gpd

            if not isinstance(gdf, gpd.GeoDataFrame):
                raise TypeError("gdf must be a GeoPandas GeoDataFrame.")

            if layer_name is None:
                layer_name = "layer_" + random_string(3)

            if "pickable" not in kwargs:
                kwargs["pickable"] = True
            if "opacity" not in kwargs:
                kwargs["opacity"] = 0.5
            if "stroked" not in kwargs:
                kwargs["stroked"] = True
            if "filled" not in kwargs:
                kwargs["filled"] = True
            if "extruded" not in kwargs:
                kwargs["extruded"] = False
            if "wireframe" not in kwargs:
                kwargs["wireframe"] = True
            if "get_line_color" not in kwargs:
                kwargs["get_line_color"] = [0, 0, 0]
            if "get_line_width" not in kwargs:
                kwargs["get_line_width"] = 2
            if "line_width_min_pixels" not in kwargs:
                kwargs["line_width_min_pixels"] = 1

            if random_color_column is not None:
                if random_color_column not in gdf.columns.values.tolist():
                    raise ValueError(
                        "The random_color_column provided does not exist in the vector file."
                    )
                color_lookup = pdk.data_utils.assign_random_colors(
                    gdf[random_color_column]
                )
                gdf["color"] = gdf.apply(
                    lambda row: color_lookup.get(row[random_color_column]), axis=1
                )
                kwargs["get_fill_color"] = "color"

            layer = pdk.Layer(
                "GeoJsonLayer",
                gdf,
                id=layer_name,
                **kwargs,
            )
            self.add_layer(layer)

        except Exception as e:
            raise Exception(e)

    def add_vector(self, filename, layer_name=None, random_color_column=None, **kwargs):
        """Adds a vector file to the map.

        Args:
            filename (str): The input file path to the vector dataset.
            layer_name (str, optional): The layer name to be used. Defaults to None.
            random_color_column (str, optional): The column name to use for random color. Defaults to None.

        Raises:
            FileNotFoundError: The provided vector file could not be found.
        """

        try:

            import geopandas as gpd

            if not filename.startswith("http"):
                filename = os.path.abspath(filename)
                if filename.endswith(".zip"):
                    filename = "zip://" + filename

            if filename.endswith(".kml"):
                gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
                gdf = gpd.read_file(filename, driver="KML")
            else:
                gdf = gpd.read_file(filename)

            self.add_gdf(gdf, layer_name, random_color_column, **kwargs)

        except Exception as e:
            raise Exception(e)

    def add_geojson(
        self, filename, layer_name=None, random_color_column=None, **kwargs
    ):
        """Adds a GeoJSON file to the map.

        Args:
            filename (str): The input file path to the vector dataset.
            layer_name (str, optional): The layer name to be used. Defaults to None.
            random_color_column (str, optional): The column name to use for random color. Defaults to None.

        Raises:
            FileNotFoundError: The provided vector file could not be found.
        """
        self.add_vector(filename, layer_name, random_color_column, **kwargs)

    def add_shp(self, filename, layer_name=None, random_color_column=None, **kwargs):
        """Adds a shapefile to the map.

        Args:
            filename (str): The input file path to the vector dataset.
            layer_name (str, optional): The layer name to be used. Defaults to None.
            random_color_column (str, optional): The column name to use for random color. Defaults to None.

        Raises:
            FileNotFoundError: The provided vector file could not be found.
        """
        self.add_vector(filename, layer_name, random_color_column, **kwargs)

    def add_kml(self, filename, layer_name=None, random_color_column=None, **kwargs):
        """Adds a KML file to the map.

        Args:
            filename (str): The input file path to the vector dataset.
            layer_name (str, optional): The layer name to be used. Defaults to None.
            random_color_column (str, optional): The column name to use for random color. Defaults to None.

        Raises:
            FileNotFoundError: The provided vector file could not be found.
        """
        self.add_vector(filename, layer_name, random_color_column, **kwargs)
