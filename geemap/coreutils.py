import base64
import json
import os
import random
import string
import sys
import tempfile
from typing import Any, Union
import uuid
import webbrowser
import zipfile

import box
import ee
import ipyleaflet
import ipywidgets as widgets
from matplotlib import colors

from . import colormaps

try:
    from IPython.display import display, Javascript
except ImportError:
    pass


def get_env_var(key: str) -> str | None:
    """Returns an environment variable or Colab secret for the given key.

    Colab secrets have precedence over environment variables.

    Args:
        key: The key that's used to fetch the environment variable.
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
    auth_mode: str | None = None,
    auth_args: dict[str, Any] | None = None,
    user_agent_prefix: str = "geemap",
    project: str | None = None,
    **kwargs: Any,
) -> None:
    """Authenticates Earth Engine and initialize an Earth Engine session.

    Args:
        token_name: The name of the Earth Engine token.
            Defaults to "EARTHENGINE_TOKEN". In Colab, you can also set a secret
            named "EE_PROJECT_ID" to initialize Earth Engine.
        auth_mode: The authentication mode, can be one of colab, notebook, localhost, or
            gcloud. See https://developers.google.com/earth-engine/guides/auth for more
            details. Defaults to None.
        auth_args: Additional authentication parameters for aa.Authenticate().
            Defaults to {}.
        user_agent_prefix: If set, the prefix (version-less) value used for setting the
            user-agent string. Defaults to "geemap".
        project: The Google cloud project ID for Earth Engine. Defaults to None.
        kwargs: Additional parameters for ee.Initialize(). For example,
            opt_url='https://earthengine-highvolume.googleapis.com' to use the Earth
            Engine High-Volume platform. Defaults to {}.
    """
    import google.oauth2.credentials
    from .__init__ import __version__

    user_agent = f"{user_agent_prefix}/{__version__}"
    ee.data.setUserAgent(user_agent)

    # pylint: disable-next=protected-access
    if ee.data._get_state().credentials is not None:
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
        # pylint: disable-next=protected-access
        if in_colab_shell() and (ee.data._get_state().credentials is None):
            ee.Authenticate()
            ee.Initialize(**kwargs)
            return
        else:
            auth_mode = "notebook"

    auth_args["auth_mode"] = auth_mode

    ee.Authenticate(**auth_args)
    ee.Initialize(**kwargs)


def new_tree_node(
    label: str,
    children: list[dict[str, Any]] | None = None,
    expanded: bool = False,
    top_level: bool = False,
) -> dict[str, Any]:
    """Returns node JSON for an interactive representation of an EE ComputedObject."""
    return {
        "label": label,
        "children": children or [],
        "expanded": expanded,
        "topLevel": top_level,
    }


def _order_items(item_dict: dict[str, Any], ordering_list: list[str]) -> dict[str, Any]:
    """Orders dictionary items in a specified order.

    Adapted from https://github.com/google/earthengine-jupyter.
    """
    # Keys consist of:
    # - keys in ordering_list first, in the correct order; and then
    # - keys not in ordering_list, sorted.
    ordered_pairs = [x for x in ordering_list if x in item_dict.keys()]
    remaining = sorted([x for x in item_dict if x not in ordering_list])
    return {key: item_dict[key] for key in ordered_pairs + remaining}


def _format_dictionary_node_name(index: int, item: dict[str, Any]) -> str:
    node_name = f"{index}: "
    extensions = []
    if "id" in item:
        extensions.append(f"\"{item['id']}\"")
    if "data_type" in item:
        extensions.append(str(item["data_type"]["precision"]))
    if "crs" in item:
        extensions.append(str(item["crs"]))
    if "dimensions" in item:
        dimensions = item["dimensions"]
        extensions.append(f"{dimensions[0]}x{dimensions[1]} px")
    node_name += ", ".join(extensions)
    return node_name


def _generate_tree(
    info: list[Any] | dict[str, Any], opened: bool
) -> list[dict[str, Any]]:
    node_list = []
    if isinstance(info, list):
        for index, item in enumerate(info):
            node_name = f"{index}: {item}"
            children = []
            if isinstance(item, dict):
                node_name = _format_dictionary_node_name(index, item)
                children = _generate_tree(item, opened)
            node_list.append(new_tree_node(node_name, children, expanded=opened))
    elif isinstance(info, dict):
        for k, v in info.items():
            if isinstance(v, (list, dict)):
                if k == "properties":
                    k = f"properties: Object ({len(v)} properties)"
                elif k == "bands":
                    k = f"bands: List ({len(v)} elements)"
                node_list.append(
                    new_tree_node(f"{k}", _generate_tree(v, opened), expanded=opened)
                )
            else:
                node_list.append(new_tree_node(f"{k}: {v}", expanded=opened))
    else:
        node_list.append(new_tree_node(f"{info}", expanded=opened))
    return node_list


def build_computed_object_tree(
    ee_object: ee.FeatureCollection | ee.Image | ee.Geometry | ee.Feature,
    layer_name: str = "",
    opened: bool = False,
) -> dict[str, Any]:
    """Return a tree structure representing an EE object.

    The source code was adapted from https://github.com/google/earthengine-jupyter.
    Credits to Tyler Erickson.

    Args:
        ee_object: The Earth Engine object.
        layer_name: The name of the layer. Defaults to "".
        opened: Whether to expand the tree. Defaults to False.

    Returns:
        The node representing the Earth Engine object information.
    """
    # Convert EE object props to dicts. It's easier to traverse the nested structure.
    if isinstance(ee_object, ee.FeatureCollection):
        ee_object = ee_object.map(lambda f: ee.Feature(None, f.toDictionary()))

    layer_info = ee_object.getInfo()
    if not layer_info:
        return {}

    # Strip geometries because they're slow to render as text.
    if "geometry" in layer_info:
        layer_info.pop("geometry")

    # Sort the keys in layer_info and the nested properties.
    if properties := layer_info.get("properties"):
        layer_info["properties"] = dict(sorted(properties.items()))
    ordering_list = ["type", "id", "version", "bands", "properties"]
    layer_info = _order_items(layer_info, ordering_list)

    ee_type = layer_info.get("type", ee_object.__class__.__name__)

    band_info = ""
    if bands := layer_info.get("bands"):
        band_info = f" ({len(bands)} bands)"
    if layer_name:
        layer_name = f"{layer_name}: "

    return new_tree_node(
        f"{layer_name}{ee_type}{band_info}",
        _generate_tree(layer_info, opened),
        expanded=opened,
    )


def get_info(
    ee_object: ee.FeatureCollection | ee.Image | ee.Geometry | ee.Feature,
    layer_name: str = "",
    opened: bool = False,
    return_node: bool = False,
) -> Union["Node", "Tree", None]:
    """Print out the information for an Earth Engine object using a tree structure.

    The source code was adapted from https://github.com/google/earthengine-jupyter.
    Credits to Tyler Erickson.

    Args:
        ee_object: The Earth Engine object.
        layer_name: The name of the layer. Defaults to "".
        opened: Whether to expand the tree. Defaults to False.
        return_node: Whether to return the widget as ipytree.Node.
            If False, returns the widget as ipytree.Tree. Defaults to False.

    Returns:
        The tree or node representing the Earth Engine object information.
    """
    import ipytree

    tree_json = build_computed_object_tree(ee_object, layer_name, opened)

    def _create_node(data):
        """Create a widget for the computed object tree."""
        node = ipytree.Node(
            data.get("label", "Node"), opened=data.get("expanded", False)
        )
        if children := data.get("children"):
            for child in children:
                node.add_node(_create_node(child))
        else:
            node.icon = "file"
            node.value = str(data)  # Store the entire data as a string.
        return node

    root_node = _create_node(tree_json)
    if return_node:
        return root_node
    else:
        tree = ipytree.Tree()
        tree.add_node(root_node)
        return tree


def create_code_cell(code: str = "", where: str = "below") -> None:
    """Creates a code cell in the IPython Notebook.

    Args:
        code: Code to fill the new code cell with. Defaults to ''.
        where: Where to add the new code cell. It can be one of the following: above,
            below, at_bottom. Defaults to 'below'.
    """
    import pyperclip

    try:
        pyperclip.copy(str(code))
    except Exception as e:
        pass

    encoded_code = (base64.b64encode(str.encode(code))).decode()
    display(
        Javascript(
            f"""
        var code = IPython.notebook.insert_cell_{where}('code');
        code.set_text(atob("{encoded_code}"));
    """
        )
    )


def geometry_type(ee_object: Any) -> str:
    """Get geometry type of an Earth Engine object.

    Args:
        ee_object: An Earth Engine object.

    Returns:
        One of Point, MultiPoint, LineString, LinearRing, MultiLineString, BBox,
            Rectangle, Polygon, MultiPolygon.

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
            "ee_object must be one of ee.Geometry, ee.Feature, ee.FeatureCollection."
        )


def get_google_maps_api_key(key: str = "GOOGLE_MAPS_API_KEY") -> str | None:
    """Returns the Google Maps API key from the environment or Colab user data.

    Args:
        key: The name of the environment variable or Colab user data key where the API
            key is stored. Defaults to 'GOOGLE_MAPS_API_KEY'.
    """
    if api_key := get_env_var(key):
        return api_key
    return os.environ.get(key, None)


def in_colab_shell() -> bool:
    """Returns True if the code is running in a Google Colab environment."""
    return "google.colab" in sys.modules


def check_color(in_color: str | tuple | list) -> str:
    """Checks the input color and returns the corresponding hex color code.

    Args:
        in_color: Can be a string (e.g., 'red', '#ffff00', 'ffff00', 'ff0') or RGB
          tuple/list (e.g., (255, 127, 0)).

    Returns:
        A hex color code.
    """
    out_color = "#000000"  # Default black color.
    # Handle RGB tuple or list.
    if isinstance(in_color, (tuple, list)) and len(in_color) == 3:
        # Rescale color if necessary.
        if all(isinstance(item, int) for item in in_color):
            # Ensure values are floats between 0 and 1 for to_hex.
            in_color = [c / 255.0 for c in in_color]
        try:
            return colors.to_hex(in_color)
        except ValueError:
            print(
                f"The provided RGB color ({in_color}) is invalid. "
                "Using the default black color."
            )
            return out_color

    # Handle string color input.
    elif isinstance(in_color, str):
        try:
            # Try converting directly (handles color names and hex with #).
            return colors.to_hex(in_color)
        except ValueError:
            try:
                # Try again by adding an extra # (handles hex without #)
                return colors.to_hex(f"#{in_color}")
            except ValueError:
                print(
                    f"The provided color string ({in_color}) is invalid. "
                    "Using the default black color."
                )
                return out_color
    else:
        print(
            f"The provided color type ({type(in_color)}) is invalid. "
            "Using the default black color."
        )
        return out_color


def check_cmap(cmap: str | list[str]) -> list[str] | str:
    """Check the colormap and return a list of colors.

    Args:
        cmap: The colormap to check.

    Returns:
        A list of colors.
    """
    if isinstance(cmap, str):
        try:
            palette = colormaps.get_palette(cmap)
            if isinstance(palette, dict):
                palette = palette["default"]
            return palette
        except Exception as e:
            try:
                return check_color(cmap)
            except Exception as e:
                raise Exception(f"{cmap} is not a valid colormap.")
    elif isinstance(cmap, box.Box):
        return list(cmap["default"])  # pytype: disable=unsupported-operands
    elif isinstance(cmap, list) or isinstance(cmap, tuple):
        return cmap
    else:
        raise Exception(f"{cmap} is not a valid colormap.")


def to_hex_colors(colors: list[str | tuple[int, int, int]]) -> list[str]:
    """Convert a GEE color palette into hexadecimal color codes.

    Can handle mixed formats.

    Args:
        colors: A list of colors in hex or RGB format.

    Returns:
        A list of hex color codes prefixed with #.
    """
    return [check_color(c) for c in colors]


def rgb_to_hex(rgb: tuple[int, int, int] = (255, 255, 255)) -> str:
    """Converts RGB to hex color.

    In RGB color, R stands for Red, G stands for Green, and B stands
    for Blue, and it ranges from the decimal value of 0 – 255.

    Args:

        rgb: RGB color code as a tuple of (red, green, blue).
            Defaults to (255, 255, 255).

    Returns:
        Hex color code.
    """
    return "%02x%02x%02x" % rgb


def hex_to_rgb(value: str = "FFFFFF") -> tuple[int, int, int]:
    """Converts hex color to RGB color.

    Args:
        value: Hex color code as a string. Defaults to 'FFFFFF'.

    Returns:
        RGB color as a tuple.
    """
    value = value.lstrip("#")
    lv = len(value)
    return tuple(int(value[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))


def random_string(string_length: int = 3) -> str:
    """Returns a random string of fixed length.

    Args:
        string_length: Fixed length. Defaults to 3.
    """
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(string_length))


def widget_template(
    widget: widgets.Widget | None = None,
    opened: bool = True,
    show_close_button: bool = True,
    widget_icon: str = "gear",
    close_button_icon: str = "times",
    widget_args: dict[str, Any] | None = None,
    close_button_args: dict[str, Any] | None = None,
    display_widget: widgets.Widget | None = None,
    m: ipyleaflet.Map | None = None,
    position: str = "topright",
) -> widgets.Widget | None:
    """Create a widget template.

    Args:
        widget: The widget to be displayed. Defaults to None.
        opened: Whether to open the toolbar. Defaults to True.
        show_close_button: Whether to show the close button. Defaults to True.
        widget_icon: The icon name for the toolbar button. Defaults to 'gear'.
        close_button_icon: The icon name for the close button. Defaults to "times".
        widget_args: Additional arguments to pass to the toolbar button.
            Defaults to None.
        close_button_args: Additional arguments to pass to the close button.
            Defaults to None.
        display_widget: The widget to be displayed when the toolbar is clicked.
            Defaults to None.
        m: The ipyleaflet.Map instance. Defaults to None.
        position: The position of the toolbar. Defaults to "topright".

    Returns:
        The created widget template.
    """
    name = "_" + random_string()  # A random attribute name.

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
        url: The URL to open.
    """
    if in_colab_shell():
        display(Javascript(f'window.open("{url}", "_blank", "noopener")'))
    else:
        webbrowser.open_new_tab(url)


def github_raw_url(url: str) -> str:
    """Returns the raw URL for a GitHub file.

    Args:
        url: The GitHub URL.
    """
    if isinstance(url, str) and url.startswith("https://github.com/") and "blob" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace(
            "blob/", "", 1
        )
    return url


def temp_file_path(extension: str) -> str:
    """Returns a temporary file path.

    Args:
        extension: The file extension.
    """
    if not extension.startswith("."):
        extension = "." + extension
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{extension}")

    return file_path


def download_file(
    url: str | None = None,
    output: str | None = None,
    quiet: bool = False,
    proxy: str | None = None,
    speed: float | None = None,
    use_cookies: bool = True,
    verify: bool | str = True,
    id: str | None = None,
    fuzzy: bool = False,
    resume: bool = False,
    unzip: bool = True,
    overwrite: bool = False,
) -> str:
    """Download a file from URL, including Google Drive shared URL.

    Args:
        url: Google Drive URL is also supported.
            Defaults to None.
        output: Output filename. Default is basename of URL.
        quiet: Suppress terminal output. Default is False.
        proxy: Proxy. Defaults to None.
        speed: Download byte size per second (e.g., 256KB/s = 256 * 1024).
            Defaults to None.
        use_cookies: Flag to use cookies. Defaults to True.
        verify: Either a bool, in which case it controls whether the server's TLS
            certificate is verified, or a string, in which case it must be a path to a
            CA bundle to use.
            Default is True.
        id: Google Drive's file ID. Defaults to None.
        fuzzy: Fuzzy extraction of Google Drive's file Id.
            Defaults to False.
        resume: Resume the download from existing tmp file if possible.
            Defaults to False.
        unzip: Unzip the file. Defaults to True.
        overwrite: Overwrite the file if it already exists.
            Defaults to False.

    Returns:
        The output file path.
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
    geo_json: dict[str, Any] | str,
    geodesic: bool = False,
    encoding: str = "utf-8",
) -> ee.Geometry | ee.FeatureCollection:
    """Converts a GeoJSON to an Earth Engine Geometry or FeatureCollection.

    Args:
        geo_json: A GeoJSON geometry dictionary or file path.
        geodesic: Whether line segments should be interpreted as spherical geodesics. If
            false, indicates that line segments should be interpreted as planar lines in
            the specified CRS. If absent, defaults to true if the CRS is geographic
            (including the default EPSG:4326), or to false if the CRS is
            projected.
            Defaults to False.
        encoding: The encoding of characters. Defaults to "utf-8".

    Returns:
        Earth Engine Geometry or FeatureCollection.

    Raises:
        Exception: If the GeoJSON cannot be converted to an Earth Engine object.
    """

    try:
        if isinstance(geo_json, str):
            if geo_json.startswith("http") and geo_json.endswith(".geojson"):
                geo_json = github_raw_url(geo_json)
                out_geojson = temp_file_path(extension=".geojson")
                download_file(geo_json, out_geojson)
                with open(out_geojson, encoding=encoding) as f:
                    geo_json = json.loads(f.read())
                os.remove(out_geojson)

            elif os.path.isfile(geo_json):
                with open(os.path.abspath(geo_json), encoding=encoding) as f:
                    geo_json = json.load(f)

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
                if "radius" in keys:  # Checks whether it is a circle.
                    geom = ee.Geometry(geo_json["geometry"])
                    radius = geo_json["properties"]["style"]["radius"]
                    geom = geom.buffer(radius)
                elif geo_json["geometry"]["type"] == "Point":
                    geom = ee.Geometry(geo_json["geometry"])
                else:
                    geom = ee.Geometry(geo_json["geometry"], "", geodesic)
            elif (
                geo_json["geometry"]["type"] == "Point"
            ):  # Checks whether it is a point.
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
