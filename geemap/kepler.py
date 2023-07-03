"""Module for creating interactive maps with kepler.gl."""

# *******************************************************************************#
# This module contains extra features of the geemap package.                     #
# The geemap community will maintain the extra features.                         #
# *******************************************************************************#

import json
import os
import sys
import requests
import ipywidgets as widgets

import pandas as pd
from IPython.display import display, HTML
from .common import *
from .osm import *
from . import examples

try:
    import keplergl

    if "google.colab" in sys.modules:
        from google.colab import output

        output.enable_custom_widget_manager()
except ImportError:
    raise ImportError(
        "Kepler needs to be installed to use this module. Use 'pip install keplergl' to install the package. See https://docs.kepler.gl/docs/keplergl-jupyter for more details."
    )


class Map(keplergl.KeplerGl):
    """The Map class inherits keplergl.KeperGl.

    Returns:
        object: keplergl.KeperGl map object.
    """

    def __init__(self, **kwargs):
        if "center" not in kwargs:
            kwargs["center"] = [20, 0]

        if "zoom" not in kwargs:
            kwargs["zoom"] = 1.3

        if "height" not in kwargs:
            kwargs["height"] = 600
        elif "px" in str(kwargs["height"]):
            kwargs["height"] = kwargs["height"].replace("px", "")

        if "width" not in kwargs:
            kwargs["width"] = 600
        elif "px" in str(kwargs["width"]):
            kwargs["width"] = kwargs["width"].replace("px", "")

        if "widescreen" not in kwargs:
            kwargs["widescreen"] = False

        if "pitch" not in kwargs:
            kwargs["pitch"] = 0

        if "bearing" not in kwargs:
            kwargs["bearing"] = 0

        if "dragRotate" not in kwargs:
            kwargs["dragRotate"] = False

        if "isSplit" not in kwargs:
            kwargs["isSplit"] = False

        if kwargs["widescreen"]:
            display(HTML("<style>.container { width:100% !important; }</style>"))

        config = {
            "version": "v1",
            "config": {
                "mapState": {
                    "latitude": kwargs["center"][0],
                    "longitude": kwargs["center"][1],
                    "zoom": kwargs["zoom"],
                    "bearing": kwargs["bearing"],
                    "pitch": kwargs["pitch"],
                    "isSplit": kwargs["isSplit"],
                    "dragRotate": kwargs["dragRotate"],
                    "height": kwargs["height"],
                    "width": kwargs["width"],
                }
            },
        }

        kwargs.pop("widescreen")
        kwargs.pop("center")
        kwargs.pop("zoom")
        if "show_docs" not in kwargs:
            kwargs["show_docs"] = False

        super().__init__(**kwargs)
        self.config = config

    # def _repr_mimebundle_(self, include=None, exclude=None):
    #     """Display the map in a notebook.

    #     Args:
    #         include (list, optional): A list of MIME types to include.
    #         exclude (list, optional): A list of MIME types to exclude.

    #     Returns:
    #         dict: A dictionary of MIME type keyed dict of MIME type data.
    #     """
    #     print("hello")
    #     # import base64

    #     # bundle = super()._repr_mimebundle_(include=include, exclude=exclude)
    #     # if bundle["text/html"]:
    #     #     bundle["text/html"] = self.display_html()
    #     # return bundle

    def add_geojson(self, in_geojson, layer_name="Untitled", config=None, **kwargs):
        """Adds a GeoJSON file to the map.

        Args:
            in_geojson (str | dict): The file path or http URL to the input GeoJSON or a dictionary containing the geojson.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            config (str, optional): Local path or HTTP URL to the config file. Defaults to None.

        Raises:
            FileNotFoundError: The provided GeoJSON file could not be found.
            TypeError: The input geojson must be a type of str or dict.
        """

        if "encoding" in kwargs:
            encoding = kwargs["encoding"]
        else:
            encoding = "utf-8"

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

                    with open(in_geojson, encoding=encoding) as f:
                        data = json.load(f)
            elif isinstance(in_geojson, dict):
                data = in_geojson
            else:
                raise TypeError("The input geojson must be a type of str or dict.")
        except Exception as e:
            raise Exception(e)

        self.add_data(data, name=layer_name)
        self.load_config(config)

    def add_shp(self, in_shp, layer_name="Untitled", config=None, **kwargs):
        """Adds a shapefile to the map.

        Args:
            in_shp (str): The input file path to the shapefile.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            config (str, optional): Local path or HTTP URL to the config file. Defaults to None.

        Raises:
            FileNotFoundError: The provided shapefile could not be found.
        """

        import glob

        if in_shp.startswith("http") and in_shp.endswith(".zip"):
            out_dir = os.path.abspath("./cache/shp")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            download_from_url(in_shp, out_dir=out_dir, verbose=False)
            files = list(glob.glob(os.path.join(out_dir, "*.shp")))
            if len(files) > 0:
                in_shp = files[0]
            else:
                raise FileNotFoundError(
                    "The downloaded zip file does not contain any shapefile in the root directory."
                )
        else:
            in_shp = os.path.abspath(in_shp)
            if not os.path.exists(in_shp):
                raise FileNotFoundError("The provided shapefile could not be found.")

        geojson = shp_to_geojson(in_shp)
        self.add_geojson(
            geojson,
            layer_name,
            **kwargs,
        )
        self.load_config(config)

    def add_gdf(
        self,
        gdf,
        layer_name="Untitled",
        config=None,
        **kwargs,
    ):
        """Adds a GeoDataFrame to the map.

        Args:
            gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            config (str, optional): Local path or HTTP URL to the config file. Defaults to None.

        """

        data = gdf_to_geojson(gdf, epsg="4326")
        self.add_geojson(data, layer_name, **kwargs)
        self.load_config(config)

    def add_df(
        self,
        df,
        layer_name="Untitled",
        config=None,
        **kwargs,
    ):
        """Adds a DataFrame to the map.

        Args:
            df (DataFrame): A Pandas DataFrame.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            config (str, optional): Local path or HTTP URL to the config file. Defaults to None.

        """
        try:
            self.add_data(data=df, name=layer_name)
            self.load_config(config)
        except Exception as e:
            print(e)

    def add_csv(
        self,
        in_csv,
        layer_name="Untitled",
        config=None,
        **kwargs,
    ):
        """Adds a CSV to the map.

        Args:
            in_csv (str): File path to the CSV.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            config (str, optional): Local path or HTTP URL to the config file. Defaults to None.

        """

        df = pd.read_csv(in_csv)
        self.add_df(df, layer_name, config, **kwargs)

    def add_vector(
        self,
        filename,
        layer_name="Untitled",
        config=None,
        **kwargs,
    ):
        """Adds any geopandas-supported vector dataset to the map.

        Args:
            filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
            layer_name (str, optional): The layer name to use. Defaults to "Untitled".
            config (str, optional): Local path or HTTP URL to the config file. Defaults to None.

        """
        if not filename.startswith("http"):
            filename = os.path.abspath(filename)

        ext = os.path.splitext(filename)[1].lower()
        if ext == ".shp":
            self.add_shp(
                filename,
                layer_name,
                **kwargs,
            )
            self.load_config(config)
        elif ext in [".json", ".geojson"]:
            self.add_geojson(
                filename,
                layer_name,
                **kwargs,
            )
            self.load_config(config)
        else:
            geojson = vector_to_geojson(
                filename,
                epsg="4326",
                **kwargs,
            )

            self.add_geojson(
                geojson,
                layer_name,
                **kwargs,
            )
            self.load_config(config)

    def add_kml(
        self,
        in_kml,
        layer_name="Untitled",
        config=None,
        **kwargs,
    ):
        """Adds a KML file to the map.

        Args:
            in_kml (str): The input file path to the KML.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            config (str, optional): Local path or HTTP URL to the config file. Defaults to None.

        Raises:
            FileNotFoundError: The provided KML file could not be found.
        """

        if in_kml.startswith("http") and in_kml.endswith(".kml"):
            out_dir = os.path.abspath("./cache")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            download_from_url(in_kml, out_dir=out_dir, unzip=False, verbose=False)
            in_kml = os.path.join(out_dir, os.path.basename(in_kml))
            if not os.path.exists(in_kml):
                raise FileNotFoundError("The downloaded kml file could not be found.")
        else:
            in_kml = os.path.abspath(in_kml)
            if not os.path.exists(in_kml):
                raise FileNotFoundError("The provided KML could not be found.")

        self.add_vector(
            in_kml,
            layer_name,
            **kwargs,
        )
        self.load_config(config)

    def add_gdf_from_postgis(
        self,
        sql,
        con,
        layer_name="Untitled",
        config=None,
        **kwargs,
    ):
        """Reads a PostGIS database and returns data as a GeoDataFrame to be added to the map.

        Args:
            sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
            con (sqlalchemy.engine.Engine): Active connection to the database to query.
            layer_name (str, optional): The layer name to be used.. Defaults to "Untitled".
            config (str, optional): Local path or HTTP URL to the config file. Defaults to None.

        """
        gdf = read_postgis(sql, con, **kwargs)
        gdf = gdf.to_crs("epsg:4326")
        self.add_gdf(
            gdf,
            layer_name,
            **kwargs,
        )
        self.load_config(config)

    def static_map(
        self, width=950, height=600, read_only=False, out_file=None, **kwargs
    ):
        """Display a kepler.gl static map in a Jupyter Notebook.

        Args
            width (int, optional): Width of the map. Defaults to 950.
            height (int, optional): Height of the map. Defaults to 600.
            read_only (bool, optional): Whether to hide the side panel to disable map customization. Defaults to False.
            out_file (str, optional): Output html file path. Defaults to None.
        """
        if isinstance(self, keplergl.KeplerGl):
            if out_file is None:
                if os.environ.get("USE_MKDOCS") is not None:
                    out_file = "../maps/" + "kepler_" + random_string(3) + ".html"
                else:
                    out_file = "./cache/" + "kepler_" + random_string(3) + ".html"
            out_dir = os.path.abspath(os.path.dirname(out_file))
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            output = widgets.Output()
            with output:
                self.save_to_html(file_name=out_file, read_only=read_only)
            display_html(src=out_file, width=width, height=height)
        else:
            raise TypeError("The provided map is not a kepler.gl map.")

    def to_html(
        self,
        filename=None,
        read_only=False,
        **kwargs,
    ):
        """Saves the map as a HTML file.

        Args:
            filename (str, optional): The output file path to the HTML file.
            read_only (bool, optional): Whether to hide the side panel to disable map customization. Defaults to False.

        """
        try:
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

            output = widgets.Output()
            with output:
                self.save_to_html(file_name=filename, read_only=read_only)

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
        self, width=800, height=600, responsive=True, scrolling=False, **kwargs
    ):
        """Renders `keplergl.KeplerGl` map figure in a Streamlit app.

        Args:
            width (int, optional): Width of the map. Defaults to 800.
            height (int, optional): Height of the map. Defaults to 600.
            responsive (bool, optional): Whether to make the map responsive. Defaults to True.
            scrolling (bool, optional): If True, show a scrollbar when the content is larger than the iframe. Otherwise, do not show a scrollbar. Defaults to False.

        Raises:
            ImportError: If streamlit is not installed.

        Returns:
            streamlit.components: components.html object.
        """

        try:
            import streamlit as st
            import streamlit.components.v1 as components

            html = self._repr_html_()
            if responsive:
                make_map_responsive = """
                <style>
                [title~="st.iframe"] { width: 100%}
                </style>
                """
                st.markdown(make_map_responsive, unsafe_allow_html=True)
            return components.html(
                html, width=width, height=height, scrolling=scrolling
            )

        except ImportError:
            raise ImportError(
                "streamlit is not installed. You need to install streamlitusing 'pip install streamlit'. Seehttps://docs.streamlit.io/library/get-started/installation"
            )

    def load_config(self, config=None):
        """Loads a kepler.gl config file.

        Args:
            config (str, optional): Local path or HTTP URL to the config file. Defaults to None.

        Raises:
            FileNotFoundError: The provided config file could not be found.
            TypeError: The provided config file is not a kepler.gl config file.
        """
        if config is None:
            pass
        elif isinstance(config, dict):
            self.config = config
        elif isinstance(config, str):
            if config.startswith("http"):
                r = requests.get(config)
                self.config = r.json()
            elif os.path.isfile(config):
                with open(config) as f:
                    self.config = json.load(f)
            else:
                raise FileNotFoundError("The provided config file could not be found.")
        else:
            raise TypeError("The provided config is not a dictionary or filepath.")

    def save_config(self, out_json):
        """Saves a kepler.gl config file.

        Args:
            out_json (str): Output file path to the config file.

        Raises:
            ValueError: The output file extension must be json.
            TypeError: The provided filepath is invalid.
        """
        if isinstance(out_json, str):
            if not out_json.endswith(".json"):
                raise ValueError("The output file extension must be json.")
            out_json = os.path.abspath(out_json)
            out_dir = os.path.dirname(out_json)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            json_str = json.dumps(self.config, indent=2)
            with open(out_json, "w") as f:
                f.write(json_str)
        else:
            raise TypeError("The provided filepath is invalid.")
