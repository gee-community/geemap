import json
import os
import sys
import zipfile

import ee
import ipywidgets as widgets
from ipytree import Node, Tree
from typing import Union, List, Dict, Optional, Tuple, Any

try:
    from IPython.display import display, Javascript
except ImportError:
    pass


def get_env_var(key: str) -> Optional[str]:
    """Retrieves an environment variable or Colab secret for the given key.

    Colab secrets have precedence over environment variables.

    Args:
        key (str): The key that's used to fetch the environment variable.

    Returns:
        Optional[str]: The retrieved key, or None if no environment variable was found.
    """
    if not key:
        return None

    if in_colab_shell():
        from google.colab import userdata

        try:
            return userdata.get(key)
        except (userdata.SecretNotFoundError, userdata.NotebookAccessError):
            pass

    return os.environ.get(key)


def ee_initialize(
    token_name: str = "EARTHENGINE_TOKEN",
    auth_mode: Optional[str] = None,
    auth_args: Optional[Dict[str, Any]] = None,
    user_agent_prefix: str = "geemap",
    project: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Authenticates Earth Engine and initialize an Earth Engine session

    Args:
        token_name (str, optional): The name of the Earth Engine token.
            Defaults to "EARTHENGINE_TOKEN". In Colab, you can also set a secret
            named "EE_PROJECT_ID" to initialize Earth Engine.
        auth_mode (str, optional): The authentication mode, can be one of colab,
            notebook, localhost, or gcloud.
            See https://developers.google.com/earth-engine/guides/auth for more
            details. Defaults to None.
        auth_args (dict, optional): Additional authentication parameters for
            aa.Authenticate(). Defaults to {}.
        user_agent_prefix (str, optional): If set, the prefix (version-less)
            value used for setting the user-agent string. Defaults to "geemap".
        project (str, optional): The Google cloud project ID for Earth Engine.
            Defaults to None.
        kwargs (dict, optional): Additional parameters for ee.Initialize().
            For example, opt_url='https://earthengine-highvolume.googleapis.com'
            to use the Earth Engine High-Volume platform. Defaults to {}.
    """
    import google.oauth2.credentials
    from .__init__ import __version__

    user_agent = f"{user_agent_prefix}/{__version__}"
    ee.data.setUserAgent(user_agent)

    if ee.data._credentials is not None:
        return

    ee_token = get_env_var(token_name)
    if ee_token is not None:

        stored = json.loads(ee_token)
        credentials = google.oauth2.credentials.Credentials(
            None,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=stored["client_id"],
            client_secret=stored["client_secret"],
            refresh_token=stored["refresh_token"],
            quota_project_id=stored["project"],
        )

        ee.Initialize(credentials=credentials, **kwargs)
        return

    if auth_args is None:
        auth_args = {}

    if project is None:
        kwargs["project"] = get_env_var("EE_PROJECT_ID")
    else:
        kwargs["project"] = project

    if auth_mode is None:
        if in_colab_shell() and (ee.data._credentials is None):
            ee.Authenticate()
            ee.Initialize(**kwargs)
            return
        else:
            auth_mode = "notebook"

    auth_args["auth_mode"] = auth_mode

    ee.Authenticate(**auth_args)
    ee.Initialize(**kwargs)


def get_info(
    ee_object: Union[ee.FeatureCollection, ee.Image, ee.Geometry, ee.Feature],
    layer_name: str = "",
    opened: bool = False,
    return_node: bool = False,
) -> Union[Node, Tree, None]:
    """Print out the information for an Earth Engine object using a tree structure.
    The source code was adapted from https://github.com/google/earthengine-jupyter.
    Credits to Tyler Erickson.

    Args:
        ee_object (Union[ee.FeatureCollection, ee.Image, ee.Geometry, ee.Feature]):
            The Earth Engine object.
        layer_name (str, optional): The name of the layer. Defaults to "".
        opened (bool, optional): Whether to expand the tree. Defaults to False.
        return_node (bool, optional): Whether to return the widget as ipytree.Node.
            If False, returns the widget as ipytree.Tree. Defaults to False.

    Returns:
        Union[Node, Tree, None]: The tree or node representing the Earth Engine
            object information.
    """

    def _order_items(item_dict, ordering_list):
        """Orders dictionary items in a specified order.
        Adapted from https://github.com/google/earthengine-jupyter.
        """
        list_of_tuples = [
            (key, item_dict[key])
            for key in [x for x in ordering_list if x in item_dict.keys()]
        ]

        return dict(list_of_tuples)

    def _process_info(info):
        node_list = []
        if isinstance(info, list):
            for count, item in enumerate(info):
                if isinstance(item, (list, dict)):
                    if "id" in item:
                        count = f"{count}: \"{item['id']}\""
                    if "data_type" in item:
                        count = f"{count}, {item['data_type']['precision']}"
                    if "crs" in item:
                        count = f"{count}, {item['crs']}"
                    if "dimensions" in item:
                        dimensions = item["dimensions"]
                        count = f"{count}, {dimensions[0]}x{dimensions[1]} px"
                    node_list.append(
                        Node(f"{count}", nodes=_process_info(item), opened=opened)
                    )
                else:
                    node_list.append(Node(f"{count}: {item}", icon="file"))
        elif isinstance(info, dict):
            for k, v in info.items():
                if isinstance(v, (list, dict)):
                    if k == "properties":
                        k = f"properties: Object ({len(v)} properties)"
                    elif k == "bands":
                        k = f"bands: List ({len(v)} elements)"
                    node_list.append(
                        Node(f"{k}", nodes=_process_info(v), opened=opened)
                    )
                else:
                    node_list.append(Node(f"{k}: {v}", icon="file"))
        else:
            node_list.append(Node(f"{info}", icon="file"))
        return node_list

    if isinstance(ee_object, ee.FeatureCollection):
        ee_object = ee_object.map(lambda f: ee.Feature(None, f.toDictionary()))
    layer_info = ee_object.getInfo()
    if not layer_info:
        return None

    props = layer_info.get("properties", {})
    layer_info["properties"] = dict(sorted(props.items()))

    ordering_list = []
    if "type" in layer_info:
        ordering_list.append("type")
        ee_type = layer_info["type"]
    else:
        ee_type = ""

    if "id" in layer_info:
        ordering_list.append("id")
        ee_id = layer_info["id"]
    else:
        ee_id = ""

    ordering_list.append("version")
    ordering_list.append("bands")
    ordering_list.append("properties")

    layer_info = _order_items(layer_info, ordering_list)
    nodes = _process_info(layer_info)

    if len(layer_name) > 0:
        layer_name = f"{layer_name}: "

    if "bands" in layer_info:
        band_info = f' ({len(layer_info["bands"])} bands)'
    else:
        band_info = ""
    root_node = Node(f"{layer_name}{ee_type} {band_info}", nodes=nodes, opened=opened)
    # root_node.open_icon = "plus-square"
    # root_node.open_icon_style = "success"
    # root_node.close_icon = "minus-square"
    # root_node.close_icon_style = "info"

    if return_node:
        return root_node
    else:
        tree = Tree()
        tree.add_node(root_node)
        return tree


def create_code_cell(code: str = "", where: str = "below") -> None:
    """Creates a code cell in the IPython Notebook.

    Args:
        code (str, optional): Code to fill the new code cell with. Defaults to ''.
        where (str, optional): Where to add the new code cell. It can be one of
            the following: above, below, at_bottom. Defaults to 'below'.
    """

    import base64
    import pyperclip

    try:
        pyperclip.copy(str(code))
    except Exception as e:
        pass

    encoded_code = (base64.b64encode(str.encode(code))).decode()
    display(
        Javascript(
            """
        var code = IPython.notebook.insert_cell_{0}('code');
        code.set_text(atob("{1}"));
    """.format(
                where, encoded_code
            )
        )
    )


def geometry_type(ee_object: Any) -> str:
    """Get geometry type of an Earth Engine object.

    Args:
        ee_object (Any): An Earth Engine object.

    Returns:
        str: Returns geometry type. One of Point, MultiPoint, LineString,
            LinearRing, MultiLineString, BBox, Rectangle, Polygon, MultiPolygon.

    Raises:
        TypeError: If the ee_object is not one of ee.Geometry, ee.Feature,
            ee.FeatureCollection.
    """
    if isinstance(ee_object, ee.Geometry):
        return ee_object.type().getInfo()
    elif isinstance(ee_object, ee.Feature):
        return ee_object.geometry().type().getInfo()
    elif isinstance(ee_object, ee.FeatureCollection):
        return ee.Feature(ee_object.first()).geometry().type().getInfo()
    else:
        raise TypeError(
            "The ee_object must be one of ee.Geometry, ee.Feature, ee.FeatureCollection."
        )


def get_google_maps_api_key(key: str = "GOOGLE_MAPS_API_KEY") -> Optional[str]:
    """
    Retrieves the Google Maps API key from the environment or Colab user data.

    Args:
        key (str, optional): The name of the environment variable or Colab user
            data key where the API key is stored. Defaults to
            'GOOGLE_MAPS_API_KEY'.

    Returns:
        str: The API key, or None if it could not be found.
    """
    if api_key := get_env_var(key):
        return api_key
    return os.environ.get(key, None)


def in_colab_shell() -> bool:
    """
    Checks if the code is running in a Google Colab environment.

    Returns:
        bool: True if running in Google Colab, False otherwise.
    """
    return "google.colab" in sys.modules


def check_color(in_color: Union[str, Tuple[int, int, int]]) -> str:
    """Checks the input color and returns the corresponding hex color code.

    Args:
        in_color (Union[str, Tuple[int, int, int]]): It can be a string (e.g.,
            'red', '#ffff00', 'ffff00', 'ff0') or RGB tuple (e.g., (255, 127, 0)).

    Returns:
        str: A hex color code.
    """
    import colour

    out_color = "#000000"  # default black color
    if isinstance(in_color, tuple) and len(in_color) == 3:
        # rescale color if necessary
        if all(isinstance(item, int) for item in in_color):
            in_color = [c / 255.0 for c in in_color]

        return colour.Color(rgb=tuple(in_color)).hex_l

    else:
        # try to guess the color system
        try:
            return colour.Color(in_color).hex_l

        except Exception as e:
            pass

        # try again by adding an extra # (GEE handle hex codes without #)
        try:
            return colour.Color(f"#{in_color}").hex_l

        except Exception as e:
            print(
                f"The provided color ({in_color}) is invalid. Using the default black color."
            )
            print(e)

        return out_color


def check_cmap(cmap: Union[str, List[str]]) -> List[str]:
    """Check the colormap and return a list of colors.

    Args:
        cmap (Union[str, List[str], Box]): The colormap to check.

    Returns:
        List[str]: A list of colors.
    """

    from box import Box
    from .colormaps import get_palette

    if isinstance(cmap, str):
        try:
            palette = get_palette(cmap)
            if isinstance(palette, dict):
                palette = palette["default"]
            return palette
        except Exception as e:
            try:
                return check_color(cmap)
            except Exception as e:
                raise Exception(f"{cmap} is not a valid colormap.")
    elif isinstance(cmap, Box):
        return list(cmap["default"])
    elif isinstance(cmap, list) or isinstance(cmap, tuple):
        return cmap
    else:
        raise Exception(f"{cmap} is not a valid colormap.")


def to_hex_colors(colors: List[Union[str, Tuple[int, int, int]]]) -> List[str]:
    """Convert a GEE color palette into hexadecimal color codes. Can handle mixed formats.

    Args:
        colors (List[Union[str, Tuple[int, int, int]]]): A list of colors in hex or RGB format.

    Returns:
        List[str]: A list of hex color codes prefixed with #.
    """

    return [check_color(c) for c in colors]


def rgb_to_hex(rgb: Tuple[int, int, int] = (255, 255, 255)) -> str:
    """Converts RGB to hex color. In RGB color, R stands for Red, G stands for
        Green, and B stands for Blue, and it ranges from the decimal value of 0 – 255.

    Args:
        rgb (Tuple[int, int, int], optional): RGB color code as a tuple of
            (red, green, blue). Defaults to (255, 255, 255).

    Returns:
        str: Hex color code.
    """
    return "%02x%02x%02x" % rgb


def hex_to_rgb(value: str = "FFFFFF") -> Tuple[int, int, int]:
    """Converts hex color to RGB color.

    Args:
        value (str, optional): Hex color code as a string. Defaults to 'FFFFFF'.

    Returns:
        Tuple[int, int, int]: RGB color as a tuple.
    """
    value = value.lstrip("#")
    lv = len(value)
    return tuple(int(value[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))


def random_string(string_length: int = 3) -> str:
    """Generates a random string of fixed length.

    Args:
        string_length (int, optional): Fixed length. Defaults to 3.

    Returns:
        str: A random string.
    """
    import random
    import string

    # random.seed(1001)
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(string_length))


def widget_template(
    widget: Optional[widgets.Widget] = None,
    opened: bool = True,
    show_close_button: bool = True,
    widget_icon: str = "gear",
    close_button_icon: str = "times",
    widget_args: Optional[Dict[str, Any]] = None,
    close_button_args: Optional[Dict[str, Any]] = None,
    display_widget: Optional[widgets.Widget] = None,
    m: Optional["ipyleaflet.Map"] = None,
    position: str = "topright",
) -> Optional[widgets.Widget]:
    """Create a widget template.

    Args:
        widget (Optional[widgets.Widget], optional): The widget to be displayed.
            Defaults to None.
        opened (bool, optional): Whether to open the toolbar. Defaults to True.
        show_close_button (bool, optional): Whether to show the close button.
            Defaults to True.
        widget_icon (str, optional): The icon name for the toolbar button.
            Defaults to 'gear'.
        close_button_icon (str, optional): The icon name for the close button.
            Defaults to "times".
        widget_args (Optional[Dict[str, Any]], optional): Additional arguments
            to pass to the toolbar button. Defaults to None.
        close_button_args (Optional[Dict[str, Any]], optional): Additional
            arguments to pass to the close button. Defaults to None.
        display_widget (Optional[widgets.Widget], optional): The widget to be
            displayed when the toolbar is clicked. Defaults to None.
        m (Optional[ipyleaflet.Map], optional): The ipyleaflet.Map instance.
            Defaults to None.
        position (str, optional): The position of the toolbar. Defaults to "topright".

    Returns:
        Optional[widgets.Widget]: The created widget template.
    """

    name = "_" + random_string()  # a random attribute name

    if widget_args is None:
        widget_args = {}

    if close_button_args is None:
        close_button_args = {}

    if "value" not in widget_args:
        widget_args["value"] = False
    if "tooltip" not in widget_args:
        widget_args["tooltip"] = "Toolbar"
    if "layout" not in widget_args:
        widget_args["layout"] = widgets.Layout(
            width="28px", height="28px", padding="0px 0px 0px 4px"
        )
    widget_args["icon"] = widget_icon

    if "value" not in close_button_args:
        close_button_args["value"] = False
    if "tooltip" not in close_button_args:
        close_button_args["tooltip"] = "Close the tool"
    if "button_style" not in close_button_args:
        close_button_args["button_style"] = "primary"
    if "layout" not in close_button_args:
        close_button_args["layout"] = widgets.Layout(
            height="28px", width="28px", padding="0px 0px 0px 4px"
        )
    close_button_args["icon"] = close_button_icon

    try:
        toolbar_button = widgets.ToggleButton(**widget_args)
    except:
        widget_args.pop("layout")
        toolbar_button = widgets.ToggleButton(**widget_args)
        toolbar_button.layout.width = "28px"
        toolbar_button.layout.height = "28px"
        toolbar_button.layout.padding = "0px 0px 0px 4px"

    try:
        close_button = widgets.ToggleButton(**close_button_args)
    except:
        close_button_args.pop("layout")
        close_button = widgets.ToggleButton(**close_button_args)
        close_button.layout.width = "28px"
        close_button.layout.height = "28px"
        close_button.layout.padding = "0px 0px 0px 4px"

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    if show_close_button:
        toolbar_header.children = [close_button, toolbar_button]
    else:
        toolbar_header.children = [toolbar_button]
    toolbar_footer = widgets.VBox()

    if widget is not None:
        toolbar_footer.children = [
            widget,
        ]
    else:
        toolbar_footer.children = []

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            if display_widget is not None:
                widget.outputs = ()
                with widget:
                    display(display_widget)
        else:
            toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                control = getattr(m, name)
                if control is not None and control in m.controls:
                    m.remove_control(control)
                    delattr(m, name)
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    toolbar_button.value = opened
    if m is not None:
        import ipyleaflet

        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position=position
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)

            setattr(m, name, toolbar_control)

    else:
        return toolbar_widget


def open_url(url: str) -> None:
    """Opens the URL in a new browser tab.

    Args:
        url (str): The URL to open.
    """
    if in_colab_shell():
        display(
            Javascript('window.open("{url}", "_blank", "noopener")'.format(url=url))
        )
    else:
        import webbrowser

        webbrowser.open_new_tab(url)


def github_raw_url(url: str) -> str:
    """Get the raw URL for a GitHub file.

    Args:
        url (str): The GitHub URL.

    Returns:
        str: The raw URL.
    """
    if isinstance(url, str) and url.startswith("https://github.com/") and "blob" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace(
            "blob/", "", 1
        )
    return url


def temp_file_path(extension: str) -> str:
    """Returns a temporary file path.

    Args:
        extension (str): The file extension.

    Returns:
        str: The temporary file path.
    """

    import tempfile
    import uuid

    if not extension.startswith("."):
        extension = "." + extension
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{extension}")

    return file_path


def download_file(
    url: Optional[str] = None,
    output: Optional[str] = None,
    quiet: bool = False,
    proxy: Optional[str] = None,
    speed: Optional[float] = None,
    use_cookies: bool = True,
    verify: Union[bool, str] = True,
    id: Optional[str] = None,
    fuzzy: bool = False,
    resume: bool = False,
    unzip: bool = True,
    overwrite: bool = False,
) -> str:
    """Download a file from URL, including Google Drive shared URL.

    Args:
        url (Optional[str], optional): Google Drive URL is also supported.
            Defaults to None.
        output (Optional[str], optional): Output filename. Default is basename of URL.
        quiet (bool, optional): Suppress terminal output. Default is False.
        proxy (Optional[str], optional): Proxy. Defaults to None.
        speed (Optional[float], optional): Download byte size per second (e.g.,
            256KB/s = 256 * 1024). Defaults to None.
        use_cookies (bool, optional): Flag to use cookies. Defaults to True.
        verify (Union[bool, str], optional): Either a bool, in which case it
            controls whether the server's TLS certificate is verified, or a
            string, in which case it must be a path to a CA bundle to use.
            Default is True.
        id (Optional[str], optional): Google Drive's file ID. Defaults to None.
        fuzzy (bool, optional): Fuzzy extraction of Google Drive's file Id.
            Defaults to False.
        resume (bool, optional): Resume the download from existing tmp file if
            possible. Defaults to False.
        unzip (bool, optional): Unzip the file. Defaults to True.
        overwrite (bool, optional): Overwrite the file if it already exists.
            Defaults to False.

    Returns:
        str: The output file path.
    """

    import gdown

    if output is None:
        if isinstance(url, str) and url.startswith("http"):
            output = os.path.basename(url)

    if isinstance(url, str):
        if os.path.exists(os.path.abspath(output)) and (not overwrite):
            print(
                f"{output} already exists. Skip downloading. Set overwrite=True to overwrite."
            )
            return os.path.abspath(output)
        else:
            url = github_raw_url(url)

    if "https://drive.google.com/file/d/" in url:
        fuzzy = True

    output = gdown.download(
        url, output, quiet, proxy, speed, use_cookies, verify, id, fuzzy, resume
    )

    if unzip and output.endswith(".zip"):
        with zipfile.ZipFile(output, "r") as zip_ref:
            if not quiet:
                print("Extracting files...")
            zip_ref.extractall(os.path.dirname(output))

    return os.path.abspath(output)


def geojson_to_ee(
    geo_json: Union[Dict[str, Any], str],
    geodesic: bool = False,
    encoding: str = "utf-8",
) -> Union[ee.Geometry, ee.FeatureCollection]:
    """Converts a GeoJSON to an Earth Engine Geometry or FeatureCollection.

    Args:
        geo_json (Union[Dict[str, Any], str]): A GeoJSON geometry dictionary or
            file path.
        geodesic (bool, optional): Whether line segments should be interpreted
            as spherical geodesics. If false, indicates that line segments
            should be interpreted as planar lines in the specified CRS. If
            absent, defaults to true if the CRS is geographic (including the
            default EPSG:4326), or to false if the CRS is projected. Defaults to False.
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    Returns:
        Union[ee.Geometry, ee.FeatureCollection]: An Earth Engine Geometry or FeatureCollection.

    Raises:
        Exception: If the GeoJSON cannot be converted to an Earth Engine object.
    """

    try:
        if isinstance(geo_json, str):
            if geo_json.startswith("http") and geo_json.endswith(".geojson"):
                geo_json = github_raw_url(geo_json)
                out_geojson = temp_file_path(extension=".geojson")
                download_file(geo_json, out_geojson)
                with open(out_geojson, "r", encoding=encoding) as f:
                    geo_json = json.loads(f.read())
                os.remove(out_geojson)

            elif os.path.isfile(geo_json):
                with open(os.path.abspath(geo_json), encoding=encoding) as f:
                    geo_json = json.load(f)

        # geo_json["geodesic"] = geodesic
        if geo_json["type"] == "FeatureCollection":
            for feature in geo_json["features"]:
                if feature["geometry"]["type"] != "Point":
                    feature["geometry"]["geodesic"] = geodesic
            features = ee.FeatureCollection(geo_json)
            return features
        elif geo_json["type"] == "Feature":
            geom = None
            if "style" in geo_json["properties"]:
                keys = geo_json["properties"]["style"].keys()
                if "radius" in keys:  # Checks whether it is a circle
                    geom = ee.Geometry(geo_json["geometry"])
                    radius = geo_json["properties"]["style"]["radius"]
                    geom = geom.buffer(radius)
                elif geo_json["geometry"]["type"] == "Point":
                    geom = ee.Geometry(geo_json["geometry"])
                else:
                    geom = ee.Geometry(geo_json["geometry"], "", geodesic)
            elif (
                geo_json["geometry"]["type"] == "Point"
            ):  # Checks whether it is a point
                coordinates = geo_json["geometry"]["coordinates"]
                longitude = coordinates[0]
                latitude = coordinates[1]
                geom = ee.Geometry.Point(longitude, latitude)
            else:
                geom = ee.Geometry(geo_json["geometry"], "", geodesic)
            return geom
        else:
            raise Exception("Could not convert the geojson to ee.Geometry()")

    except Exception as e:
        print("Could not convert the geojson to ee.Geometry()")
        raise Exception(e)
