""" This module extends the folium Map class. It is designed to be used in Google Colab, as Google Colab currently does not support ipyleaflet.
"""

import colour
import ee
import folium
import os
import ipywidgets as widgets
from folium import plugins
from .conversion import *


def ee_initialize(token_name='EARTHENGINE_TOKEN'):
    """Authenticates Earth Engine and initialize an Earth Engine session

    """
    try:
        ee_token = os.environ.get(token_name)
        if ee_token is not None:
            credential = '{"refresh_token":"%s"}' % ee_token
            credential_file_path = os.path.expanduser("~/.config/earthengine/")
            os.makedirs(credential_file_path, exist_ok=True)
            with open(credential_file_path + 'credentials', 'w') as file:
                file.write(credential)
        elif in_colab_shell():
            if credentials_in_drive() and (not credentials_in_colab()):
                copy_credentials_to_colab()
            elif not credentials_in_colab:
                ee.Authenticate()
                if is_drive_mounted() and (not credentials_in_drive()):
                    copy_credentials_to_drive() 
            else:
                if is_drive_mounted():
                    copy_credentials_to_drive()       

        ee.Initialize()
    except:
        ee.Authenticate()
        ee.Initialize()


# More WMS basemaps can be found at https://viewer.nationalmap.gov/services/
ee_basemaps = {
    'ROADMAP': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Maps',
        overlay=True,
        control=True
    ),

    'SATELLITE': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=True,
        control=True
    ),

    'TERRAIN': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Terrain',
        overlay=True,
        control=True
    ),

    'HYBRID': folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=True,
        control=True
    ),

    'ESRI': folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=True,
        control=True
    ),

    'Esri Ocean': folium.TileLayer(
        tiles='https://services.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Ocean',
        overlay=True,
        control=True
    ),

    'Esri Satellite': folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=True,
        control=True
    ),

    'Esri Standard': folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Standard',
        overlay=True,
        control=True
    ),

    'Esri Terrain': folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Terrain',
        overlay=True,
        control=True
    ),

    'Esri Transportation': folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Transportation',
        overlay=True,
        control=True
    ),

    'Esri Topo World': folium.TileLayer(
        tiles='https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Topo World',
        overlay=True,
        control=True
    ),

    'Esri National Geographic': folium.TileLayer(
        tiles='http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri National Geographic',
        overlay=True,
        control=True
    ),

    'Esri Shaded Relief': folium.TileLayer(
        tiles='https://services.arcgisonline.com/arcgis/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Shaded Relief',
        overlay=True,
        control=True
    ),

    'Esri Physical Map': folium.TileLayer(
        tiles='https://services.arcgisonline.com/arcgis/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Physical Map',
        overlay=True,
        control=True
    ),

    'Bing VirtualEarth': folium.TileLayer(
        tiles='http://ecn.t3.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1',
        attr='Microsoft',
        name='Bing VirtualEarth',
        overlay=True,
        control=True
    ),

    '3DEP Elevation': folium.WmsTileLayer(
        url='https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WMSServer?',
        layers='3DEPElevation:None',
        attr='USGS',
        name='3DEP Elevation',
        overlay=True,
        control=True
    ),

    'NAIP Imagery': folium.WmsTileLayer(
        url='https://services.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?',
        layers='0',
        attr='USGS',
        name='NAIP Imagery',
        overlay=True,
        control=True
    ),
}


class Map(folium.Map):
    """The Map class inherits from folium.Map. By default, the Map will add Google Maps as the basemap. Set add_google_map = False to use OpenStreetMap as the basemap.

    Returns:
        object: folium map object.
    """

    def __init__(self, **kwargs):

        import logging
        logging.getLogger(
            'googleapiclient.discovery_cache').setLevel(logging.ERROR)
        ee_initialize()

        # Default map center location and zoom level
        latlon = [40, -100]
        zoom = 4

        # Interchangeable parameters between ipyleaflet and folium
        if 'center' in kwargs.keys():
            kwargs['location'] = kwargs['center']
            kwargs.pop('center')
        if 'location' in kwargs.keys():
            latlon = kwargs['location']
        else:
            kwargs['location'] = latlon

        if 'zoom' in kwargs.keys():
            kwargs['zoom_start'] = kwargs['zoom']
            kwargs.pop('zoom')
        if 'zoom_start' in kwargs.keys():
            zoom = kwargs['zoom_start']
        else:
            kwargs['zoom_start'] = zoom

        if 'add_google_map' not in kwargs.keys():
            kwargs['add_google_map'] = True

        super().__init__(**kwargs)

        if kwargs.get('add_google_map'):
            ee_basemaps['ROADMAP'].add_to(self)
        folium.LatLngPopup().add_to(self)
        # plugins.Fullscreen().add_to(self)

        self.fit_bounds([latlon, latlon], max_zoom=zoom)

    def setOptions(self, mapTypeId='HYBRID', styles={}, types=[]):
        """Adds Google basemap to the map.

        Args:
            mapTypeId (str, optional): A mapTypeId to set the basemap to. Can be one of "ROADMAP", "SATELLITE", "HYBRID" or "TERRAIN" to select one of the standard Google Maps API map types. Defaults to 'HYBRID'.
            styles ([type], optional): A dictionary of custom MapTypeStyle objects keyed with a name that will appear in the map's Map Type Controls. Defaults to None.
            types ([type], optional): A list of mapTypeIds to make available. If omitted, but opt_styles is specified, appends all of the style keys to the standard Google Maps API map types.. Defaults to None.
        """
        try:
            ee_basemaps[mapTypeId].add_to(self)
        except:
            print('Basemap can only be one of the following: {}'.format(
                ', '.join(ee_basemaps.keys())))

    set_options = setOptions

    def add_basemap(self, basemap='HYBRID'):
        """Adds a basemap to the map.

        Args:
            basemap (str, optional): Can be one of string from ee_basemaps. Defaults to 'HYBRID'.
        """
        try:
            ee_basemaps[basemap].add_to(self)
        except:
            print('Basemap can only be one of the following: {}'.format(
                ', '.join(ee_basemaps.keys())))

    def add_layer(self, ee_object, vis_params={}, name='Layer untitled', shown=True, opacity=1.0):
        """Adds a given EE object to the map as a layer.

        Args:
            ee_object (Collection|Feature|Image|MapId): The object to add to the map.
            vis_params (dict, optional): The visualization parameters. Defaults to {}.
            name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
        """
        image = None

        if not isinstance(ee_object, ee.Image) and not isinstance(ee_object, ee.ImageCollection) and not isinstance(ee_object, ee.FeatureCollection) and not isinstance(ee_object, ee.Feature) and not isinstance(ee_object, ee.Geometry):
            err_str = "\n\nThe image argument in 'addLayer' function must be an instace of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
            raise AttributeError(err_str)

        if isinstance(ee_object, ee.geometry.Geometry) or isinstance(ee_object, ee.feature.Feature) or isinstance(ee_object, ee.featurecollection.FeatureCollection):
            features = ee.FeatureCollection(ee_object)

            width = 2

            if 'width' in vis_params:
                width = vis_params['width']

            color = '000000'

            if 'color' in vis_params:
                color = vis_params['color']

            image_fill = features.style(
                **{'fillColor': color}).updateMask(ee.Image.constant(0.5))
            image_outline = features.style(
                **{'color': color, 'fillColor': '00000000', 'width': width})

            image = image_fill.blend(image_outline)
        elif isinstance(ee_object, ee.image.Image):
            image = ee_object
        elif isinstance(ee_object, ee.imagecollection.ImageCollection):
            image = ee_object.mosaic()

        map_id_dict = ee.Image(image).getMapId(vis_params)
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name=name,
            overlay=True,
            control=True,
            show=shown,
            opacity=opacity
        ).add_to(self)

    addLayer = add_layer

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
        bounds = [[lat, lon], [lat, lon]]
        if isinstance(ee_object, ee.geometry.Geometry):
            centroid = ee_object.centroid()
            lon, lat = centroid.getInfo()['coordinates']
            bounds = [[lat, lon], [lat, lon]]
        elif isinstance(ee_object, ee.featurecollection.FeatureCollection):
            centroid = ee_object.geometry().centroid()
            lon, lat = centroid.getInfo()['coordinates']
            bounds = [[lat, lon], [lat, lon]]
        elif isinstance(ee_object, ee.image.Image):
            geometry = ee_object.geometry()
            coordinates = geometry.getInfo()['coordinates'][0]
            bounds = [coordinates[0][::-1], coordinates[2][::-1]]
        elif isinstance(ee_object, ee.imagecollection.ImageCollection):
            geometry = ee_object.geometry()
            coordinates = geometry.getInfo()['coordinates'][0]
            bounds = [coordinates[0][::-1], coordinates[2][::-1]]
        else:
            bounds = [[0, 0], [0, 0]]

        self.fit_bounds(bounds, max_zoom=zoom)

    centerObject = center_object

    def set_control_visibility(self, layerControl=True, fullscreenControl=True, latLngPopup=True):
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
        """Adds layer basemap to the map.
        """
        folium.LayerControl().add_to(self)

    addLayerControl = add_layer_control

    def add_wms_layer(self, url, layers, name=None, attribution='', overlay=True, control=True, shown=True, format='image/png'):
        """Add a WMS layer to the map.

        Args:
            url (str): The URL of the WMS web service.
            layers (str): Comma-separated list of WMS layers to show. 
            name (str, optional): The layer name to use on the layer control. Defaults to None.
            attribution (str, optional): The attribution of the data layer. Defaults to ''.
            overlay (str, optional): Allows overlay. Defaults to True.
            control (str, optional): Adds the layer to the layer control. Defaults to True.
            shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
            format (str, optional): WMS image format (use ‘image/png’ for layers with transparency). Defaults to 'image/jpeg'.
        """
        try:
            folium.raster_layers.WmsTileLayer(
                url=url,
                layers=layers,
                attr=attribution,
                name=name,
                overlay=overlay,
                control=control,
                show=shown
            ).add_to(self)
        except:
            print("Failed to add the specified WMS TileLayer.")

    def add_tile_layer(self, tiles='OpenStreetMap', name=None, attribution='', overlay=True, control=True, shown=True, opacity=1.0, API_key=None):
        """Add a XYZ tile layer to the map.

        Args:
            tiles (str): The URL of the XYZ tile service.
            name (str, optional): The layer name to use on the layer control. Defaults to None.
            attribution (str, optional): The attribution of the data layer. Defaults to ''.
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
                API_key=API_key
            ).add_to(self)
        except:
            print("Failed to add the specified TileLayer.")

    def publish(self, name=None, headline='Untitled', visibility='PUBLIC', overwrite=True, open=True):
        """Publish the map to datapane.com

        Args:
            name (str, optional): The URL of the map. Defaults to None.
            headline (str, optional): Title of the map. Defaults to 'Untitled'.
            visibility (str, optional): Visibility of the map. It can be one of the following: PUBLIC, PRIVATE, ORG. Defaults to 'PUBLIC'.
            overwrite (bool, optional): Whether to overwrite the existing map with the same name. Defaults to True.
            open (bool, optional): Whether to open the map. Defaults to True.
        """
        import webbrowser
        try:
            import datapane as dp
        except Exception as e:
            print('The datapane Python package is not installed. You need to install and authenticate datapane first.')
            webbrowser.open_new_tab(
                'https://docs.datapane.com/tutorials/tut-getting-started')
            return

        import datapane as dp
        # import logging
        # logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

        if name is None:
            name = 'folium_' + random_string(6)

        visibility = visibility.upper()
        if visibility not in ['PUBLIC', 'PRIVATE', 'ORG']:
            visibility = 'PRIVATE'

        if overwrite:
            delete_dp_report(name)

        report = dp.Report(dp.Plot(self))
        report.publish(name=name, headline=headline,
                       visibility=visibility, open=open)


def delete_dp_report(name):
    """Deletes a datapane report.

    Args:
        name (str): Name of the report to delete.
    """
    try:
        import datapane as dp

        reports = dp.Report.list()
        items = list(reports)
        names = list(map(lambda item: item['name'], items))
        if name in names:
            report = dp.Report.get(name)
            url = report.blocks[0]['url']
            # print('Deleting {}...'.format(url))
            dp.Report.delete(dp.Report.by_id(url))
    except Exception as e:
        print(e)
        return


def delete_dp_reports():
    """Deletes all datapane reports.
    """
    try:
        import datapane as dp
        reports = dp.Report.list()
        for item in reports:
            print(item['name'])
            report = dp.Report.get(item['name'])
            url = report.blocks[0]['url']
            print('Deleting {}...'.format(url))
            dp.Report.delete(dp.Report.by_id(url))
    except Exception as e:
        print(e)
        return


def install_from_github(url):
    """Install a package from a GitHub repository.

    Args:
        url (str): The URL of the GitHub repository.
    """

    try:
        download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        repo_name = os.path.basename(url)
        zip_url = os.path.join(url, 'archive/master.zip')
        filename = repo_name + '-master.zip'
        download_from_url(url=zip_url, out_file_name=filename,
                          out_dir=download_dir, unzip=True)

        pkg_dir = os.path.join(download_dir, repo_name + '-master')
        work_dir = os.getcwd()
        os.chdir(pkg_dir)
        cmd = 'pip install .'
        os.system(cmd)
        os.chdir(work_dir)

        print("\nPlease comment out 'install_from_github()' and restart the kernel to take effect:\nJupyter menu -> Kernel -> Restart & Clear Output")

    except Exception as e:
        print(e)


def rgb_to_hex(rgb=(255, 255, 255)):
    """Converts RGB to hex color. In RGB color R stands for Red, G stands for Green, and B stands for Blue, and it ranges from the decimal value of 0 – 255.

    Args:
        rgb (tuple, optional): RGB color code as a tuple of (red, green, blue). Defaults to (255, 255, 255).

    Returns:
        str: hex color code
    """
    return '%02x%02x%02x' % rgb


def hex_to_rgb(value='FFFFFF'):
    """Converts hex color to RGB color. 

    Args:
        value (str, optional): Hex color code as a string. Defaults to 'FFFFFF'.

    Returns:
        tuple: RGB color as a tuple.
    """
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))


def check_color(in_color):
    """Checks the input color and returns the corresponding hex color code.

    Args:
        in_color (str or tuple): It can be a string (e.g., 'red', '#ffff00') or tuple (e.g., (255, 127, 0)).

    Returns:
        str: A hex color code.
    """
    out_color = '#000000'  # default black color
    if isinstance(in_color, tuple) and len(in_color) == 3:
        if all(isinstance(item, int) for item in in_color):
            rescaled_color = [x / 255.0 for x in in_color]
            out_color = colour.Color(rgb=tuple(rescaled_color))
            return out_color.hex_l
        else:
            print(
                'RGB color must be a tuple with three integer values ranging from 0 to 255.')
            return
    else:
        try:
            out_color = colour.Color(in_color)
            return out_color.hex_l
        except Exception as e:
            print('The provided color is invalid. Using the default black color.')
            print(e)
            return out_color


def system_fonts(show_full_path=False):
    """Gets a list of system fonts.

        # Common font locations:
        # Linux: /usr/share/fonts/TTF/
        # Windows: C:\Windows\Fonts
        # macOS:  System > Library > Fonts

    Args:
        show_full_path (bool, optional): Whether to show the full path of each system font. Defaults to False.

    Returns:
        list: A list of system fonts.
    """
    try:
        import matplotlib.font_manager

        font_list = matplotlib.font_manager.findSystemFonts(
            fontpaths=None, fontext='ttf')
        font_list.sort()

        font_names = [os.path.basename(f) for f in font_list]
        font_names.sort()

        if show_full_path:
            return font_list
        else:
            return font_names

    except Exception as e:
        print(e)


def add_text_to_gif(in_gif, out_gif, xy=None, text_sequence=None, font_type="arial.ttf", font_size=20, font_color='#000000', add_progress_bar=True, progress_bar_color='white', progress_bar_height=5, duration=100, loop=0):
    """Adds animated text to a GIF image.

    Args:
        in_gif (str): The file path to the input GIF image.
        out_gif (str): The file path to the output GIF image.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        text_sequence (int, str, list, optional): Text to be drawn. It can be an integer number, a string, or a list of strings. Defaults to None.
        font_type (str, optional): Font type. Defaults to "arial.ttf".
        font_size (int, optional): Font size. Defaults to 20.
        font_color (str, optional): Font color. It can be a string (e.g., 'red'), rgb tuple (e.g., (255, 127, 0)), or hex code (e.g., '#ff00ff').  Defaults to '#000000'.
        add_progress_bar (bool, optional): Whether to add a progress bar at the bottom of the GIF. Defaults to True.
        progress_bar_color (str, optional): Color for the progress bar. Defaults to 'white'.
        progress_bar_height (int, optional): Height of the progress bar. Defaults to 5.
        duration (int, optional): controls how long each frame will be displayed for, in milliseconds. It is the inverse of the frame rate. Setting it to 100 milliseconds gives 10 frames per second. You can decrease the duration to give a smoother animation.. Defaults to 100.
        loop (int, optional): controls how many times the animation repeats. The default, 1, means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.

    """
    import io
    import pkg_resources
    import warnings
    from PIL import Image, ImageDraw, ImageSequence, ImageFont

    warnings.simplefilter('ignore')
    pkg_dir = os.path.dirname(
        pkg_resources.resource_filename("geemap", "geemap.py"))
    default_font = os.path.join(pkg_dir, 'data/fonts/arial.ttf')

    in_gif = os.path.abspath(in_gif)
    out_gif = os.path.abspath(out_gif)

    if not os.path.exists(in_gif):
        print('The input gif file does not exist.')
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if font_type == 'arial.ttf':
        font = ImageFont.truetype(default_font, font_size)
    else:
        try:
            font_list = system_fonts(show_full_path=True)
            font_names = [os.path.basename(f) for f in font_list]
            if (font_type in font_list) or (font_type in font_names):
                font = ImageFont.truetype(font_type, font_size)
            else:
                print(
                    'The specified font type could not be found on your system. Using the default font instead.')
                font = ImageFont.truetype(default_font, font_size)
        except Exception as e:
            print(e)
            font = ImageFont.truetype(default_font, font_size)

    color = check_color(font_color)
    progress_bar_color = check_color(progress_bar_color)

    try:
        image = Image.open(in_gif)
    except Exception as e:
        print('An error occurred while opening the gif.')
        print(e)
        return

    count = image.n_frames
    W, H = image.size
    progress_bar_widths = [i * 1.0 / count * W for i in range(1, count + 1)]
    progress_bar_shapes = [[(0, H - progress_bar_height), (x, H)]
                           for x in progress_bar_widths]

    if xy is None:
        # default text location is 5% width and 5% height of the image.
        xy = (int(0.05 * W), int(0.05 * H))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        print("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")
        return
    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < W) and (y > 0) and (y < H):
            pass
        else:
            print(
                'xy is out of bounds. x must be within [0, {}], and y must be within [0, {}]'.format(W, H))
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ('%' in x) and ('%' in y):
            try:
                x = int(float(x.replace('%', '')) / 100.0 * W)
                y = int(float(y.replace('%', '')) / 100.0 * H)
                xy = (x, y)
            except Exception as e:
                print(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')")
                return
    else:
        print("The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')")
        return

    if text_sequence is None:
        text = [str(x) for x in range(1, count + 1)]
    elif isinstance(text_sequence, int):
        text = [str(x) for x in range(
            text_sequence, text_sequence + count + 1)]
    elif isinstance(text_sequence, str):
        try:
            text_sequence = int(text_sequence)
            text = [str(x) for x in range(
                text_sequence, text_sequence + count + 1)]
        except Exception as e:
            text = [text_sequence] * count
    elif isinstance(text_sequence, list) and len(text_sequence) != count:
        print('The length of the text sequence must be equal to the number ({}) of frames in the gif.'.format(count))
        return
    else:
        text = [str(x) for x in text_sequence]

    try:

        frames = []
        # Loop over each frame in the animated image
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            # Draw the text on the frame
            frame = frame.convert('RGB')
            draw = ImageDraw.Draw(frame)
            # w, h = draw.textsize(text[index])
            draw.text(xy, text[index], font=font, fill=color)
            if add_progress_bar:
                draw.rectangle(
                    progress_bar_shapes[index], fill=progress_bar_color)
            del draw

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)

            frames.append(frame)
        # https://www.pythoninformer.com/python-libraries/pillow/creating-animated-gif/
        # Save the frames as a new image

        frames[0].save(out_gif, save_all=True,
                       append_images=frames[1:], duration=duration, loop=loop, optimize=True)
    except Exception as e:
        print(e)
        return


def open_image_from_url(url):
    """Loads an image from the specified URL.

    Args:
        url (str): URL of the image.

    Returns:
        object: Image object.
    """
    from PIL import Image
    import requests
    from io import BytesIO
    from urllib.parse import urlparse

    try:

        # if url.endswith('.gif'):
        #     out_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        #     if not os.path.exists(out_dir):
        #         os.makedirs(out_dir)
        #     a = urlparse(url)
        #     out_name = os.path.basename(a.path)
        #     out_path = os.path.join(out_dir, out_name)
        #     download_from_url(url, out_name, out_dir, unzip=False)
        #     img =  Image.open(out_path)
        # else:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        print(e)


def has_transparency(img):
    """Checks whether an image has transparency.

    Args:
        img (object):  a PIL Image object.

    Returns:
        bool: True if it has transparency, False otherwise.
    """

    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True

    return False


def add_image_to_gif(in_gif, out_gif, in_image, xy=None, image_size=(80, 80), circle_mask=False):
    """Adds an image logo to a GIF image.

    Args:
        in_gif (str): Input file path to the GIF image.
        out_gif (str): Output file path to the GIF image.
        in_image (str): Input file path to the image.
        xy (tuple, optional): Top left corner of the text. It can be formatted like this: (10, 10) or ('15%', '25%'). Defaults to None.
        image_size (tuple, optional): Resize image. Defaults to (80, 80).
        circle_mask (bool, optional): Whether to apply a circle mask to the image. This only works with non-png images. Defaults to False.
    """
    import io
    import warnings
    from PIL import Image, ImageDraw, ImageSequence, ImageFilter

    warnings.simplefilter('ignore')

    in_gif = os.path.abspath(in_gif)

    is_url = False
    if in_image.startswith('http'):
        is_url = True

    if not os.path.exists(in_gif):
        print('The input gif file does not exist.')
        return

    if (not is_url) and (not os.path.exists(in_image)):
        print('The provided logo file does not exist.')
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    try:
        image = Image.open(in_gif)
    except Exception as e:
        print('An error occurred while opening the image.')
        print(e)
        return

    try:
        if in_image.startswith('http'):
            logo_raw_image = open_image_from_url(in_image)
        else:
            in_image = os.path.abspath(in_image)
            logo_raw_image = Image.open(in_image)
    except Exception as e:
        print(e)

    logo_raw_size = logo_raw_image.size
    image_size = min(logo_raw_size[0], image_size[0]), min(
        logo_raw_size[1], image_size[1])

    logo_image = logo_raw_image.convert('RGBA')
    logo_image.thumbnail(image_size, Image.ANTIALIAS)

    W, H = image.size
    mask_im = None

    if circle_mask:
        mask_im = Image.new("L", image_size, 0)
        draw = ImageDraw.Draw(mask_im)
        draw.ellipse((0, 0, image_size[0], image_size[1]), fill=255)

    if has_transparency(logo_raw_image):
        mask_im = logo_image.copy()

    if xy is None:
        # default logo location is 5% width and 5% height of the image.
        xy = (int(0.05 * W), int(0.05 * H))
    elif (xy is not None) and (not isinstance(xy, tuple)) and (len(xy) == 2):
        print("xy must be a tuple, e.g., (10, 10), ('10%', '10%')")
        return
    elif all(isinstance(item, int) for item in xy) and (len(xy) == 2):
        x, y = xy
        if (x > 0) and (x < W) and (y > 0) and (y < H):
            pass
        else:
            print(
                'xy is out of bounds. x must be within [0, {}], and y must be within [0, {}]'.format(W, H))
            return
    elif all(isinstance(item, str) for item in xy) and (len(xy) == 2):
        x, y = xy
        if ('%' in x) and ('%' in y):
            try:
                x = int(float(x.replace('%', '')) / 100.0 * W)
                y = int(float(y.replace('%', '')) / 100.0 * H)
                xy = (x, y)
            except Exception as e:
                print(
                    "The specified xy is invalid. It must be formatted like this ('10%', '10%')")
                return
    else:
        print("The specified xy is invalid. It must be formatted like this: (10, 10) or ('10%', '10%')")
        return

    try:

        frames = []
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            frame = frame.convert('RGBA')
            frame.paste(logo_image, xy, mask_im)

            b = io.BytesIO()
            frame.save(b, format="GIF")
            frame = Image.open(b)
            frames.append(frame)

        frames[0].save(out_gif, save_all=True, append_images=frames[1:])
    except Exception as e:
        print(e)
        return


def show_image(img_path, width=None, height=None):
    """Shows an image within Jupyter notebook.

    Args:
        img_path (str): The image file path.
        width (int, optional): Width of the image in pixels. Defaults to None.
        height (int, optional): Height of the image in pixels. Defaults to None.

    """
    from IPython.display import display

    try:
        out = widgets.Output()
        # layout={'border': '1px solid black'})
        # layout={'border': '1px solid black', 'width': str(width + 20) + 'px', 'height': str(height + 10) + 'px'},)
        out.clear_output(wait=True)
        display(out)
        with out:
            file = open(img_path, "rb")
            image = file.read()
            if (width is None) and (height is None):
                display(widgets.Image(value=image))
            elif (width is not None) and (height is not None):
                display(widgets.Image(value=image, width=width, height=height))
            else:
                print('You need set both width and height.')
                return
    except Exception as e:
        print(e)


def legend_from_ee(ee_class_table):
    """Extract legend from an Earth Engine class table on the Earth Engine Data Catalog page
    such as https://developers.google.com/earth-engine/datasets/catalog/MODIS_051_MCD12Q1

    Value	Color	Description
    0	1c0dff	Water
    1	05450a	Evergreen needleleaf forest
    2	086a10	Evergreen broadleaf forest
    3	54a708	Deciduous needleleaf forest
    4	78d203	Deciduous broadleaf forest
    5	009900	Mixed forest
    6	c6b044	Closed shrublands
    7	dcd159	Open shrublands
    8	dade48	Woody savannas
    9	fbff13	Savannas
    10	b6ff05	Grasslands
    11	27ff87	Permanent wetlands
    12	c24f44	Croplands
    13	a5a5a5	Urban and built-up
    14	ff6d4c	Cropland/natural vegetation mosaic
    15	69fff8	Snow and ice
    16	f9ffa4	Barren or sparsely vegetated
    254	ffffff	Unclassified

    Args:
        ee_class_table (str): An Earth Engine class table with triple quotes.

    Returns:
        dict: Returns a legend dictionary that can be used to create a legend.
    """
    try:
        ee_class_table = ee_class_table.strip()
        lines = ee_class_table.split('\n')[1:]

        if lines[0] == 'Value\tColor\tDescription':
            lines = lines[1:]

        legend_dict = {}
        for index, line in enumerate(lines):
            items = line.split("\t")
            items = [item.strip() for item in items]
            color = items[1]
            key = items[0] + " " + items[2]
            legend_dict[key] = color

        return legend_dict

    except Exception as e:
        print(e)


def ee_tile_layer(ee_object, vis_params={}, name='Layer untitled', shown=True, opacity=1.0):
    """Converts and Earth Engine layer to ipyleaflet TileLayer.

    Args:
        ee_object (Collection|Feature|Image|MapId): The object to add to the map.
        vis_params (dict, optional): The visualization parameters. Defaults to {}.
        name (str, optional): The name of the layer. Defaults to 'Layer untitled'.
        shown (bool, optional): A flag indicating whether the layer should be on by default. Defaults to True.
        opacity (float, optional): The layer's opacity represented as a number between 0 and 1. Defaults to 1.
    """
    ee_initialize()

    image = None

    if not isinstance(ee_object, ee.Image) and not isinstance(ee_object, ee.ImageCollection) and not isinstance(ee_object, ee.FeatureCollection) and not isinstance(ee_object, ee.Feature) and not isinstance(ee_object, ee.Geometry):
        err_str = "\n\nThe image argument in 'addLayer' function must be an instace of one of ee.Image, ee.Geometry, ee.Feature or ee.FeatureCollection."
        raise AttributeError(err_str)

    if isinstance(ee_object, ee.geometry.Geometry) or isinstance(ee_object, ee.feature.Feature) or isinstance(ee_object, ee.featurecollection.FeatureCollection):
        features = ee.FeatureCollection(ee_object)

        width = 2

        if 'width' in vis_params:
            width = vis_params['width']

        color = '000000'

        if 'color' in vis_params:
            color = vis_params['color']

        image_fill = features.style(
            **{'fillColor': color}).updateMask(ee.Image.constant(0.5))
        image_outline = features.style(
            **{'color': color, 'fillColor': '00000000', 'width': width})

        image = image_fill.blend(image_outline)
    elif isinstance(ee_object, ee.image.Image):
        image = ee_object
    elif isinstance(ee_object, ee.imagecollection.ImageCollection):
        image = ee_object.mosaic()

    map_id_dict = ee.Image(image).getMapId(vis_params)
    tile_layer = ipyleaflet.TileLayer(
        url=map_id_dict['tile_fetcher'].url_format,
        attribution='Google Earth Engine',
        name=name,
        opacity=opacity,
        visible=True
        # visible=shown
    )
    return tile_layer


def geojson_to_ee(geo_json, geodesic=True):
    """Converts a geojson to ee.Geometry()

    Args:
        geo_json (dict): A geojson geometry dictionary or file path.

    Returns:
        ee_object: An ee.Geometry object
    """
    ee_initialize()

    try:

        import json

        if not isinstance(geo_json, dict) and os.path.isfile(geo_json):
            with open(os.path.abspath(geo_json)) as f:
                geo_json = json.load(f)

        if geo_json['type'] == 'FeatureCollection':
            features = ee.FeatureCollection(geo_json['features'])
            return features
        elif geo_json['type'] == 'Feature':
            geom = None
            keys = geo_json['properties']['style'].keys()
            if 'radius' in keys:  # Checks whether it is a circle
                geom = ee.Geometry(geo_json['geometry'])
                radius = geo_json['properties']['style']['radius']
                geom = geom.buffer(radius)
            elif geo_json['geometry']['type'] == 'Point':  # Checks whether it is a point
                coordinates = geo_json['geometry']['coordinates']
                longitude = coordinates[0]
                latitude = coordinates[1]
                geom = ee.Geometry.Point(longitude, latitude)
            else:
                geom = ee.Geometry(geo_json['geometry'], "", geodesic)
            return geom
        else:
            print("Could not convert the geojson to ee.Geometry()")

    except Exception as e:
        print("Could not convert the geojson to ee.Geometry()")
        print(e)


def ee_to_geojson(ee_object, out_json=None):
    """Converts Earth Engine object to geojson.

    Args:
        ee_object (object): An Earth Engine object.

    Returns:
        object: GeoJSON object.
    """
    from json import dumps
    ee_initialize()

    try:
        if isinstance(ee_object, ee.geometry.Geometry) or isinstance(ee_object, ee.feature.Feature) or isinstance(ee_object, ee.featurecollection.FeatureCollection):
            json_object = ee_object.getInfo()
            if out_json is not None:
                out_json = os.path.abspath(out_json)
                if not os.path.exists(os.path.dirname(out_json)):
                    os.makedirs(os.path.dirname(out_json))
                geojson = open(out_json, "w")
                geojson.write(
                    dumps({"type": "FeatureCollection", "features": json_object}, indent=2) + "\n")
                geojson.close()
            return json_object
        else:
            print("Could not convert the Earth Engine object to geojson")
    except Exception as e:
        print(e)


def open_github(subdir=None):
    """Opens the GitHub repository for this package.

    Args:
        subdir (str, optional): Sub-directory of the repository. Defaults to None.
    """
    import webbrowser

    url = 'https://github.com/giswqs/geemap'

    if subdir == 'source':
        url += '/tree/master/geemap/'
    elif subdir == 'examples':
        url += '/tree/master/examples'
    elif subdir == 'tutorials':
        url += '/tree/master/tutorials'

    webbrowser.open_new_tab(url)


def clone_repo(out_dir='.', unzip=True):
    """Clones the geemap GitHub repository.

    Args:
        out_dir (str, optional): Output folder for the repo. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the repository. Defaults to True.
    """
    url = 'https://github.com/giswqs/geemap/archive/master.zip'
    filename = 'geemap-master.zip'
    download_from_url(url, out_file_name=filename,
                      out_dir=out_dir, unzip=unzip)


def open_youtube():
    """Opens the YouTube tutorials for geemap.
    """
    import webbrowser

    url = 'https://www.youtube.com/playlist?list=PLAxJ4-o7ZoPccOFv1dCwvGI6TYnirRTg3'
    webbrowser.open_new_tab(url)


def show_youtube(id='h0pz3S6Tvx0'):
    """Displays a YouTube video within Jupyter notebooks.

    Args:
        id (str, optional): Unique ID of the video. Defaults to 'h0pz3S6Tvx0'.

    """
    from IPython.display import YouTubeVideo, display
    try:
        out = widgets.Output(
            layout={'width': '815px'})
        # layout={'border': '1px solid black', 'width': '815px'})
        out.clear_output(wait=True)
        display(out)
        with out:
            display(YouTubeVideo(id, width=800, height=450))
    except Exception as e:
        print(e)


def check_install(package):
    """Checks whether a package is installed. If not, it will install the package.

    Args:
        package (str): The name of the package to check.
    """
    import subprocess

    try:
        __import__(package)
        # print('{} is already installed.'.format(package))
    except ImportError:
        print('{} is not installed. Installing ...'.format(package))
        try:
            subprocess.check_call(["python", '-m', 'pip', 'install', package])
        except Exception as e:
            print('Failed to install {}'.format(package))
            print(e)
        print("{} has been installed successfully.".format(package))


def update_package():
    """Updates the geemap package from the geemap GitHub repository without the need to use pip or conda.
        In this way, I don't have to keep updating pypi and conda-forge with every minor update of the package.

    """
    try:
        download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        clone_repo(out_dir=download_dir)

        pkg_dir = os.path.join(download_dir, 'geemap-master')
        work_dir = os.getcwd()
        os.chdir(pkg_dir)
        cmd = 'pip install .'
        os.system(cmd)
        os.chdir(work_dir)

        print("\nPlease comment out 'geemap.update_package()' and restart the kernel to take effect:\nJupyter menu -> Kernel -> Restart & Clear Output")

    except Exception as e:
        print(e)


def shp_to_geojson(in_shp, out_json=None):
    """Converts a shapefile to GeoJSON.

    Args:
        in_shp (str): File path of the input shapefile.
        out_json (str, optional): File path of the output GeoJSON. Defaults to None.

    Returns:
        object: The json object representing the shapefile.
    """
    # check_install('pyshp')
    ee_initialize()
    try:
        import json
        import shapefile
        in_shp = os.path.abspath(in_shp)

        if out_json is None:
            out_json = os.path.splitext(in_shp)[0] + ".json"

            if os.path.exists(out_json):
                out_json = out_json.replace('.json', '_bk.json')

        elif not os.path.exists(os.path.dirname(out_json)):
            os.makedirs(os.path.dirname(out_json))

        reader = shapefile.Reader(in_shp)
        fields = reader.fields[1:]
        field_names = [field[0] for field in fields]
        buffer = []
        for sr in reader.shapeRecords():
            atr = dict(zip(field_names, sr.record))
            geom = sr.shape.__geo_interface__
            buffer.append(dict(type="Feature", geometry=geom, properties=atr))

        from json import dumps
        geojson = open(out_json, "w")
        geojson.write(dumps({"type": "FeatureCollection",
                             "features": buffer}, indent=2) + "\n")
        geojson.close()

        with open(out_json) as f:
            json_data = json.load(f)

        return json_data

    except Exception as e:
        print(e)


def shp_to_ee(in_shp):
    """Converts a shapefile to Earth Engine objects.

    Args:
        in_shp (str): File path to a shapefile.

    Returns:
        object: Earth Engine objects representing the shapefile.
    """
    ee_initialize()
    try:
        json_data = shp_to_geojson(in_shp)
        ee_object = geojson_to_ee(json_data)
        return ee_object
    except Exception as e:
        print(e)


def filter_polygons(ftr):
    """Converts GeometryCollection to Polygon/MultiPolygon

    Args:
        ftr (object): ee.Feature

    Returns:
        object: ee.Feature
    """
    ee_initialize()
    geometries = ftr.geometry().geometries()
    geometries = geometries.map(lambda geo: ee.Feature(
        ee.Geometry(geo)).set('geoType',  ee.Geometry(geo).type()))

    polygons = ee.FeatureCollection(geometries).filter(
        ee.Filter.eq('geoType', 'Polygon')).geometry()
    return ee.Feature(polygons).copyProperties(ftr)


def ee_export_vector(ee_object, filename, selectors=None):
    """Exports Earth Engine FeatureCollection to other formats, including shp, csv, json, kml, and kmz.

    Args:
        ee_object (object): ee.FeatureCollection to export.
        filename (str): Output file name.
        selectors (list, optional): A list of attributes to export. Defaults to None.
    """
    import requests
    import zipfile
    ee_initialize()

    if not isinstance(ee_object, ee.FeatureCollection):
        print('The ee_object must be an ee.FeatureCollection.')
        return

    allowed_formats = ['csv', 'json', 'kml', 'kmz', 'shp']
    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()
    filename_shp = filename

    if filetype == 'shp':
        filename = filename.replace('.shp', '.zip')

    if not (filetype.lower() in allowed_formats):
        print('The file type must be one of the following: {}'.format(
            ', '.join(allowed_formats)))
        return

    if selectors is None:
        selectors = ee_object.first().propertyNames().getInfo()
    elif not isinstance(selectors, list):
        print("selectors must be a list, such as ['attribute1', 'attribute2']")
        return
    else:
        allowed_attributes = ee_object.first().propertyNames().getInfo()
        for attribute in selectors:
            if not (attribute in allowed_attributes):
                print('Attributes must be one chosen from: {} '.format(
                    ', '.join(allowed_attributes)))
                return

    try:
        print('Generating URL ...')
        url = ee_object.getDownloadURL(
            filetype=filetype, selectors=selectors, filename=name)
        print('Downloading data from {}\nPlease wait ...'.format(url))
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print('An error occurred while downloading. \n Retrying ...')
            try:
                new_ee_object = ee_object.map(filter_polygons)
                print('Generating URL ...')
                url = new_ee_object.getDownloadURL(
                    filetype=filetype, selectors=selectors, filename=name)
                print('Downloading data from {}\nPlease wait ...'.format(url))
                r = requests.get(url, stream=True)
            except Exception as e:
                print(e)

        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)
    except Exception as e:
        print('An error occurred while downloading.')
        print(e)
        return

    try:
        if filetype == 'shp':
            z = zipfile.ZipFile(filename)
            z.extractall(os.path.dirname(filename))
            os.remove(filename)
            filename = filename.replace('.zip', '.shp')

        print('Data downloaded to {}'.format(filename))
    except Exception as e:
        print(e)


def ee_to_shp(ee_object, filename, selectors=None):
    """Downloads an ee.FeatureCollection as a shapefile.

    Args:
        ee_object (object): ee.FeatureCollection
        filename (str): The output filepath of the shapefile.
        selectors (list, optional): A list of attributes to export. Defaults to None.
    """
    ee_initialize()
    try:
        if filename.lower().endswith('.shp'):
            ee_export_vector(ee_object=ee_object,
                             filename=filename, selectors=selectors)
        else:
            print('The filename must end with .shp')

    except Exception as e:
        print(e)


def ee_to_csv(ee_object, filename, selectors=None):
    """Downloads an ee.FeatureCollection as a CSV file.

    Args:
        ee_object (object): ee.FeatureCollection
        filename (str): The output filepath of the CSV file.
        selectors (list, optional): A list of attributes to export. Defaults to None.
    """
    ee_initialize()
    try:
        if filename.lower().endswith('.csv'):
            ee_export_vector(ee_object=ee_object,
                             filename=filename, selectors=selectors)
        else:
            print('The filename must end with .csv')

    except Exception as e:
        print(e)


def ee_export_image(ee_object, filename, scale=None, crs=None, region=None, file_per_band=False):
    """Exports an ee.Image as a GeoTIFF.

    Args:
        ee_object (object): The ee.Image to download.
        filename (str): Output filename for the exported image.
        scale (float, optional): A default scale to use for any bands that do not specify one; ignored if crs and crs_transform is specified. Defaults to None.
        crs (str, optional): A default CRS string to use for any bands that do not explicitly specify one. Defaults to None.
        region (object, optional): A polygon specifying a region to download; ignored if crs and crs_transform is specified. Defaults to None.
        file_per_band (bool, optional): Whether to produce a different GeoTIFF per band. Defaults to False.
    """
    import requests
    import zipfile
    ee_initialize()

    if not isinstance(ee_object, ee.Image):
        print('The ee_object must be an ee.Image.')
        return

    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()
    filename_zip = filename.replace('.tif', '.zip')

    if filetype != 'tif':
        print('The filename must end with .tif')
        return

    try:
        print('Generating URL ...')
        params = {'name': name, 'filePerBand': file_per_band}
        if scale is None:
            scale = ee_object.projection().nominalScale().multiply(10)
        params['scale'] = scale
        if region is None:
            region = ee_object.geometry()
        params['region'] = region
        if crs is not None:
            params['crs'] = crs

        url = ee_object.getDownloadURL(params)
        print('Downloading data from {}\nPlease wait ...'.format(url))
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print('An error occurred while downloading.')
            return

        with open(filename_zip, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)

    except Exception as e:
        print('An error occurred while downloading.')
        print(e)
        return

    try:
        z = zipfile.ZipFile(filename_zip)
        z.extractall(os.path.dirname(filename))
        os.remove(filename_zip)

        if file_per_band:
            print('Data downloaded to {}'.format(os.path.dirname(filename)))
        else:
            print('Data downloaded to {}'.format(filename))
    except Exception as e:
        print(e)


def ee_export_image_collection(ee_object, out_dir, scale=None, crs=None, region=None, file_per_band=False):
    """Exports an ImageCollection as GeoTIFFs.

    Args:
        ee_object (object): The ee.Image to download.
        out_dir (str): The output directory for the exported images.
        scale (float, optional): A default scale to use for any bands that do not specify one; ignored if crs and crs_transform is specified. Defaults to None.
        crs (str, optional): A default CRS string to use for any bands that do not explicitly specify one. Defaults to None.
        region (object, optional): A polygon specifying a region to download; ignored if crs and crs_transform is specified. Defaults to None.
        file_per_band (bool, optional): Whether to produce a different GeoTIFF per band. Defaults to False.
    """

    import requests
    import zipfile
    ee_initialize()

    if not isinstance(ee_object, ee.ImageCollection):
        print('The ee_object must be an ee.ImageCollection.')
        return

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:

        count = int(ee_object.size().getInfo())
        print("Total number of images: {}\n".format(count))

        for i in range(0, count):
            image = ee.Image(ee_object.toList(count).get(i))
            name = image.get('system:index').getInfo() + '.tif'
            filename = os.path.join(os.path.abspath(out_dir), name)
            print('Exporting {}/{}: {}'.format(i+1, count, name))
            ee_export_image(image, filename=filename, scale=scale,
                            crs=crs, region=region, file_per_band=file_per_band)
            print('\n')

    except Exception as e:
        print(e)


def ee_to_numpy(ee_object, bands=None, region=None, properties=None, default_value=None):
    """Extracts a rectangular region of pixels from an image into a 2D numpy array per band.

    Args:
        ee_object (object): The image to sample.
        bands (list, optional): The list of band names to extract. Please make sure that all bands have the same spatial resolution. Defaults to None. 
        region (object, optional): The region whose projected bounding box is used to sample the image. The maximum number of pixels you can export is 262,144. Resampling and reprojecting all bands to a fixed scale can be useful. Defaults to the footprint in each band.
        properties (list, optional): The properties to copy over from the sampled image. Defaults to all non-system properties.
        default_value (float, optional): A default value used when a sampled pixel is masked or outside a band's footprint. Defaults to None.

    Returns:
        array: A 3D numpy array.
    """
    import numpy as np
    if not isinstance(ee_object, ee.Image):
        print('The input must be an ee.Image.')
        return

    if region is None:
        region = ee_object.geometry()

    try:

        if bands is not None:
            ee_object = ee_object.select(bands)
        else:
            bands = ee_object.bandNames().getInfo()

        band_count = len(bands)
        band_arrs = ee_object.sampleRectangle(
            region=region, properties=properties, defaultValue=default_value)
        band_values = []

        for band in bands:
            band_arr = band_arrs.get(band).getInfo()
            band_value = np.array(band_arr)
            band_values.append(band_value)

        image = np.dstack(band_values)
        return image

    except Exception as e:
        print(e)


def download_ee_video(collection, video_args, out_gif):
    """Downloads a video thumbnail as a GIF image from Earth Engine.

    Args:
        collection (object): An ee.ImageCollection.
        video_args ([type]): Parameters for expring the video thumbnail.
        out_gif (str): File path to the output GIF.
    """
    import requests

    out_gif = os.path.abspath(out_gif)
    if not out_gif.endswith(".gif"):
        print('The output file must have an extension of .gif.')
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if 'region' in video_args.keys():
        roi = video_args['region']

        if not isinstance(roi, ee.Geometry):

            try:
                roi = roi.geometry()
            except Exception as e:
                print('Could not convert the provided roi to ee.Geometry')
                print(e)
                return

        video_args['region'] = roi

    try:
        print('Generating URL...')
        url = collection.getVideoThumbURL(video_args)

        print('Downloading GIF image from {}\nPlease wait ...'.format(url))
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print('An error occurred while downloading.')
            return
        else:
            with open(out_gif, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=1024):
                    fd.write(chunk)
            print('The GIF image has been saved to: {}'.format(out_gif))
    except Exception as e:
        print(e)


def zonal_statistics(in_value_raster, in_zone_vector, out_file_path, statistics_type='MEAN', scale=None, crs=None, tile_scale=1.0, **kwargs):
    """Summarizes the values of a raster within the zones of another dataset and exports the results as a csv, shp, json, kml, or kmz.

    Args:
        in_value_raster (object): An ee.Image that contains the values on which to calculate a statistic.
        in_zone_vector (object): An ee.FeatureCollection that defines the zones.
        out_file_path (str): Output file path that will contain the summary of the values in each zone. The file type can be: csv, shp, json, kml, kmz
        statistics_type (str, optional): Statistic type to be calculated. Defaults to 'MEAN'. For 'HIST', you can provide three parameters: max_buckets, min_bucket_width, and max_raw. For 'FIXED_HIST', you must provide three parameters: hist_min, hist_max, and hist_steps.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        crs (str, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        tile_scale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.0.
    """

    if not isinstance(in_value_raster, ee.Image):
        print('The input raster must be an ee.Image.')
        return

    if not isinstance(in_zone_vector, ee.FeatureCollection):
        print('The input zone data must be an ee.FeatureCollection.')
        return

    allowed_formats = ['csv', 'json', 'kml', 'kmz', 'shp']
    filename = os.path.abspath(out_file_path)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()

    if not (filetype in allowed_formats):
        print('The file type must be one of the following: {}'.format(
            ', '.join(allowed_formats)))
        return

    # Parameters for histogram
    # The maximum number of buckets to use when building a histogram; will be rounded up to a power of 2.
    max_buckets = None
    # The minimum histogram bucket width, or null to allow any power of 2.
    min_bucket_width = None
    # The number of values to accumulate before building the initial histogram.
    max_raw = None
    hist_min = 1.0  # The lower (inclusive) bound of the first bucket.
    hist_max = 100.0  # The upper (exclusive) bound of the last bucket.
    hist_steps = 10  # The number of buckets to use.

    if 'max_buckets' in kwargs.keys():
        max_buckets = kwargs['max_buckets']
    if 'min_bucket_width' in kwargs.keys():
        min_bucket_width = kwargs['min_bucket']
    if 'max_raw' in kwargs.keys():
        max_raw = kwargs['max_raw']

    if statistics_type.upper() == 'FIXED_HIST' and ('hist_min' in kwargs.keys()) and ('hist_max' in kwargs.keys()) and ('hist_steps' in kwargs.keys()):
        hist_min = kwargs['hist_min']
        hist_max = kwargs['hist_max']
        hist_steps = kwargs['hist_steps']
    elif statistics_type.upper() == 'FIXED_HIST':
        print('To use fixedHistogram, please provide these three parameters: hist_min, hist_max, and hist_steps.')
        return

    allowed_statistics = {
        'MEAN': ee.Reducer.mean(),
        'MAXIMUM': ee.Reducer.max(),
        'MEDIAN': ee.Reducer.median(),
        'MINIMUM': ee.Reducer.min(),
        'STD': ee.Reducer.stdDev(),
        'MIN_MAX': ee.Reducer.minMax(),
        'SUM': ee.Reducer.sum(),
        'VARIANCE': ee.Reducer.variance(),
        'HIST': ee.Reducer.histogram(maxBuckets=max_buckets, minBucketWidth=min_bucket_width, maxRaw=max_raw),
        'FIXED_HIST': ee.Reducer.fixedHistogram(hist_min, hist_max, hist_steps)
    }

    if not (statistics_type.upper() in allowed_statistics.keys()):
        print('The statistics type must be one of the following: {}'.format(
            ', '.join(list(allowed_statistics.keys()))))
        return

    if scale is None:
        scale = in_value_raster.projection().nominalScale().multiply(10)

    try:
        print('Computing statistics ...')
        result = in_value_raster.reduceRegions(
            collection=in_zone_vector, reducer=allowed_statistics[statistics_type], scale=scale, crs=crs, tileScale=tile_scale)
        ee_export_vector(result, filename)
    except Exception as e:
        print(e)


def zonal_statistics_by_group(in_value_raster, in_zone_vector, out_file_path, statistics_type='SUM', decimal_places=0, denominator=1.0, scale=None, crs=None, tile_scale=1.0):
    """Summarizes the area or percentage of a raster by group within the zones of another dataset and exports the results as a csv, shp, json, kml, or kmz.

    Args:
        in_value_raster (object): An integer Image that contains the values on which to calculate area/percentage.
        in_zone_vector (object): An ee.FeatureCollection that defines the zones.
        out_file_path (str): Output file path that will contain the summary of the values in each zone. The file type can be: csv, shp, json, kml, kmz
        statistics_type (str, optional): Can be either 'SUM' or 'PERCENTAGE' . Defaults to 'SUM'.
        decimal_places (int, optional): The number of decimal places to use. Defaults to 0.
        denominator (float, optional): To covert area units (e.g., from square meters to square kilometers). Defaults to 1.0.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        crs (str, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        tile_scale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.0.

    """
    if not isinstance(in_value_raster, ee.Image):
        print('The input raster must be an ee.Image.')
        return

    band_count = in_value_raster.bandNames().size().getInfo()

    band_name = ''
    if band_count == 1:
        band_name = in_value_raster.bandNames().get(0)
    else:
        print('The input image can only have one band.')
        return

    band_types = in_value_raster.bandTypes().get(band_name).getInfo()
    band_type = band_types.get('precision')
    if band_type != 'int':
        print('The input image band must be integer type.')
        return

    if not isinstance(in_zone_vector, ee.FeatureCollection):
        print('The input zone data must be an ee.FeatureCollection.')
        return

    allowed_formats = ['csv', 'json', 'kml', 'kmz', 'shp']
    filename = os.path.abspath(out_file_path)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:]

    if not (filetype.lower() in allowed_formats):
        print('The file type must be one of the following: {}'.format(
            ', '.join(allowed_formats)))
        return

    out_dir = os.path.dirname(filename)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    allowed_statistics = ['SUM', 'PERCENTAGE']
    if not (statistics_type.upper() in allowed_statistics):
        print('The statistics type can only be one of {}'.format(
            ', '.join(allowed_statistics)))
        return

    if scale is None:
        scale = in_value_raster.projection().nominalScale().multiply(10)

    try:

        print('Computing ... ')
        geometry = in_zone_vector.geometry()

        hist = in_value_raster.reduceRegion(ee.Reducer.frequencyHistogram(
        ), geometry=geometry, bestEffort=True, scale=scale)
        class_values = ee.Dictionary(hist.get(band_name)).keys().map(
            lambda v: ee.Number.parse(v)).sort()

        class_names = class_values.map(
            lambda c: ee.String('Class_').cat(ee.Number(c).format()))

        class_count = class_values.size().getInfo()
        dataset = ee.Image.pixelArea().divide(denominator).addBands(in_value_raster)

        init_result = dataset.reduceRegions(**{
            'collection': in_zone_vector,
            'reducer': ee.Reducer.sum().group(**{
                'groupField': 1,
                'groupName': 'group',
            }),
            'scale': scale
        })

        def build_dict(input_list):

            decimal_format = '%.{}f'.format(decimal_places)
            in_dict = input_list.map(lambda x: ee.Dictionary().set(ee.String('Class_').cat(
                ee.Number(ee.Dictionary(x).get('group')).format()), ee.Number.parse(ee.Number(ee.Dictionary(x).get('sum')).format(decimal_format))))
            return in_dict

        def get_keys(input_list):
            return input_list.map(lambda x: ee.String('Class_').cat(ee.Number(ee.Dictionary(x).get('group')).format()))

        def get_values(input_list):
            decimal_format = '%.{}f'.format(decimal_places)
            return input_list.map(lambda x: ee.Number.parse(ee.Number(ee.Dictionary(x).get('sum')).format(decimal_format)))

        def set_attribute(f):
            groups = ee.List(f.get('groups'))
            keys = get_keys(groups)
            values = get_values(groups)
            total_area = ee.List(values).reduce(ee.Reducer.sum())

            def get_class_values(x):
                cls_value = ee.Algorithms.If(
                    keys.contains(x), values.get(keys.indexOf(x)), 0)
                cls_value = ee.Algorithms.If(ee.String(statistics_type).compareTo(ee.String(
                    'SUM')), ee.Number(cls_value).divide(ee.Number(total_area)), cls_value)
                return cls_value

            full_values = class_names.map(lambda x: get_class_values(x))
            attr_dict = ee.Dictionary.fromLists(class_names, full_values)
            attr_dict = attr_dict.set('Class_sum', total_area)

            return f.set(attr_dict).set('groups', None)

        final_result = init_result.map(set_attribute)
        ee_export_vector(final_result, filename)

    except Exception as e:
        print(e)


def create_colorbar(width=150, height=30, palette=['blue', 'green', 'red'], add_ticks=True, add_labels=True, labels=None, vertical=False, out_file=None, font_type='arial.ttf', font_size=12, font_color='black', add_outline=True, outline_color='black'):
    """Creates a colorbar based on the provided palette.

    Args:
        width (int, optional): Width of the colorbar in pixels. Defaults to 150.
        height (int, optional): Height of the colorbar in pixels. Defaults to 30.
        palette (list, optional): Palette for the colorbar. Each color can be provided as a string (e.g., 'red'), a hex string (e.g., '#ff0000'), or an RGB tuple (255, 0, 255). Defaults to ['blue', 'green', 'red'].
        add_ticks (bool, optional): Whether to add tick markers to the colorbar. Defaults to True.
        add_labels (bool, optional): Whether to add labels to the colorbar. Defaults to True.
        labels (list, optional): A list of labels to add to the colorbar. Defaults to None.
        vertical (bool, optional): Whether to rotate the colorbar vertically. Defaults to False.
        out_file (str, optional): File path to the output colorbar in png format. Defaults to None.
        font_type (str, optional): Font type to use for labels. Defaults to 'arial.ttf'.
        font_size (int, optional): Font size to use for labels. Defaults to 12.
        font_color (str, optional): Font color to use for labels. Defaults to 'black'.
        add_outline (bool, optional): Whether to add an outline to the colorbar. Defaults to True.
        outline_color (str, optional): Color for the outline of the colorbar. Defaults to 'black'.

    Returns:
        str: File path of the output colorbar in png format.

    """
    import decimal
    import io
    import math
    import pkg_resources
    import warnings
    from colour import Color
    from PIL import Image, ImageDraw, ImageFont

    warnings.simplefilter('ignore')
    pkg_dir = os.path.dirname(
        pkg_resources.resource_filename("geemap", "geemap.py"))

    if out_file is None:
        filename = 'colorbar_' + random_string() + '.png'
        out_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        out_file = os.path.join(out_dir, filename)
    elif not out_file.endswith('.png'):
        print('The output file must end with .png')
        return
    else:
        out_file = os.path.abspath(out_file)

    if not os.path.exists(os.path.dirname(out_file)):
        os.makedirs(os.path.dirname(out_file))

    im = Image.new('RGBA', (width, height))
    ld = im.load()

    def float_range(start, stop, step):
        while start < stop:
            yield float(start)
            start += decimal.Decimal(step)

    n_colors = len(palette)
    decimal_places = 2
    rgb_colors = [Color(check_color(c)).rgb for c in palette]
    keys = [round(c, decimal_places)
            for c in list(float_range(0, 1.0001, 1.0/(n_colors - 1)))]

    heatmap = []
    for index, item in enumerate(keys):
        pair = [item, rgb_colors[index]]
        heatmap.append(pair)

    def gaussian(x, a, b, c, d=0):
        return a * math.exp(-(x - b)**2 / (2 * c**2)) + d

    def pixel(x, width=100, map=[], spread=1):
        width = float(width)
        r = sum([gaussian(x, p[1][0], p[0] * width, width/(spread*len(map)))
                 for p in map])
        g = sum([gaussian(x, p[1][1], p[0] * width, width/(spread*len(map)))
                 for p in map])
        b = sum([gaussian(x, p[1][2], p[0] * width, width/(spread*len(map)))
                 for p in map])
        return min(1.0, r), min(1.0, g), min(1.0, b)

    for x in range(im.size[0]):
        r, g, b = pixel(x, width=width, map=heatmap)
        r, g, b = [int(256*v) for v in (r, g, b)]
        for y in range(im.size[1]):
            ld[x, y] = r, g, b

    if add_outline:
        draw = ImageDraw.Draw(im)
        draw.rectangle([(0, 0), (width-1, height-1)],
                       outline=check_color(outline_color))
        del draw

    if add_ticks:
        tick_length = height * 0.1
        x = [key * width for key in keys]
        y_top = height - tick_length
        y_bottom = height
        draw = ImageDraw.Draw(im)
        for i in x:
            shape = [(i, y_top), (i, y_bottom)]
            draw.line(shape, fill='black', width=0)
        del draw

    if vertical:
        im = im.transpose(Image.ROTATE_90)

    width, height = im.size

    if labels is None:
        labels = [str(c) for c in keys]
    elif len(labels) == 2:
        try:
            lowerbound = float(labels[0])
            upperbound = float(labels[1])
            step = (upperbound - lowerbound) / (len(palette) - 1)
            labels = [str(lowerbound + c * step)
                      for c in range(0, len(palette))]
        except Exception as e:
            print(e)
            print('The labels are invalid.')
            return
    elif len(labels) == len(palette):
        labels = [str(c) for c in labels]
    else:
        print('The labels must have the same length as the palette.')
        return

    if add_labels:

        default_font = os.path.join(pkg_dir, 'data/fonts/arial.ttf')
        if font_type == 'arial.ttf':
            font = ImageFont.truetype(default_font, font_size)
        else:
            try:
                font_list = system_fonts(show_full_path=True)
                font_names = [os.path.basename(f) for f in font_list]
                if (font_type in font_list) or (font_type in font_names):
                    font = ImageFont.truetype(font_type, font_size)
                else:
                    print(
                        'The specified font type could not be found on your system. Using the default font instead.')
                    font = ImageFont.truetype(default_font, font_size)
            except Exception as e:
                print(e)
                font = ImageFont.truetype(default_font, font_size)

        font_color = check_color(font_color)

        draw = ImageDraw.Draw(im)
        w, h = draw.textsize(labels[0], font=font)

        for label in labels:
            w_tmp, h_tmp = draw.textsize(label, font)
            if w_tmp > w:
                w = w_tmp
            if h_tmp > h:
                h = h_tmp

        W, H = width + w * 2, height + h * 2
        background = Image.new('RGBA', (W, H))
        draw = ImageDraw.Draw(background)

        if vertical:
            xy = (0, h)
        else:
            xy = (w, 0)
        background.paste(im, xy, im)

        for index, label in enumerate(labels):

            w_tmp, h_tmp = draw.textsize(label, font)

            if vertical:
                spacing = 5
                x = width + spacing
                y = int(height + h - keys[index] * height - h_tmp / 2 - 1)
                draw.text((x, y), label, font=font, fill=font_color)

            else:
                x = int(keys[index] * width + w - w_tmp / 2)
                spacing = int(h * 0.05)
                y = height + spacing
                draw.text((x, y), label, font=font, fill=font_color)

        im = background.copy()

    im.save(out_file)
    return out_file


def naip_timeseries(roi=None, start_year=2009, end_year=2018):
    """Creates NAIP annual timeseries

    Args:
        roi (object, optional): An ee.Geometry representing the region of interest. Defaults to None.
        start_year (int, optional): Starting year for the timeseries. Defaults to2009.
        end_year (int, optional): Ending year for the timeseries. Defaults to 2018.

    Returns:
        object: An ee.ImageCollection representing annual NAIP imagery.
    """
    ee_initialize()
    try:

        def get_annual_NAIP(year):
            try:
                collection = ee.ImageCollection('USDA/NAIP/DOQQ')
                if roi is not None:
                    collection = collection.filterBounds(roi)
                start_date = ee.Date.fromYMD(year, 1, 1)
                end_date = ee.Date.fromYMD(year, 12, 31)
                naip = collection.filterDate(start_date, end_date) \
                    .filter(ee.Filter.listContains("system:band_names", "N"))
                naip = ee.Image(ee.ImageCollection(naip).mosaic())
                return naip
            except Exception as e:
                print(e)

        years = ee.List.sequence(start_year, end_year)
        collection = years.map(get_annual_NAIP)
        return collection

    except Exception as e:
        print(e)


def sentinel2_timeseries(roi=None, start_year=2015, end_year=2019, start_date='01-01', end_date='12-31'):
    """Generates an annual Sentinel 2 ImageCollection. This algorithm is adapted from https://gist.github.com/jdbcode/76b9ac49faf51627ebd3ff988e10adbc. A huge thank you to Justin Braaten for sharing his fantastic work.
       Images include both level 1C and level 2A imagery.
    Args:

        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 2015.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2019.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '01-01'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '12-31'.
    Returns:
        object: Returns an ImageCollection containing annual Sentinel 2 images.
    """
    ################################################################################

    ################################################################################
    # Input and output parameters.
    import re
    import datetime

    ee_initialize()

    if roi is None:
        # roi = ee.Geometry.Polygon(
        #     [[[-180, -80],
        #       [-180, 80],
        #         [180, 80],
        #         [180, -80],
        #         [-180, -80]]], None, False)
        roi = ee.Geometry.Polygon(
            [[[-115.471773, 35.892718],
              [-115.471773, 36.409454],
                [-114.271283, 36.409454],
                [-114.271283, 35.892718],
                [-115.471773, 35.892718]]], None, False)

    if not isinstance(roi, ee.Geometry):

        try:
            roi = roi.geometry()
        except Exception as e:
            print('Could not convert the provided roi to ee.Geometry')
            print(e)
            return

    ################################################################################
    # Setup vars to get dates.
    if isinstance(start_year, int) and (start_year >= 2015) and (start_year <= 2020):
        pass
    else:
        print('The start year must be an integer >= 2015.')
        return

    if isinstance(end_year, int) and (end_year >= 2015) and (end_year <= 2020):
        pass
    else:
        print('The end year must be an integer <= 2020.')
        return

    if re.match("[0-9]{2}\-[0-9]{2}", start_date) and re.match("[0-9]{2}\-[0-9]{2}", end_date):
        pass
    else:
        print('The start data and end date must be month-day, such as 06-10, 09-20')
        return

    try:
        datetime.datetime(int(start_year), int(
            start_date[:2]), int(start_date[3:5]))
        datetime.datetime(int(end_year), int(end_date[:2]), int(end_date[3:5]))
    except Exception as e:
        print('The input dates are invalid.')
        print(e)
        return

    try:
        start_test = datetime.datetime(int(start_year), int(
            start_date[:2]), int(start_date[3:5]))
        end_test = datetime.datetime(
            int(end_year), int(end_date[:2]), int(end_date[3:5]))
        if start_test > end_test:
            raise ValueError('Start date must be prior to end date')
    except Exception as e:
        print(e)
        return

    def days_between(d1, d2):
        d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    n_days = days_between(str(start_year) + '-' + start_date,
                          str(start_year) + '-' + end_date)
    start_month = int(start_date[:2])
    start_day = int(start_date[3:5])
    start_date = str(start_year) + '-' + start_date
    end_date = str(end_year) + '-' + end_date

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, aoi):  # , startDate, endDate):
        return(col.filterBounds(aoi))

    # Get Sentinel 2 collections, both Level-1C (top of atmophere) and Level-2A (surface reflectance)
    MSILCcol = ee.ImageCollection('COPERNICUS/S2')
    MSI2Acol = ee.ImageCollection('COPERNICUS/S2_SR')

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, roi, start_date, end_date):
        return(col
               .filterBounds(roi)
               .filterDate(start_date, end_date))
        # .filter('CLOUD_COVER < 5')
        # .filter('GEOMETRIC_RMSE_MODEL < 15')
        # .filter('IMAGE_QUALITY == 9 || IMAGE_QUALITY_OLI == 9'))

    # Function to get and rename bands of interest from MSI
    def renameMSI(img):
        return(img.select(
            ['B2', 'B3', 'B4', 'B5', 'B6', 'B7',
                'B8', 'B8A', 'B11', 'B12', 'QA60'],
            ['Blue', 'Green', 'Red', 'Red Edge 1', 'Red Edge 2', 'Red Edge 3', 'NIR', 'Red Edge 4', 'SWIR1', 'SWIR2', 'QA60']))

    # Add NBR for LandTrendr segmentation.

    def calcNbr(img):
        return(img.addBands(img.normalizedDifference(['NIR', 'SWIR2'])
                            .multiply(-10000).rename('NBR')).int16())

    # Define function to mask out clouds and cloud shadows in images.
    # Use CFmask band included in USGS Landsat SR image product.

    def fmask(img):
        cloudOpaqueBitMask = 1 << 10
        cloudCirrusBitMask = 1 << 11
        qa = img.select('QA60')
        mask = qa.bitwiseAnd(cloudOpaqueBitMask).eq(0) \
            .And(qa.bitwiseAnd(cloudCirrusBitMask).eq(0))
        return(img.updateMask(mask))

    # Define function to prepare MSI images.
    def prepMSI(img):
        orig = img
        img = renameMSI(img)
        img = fmask(img)
        return(ee.Image(img.copyProperties(orig, orig.propertyNames()))
               .resample('bicubic'))

    # Get annual median collection.
    def getAnnualComp(y):
        startDate = ee.Date.fromYMD(
            ee.Number(y), ee.Number(start_month), ee.Number(start_day))
        endDate = startDate.advance(ee.Number(n_days), 'day')

        # Filter collections and prepare them for merging.
        MSILCcoly = colFilter(MSILCcol, roi, startDate, endDate).map(prepMSI)
        MSI2Acoly = colFilter(MSI2Acol, roi, startDate, endDate).map(prepMSI)

        # Merge the collections.
        col = MSILCcoly.merge(MSI2Acoly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(
            nBands,
            yearImg,
            dummyImg))
        return(calcNbr(yearImg)
               .set({'year': y, 'system:time_start': startDate.millis(), 'nBands': nBands}))

    ################################################################################

    # Make a dummy image for missing years.
    bandNames = ee.List(['Blue', 'Green', 'Red', 'Red Edge 1',
                         'Red Edge 2', 'Red Edge 3', 'NIR',
                         'Red Edge 4', 'SWIR1', 'SWIR2', 'QA60'])
    fillerValues = ee.List.repeat(0, bandNames.size())
    dummyImg = ee.Image.constant(fillerValues).rename(bandNames) \
        .selfMask().int16()

    ################################################################################
    # Get a list of years
    years = ee.List.sequence(start_year, end_year)

    ################################################################################
    # Make list of annual image composites.
    imgList = years.map(getAnnualComp)

    # Convert image composite list to collection
    imgCol = ee.ImageCollection.fromImages(imgList)

    imgCol = imgCol.map(lambda img: img.clip(roi))

    return imgCol


def landsat_timeseries(roi=None, start_year=1984, end_year=2019, start_date='06-10', end_date='09-20'):
    """Generates an annual Landsat ImageCollection. This algorithm is adapted from https://gist.github.com/jdbcode/76b9ac49faf51627ebd3ff988e10adbc. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi ([type], optional): [description]. Defaults to None.
        start_year (int, optional): [description]. Defaults to 1984.
        end_year (int, optional): [description]. Defaults to 2019.
        start_date (str, optional): [description]. Defaults to '06-10'.
        end_date (str, optional): [description]. Defaults to '09-20'.

        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2019.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
    Returns:
        object: Returns an ImageCollection containing annual Landsat images.
    """

    ################################################################################
    # Input and output parameters.
    import re
    import datetime

    ee_initialize()

    if roi is None:
        # roi = ee.Geometry.Polygon(
        #     [[[-180, -80],
        #       [-180, 80],
        #         [180, 80],
        #         [180, -80],
        #         [-180, -80]]], None, False)
        roi = ee.Geometry.Polygon(
            [[[-115.471773, 35.892718],
              [-115.471773, 36.409454],
                [-114.271283, 36.409454],
                [-114.271283, 35.892718],
                [-115.471773, 35.892718]]], None, False)

    if not isinstance(roi, ee.Geometry):

        try:
            roi = roi.geometry()
        except Exception as e:
            print('Could not convert the provided roi to ee.Geometry')
            print(e)
            return

    ################################################################################

    # Setup vars to get dates.
    if isinstance(start_year, int) and (start_year >= 1984) and (start_year < 2020):
        pass
    else:
        print('The start year must be an integer >= 1984.')
        return

    if isinstance(end_year, int) and (end_year > 1984) and (end_year <= 2020):
        pass
    else:
        print('The end year must be an integer <= 2020.')
        return

    if re.match("[0-9]{2}\-[0-9]{2}", start_date) and re.match("[0-9]{2}\-[0-9]{2}", end_date):
        pass
    else:
        print('The start date and end date must be month-day, such as 06-10, 09-20')
        return

    try:
        datetime.datetime(int(start_year), int(
            start_date[:2]), int(start_date[3:5]))
        datetime.datetime(int(end_year), int(end_date[:2]), int(end_date[3:5]))
    except Exception as e:
        print('The input dates are invalid.')
        return

    def days_between(d1, d2):
        d1 = datetime.datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)

    n_days = days_between(str(start_year) + '-' + start_date,
                          str(start_year) + '-' + end_date)
    start_month = int(start_date[:2])
    start_day = int(start_date[3:5])
    start_date = str(start_year) + '-' + start_date
    end_date = str(end_year) + '-' + end_date

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, aoi):  # , startDate, endDate):
        return(col.filterBounds(aoi))

    # Landsat collection preprocessingEnabled
    # Get Landsat surface reflectance collections for OLI, ETM+ and TM sensors.
    LC08col = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')
    LE07col = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR')
    LT05col = ee.ImageCollection('LANDSAT/LT05/C01/T1_SR')
    LT04col = ee.ImageCollection('LANDSAT/LT04/C01/T1_SR')

    # Define a collection filter by date, bounds, and quality.
    def colFilter(col, roi, start_date, end_date):
        return(col
               .filterBounds(roi)
               .filterDate(start_date, end_date))
        # .filter('CLOUD_COVER < 5')
        # .filter('GEOMETRIC_RMSE_MODEL < 15')
        # .filter('IMAGE_QUALITY == 9 || IMAGE_QUALITY_OLI == 9'))

    # Function to get and rename bands of interest from OLI.
    def renameOli(img):
        return(img.select(
            ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'pixel_qa'],
            ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']))

    # Function to get and rename bands of interest from ETM+.
    def renameEtm(img):
        return(img.select(
            ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'pixel_qa'],
            ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']))

    # Add NBR for LandTrendr segmentation.
    def calcNbr(img):
        return(img.addBands(img.normalizedDifference(['NIR', 'SWIR2'])
                            .multiply(-10000).rename('NBR')).int16())

    # Define function to mask out clouds and cloud shadows in images.
    # Use CFmask band included in USGS Landsat SR image product.
    def fmask(img):
        cloudShadowBitMask = 1 << 3
        cloudsBitMask = 1 << 5
        qa = img.select('pixel_qa')
        mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0) \
            .And(qa.bitwiseAnd(cloudsBitMask).eq(0))
        return(img.updateMask(mask))

    # Define function to prepare OLI images.
    def prepOli(img):
        orig = img
        img = renameOli(img)
        img = fmask(img)
        return (ee.Image(img.copyProperties(orig, orig.propertyNames()))
                .resample('bicubic'))

    # Define function to prepare ETM+ images.
    def prepEtm(img):
        orig = img
        img = renameEtm(img)
        img = fmask(img)
        return(ee.Image(img.copyProperties(orig, orig.propertyNames()))
               .resample('bicubic'))

    # Get annual median collection.
    def getAnnualComp(y):
        startDate = ee.Date.fromYMD(
            ee.Number(y), ee.Number(start_month), ee.Number(start_day))
        endDate = startDate.advance(ee.Number(n_days), 'day')

        # Filter collections and prepare them for merging.
        LC08coly = colFilter(LC08col, roi, startDate, endDate).map(prepOli)
        LE07coly = colFilter(LE07col, roi, startDate, endDate).map(prepEtm)
        LT05coly = colFilter(LT05col, roi, startDate, endDate).map(prepEtm)
        LT04coly = colFilter(LT04col, roi, startDate, endDate).map(prepEtm)

        # Merge the collections.
        col = LC08coly.merge(LE07coly).merge(LT05coly).merge(LT04coly)

        yearImg = col.median()
        nBands = yearImg.bandNames().size()
        yearImg = ee.Image(ee.Algorithms.If(
            nBands,
            yearImg,
            dummyImg))
        return(calcNbr(yearImg)
               .set({'year': y, 'system:time_start': startDate.millis(), 'nBands': nBands}))

    ################################################################################

    # Make a dummy image for missing years.
    bandNames = ee.List(['Blue', 'Green', 'Red', 'NIR',
                         'SWIR1', 'SWIR2', 'pixel_qa'])
    fillerValues = ee.List.repeat(0, bandNames.size())
    dummyImg = ee.Image.constant(fillerValues).rename(bandNames) \
        .selfMask().int16()

    ################################################################################
    # Get a list of years
    years = ee.List.sequence(start_year, end_year)

    ################################################################################
    # Make list of annual image composites.
    imgList = years.map(getAnnualComp)

    # Convert image composite list to collection
    imgCol = ee.ImageCollection.fromImages(imgList)

    imgCol = imgCol.map(lambda img: img.clip(roi))

    return imgCol

    # ################################################################################
    # # Run LandTrendr.
    # lt = ee.Algorithms.TemporalSegmentation.LandTrendr(
    #     timeSeries=imgCol.select(['NBR', 'SWIR1', 'NIR', 'Green']),
    #     maxSegments=10,
    #     spikeThreshold=0.7,
    #     vertexCountOvershoot=3,
    #     preventOneYearRecovery=True,
    #     recoveryThreshold=0.5,
    #     pvalThreshold=0.05,
    #     bestModelProportion=0.75,
    #     minObservationsNeeded=6)

    # ################################################################################
    # # Get fitted imagery. This starts export tasks.
    # def getYearStr(year):
    #     return(ee.String('yr_').cat(ee.Algorithms.String(year).slice(0,4)))

    # yearsStr = years.map(getYearStr)

    # r = lt.select(['SWIR1_fit']).arrayFlatten([yearsStr]).toShort()
    # g = lt.select(['NIR_fit']).arrayFlatten([yearsStr]).toShort()
    # b = lt.select(['Green_fit']).arrayFlatten([yearsStr]).toShort()

    # for i, c in zip([r, g, b], ['r', 'g', 'b']):
    #     descr = 'mamore-river-'+c
    #     name = 'users/user/'+descr
    #     print(name)
    #     task = ee.batch.Export.image.toAsset(
    #     image=i,
    #     region=roi.getInfo()['coordinates'],
    #     assetId=name,
    #     description=descr,
    #     scale=30,
    #     crs='EPSG:3857',
    #     maxPixels=1e13)
    #     task.start()


def landsat_ts_gif(roi=None, out_gif=None, start_year=1984, end_year=2019, start_date='06-10', end_date='09-20', bands=['NIR', 'Red', 'Green'], vis_params=None, dimensions=768, frames_per_second=10):
    """Generates a Landsat timelapse GIF image. This function is adapted from https://emaprlab.users.earthengine.app/view/lt-gee-time-series-animator. A huge thank you to Justin Braaten for sharing his fantastic work.

    Args:
        roi (object, optional): Region of interest to create the timelapse. Defaults to None.
        out_gif ([type], optional): File path to the output animated GIF. Defaults to None.
        start_year (int, optional): Starting year for the timelapse. Defaults to 1984.
        end_year (int, optional): Ending year for the timelapse. Defaults to 2019.
        start_date (str, optional): Starting date (month-day) each year for filtering ImageCollection. Defaults to '06-10'.
        end_date (str, optional): Ending date (month-day) each year for filtering ImageCollection. Defaults to '09-20'.
        bands (list, optional): Three bands selected from ['Blue', 'Green', 'Red', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']. Defaults to ['NIR', 'Red', 'Green'].
        vis_params (dict, optional): Visualization parameters. Defaults to None.
        dimensions (int, optional): a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 768.
        frames_per_second (int, optional): Animation speed. Defaults to 10.

    Returns:
        str: File path to the output GIF image.
    """

    ee_initialize()

    if roi is None:
        roi = ee.Geometry.Polygon(
            [[[-115.471773, 35.892718],
              [-115.471773, 36.409454],
                [-114.271283, 36.409454],
                [-114.271283, 35.892718],
                [-115.471773, 35.892718]]], None, False)
    elif isinstance(roi, ee.Feature) or isinstance(roi, ee.FeatureCollection):
        roi = roi.geometry()
    elif isinstance(roi, ee.Geometry):
        pass
    else:
        print('The provided roi is invalid. It must be an ee.Geometry')
        return

    if out_gif is None:
        out_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        filename = 'landsat_ts_' + random_string() + '.gif'
        out_gif = os.path.join(out_dir, filename)
    elif not out_gif.endswith('.gif'):
        print('The output file must end with .gif')
        return
    elif not os.path.isfile(out_gif):
        print('The output file must be a file')
        return
    else:
        out_gif = os.path.abspath(out_gif)
        out_dir = os.path.dirname(out_gif)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    allowed_bands = ['Blue', 'Green', 'Red',
                     'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']

    if len(bands) == 3 and all(x in allowed_bands for x in bands):
        pass
    else:
        print('You can only select 3 bands from the following: {}'.format(
            ', '.join(allowed_bands)))
        return

    try:
        col = landsat_timeseries(
            roi, start_year, end_year, start_date, end_date)

        if vis_params is None:
            vis_params = {}
            vis_params['bands'] = bands
            vis_params['min'] = 0
            vis_params['max'] = 4000
            vis_params['gamma'] = [1, 1, 1]

        video_args = vis_params.copy()
        video_args['dimensions'] = dimensions
        video_args['region'] = roi
        video_args['framesPerSecond'] = frames_per_second
        video_args['crs'] = 'EPSG:3857'

        if 'bands' not in video_args.keys():
            video_args['bands'] = bands

        if 'min' not in video_args.keys():
            video_args['min'] = 0

        if 'max' not in video_args.keys():
            video_args['max'] = 4000

        if 'gamma' not in video_args.keys():
            video_args['gamma'] = [1, 1, 1]

        download_ee_video(col, video_args, out_gif)

        return out_gif

    except Exception as e:
        print(e)
        return


def minimum_bounding_box(geojson):
    """Gets the minimum bounding box for a geojson polygon.

    Args:
        geojson (dict): A geojson dictionary.

    Returns:
        tuple: Returns a tuple containing the minimum bounding box in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -120)).
    """
    coordinates = []
    try:
        if 'geometry' in geojson.keys():
            coordinates = geojson['geometry']['coordinates'][0]
        else:
            coordinates = geojson['coordinates'][0]

        lower_left = min([x[1] for x in coordinates]), min(
            [x[0] for x in coordinates])  # (lat, lon)
        upper_right = max([x[1] for x in coordinates]), max([x[0]
                                                             for x in coordinates])  # (lat, lon)
        bounds = (lower_left, upper_right)
        return bounds
    except Exception as e:
        print(e)
        return


def geocode(location, max_rows=10, reverse=False):
    """Search location by address and lat/lon coordinates.

    Args:
        location (str): Place name or address
        max_rows (int, optional): Maximum number of records to return. Defaults to 10.
        reverse (bool, optional): Search place based on coordinates. Defaults to False.

    Returns:
        list: Returns a list of locations.
    """
    if not isinstance(location, str):
        print('The location must be a string.')
        return None

    if not reverse:

        locations = []
        addresses = set()
        g = geocoder.arcgis(location, maxRows=max_rows)

        for result in g:
            address = result.address
            if not address in addresses:
                addresses.add(address)
                locations.append(result)

        if len(locations) > 0:
            return locations
        else:
            return None

    else:
        try:
            if ',' in location:
                latlon = [float(x) for x in location.split(',')]
            elif ' ' in location:
                latlon = [float(x) for x in location.split(' ')]
            else:
                print(
                    'The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3')
                return
            g = geocoder.arcgis(latlon, method='reverse')
            locations = []
            addresses = set()

            for result in g:
                address = result.address
                if not address in addresses:
                    addresses.add(address)
                    locations.append(result)

            if len(locations) > 0:
                return locations
            else:
                return None

        except Exception as e:
            print(e)
            return None


def is_latlon_valid(location):
    """Checks whether a pair of coordinates is valid.

    Args:
        location (str): A pair of latlon coordinates separated by comma or space.

    Returns:
        bool: Returns True if valid.
    """
    latlon = []
    if ',' in location:
        latlon = [float(x) for x in location.split(',')]
    elif ' ' in location:
        latlon = [float(x) for x in location.split(' ')]
    else:
        print(
            'The coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3')
        return False

    try:
        lat, lon = float(latlon[0]), float(latlon[1])
        if lat >= -90 and lat <= 90 and lon >= -180 and lat <= 180:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def latlon_from_text(location):
    """Extracts latlon from text.

    Args:
        location (str): A pair of latlon coordinates separated by comma or space.

    Returns:
        bool: Returns (lat, lon) if valid.
    """
    latlon = []
    try:
        if ',' in location:
            latlon = [float(x) for x in location.split(',')]
        elif ' ' in location:
            latlon = [float(x) for x in location.split(' ')]
        else:
            print(
                'The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3')
            return None

        lat, lon = latlon[0], latlon[1]
        if lat >= -90 and lat <= 90 and lon >= -180 and lat <= 180:
            return lat, lon
        else:
            return None

    except Exception as e:
        print(e)
        print('The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3')
        return None


def search_ee_data(keywords):
    """Searches Earth Engine data catalog.

    Args:
        keywords (str): Keywords to search for can be id, provider, tag and so on

    Returns:
        list: Returns a lit of assets.
    """
    try:
        cmd = 'geeadd search --keywords "{}"'.format(str(keywords))
        output = os.popen(cmd).read()
        start_index = output.index('[')
        assets = eval(output[start_index:])

        results = []
        for asset in assets:
            asset_dates = asset['start_date'] + ' - ' + asset['end_date']
            asset_snippet = asset['ee_id_snippet']
            start_index = asset_snippet.index("'") + 1
            end_index = asset_snippet.index("'", start_index)
            asset_id = asset_snippet[start_index:end_index]

            asset['dates'] = asset_dates
            asset['id'] = asset_id
            asset['uid'] = asset_id.replace('/', '_')
            # asset['url'] = 'https://developers.google.com/earth-engine/datasets/catalog/' + asset['uid']
            # asset['thumbnail'] = 'https://mw1.google.com/ges/dd/images/{}_sample.png'.format(
            #     asset['uid'])
            results.append(asset)

        return results

    except Exception as e:
        print(e)
        return


def ee_data_thumbnail(asset_id):
    """Retrieves the thumbnail URL of an Earth Engine asset.

    Args:
        asset_id (str): An Earth Engine asset id.

    Returns:
        str: An http url of the thumbnail.
    """
    import requests
    import urllib
    from bs4 import BeautifulSoup

    asset_uid = asset_id.replace('/', '_')
    asset_url = "https://developers.google.com/earth-engine/datasets/catalog/{}".format(
        asset_uid)
    thumbnail_url = 'https://mw1.google.com/ges/dd/images/{}_sample.png'.format(
        asset_uid)

    r = requests.get(thumbnail_url)

    try:
        if r.status_code != 200:
            html_page = urllib.request.urlopen(asset_url)
            soup = BeautifulSoup(html_page, features="html.parser")

            for img in soup.findAll('img'):
                if 'sample.png' in img.get('src'):
                    thumbnail_url = img.get('src')
                    return thumbnail_url

        return thumbnail_url
    except Exception as e:
        print(e)
        return


def ee_data_html(asset):
    """Generates HTML from an asset to be used in the HTML widget.

    Args:
        asset (dict): A dictionary containing an Earth Engine asset.

    Returns:
        str: A string containing HTML.
    """
    template = '''
        <html>
        <body>
            <h3>asset_title</h3>
            <h4>Dataset Availability</h4>
                <p style="margin-left: 40px">asset_dates</p>
            <h4>Earth Engine Snippet</h4>
                <p style="margin-left: 40px">ee_id_snippet</p>
            <h4>Earth Engine Data Catalog</h4>
                <p style="margin-left: 40px"><a href="asset_url" target="_blank">asset_id</a></p>
            <h4>Dataset Thumbnail</h4>
                <img src="thumbnail_url">
        </body>
        </html>
    '''

    try:

        text = template.replace('asset_title', asset['title'])
        text = text.replace('asset_dates', asset['dates'])
        text = text.replace('ee_id_snippet', asset['ee_id_snippet'])
        text = text.replace('asset_id', asset['id'])
        text = text.replace('asset_url', asset['asset_url'])
        # asset['thumbnail'] = ee_data_thumbnail(asset['id'])
        text = text.replace('thumbnail_url', asset['thumbnail_url'])

        return text

    except Exception as e:
        print(e)
        return


def create_code_cell(code='', where='below'):
    """Creates a code cell in the IPython Notebook.

    Args:
        code (str, optional): Code to fill the new code cell with. Defaults to ''.
        where (str, optional): Where to add the new code cell. It can be one of the following: above, below, at_bottom. Defaults to 'below'.
    """

    import base64
    from IPython.display import Javascript, display
    encoded_code = (base64.b64encode(str.encode(code))).decode()
    display(Javascript("""
        var code = IPython.notebook.insert_cell_{0}('code');
        code.set_text(atob("{1}"));
    """.format(where, encoded_code)))


def in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    try:
        import google.colab  # pylint: disable=unused-variable
        return True
    except ImportError:
        return False


def is_drive_mounted():
    """Checks whether Google Drive is mounted in Google Colab.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    drive_path = '/content/drive/My Drive'
    if os.path.exists(drive_path):
        return True
    else:
        return False


def credentials_in_drive():
    """Checks if the ee credentials file exists in Google Drive.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    credentials_path = '/content/drive/My Drive/.config/earthengine/credentials'
    if os.path.exists(credentials_path):
        return True
    else:
        return False


def credentials_in_colab():
    """Checks if the ee credentials file exists in Google Colab.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    credentials_path = '/root/.config/earthengine/credentials'
    if os.path.exists(credentials_path):
        return True
    else:
        return False


def copy_credentials_to_drive():
    """Copies ee credentials from Google Colab to Google Drive.
    """
    import shutil
    src = '/root/.config/earthengine/credentials'
    dst = '/content/drive/My Drive/.config/earthengine/credentials'

    wd = os.path.dirname(dst)
    if not os.path.exists(wd):
        os.makedirs(wd)

    shutil.copyfile(src, dst)


def copy_credentials_to_colab():
    """Copies ee credentials from Google Drive to Google Colab.
    """
    import shutil
    src = '/content/drive/My Drive/.config/earthengine/credentials'
    dst = '/root/.config/earthengine/credentials'

    wd = os.path.dirname(dst)
    if not os.path.exists(wd):
        os.makedirs(wd)

    shutil.copyfile(src, dst)
