"""This module contains some common functions for both folium and ipyleaflet to interact with the Earth Engine Python API.
"""

import csv
import datetime
import io
import json
import math
import os
import requests
import shutil
import tarfile
import urllib.request
import zipfile

import ee
import ipywidgets as widgets
from IPython.display import display
from ipytree import Node, Tree


class TitilerEndpoint:
    """This class contains the methods for the titiler endpoint."""

    def __init__(
        self,
        endpoint="https://titiler.xyz",
        name="stac",
        TileMatrixSetId="WebMercatorQuad",
    ):
        """Initialize the TitilerEndpoint object.

        Args:
            endpoint (str, optional): The endpoint of the titiler server. Defaults to "https://titiler.xyz".
            name (str, optional): The name to be used in the file path. Defaults to "stac".
            TileMatrixSetId (str, optional): The TileMatrixSetId to be used in the file path. Defaults to "WebMercatorQuad".
        """
        self.endpoint = endpoint
        self.name = name
        self.TileMatrixSetId = TileMatrixSetId

    def url_for_stac_item(self):
        return f"{self.endpoint}/{self.name}/{self.TileMatrixSetId}/tilejson.json"

    def url_for_stac_assets(self):
        return f"{self.endpoint}/{self.name}/assets"

    def url_for_stac_bounds(self):
        return f"{self.endpoint}/{self.name}/bounds"

    def url_for_stac_info(self):
        return f"{self.endpoint}/{self.name}/info"

    def url_for_stac_info_geojson(self):
        return f"{self.endpoint}/{self.name}/info.geojson"

    def url_for_stac_statistics(self):
        return f"{self.endpoint}/{self.name}/statistics"

    def url_for_stac_pixel_value(self, lon, lat):
        return f"{self.endpoint}/{self.name}/point/{lon},{lat}"

    def url_for_stac_wmts(self):
        return (
            f"{self.endpoint}/{self.name}/{self.TileMatrixSetId}/WMTSCapabilities.xml"
        )


class PlanetaryComputerEndpoint(TitilerEndpoint):
    """This class contains the methods for the Microsoft Planetary Computer endpoint."""

    def __init__(
        self,
        endpoint="https://planetarycomputer.microsoft.com/api/data/v1",
        name="item",
        TileMatrixSetId="WebMercatorQuad",
    ):
        """Initialize the PlanetaryComputerEndpoint object.

        Args:
            endpoint (str, optional): The endpoint of the titiler server. Defaults to "https://planetarycomputer.microsoft.com/api/data/v1".
            name (str, optional): The name to be used in the file path. Defaults to "item".
            TileMatrixSetId (str, optional): The TileMatrixSetId to be used in the file path. Defaults to "WebMercatorQuad".
        """
        super().__init__(endpoint, name, TileMatrixSetId)

    def url_for_stac_collection(self):
        return f"{self.endpoint}/collection/{self.TileMatrixSetId}/tilejson.json"

    def url_for_collection_assets(self):
        return f"{self.endpoint}/collection/assets"

    def url_for_collection_bounds(self):
        return f"{self.endpoint}/collection/bounds"

    def url_for_collection_info(self):
        return f"{self.endpoint}/collection/info"

    def url_for_collection_info_geojson(self):
        return f"{self.endpoint}/collection/info.geojson"

    def url_for_collection_pixel_value(self, lon, lat):
        return f"{self.endpoint}/collection/point/{lon},{lat}"

    def url_for_collection_wmts(self):
        return f"{self.endpoint}/collection/{self.TileMatrixSetId}/WMTSCapabilities.xml"

    def url_for_collection_lat_lon_assets(self, lng, lat):
        return f"{self.endpoint}/collection/{lng},{lat}/assets"

    def url_for_collection_bbox_assets(self, minx, miny, maxx, maxy):
        return f"{self.endpoint}/collection/{minx},{miny},{maxx},{maxy}/assets"

    def url_for_stac_mosaic(self, searchid):
        return f"{self.endpoint}/mosaic/{searchid}/{self.TileMatrixSetId}/tilejson.json"

    def url_for_mosaic_info(self, searchid):
        return f"{self.endpoint}/mosaic/{searchid}/info"

    def url_for_mosaic_lat_lon_assets(self, searchid, lon, lat):
        return f"{self.endpoint}/mosaic/{searchid}/{lon},{lat}/assets"


def check_titiler_endpoint(titiler_endpoint=None):
    """Returns the default titiler endpoint.

    Returns:
        object: A titiler endpoint.
    """
    if titiler_endpoint is None:
        if os.environ.get("TITILER_ENDPOINT") == "planetary-computer":
            titiler_endpoint = PlanetaryComputerEndpoint()
        else:
            titiler_endpoint = TitilerEndpoint()
    elif titiler_endpoint in ["planetary-computer", "pc"]:
        titiler_endpoint = PlanetaryComputerEndpoint()

    return titiler_endpoint


########################################
# EE Authentication and Initialization #
########################################


def ee_initialize(token_name="EARTHENGINE_TOKEN"):
    """Authenticates Earth Engine and initialize an Earth Engine session"""
    if ee.data._credentials is None:
        try:
            ee_token = os.environ.get(token_name)
            if ee_token is not None:
                credential_file_path = os.path.expanduser("~/.config/earthengine/")
                if not os.path.exists(credential_file_path):
                    credential = '{"refresh_token":"%s"}' % ee_token
                    os.makedirs(credential_file_path, exist_ok=True)
                    with open(credential_file_path + "credentials", "w") as file:
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
        except Exception:
            ee.Authenticate()
            ee.Initialize()


def set_proxy(port=1080, ip="http://127.0.0.1"):
    """Sets proxy if needed. This is only needed for countries where Google services are not available.

    Args:
        port (int, optional): The proxy port number. Defaults to 1080.
        ip (str, optional): The IP address. Defaults to 'http://127.0.0.1'.
    """
    import requests

    try:

        if not ip.startswith("http"):
            ip = "http://" + ip
        proxy = "{}:{}".format(ip, port)

        os.environ["HTTP_PROXY"] = proxy
        os.environ["HTTPS_PROXY"] = proxy

        a = requests.get("https://earthengine.google.com/")

        if a.status_code != 200:
            print(
                "Failed to connect to Earth Engine. Please double check the port number and ip address."
            )

    except Exception as e:
        print(e)


def in_colab_shell():
    """Tests if the code is being executed within Google Colab."""
    import sys

    if "google.colab" in sys.modules:
        return True
    else:
        return False


def is_drive_mounted():
    """Checks whether Google Drive is mounted in Google Colab.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    drive_path = "/content/drive/My Drive"
    if os.path.exists(drive_path):
        return True
    else:
        return False


def credentials_in_drive():
    """Checks if the ee credentials file exists in Google Drive.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    credentials_path = "/content/drive/My Drive/.config/earthengine/credentials"
    if os.path.exists(credentials_path):
        return True
    else:
        return False


def credentials_in_colab():
    """Checks if the ee credentials file exists in Google Colab.

    Returns:
        bool: Returns True if Google Drive is mounted, False otherwise.
    """
    credentials_path = "/root/.config/earthengine/credentials"
    if os.path.exists(credentials_path):
        return True
    else:
        return False


def copy_credentials_to_drive():
    """Copies ee credentials from Google Colab to Google Drive."""
    src = "/root/.config/earthengine/credentials"
    dst = "/content/drive/My Drive/.config/earthengine/credentials"

    wd = os.path.dirname(dst)
    if not os.path.exists(wd):
        os.makedirs(wd)

    shutil.copyfile(src, dst)


def copy_credentials_to_colab():
    """Copies ee credentials from Google Drive to Google Colab."""
    src = "/content/drive/My Drive/.config/earthengine/credentials"
    dst = "/root/.config/earthengine/credentials"

    wd = os.path.dirname(dst)
    if not os.path.exists(wd):
        os.makedirs(wd)

    shutil.copyfile(src, dst)


########################################
#         Package Installation         #
########################################


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
        print(f"{package} is not installed. Installing ...")
        try:
            subprocess.check_call(["python", "-m", "pip", "install", package])
        except Exception as e:
            print(f"Failed to install {package}")
            print(e)
        print(f"{package} has been installed successfully.")


def update_package():
    """Updates the geemap package from the geemap GitHub repository without the need to use pip or conda.
    In this way, I don't have to keep updating pypi and conda-forge with every minor update of the package.

    """

    try:
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        clone_repo(out_dir=download_dir)

        pkg_dir = os.path.join(download_dir, "geemap-master")
        work_dir = os.getcwd()
        os.chdir(pkg_dir)

        if shutil.which("pip") is None:
            cmd = "pip3 install ."
        else:
            cmd = "pip install ."

        os.system(cmd)
        os.chdir(work_dir)

        print(
            "\nPlease comment out 'geemap.update_package()' and restart the kernel to take effect:\nJupyter menu -> Kernel -> Restart & Clear Output"
        )

    except Exception as e:
        raise Exception(e)


def check_package(name, URL=""):

    try:
        __import__(name.lower())
    except Exception:
        raise ImportError(
            f"{name} is not installed. Please install it before proceeding. {URL}"
        )


def clone_repo(out_dir=".", unzip=True):
    """Clones the geemap GitHub repository.

    Args:
        out_dir (str, optional): Output folder for the repo. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the repository. Defaults to True.
    """
    url = "https://github.com/giswqs/geemap/archive/master.zip"
    filename = "geemap-master.zip"
    download_from_url(url, out_file_name=filename, out_dir=out_dir, unzip=unzip)


def install_from_github(url):
    """Install a package from a GitHub repository.

    Args:
        url (str): The URL of the GitHub repository.
    """

    try:
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        repo_name = os.path.basename(url)
        zip_url = os.path.join(url, "archive/master.zip")
        filename = repo_name + "-master.zip"
        download_from_url(
            url=zip_url, out_file_name=filename, out_dir=download_dir, unzip=True
        )

        pkg_dir = os.path.join(download_dir, repo_name + "-master")
        pkg_name = os.path.basename(url)
        work_dir = os.getcwd()
        os.chdir(pkg_dir)
        print(f"Installing {pkg_name}...")
        cmd = "pip install ."
        os.system(cmd)
        os.chdir(work_dir)
        print(f"{pkg_name} has been installed successfully.")
        # print("\nPlease comment out 'install_from_github()' and restart the kernel to take effect:\nJupyter menu -> Kernel -> Restart & Clear Output")

    except Exception as e:
        print(e)


def check_git_install():
    """Checks if Git is installed.

    Returns:
        bool: Returns True if Git is installed, otherwise returns False.
    """
    import webbrowser

    cmd = "git --version"
    output = os.popen(cmd).read()

    if "git version" in output:
        return True
    else:
        url = "https://git-scm.com/downloads"
        print(f"Git is not installed. Please download Git from {url} and install it.")
        webbrowser.open_new_tab(url)
        return False


def clone_github_repo(url, out_dir):
    """Clones a GitHub repository.

    Args:
        url (str): The link to the GitHub repository
        out_dir (str): The output directory for the cloned repository.
    """

    repo_name = os.path.basename(url)
    # url_zip = os.path.join(url, 'archive/master.zip')
    url_zip = url + "/archive/master.zip"

    if os.path.exists(out_dir):
        print(
            "The specified output directory already exists. Please choose a new directory."
        )
        return

    parent_dir = os.path.dirname(out_dir)
    out_file_path = os.path.join(parent_dir, repo_name + ".zip")

    try:
        urllib.request.urlretrieve(url_zip, out_file_path)
    except Exception:
        print("The provided URL is invalid. Please double check the URL.")
        return

    with zipfile.ZipFile(out_file_path, "r") as zip_ref:
        zip_ref.extractall(parent_dir)

    src = out_file_path.replace(".zip", "-master")
    os.rename(src, out_dir)
    os.remove(out_file_path)


def clone_google_repo(url, out_dir=None):
    """Clones an Earth Engine repository from https://earthengine.googlesource.com, such as https://earthengine.googlesource.com/users/google/datasets

    Args:
        url (str): The link to the Earth Engine repository
        out_dir (str, optional): The output directory for the cloned repository. Defaults to None.
    """
    repo_name = os.path.basename(url)

    if out_dir is None:
        out_dir = os.path.join(os.getcwd(), repo_name)

    if not os.path.exists(os.path.dirname(out_dir)):
        os.makedirs(os.path.dirname(out_dir))

    if os.path.exists(out_dir):
        print(
            "The specified output directory already exists. Please choose a new directory."
        )
        return

    if check_git_install():

        cmd = f'git clone "{url}" "{out_dir}"'
        os.popen(cmd).read()


def open_github(subdir=None):
    """Opens the GitHub repository for this package.

    Args:
        subdir (str, optional): Sub-directory of the repository. Defaults to None.
    """
    import webbrowser

    url = "https://github.com/giswqs/geemap"

    if subdir == "source":
        url += "/tree/master/geemap/"
    elif subdir == "examples":
        url += "/tree/master/examples"
    elif subdir == "tutorials":
        url += "/tree/master/tutorials"

    webbrowser.open_new_tab(url)


def open_youtube():
    """Opens the YouTube tutorials for geemap."""
    import webbrowser

    url = "https://www.youtube.com/playlist?list=PLAxJ4-o7ZoPccOFv1dCwvGI6TYnirRTg3"
    webbrowser.open_new_tab(url)


########################################
#           Python Utilities           #
########################################


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""

    # from shutil import which

    return shutil.which(name) is not None


def random_string(string_length=3):
    """Generates a random string of fixed length.

    Args:
        string_length (int, optional): Fixed length. Defaults to 3.

    Returns:
        str: A random string
    """
    import random
    import string

    # random.seed(1001)
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(string_length))


def open_image_from_url(url):
    """Loads an image from the specified URL.

    Args:
        url (str): URL of the image.

    Returns:
        object: Image object.
    """
    import requests
    from PIL import Image

    # from io import BytesIO
    # from urllib.parse import urlparse

    try:
        response = requests.get(url)
        img = Image.open(io.BytesIO(response.content))
        return img
    except Exception as e:
        print(e)


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
                print("You need set both width and height.")
                return
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


def upload_to_imgur(in_gif):
    """Uploads an image to imgur.com

    Args:
        in_gif (str): The file path to the image.
    """
    import subprocess

    pkg_name = "imgur-uploader"
    if not is_tool(pkg_name):
        check_install(pkg_name)

    try:
        IMGUR_API_ID = os.environ.get("IMGUR_API_ID", None)
        IMGUR_API_SECRET = os.environ.get("IMGUR_API_SECRET", None)
        credentials_path = os.path.join(
            os.path.expanduser("~"), ".config/imgur_uploader/uploader.cfg"
        )

        if (
            (IMGUR_API_ID is not None) and (IMGUR_API_SECRET is not None)
        ) or os.path.exists(credentials_path):

            proc = subprocess.Popen(["imgur-uploader", in_gif], stdout=subprocess.PIPE)
            for _ in range(0, 2):
                line = proc.stdout.readline()
                print(line.rstrip().decode("utf-8"))
            # while True:
            #     line = proc.stdout.readline()
            #     if not line:
            #         break
            #     print(line.rstrip().decode("utf-8"))
        else:
            print(
                "Imgur API credentials could not be found. Please check https://pypi.org/project/imgur-uploader/ for instructions on how to get Imgur API credentials"
            )
            return

    except Exception as e:
        print(e)


########################################
#           Color and Fonts            #
########################################


def rgb_to_hex(rgb=(255, 255, 255)):
    """Converts RGB to hex color. In RGB color R stands for Red, G stands for Green, and B stands for Blue, and it ranges from the decimal value of 0 – 255.

    Args:
        rgb (tuple, optional): RGB color code as a tuple of (red, green, blue). Defaults to (255, 255, 255).

    Returns:
        str: hex color code
    """
    return "%02x%02x%02x" % rgb


def hex_to_rgb(value="FFFFFF"):
    """Converts hex color to RGB color.

    Args:
        value (str, optional): Hex color code as a string. Defaults to 'FFFFFF'.

    Returns:
        tuple: RGB color as a tuple.
    """
    value = value.lstrip("#")
    lv = len(value)
    return tuple(int(value[i: i + lv // 3], 16) for i in range(0, lv, lv // 3))


def check_color(in_color):
    """Checks the input color and returns the corresponding hex color code.

    Args:
        in_color (str or tuple): It can be a string (e.g., 'red', '#ffff00', 'ffff00', 'ff0') or RGB tuple (e.g., (255, 127, 0)).

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


def to_hex_colors(colors):
    """Convert a GEE color palette into hexadecimal color codes. can handle mixin formats

    Args:
        colors (list): A list of hex color codes.

    Returns:
        list: A list of hex color codes prefixed with #.
    """

    return [check_color(c) for c in colors]


def system_fonts(show_full_path=False):
    """Gets a list of system fonts

        # Common font locations:
        # Linux: /usr/share/fonts/TTF/
        # Windows: C:/Windows/Fonts
        # macOS:  System > Library > Fonts

    Args:
        show_full_path (bool, optional): Whether to show the full path of each system font. Defaults to False.

    Returns:
        list: A list of system fonts.
    """
    try:
        import matplotlib.font_manager

        font_list = matplotlib.font_manager.findSystemFonts(
            fontpaths=None, fontext="ttf"
        )
        font_list.sort()

        font_names = [os.path.basename(f) for f in font_list]
        font_names.sort()

        if show_full_path:
            return font_list
        else:
            return font_names

    except Exception as e:
        print(e)


########################################
#           Data Download              #
########################################


def download_from_url(url, out_file_name=None, out_dir=".", unzip=True, verbose=True):
    """Download a file from a URL (e.g., https://github.com/giswqs/whitebox/raw/master/examples/testdata.zip)

    Args:
        url (str): The HTTP URL to download.
        out_file_name (str, optional): The output file name to use. Defaults to None.
        out_dir (str, optional): The output directory to use. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the downloaded file if it is a zip file. Defaults to True.
        verbose (bool, optional): Whether to display or not the output of the function
    """
    in_file_name = os.path.basename(url)

    if out_file_name is None:
        out_file_name = in_file_name
    out_file_path = os.path.join(os.path.abspath(out_dir), out_file_name)

    if verbose:
        print(f"Downloading {url} ...")

    try:
        urllib.request.urlretrieve(url, out_file_path)
    except Exception:
        raise Exception("The URL is invalid. Please double check the URL.")

    final_path = out_file_path

    if unzip:
        # if it is a zip file
        if ".zip" in out_file_name:
            if verbose:
                print(f"Unzipping {out_file_name} ...")
            with zipfile.ZipFile(out_file_path, "r") as zip_ref:
                zip_ref.extractall(out_dir)
            final_path = os.path.join(
                os.path.abspath(out_dir), out_file_name.replace(".zip", "")
            )

        # if it is a tar file
        if ".tar" in out_file_name:
            if verbose:
                print(f"Unzipping {out_file_name} ...")
            with tarfile.open(out_file_path, "r") as tar_ref:
                tar_ref.extractall(out_dir)
            final_path = os.path.join(
                os.path.abspath(out_dir), out_file_name.replace(".tar", "")
            )

    if verbose:
        print(f"Data downloaded to: {final_path}")

    return


def download_from_gdrive(gfile_url, file_name, out_dir=".", unzip=True, verbose=True):
    """Download a file shared via Google Drive
       (e.g., https://drive.google.com/file/d/18SUo_HcDGltuWYZs1s7PpOmOq_FvFn04/view?usp=sharing)

    Args:
        gfile_url (str): The Google Drive shared file URL
        file_name (str): The output file name to use.
        out_dir (str, optional): The output directory. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the output file if it is a zip file. Defaults to True.
        verbose (bool, optional): Whether to display or not the output of the function
    """
    from google_drive_downloader import GoogleDriveDownloader as gdd

    file_id = gfile_url.split("/")[5]
    if verbose:
        print(f"Google Drive file id: {file_id}")

    dest_path = os.path.join(out_dir, file_name)
    gdd.download_file_from_google_drive(file_id, dest_path, True, unzip)

    return


def create_download_link(filename, title="Click here to download: "):
    """Downloads a file from voila. Adopted from https://github.com/voila-dashboards/voila/issues/578

    Args:
        filename (str): The file path to the file to download
        title (str, optional): str. Defaults to "Click here to download: ".

    Returns:
        str: HTML download URL.
    """
    import base64

    from IPython.display import HTML

    data = open(filename, "rb").read()
    b64 = base64.b64encode(data)
    payload = b64.decode()
    basename = os.path.basename(filename)
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" style="color:#0000FF;" target="_blank">{title}</a>'
    html = html.format(payload=payload, title=title + f" {basename}", filename=basename)
    return HTML(html)


def edit_download_html(htmlWidget, filename, title="Click here to download: "):
    """Downloads a file from voila. Adopted from https://github.com/voila-dashboards/voila/issues/578#issuecomment-617668058

    Args:
        htmlWidget (object): The HTML widget to display the URL.
        filename (str): File path to download.
        title (str, optional): Download description. Defaults to "Click here to download: ".
    """

    # from IPython.display import HTML
    # import ipywidgets as widgets
    import base64

    # Change widget html temporarily to a font-awesome spinner
    htmlWidget.value = '<i class="fa fa-spinner fa-spin fa-2x fa-fw"></i><span class="sr-only">Loading...</span>'

    # Process raw data
    data = open(filename, "rb").read()
    b64 = base64.b64encode(data)
    payload = b64.decode()

    basename = os.path.basename(filename)

    # Create and assign html to widget
    html = '<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">{title}</a>'
    htmlWidget.value = html.format(
        payload=payload, title=title + basename, filename=basename
    )

    # htmlWidget = widgets.HTML(value = '')
    # htmlWidget


########################################
#           Data Conversion            #
########################################


def xy_to_points(in_csv, latitude="latitude", longitude="longitude", encoding="utf-8"):
    """Converts a csv containing points (latitude and longitude) into an ee.FeatureCollection.

    Args:
        in_csv (str): File path or HTTP URL to the input csv file. For example, https://raw.githubusercontent.com/giswqs/data/main/world/world_cities.csv
        latitude (str, optional): Column name for the latitude column. Defaults to 'latitude'.
        longitude (str, optional): Column name for the longitude column. Defaults to 'longitude'.

    Returns:
        ee.FeatureCollection: The ee.FeatureCollection containing the points converted from the input csv.
    """

    geojson = csv_to_geojson(in_csv, None, latitude, longitude, encoding)
    fc = geojson_to_ee(geojson)
    return fc


def csv_points_to_shp(in_csv, out_shp, latitude="latitude", longitude="longitude"):
    """Converts a csv file containing points (latitude, longitude) into a shapefile.

    Args:
        in_csv (str): File path or HTTP URL to the input csv file. For example, https://raw.githubusercontent.com/giswqs/data/main/world/world_cities.csv
        out_shp (str): File path to the output shapefile.
        latitude (str, optional): Column name for the latitude column. Defaults to 'latitude'.
        longitude (str, optional): Column name for the longitude column. Defaults to 'longitude'.

    """
    import whitebox

    if in_csv.startswith("http") and in_csv.endswith(".csv"):
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        out_name = os.path.basename(in_csv)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        download_from_url(in_csv, out_dir=out_dir, verbose=False)
        in_csv = os.path.join(out_dir, out_name)

    wbt = whitebox.WhiteboxTools()
    in_csv = os.path.abspath(in_csv)
    out_shp = os.path.abspath(out_shp)

    if not os.path.exists(in_csv):
        raise Exception("The provided csv file does not exist.")

    with open(in_csv, encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fields = reader.fieldnames
        xfield = fields.index(longitude)
        yfield = fields.index(latitude)

    wbt.csv_points_to_vector(in_csv, out_shp, xfield=xfield, yfield=yfield, epsg=4326)


def csv_to_shp(in_csv, out_shp, latitude="latitude", longitude="longitude"):
    """Converts a csv file with latlon info to a point shapefile.

    Args:
        in_csv (str): The input csv file containing longitude and latitude columns.
        out_shp (str): The file path to the output shapefile.
        latitude (str, optional): The column name of the latitude column. Defaults to 'latitude'.
        longitude (str, optional): The column name of the longitude column. Defaults to 'longitude'.
    """
    import shapefile as shp

    if in_csv.startswith("http") and in_csv.endswith(".csv"):
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        out_name = os.path.basename(in_csv)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        download_from_url(in_csv, out_dir=out_dir, verbose=False)
        in_csv = os.path.join(out_dir, out_name)

    out_dir = os.path.dirname(out_shp)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        points = shp.Writer(out_shp, shapeType=shp.POINT)
        with open(in_csv, encoding="utf-8-sig") as csvfile:
            csvreader = csv.DictReader(csvfile)
            header = csvreader.fieldnames
            [points.field(field) for field in header]
            for row in csvreader:
                points.point((float(row[longitude])), (float(row[latitude])))
                points.record(*tuple([row[f] for f in header]))

        out_prj = out_shp.replace(".shp", ".prj")
        with open(out_prj, "w") as f:
            prj_str = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]] '
            f.write(prj_str)

    except Exception as e:
        raise Exception(e)


def csv_to_geojson(
    in_csv,
    out_geojson=None,
    latitude="latitude",
    longitude="longitude",
    encoding="utf-8",
):
    """Creates points for a CSV file and exports data as a GeoJSON.

    Args:
        in_csv (str): The file path to the input CSV file.
        out_geojson (str): The file path to the exported GeoJSON. Default to None.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    """

    # import json
    import pandas as pd

    if out_geojson is not None:
        out_dir = os.path.dirname(os.path.abspath(out_geojson))
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    df = pd.read_csv(in_csv)
    geojson = pandas_to_geojson(
        df, latitude=latitude, longitude=longitude, encoding=encoding
    )

    if out_geojson is None:
        return geojson
    else:
        with open(out_geojson, "w", encoding=encoding) as f:
            f.write(json.dumps(geojson))


def pandas_to_geojson(
    df,
    out_geojson=None,
    latitude="latitude",
    longitude="longitude",
    encoding="utf-8",
):
    """Creates points for a Pandas DataFrame and exports data as a GeoJSON.

    Args:
        df (pandas.DataFrame): The input Pandas DataFrame.
        out_geojson (str): The file path to the exported GeoJSON. Default to None.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    """

    # import json
    from geojson import Feature, FeatureCollection, Point

    if out_geojson is not None:
        out_dir = os.path.dirname(os.path.abspath(out_geojson))
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    features = df.apply(
        lambda row: Feature(
            geometry=Point((float(row[longitude]), float(row[latitude]))),
            properties=dict(row),
        ),
        axis=1,
    ).tolist()

    geojson = FeatureCollection(features=features)

    if out_geojson is None:
        return geojson
    else:
        with open(out_geojson, "w", encoding=encoding) as f:
            f.write(json.dumps(geojson))


def csv_to_ee(
    in_csv, latitude="latitude", longitude="longitude", encoding="utf-8", geodesic=True
):
    """Creates points for a CSV file and exports data as a GeoJSON.

    Args:
        in_csv (str): The file path to the input CSV file.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".
        geodesic (bool, optional): Whether line segments should be interpreted as spherical geodesics. If false, indicates that line segments should be interpreted as planar lines in the specified CRS. If absent, defaults to true if the CRS is geographic (including the default EPSG:4326), or to false if the CRS is projected.

    Returns:
        ee_object: An ee.Geometry object
    """

    geojson = csv_to_geojson(
        in_csv, latitude=latitude, longitude=longitude, encoding=encoding
    )
    fc = geojson_to_ee(geojson, geodesic=geodesic)
    return fc


def csv_to_gdf(in_csv, latitude="latitude", longitude="longitude", encoding="utf-8"):
    """Creates points for a CSV file and converts them to a GeoDataFrame.

    Args:
        in_csv (str): The file path to the input CSV file.
        latitude (str, optional): The name of the column containing latitude coordinates. Defaults to "latitude".
        longitude (str, optional): The name of the column containing longitude coordinates. Defaults to "longitude".
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    Returns:
        object: GeoDataFrame.
    """

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    out_dir = os.getcwd()

    out_geojson = os.path.join(out_dir, random_string() + ".geojson")
    csv_to_geojson(in_csv, out_geojson, latitude, longitude, encoding)

    gdf = gpd.read_file(out_geojson)
    os.remove(out_geojson)
    return gdf


csv_to_geopandas = csv_to_gdf


def geojson_to_ee(geo_json, geodesic=False, encoding="utf-8"):
    """Converts a geojson to ee.Geometry()

    Args:
        geo_json (dict): A geojson geometry dictionary or file path.
        geodesic (bool, optional): Whether line segments should be interpreted as spherical geodesics. If false, indicates that line segments should be interpreted as planar lines in the specified CRS. If absent, defaults to true if the CRS is geographic (including the default EPSG:4326), or to false if the CRS is projected. Defaults to False.
        encoding (str, optional): The encoding of characters. Defaults to "utf-8".

    Returns:
        ee_object: An ee.Geometry object
    """

    try:

        if isinstance(geo_json, str):
            if geo_json.startswith("http") and geo_json.endswith(".geojson"):
                out_geojson = temp_file_path(extension=".geojson")
                download_from_url(geo_json, out_geojson, verbose=False)
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
            keys = geo_json["properties"]["style"].keys()
            if "radius" in keys:  # Checks whether it is a circle
                geom = ee.Geometry(geo_json["geometry"])
                radius = geo_json["properties"]["style"]["radius"]
                geom = geom.buffer(radius)
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


def ee_to_geojson(ee_object, out_json=None):
    """Converts Earth Engine object to geojson.

    Args:
        ee_object (object): An Earth Engine object.

    Returns:
        object: GeoJSON object.
    """
    # from json import dumps

    # ee_initialize()

    try:
        if (
            isinstance(ee_object, ee.geometry.Geometry)
            or isinstance(ee_object, ee.feature.Feature)
            or isinstance(ee_object, ee.featurecollection.FeatureCollection)
        ):
            json_object = ee_object.getInfo()
            if out_json is not None:
                out_json = os.path.abspath(out_json)
                if not os.path.exists(os.path.dirname(out_json)):
                    os.makedirs(os.path.dirname(out_json))
                with open(out_json, "w") as geojson:
                    geojson.write(json.dumps(json_object, indent=2) + "\n")
            return json_object
        else:
            print("Could not convert the Earth Engine object to geojson")
    except Exception as e:
        print(e)


def shp_to_geojson(in_shp, out_json=None, **kwargs):
    """Converts a shapefile to GeoJSON.

    Args:
        in_shp (str): File path of the input shapefile.
        out_json (str, optional): File path of the output GeoJSON. Defaults to None.

    Returns:
        object: The json object representing the shapefile.
    """
    try:
        import shapefile

        # from datetime import date

        in_shp = os.path.abspath(in_shp)

        if out_json is not None:
            ext = os.path.splitext(out_json)[1]
            print(ext)
            if ext.lower() not in [".json", ".geojson"]:
                raise TypeError("The output file extension must the .json or .geojson.")

            if not os.path.exists(os.path.dirname(out_json)):
                os.makedirs(os.path.dirname(out_json))

        if not is_GCS(in_shp):
            try:
                import geopandas as gpd

            except Exception:
                raise ImportError(
                    "Geopandas is required to perform reprojection of the data. See https://geopandas.org/install.html"
                )

            try:
                in_gdf = gpd.read_file(in_shp)
                out_gdf = in_gdf.to_crs(epsg="4326")
                out_shp = in_shp.replace(".shp", "_gcs.shp")
                out_gdf.to_file(out_shp)
                in_shp = out_shp
            except Exception as e:
                raise Exception(e)

        if "encoding" in kwargs:
            reader = shapefile.Reader(in_shp, encoding=kwargs.pop("encoding"))
        else:
            reader = shapefile.Reader(in_shp)
        out_dict = reader.__geo_interface__
        # fields = reader.fields[1:]
        # field_names = [field[0] for field in fields]
        # # pyShp returns dates as `datetime.date` or as `bytes` when they are empty
        # # This is not JSON compatible, so we keep track of them to convert them to str
        # date_fields_names = [field[0] for field in fields if field[1] == "D"]
        # buffer = []
        # for sr in reader.shapeRecords():
        #     atr = dict(zip(field_names, sr.record))
        #     for date_field in date_fields_names:
        #         value = atr[date_field]
        #         # convert date to string, similar to pyShp writing
        #         # https://github.com/GeospatialPython/pyshp/blob/69c60f6d07c329f7d3ac2cba79bc03643bd424d8/shapefile.py#L1814
        #         if isinstance(value, date):
        #             value = "{:04d}{:02d}{:02d}".format(
        #                 value.year, value.month, value.day
        #             )
        #         elif not value:  # empty bytes string
        #             value = "0" * 8  # QGIS NULL for date type
        #         atr[date_field] = value
        #     geom = sr.shape.__geo_interface__
        #     buffer.append(dict(type="Feature", geometry=geom, properties=atr))

        # out_dict = {"type": "FeatureCollection", "features": buffer}

        if out_json is not None:
            # from json import dumps

            with open(out_json, "w") as geojson:
                geojson.write(json.dumps(out_dict, indent=2) + "\n")
        else:
            return out_dict

    except Exception as e:
        raise Exception(e)


def shp_to_ee(in_shp, **kwargs):
    """Converts a shapefile to Earth Engine objects. Note that the CRS of the shapefile must be EPSG:4326

    Args:
        in_shp (str): File path to a shapefile.

    Returns:
        object: Earth Engine objects representing the shapefile.
    """
    # ee_initialize()
    try:
        if "encoding" in kwargs:
            json_data = shp_to_geojson(in_shp, encoding=kwargs.pop("encoding"))
        else:
            json_data = shp_to_geojson(in_shp)
        ee_object = geojson_to_ee(json_data)
        return ee_object
    except Exception as e:
        print(e)


########################################
#              Export Data             #
########################################


def filter_polygons(ftr):
    """Converts GeometryCollection to Polygon/MultiPolygon

    Args:
        ftr (object): ee.Feature

    Returns:
        object: ee.Feature
    """
    # ee_initialize()
    geometries = ftr.geometry().geometries()
    geometries = geometries.map(
        lambda geo: ee.Feature(ee.Geometry(geo)).set("geoType", ee.Geometry(geo).type())
    )

    polygons = (
        ee.FeatureCollection(geometries)
        .filter(ee.Filter.eq("geoType", "Polygon"))
        .geometry()
    )
    return ee.Feature(polygons).copyProperties(ftr)


def ee_export_vector(ee_object, filename, selectors=None, verbose=True, keep_zip=False):
    """Exports Earth Engine FeatureCollection to other formats, including shp, csv, json, kml, and kmz.

    Args:
        ee_object (object): ee.FeatureCollection to export.
        filename (str): Output file name.
        selectors (list, optional): A list of attributes to export. Defaults to None.
        verbose (bool, optional): Whether to print out descriptive text.
        keep_zip (bool, optional): Whether to keep the downloaded shapefile as a zip file.
    """
    import requests

    if not isinstance(ee_object, ee.FeatureCollection):
        raise ValueError("ee_object must be an ee.FeatureCollection")

    allowed_formats = ["csv", "geojson", "json", "kml", "kmz", "shp"]
    # allowed_formats = ['csv', 'kml', 'kmz']
    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()

    if filetype == "shp":
        filename = filename.replace(".shp", ".zip")

    if not (filetype.lower() in allowed_formats):
        print(
            "The file type must be one of the following: {}".format(
                ", ".join(allowed_formats)
            )
        )
        print(
            "Earth Engine no longer supports downloading featureCollection as shapefile or json. \nPlease use geemap.ee_export_vector_to_drive() to export featureCollection to Google Drive."
        )
        raise ValueError

    if selectors is None:
        selectors = ee_object.first().propertyNames().getInfo()
        if filetype == "csv":
            # remove .geo coordinate field
            ee_object = ee_object.select([".*"], None, False)

    if filetype == "geojson":
        selectors = [".geo"] + selectors

    elif not isinstance(selectors, list):
        raise ValueError(
            "selectors must be a list, such as ['attribute1', 'attribute2']"
        )
    else:
        allowed_attributes = ee_object.first().propertyNames().getInfo()
        for attribute in selectors:
            if not (attribute in allowed_attributes):
                raise ValueError(
                    "Attributes must be one chosen from: {} ".format(
                        ", ".join(allowed_attributes)
                    )
                )

    try:
        if verbose:
            print("Generating URL ...")
        url = ee_object.getDownloadURL(
            filetype=filetype, selectors=selectors, filename=name
        )
        if verbose:
            print(f"Downloading data from {url}\nPlease wait ...")
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print("An error occurred while downloading. \n Retrying ...")
            try:
                new_ee_object = ee_object.map(filter_polygons)
                print("Generating URL ...")
                url = new_ee_object.getDownloadURL(
                    filetype=filetype, selectors=selectors, filename=name
                )
                print(f"Downloading data from {url}\nPlease wait ...")
                r = requests.get(url, stream=True)
            except Exception as e:
                print(e)
                raise ValueError

        with open(filename, "wb") as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)
    except Exception as e:
        print("An error occurred while downloading.")
        print(r.json()["error"]["message"])
        raise ValueError(e)

    try:
        if filetype == "shp":
            with zipfile.ZipFile(filename) as z:
                z.extractall(os.path.dirname(filename))
            if not keep_zip:
                os.remove(filename)
            filename = filename.replace(".zip", ".shp")
        if verbose:
            print(f"Data downloaded to {filename}")
    except Exception as e:
        raise ValueError(e)


def ee_export_vector_to_drive(
    ee_object, description, folder, file_format="shp", selectors=None
):
    """Exports Earth Engine FeatureCollection to Google Drive. other formats, including shp, csv, json, kml, and kmz.

    Args:
        ee_object (object): ee.FeatureCollection to export.
        description (str): File name of the output file.
        folder (str): Folder name within Google Drive to save the exported file.
        file_format (str, optional): The supported file format include shp, csv, json, kml, kmz, and TFRecord. Defaults to 'shp'.
        selectors (list, optional): The list of attributes to export. Defaults to None.
    """
    if not isinstance(ee_object, ee.FeatureCollection):
        print("The ee_object must be an ee.FeatureCollection.")
        return

    allowed_formats = ["csv", "json", "kml", "kmz", "shp", "tfrecord"]
    if not (file_format.lower() in allowed_formats):
        print(
            "The file type must be one of the following: {}".format(
                ", ".join(allowed_formats)
            )
        )
        return

    task_config = {
        "folder": folder,
        "fileFormat": file_format,
    }

    if selectors is not None:
        task_config["selectors"] = selectors
    elif (selectors is None) and (file_format.lower() == "csv"):
        # remove .geo coordinate field
        ee_object = ee_object.select([".*"], None, False)

    print(f"Exporting {description}...")
    task = ee.batch.Export.table.toDrive(ee_object, description, **task_config)
    task.start()


def ee_export_geojson(ee_object, filename=None, selectors=None):
    """Exports Earth Engine FeatureCollection to geojson.

    Args:
        ee_object (object): ee.FeatureCollection to export.
        filename (str): Output file name. Defaults to None.
        selectors (list, optional): A list of attributes to export. Defaults to None.
    """
    import requests

    if not isinstance(ee_object, ee.FeatureCollection):
        print("The ee_object must be an ee.FeatureCollection.")
        return

    if filename is None:
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = os.path.join(out_dir, random_string(6) + ".geojson")

    allowed_formats = ["geojson"]
    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()

    if not (filetype.lower() in allowed_formats):
        print("The output file type must be geojson.")
        return

    if selectors is None:
        selectors = ee_object.first().propertyNames().getInfo()
        selectors = [".geo"] + selectors

    elif not isinstance(selectors, list):
        print("selectors must be a list, such as ['attribute1', 'attribute2']")
        return
    else:
        allowed_attributes = ee_object.first().propertyNames().getInfo()
        for attribute in selectors:
            if not (attribute in allowed_attributes):
                print(
                    "Attributes must be one chosen from: {} ".format(
                        ", ".join(allowed_attributes)
                    )
                )
                return

    try:
        # print('Generating URL ...')
        url = ee_object.getDownloadURL(
            filetype=filetype, selectors=selectors, filename=name
        )
        # print('Downloading data from {}\nPlease wait ...'.format(url))
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print("An error occurred while downloading. \n Retrying ...")
            try:
                new_ee_object = ee_object.map(filter_polygons)
                print("Generating URL ...")
                url = new_ee_object.getDownloadURL(
                    filetype=filetype, selectors=selectors, filename=name
                )
                print(f"Downloading data from {url}\nPlease wait ...")
                r = requests.get(url, stream=True)
            except Exception as e:
                print(e)

        with open(filename, "wb") as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)
    except Exception as e:
        print("An error occurred while downloading.")
        print(r.json()["error"]["message"])

        return

    with open(filename) as f:
        geojson = f.read()

    return geojson


def ee_to_shp(ee_object, filename, selectors=None, verbose=True, keep_zip=False):
    """Downloads an ee.FeatureCollection as a shapefile.

    Args:
        ee_object (object): ee.FeatureCollection
        filename (str): The output filepath of the shapefile.
        selectors (list, optional): A list of attributes to export. Defaults to None.
        verbose (bool, optional): Whether to print out descriptive text.
        keep_zip (bool, optional): Whether to keep the downloaded shapefile as a zip file.
    """
    # ee_initialize()
    try:
        if filename.lower().endswith(".shp"):
            ee_export_vector(
                ee_object=ee_object,
                filename=filename,
                selectors=selectors,
                verbose=verbose,
                keep_zip=keep_zip,
            )
        else:
            print("The filename must end with .shp")

    except Exception as e:
        print(e)


def ee_to_csv(ee_object, filename, selectors=None, verbose=True):
    """Downloads an ee.FeatureCollection as a CSV file.

    Args:
        ee_object (object): ee.FeatureCollection
        filename (str): The output filepath of the CSV file.
        selectors (list, optional): A list of attributes to export. Defaults to None.
        verbose (bool, optional): Whether to print out descriptive text.

    """
    # ee_initialize()
    try:
        if filename.lower().endswith(".csv"):
            ee_export_vector(
                ee_object=ee_object,
                filename=filename,
                selectors=selectors,
                verbose=verbose,
            )
        else:
            print("The filename must end with .csv")

    except Exception as e:
        print(e)


def dict_to_csv(data_dict, out_csv, by_row=False):
    """Downloads an ee.Dictionary as a CSV file.

    Args:
        data_dict (ee.Dictionary): The input ee.Dictionary.
        out_csv (str): The output file path to the CSV file.
        by_row (bool, optional): Whether to use by row or by column. Defaults to False.
    """

    out_dir = os.path.dirname(out_csv)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not by_row:
        csv_feature = ee.Feature(None, data_dict)
        csv_feat_col = ee.FeatureCollection([csv_feature])
    else:
        keys = data_dict.keys()
        data = keys.map(lambda k: ee.Dictionary({"name": k, "value": data_dict.get(k)}))
        csv_feature = data.map(lambda f: ee.Feature(None, f))
        csv_feat_col = ee.FeatureCollection(csv_feature)

    ee_export_vector(csv_feat_col, out_csv)


def ee_export_image(
    ee_object, filename, scale=None, crs=None, region=None, file_per_band=False
):
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

    if not isinstance(ee_object, ee.Image):
        print("The ee_object must be an ee.Image.")
        return

    filename = os.path.abspath(filename)
    basename = os.path.basename(filename)
    name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()
    filename_zip = filename.replace(".tif", ".zip")

    if filetype != "tif":
        print("The filename must end with .tif")
        return

    try:
        print("Generating URL ...")
        params = {"name": name, "filePerBand": file_per_band}
        if scale is None:
            scale = ee_object.projection().nominalScale().multiply(10)
        params["scale"] = scale
        if region is None:
            region = ee_object.geometry()
        params["region"] = region
        if crs is not None:
            params["crs"] = crs

        try:
            url = ee_object.getDownloadURL(params)
        except Exception as e:
            print("An error occurred while downloading.")
            print(e)
            return
        print(f"Downloading data from {url}\nPlease wait ...")
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print("An error occurred while downloading.")
            return

        with open(filename_zip, "wb") as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)

    except Exception as e:
        print("An error occurred while downloading.")
        print(r.json()["error"]["message"])
        return

    try:
        with zipfile.ZipFile(filename_zip) as z:
            z.extractall(os.path.dirname(filename))
        os.remove(filename_zip)

        if file_per_band:
            print(f"Data downloaded to {os.path.dirname(filename)}")
        else:
            print(f"Data downloaded to {filename}")
    except Exception as e:
        print(e)


def ee_export_image_collection(
    ee_object, out_dir, scale=None, crs=None, region=None, file_per_band=False
):
    """Exports an ImageCollection as GeoTIFFs.

    Args:
        ee_object (object): The ee.Image to download.
        out_dir (str): The output directory for the exported images.
        scale (float, optional): A default scale to use for any bands that do not specify one; ignored if crs and crs_transform is specified. Defaults to None.
        crs (str, optional): A default CRS string to use for any bands that do not explicitly specify one. Defaults to None.
        region (object, optional): A polygon specifying a region to download; ignored if crs and crs_transform is specified. Defaults to None.
        file_per_band (bool, optional): Whether to produce a different GeoTIFF per band. Defaults to False.
    """

    if not isinstance(ee_object, ee.ImageCollection):
        print("The ee_object must be an ee.ImageCollection.")
        return

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:

        count = int(ee_object.size().getInfo())
        print(f"Total number of images: {count}\n")

        for i in range(0, count):
            image = ee.Image(ee_object.toList(count).get(i))
            name = image.get("system:index").getInfo() + ".tif"
            filename = os.path.join(os.path.abspath(out_dir), name)
            print(f"Exporting {i + 1}/{count}: {name}")
            ee_export_image(
                image,
                filename=filename,
                scale=scale,
                crs=crs,
                region=region,
                file_per_band=file_per_band,
            )
            print("\n")

    except Exception as e:
        print(e)


def ee_export_image_to_drive(
    ee_object,
    description,
    folder=None,
    region=None,
    scale=None,
    crs=None,
    max_pixels=1.0e13,
    file_format="GeoTIFF",
    format_options={},
):
    """Creates a batch task to export an Image as a raster to Google Drive.

    Args:
        ee_object (object): The image to export.
        description (str): A human-readable name of the task.
        folder (str, optional): The Google Drive Folder that the export will reside in. Defaults to None.
        region (object, optional): A LinearRing, Polygon, or coordinates representing region to export. These may be specified as the Geometry objects or coordinates serialized as a string. If not specified, the region defaults to the viewport at the time of invocation. Defaults to None.
        scale (float, optional): Resolution in meters per pixel. Defaults to 10 times of the image resolution.
        crs (str, optional): CRS to use for the exported image.. Defaults to None.
        max_pixels (int, optional): Restrict the number of pixels in the export. Defaults to 1.0E13.
        file_format (str, optional): The string file format to which the image is exported. Currently only 'GeoTIFF' and 'TFRecord' are supported. Defaults to 'GeoTIFF'.
        format_options (dict, optional): A dictionary of string keys to format specific options, e.g., {'compressed': True, 'cloudOptimized': True}
    """
    # ee_initialize()

    if not isinstance(ee_object, ee.Image):
        print("The ee_object must be an ee.Image.")
        return

    try:
        params = {}

        if folder is not None:
            params["driveFolder"] = folder
        if region is not None:
            params["region"] = region
        if scale is None:
            scale = ee_object.projection().nominalScale().multiply(10)
        params["scale"] = scale
        if crs is not None:
            params["crs"] = crs
        params["maxPixels"] = max_pixels
        params["fileFormat"] = file_format
        params["formatOptions"] = format_options

        task = ee.batch.Export.image(ee_object, description, params)
        task.start()

        print(f"Exporting {description} ...")

    except Exception as e:
        print(e)


def ee_export_image_collection_to_drive(
    ee_object,
    descriptions=None,
    folder=None,
    region=None,
    scale=None,
    crs=None,
    max_pixels=1.0e13,
    file_format="GeoTIFF",
    format_options={},
):
    """Creates a batch task to export an ImageCollection as raster images to Google Drive.

    Args:
        ee_object (object): The image to export.
        descriptions (list): A list of human-readable names of the tasks.
        folder (str, optional): The Google Drive Folder that the export will reside in. Defaults to None.
        region (object, optional): A LinearRing, Polygon, or coordinates representing region to export. These may be specified as the Geometry objects or coordinates serialized as a string. If not specified, the region defaults to the viewport at the time of invocation. Defaults to None.
        scale (float, optional): Resolution in meters per pixel. Defaults to 10 times of the image resolution.
        crs (str, optional): CRS to use for the exported image.. Defaults to None.
        max_pixels (int, optional): Restrict the number of pixels in the export. Defaults to 1.0E13.
        file_format (str, optional): The string file format to which the image is exported. Currently only 'GeoTIFF' and 'TFRecord' are supported. Defaults to 'GeoTIFF'.
        format_options (dict, optional): A dictionary of string keys to format specific options, e.g., {'compressed': True, 'cloudOptimized': True}
    """
    # ee_initialize()

    if not isinstance(ee_object, ee.ImageCollection):
        print("The ee_object must be an ee.ImageCollection.")
        return

    try:
        count = int(ee_object.size().getInfo())
        print(f"Total number of images: {count}\n")

        if (descriptions is not None) and (len(descriptions) != count):
            print("The number of descriptions is not equal to the number of images.")
            return

        if descriptions is None:
            descriptions = ee_object.aggregate_array("system:index").getInfo()

        images = ee_object.toList(count)

        for i in range(0, count):
            image = ee.Image(images.get(i))
            name = descriptions[i]
            ee_export_image_to_drive(
                image,
                name,
                folder,
                region,
                scale,
                crs,
                max_pixels,
                file_format,
                format_options,
            )

    except Exception as e:
        print(e)


def get_image_thumbnail(
    ee_object,
    out_img,
    vis_params,
    dimensions=500,
    region=None,
    format="jpg",
    crs="EPSG:3857",
):
    """Download a thumbnail for an ee.Image.

    Args:
        ee_object (object): The ee.Image instance.
        out_img (str): The output file path to the png thumbnail.
        vis_params (dict): The visualization parameters.
        dimensions (int, optional):(a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 500.
        region (object, optional): Geospatial region of the image to render, it may be an ee.Geometry, GeoJSON, or an array of lat/lon points (E,S,W,N). If not set the default is the bounds image. Defaults to None.
        format (str, optional): Either 'png' or 'jpg'. Default to 'jpg'.
    """
    import requests

    if not isinstance(ee_object, ee.Image):
        raise TypeError("The ee_object must be an ee.Image.")

    ext = os.path.splitext(out_img)[1][1:]
    if ext not in ["png", "jpg"]:
        raise ValueError("The output image format must be png or jpg.")
    else:
        format = ext

    out_image = os.path.abspath(out_img)
    out_dir = os.path.dirname(out_image)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if region is not None:
        vis_params["region"] = region

    vis_params["dimensions"] = dimensions
    vis_params["format"] = format
    vis_params["crs"] = crs
    url = ee_object.getThumbURL(vis_params)

    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print("An error occurred while downloading.")
        print(r.json()["error"]["message"])

    else:
        with open(out_img, "wb") as fd:
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)


def get_image_collection_thumbnails(
    ee_object,
    out_dir,
    vis_params,
    dimensions=500,
    region=None,
    format="jpg",
    names=None,
    verbose=True,
):
    """Download thumbnails for all images in an ImageCollection.

    Args:
        ee_object (object): The ee.ImageCollection instance.
        out_dir ([str): The output directory to store thumbnails.
        vis_params (dict): The visualization parameters.
        dimensions (int, optional):(a number or pair of numbers in format WIDTHxHEIGHT) Maximum dimensions of the thumbnail to render, in pixels. If only one number is passed, it is used as the maximum, and the other dimension is computed by proportional scaling. Defaults to 500.
        region (object, optional): Geospatial region of the image to render, it may be an ee.Geometry, GeoJSON, or an array of lat/lon points (E,S,W,N). If not set the default is the bounds image. Defaults to None.
        format (str, optional): Either 'png' or 'jpg'. Default to 'jpg'.
        names (list, optional): The list of output file names. Defaults to None.
        verbose (bool, optional): Whether or not to print hints. Defaults to True.
    """
    if not isinstance(ee_object, ee.ImageCollection):
        print("The ee_object must be an ee.ImageCollection.")
        raise TypeError("The ee_object must be an ee.Image.")

    if format not in ["png", "jpg"]:
        raise ValueError("The output image format must be png or jpg.")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        count = int(ee_object.size().getInfo())
        if verbose:
            print(f"Total number of images: {count}\n")

        if (names is not None) and (len(names) != count):
            print("The number of names is not equal to the number of images.")
            return

        if names is None:
            names = ee_object.aggregate_array("system:index").getInfo()

        images = ee_object.toList(count)

        for i in range(0, count):
            image = ee.Image(images.get(i))
            name = str(names[i])
            ext = os.path.splitext(name)[1][1:]
            if ext != format:
                name = name + "." + format
            out_img = os.path.join(out_dir, name)
            if verbose:
                print(f"Downloading {i+1}/{count}: {name} ...")

            get_image_thumbnail(image, out_img, vis_params, dimensions, region, format)

    except Exception as e:
        print(e)


def netcdf_to_ee(nc_file, var_names, band_names=None, lon="lon", lat="lat"):
    """
    Creates an ee.Image from netCDF variables band_names that are read from nc_file. Currently only supports variables in a regular longitude/latitude grid (EPSG:4326).

    Args:
        nc_file (str): the name of the netCDF file to read
        var_names (str or list): the name(s) of the variable(s) to read
        band_names (list, optional): if given, the bands are renamed to band_names. Defaults to the original var_names
        lon (str, optional): the name of the longitude variable in the netCDF file. Defaults to "lon"
        lat (str, optional): the name of the latitude variable in the netCDF file. Defaults to "lat"

    Returns:
        image: An ee.Image

    """
    try:
        import xarray as xr

    except Exception:
        raise ImportError(
            "You need to install xarray first. See https://github.com/pydata/xarray"
        )

    import numpy as np

    try:

        if not isinstance(nc_file, str):
            print("The input file must be a string.")
            return
        if band_names and not isinstance(band_names, (list, str)):
            print("Band names must be a string or list.")
            return
        if not isinstance(lon, str) or not isinstance(lat, str):
            print("The longitude and latitude variable names must be a string.")
            return

        ds = xr.open_dataset(nc_file)
        data = ds[var_names]

        lon_data = data[lon]
        lat_data = data[lat]

        dim_lon = np.unique(np.ediff1d(lon_data))
        dim_lat = np.unique(np.ediff1d(lat_data))

        if (len(dim_lon) != 1) or (len(dim_lat) != 1):
            print("The netCDF file is not a regular longitude/latitude grid")
            return

        try:
            data = data.to_array()
            # ^ this is only needed (and works) if we have more than 1 variable
            # axis_for_roll will be used in case we need to use np.roll
            # and should be 1 for the case with more than 1 variable
            axis_for_roll = 1
        except Exception:
            axis_for_roll = 0
            # .to_array() does not work (and is not needed!) if there is only 1 variable
            # in this case, the axis_for_roll needs to be 0

        data_np = np.array(data)

        do_transpose = True  # To do: figure out if we need to tranpose the data or not
        if do_transpose:
            try:
                data_np = np.transpose(data_np, (0, 2, 1))
            except Exception:
                data_np = np.transpose(data_np)

        # Figure out if we need to roll the data or not
        # (see https://github.com/giswqs/geemap/issues/285#issuecomment-791385176)
        if np.max(lon_data) > 180:
            data_np = np.roll(data_np, 180, axis=axis_for_roll)
            west_lon = lon_data[0] - 180
        else:
            west_lon = lon_data[0]

        transform = [dim_lon[0], 0, float(west_lon), 0, dim_lat[0], float(lat_data[0])]

        if band_names is None:
            band_names = var_names

        image = numpy_to_ee(
            data_np, "EPSG:4326", transform=transform, band_names=band_names
        )

        return image

    except Exception as e:
        print(e)


def numpy_to_ee(np_array, crs=None, transform=None, transformWkt=None, band_names=None):
    """
    Creates an ee.Image from a 3D numpy array where each 2D numpy slice is added to a band, and a geospatial transform that indicates where to put the data. If the np_array is already 2D only, then it is only a one-band image.

    Args:
        np_array (np.array): the 3D (or 2D) numpy array to add to an image
        crs (str): The base coordinate reference system of this Projection, given as a well-known authority code (e.g. 'EPSG:4326') or a WKT string.
        transform (list): The transform between projected coordinates and the base coordinate system, specified as a 2x3 affine transform matrix in row-major order: [xScale, xShearing, xTranslation, yShearing, yScale, yTranslation]. May not specify both this and 'transformWkt'.
        transformWkt (str): The transform between projected coordinates and the base coordinate system, specified as a WKT string. May not specify both this and 'transform'.
        band_names (str or list, optional): The list of names for the bands. The default names are 'constant', and 'constant_1', 'constant_2', etc.

    Returns:
        image: An ee.Image

    """
    import numpy as np

    if not isinstance(np_array, np.ndarray):
        print("The input must be a numpy.ndarray.")
        return
    if not len(np_array.shape) in [2, 3]:
        print("The input must have 2 or 3 dimensions")
        return
    if band_names and not isinstance(band_names, (list, str)):
        print("Band names must be a str or list")
        return

    try:

        projection = ee.Projection(crs, transform, transformWkt)
        coords = ee.Image.pixelCoordinates(projection).floor().int32()
        x = coords.select("x")
        y = coords.select("y")
        s = np_array.shape
        if len(s) < 3:
            dimx = s[0]
            dimy = s[1]
        else:
            dimx = s[1]
            dimy = s[2]
            dimz = s[0]

        coord_mask = x.gte(0).And(y.gte(0)).And(x.lt(dimx)).And(y.lt(dimy))
        coords = coords.updateMask(coord_mask)

        def list_to_ee(a_list):
            ee_data = ee.Array(a_list)
            image = ee.Image(ee_data).arrayGet(coords)
            return image

        if len(s) < 3:
            image = list_to_ee(np_array.tolist())
        else:
            image = list_to_ee(np_array[0].tolist())
            for z in np.arange(1, dimz):
                image = image.addBands(list_to_ee(np_array[z].tolist()))

        if band_names:
            image = image.rename(band_names)

        return image

    except Exception as e:
        print(e)


def ee_to_numpy(
    ee_object, bands=None, region=None, properties=None, default_value=None
):
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
        print("The input must be an ee.Image.")
        return

    if region is None:
        region = ee_object.geometry()

    try:

        if bands is not None:
            ee_object = ee_object.select(bands)
        else:
            bands = ee_object.bandNames().getInfo()

        band_arrs = ee_object.sampleRectangle(
            region=region, properties=properties, defaultValue=default_value
        )
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
        video_args (object): Parameters for expring the video thumbnail.
        out_gif (str): File path to the output GIF.
    """
    import requests

    out_gif = os.path.abspath(out_gif)
    if not out_gif.endswith(".gif"):
        print("The output file must have an extension of .gif.")
        return

    if not os.path.exists(os.path.dirname(out_gif)):
        os.makedirs(os.path.dirname(out_gif))

    if "region" in video_args.keys():
        roi = video_args["region"]

        if not isinstance(roi, ee.Geometry):

            try:
                roi = roi.geometry()
            except Exception as e:
                print("Could not convert the provided roi to ee.Geometry")
                print(e)
                return

        video_args["region"] = roi
    if "dimensions" not in video_args:
        video_args["dimensions"] = 768

    try:
        print("Generating URL...")
        url = collection.getVideoThumbURL(video_args)

        print(f"Downloading GIF image from {url}\nPlease wait ...")
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            print("An error occurred while downloading.")
            print(r.json()["error"]["message"])
            return
        else:
            with open(out_gif, "wb") as fd:
                for chunk in r.iter_content(chunk_size=1024):
                    fd.write(chunk)
            print(f"The GIF image has been saved to: {out_gif}")
    except Exception as e:
        print(e)


def screen_capture(outfile, monitor=1):
    """Takes a full screenshot of the selected monitor.

    Args:
        outfile (str): The output file path to the screenshot.
        monitor (int, optional): The monitor to take the screenshot. Defaults to 1.
    """
    from mss import mss

    out_dir = os.path.dirname(outfile)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not isinstance(monitor, int):
        print("The monitor number must be an integer.")
        return

    try:
        with mss() as sct:
            sct.shot(output=outfile, mon=monitor)
            return outfile

    except Exception as e:
        print(e)


########################################
#               geemap GUI             #
########################################


def api_docs():
    """Open a browser and navigate to the geemap API documentation."""
    import webbrowser

    url = "https://geemap.org/geemap"
    webbrowser.open_new_tab(url)


def show_youtube(id="h0pz3S6Tvx0"):
    """Displays a YouTube video within Jupyter notebooks.

    Args:
        id (str, optional): Unique ID of the video. Defaults to 'h0pz3S6Tvx0'.

    """
    from IPython.display import YouTubeVideo, display

    if "/" in id:
        id = id.split("/")[-1]

    try:
        out = widgets.Output(layout={"width": "815px"})
        # layout={'border': '1px solid black', 'width': '815px'})
        out.clear_output(wait=True)
        display(out)
        with out:
            display(YouTubeVideo(id, width=800, height=450))
    except Exception as e:
        print(e)


def create_colorbar(
    width=150,
    height=30,
    palette=["blue", "green", "red"],
    add_ticks=True,
    add_labels=True,
    labels=None,
    vertical=False,
    out_file=None,
    font_type="arial.ttf",
    font_size=12,
    font_color="black",
    add_outline=True,
    outline_color="black",
):
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
    import warnings

    # import io
    import pkg_resources
    from colour import Color
    from PIL import Image, ImageDraw, ImageFont

    warnings.simplefilter("ignore")
    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))

    if out_file is None:
        filename = "colorbar_" + random_string() + ".png"
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        out_file = os.path.join(out_dir, filename)
    elif not out_file.endswith(".png"):
        print("The output file must end with .png")
        return
    else:
        out_file = os.path.abspath(out_file)

    if not os.path.exists(os.path.dirname(out_file)):
        os.makedirs(os.path.dirname(out_file))

    im = Image.new("RGBA", (width, height))
    ld = im.load()

    def float_range(start, stop, step):
        while start < stop:
            yield float(start)
            start += decimal.Decimal(step)

    n_colors = len(palette)
    decimal_places = 2
    rgb_colors = [Color(check_color(c)).rgb for c in palette]
    keys = [
        round(c, decimal_places)
        for c in list(float_range(0, 1.0001, 1.0 / (n_colors - 1)))
    ]

    heatmap = []
    for index, item in enumerate(keys):
        pair = [item, rgb_colors[index]]
        heatmap.append(pair)

    def gaussian(x, a, b, c, d=0):
        return a * math.exp(-((x - b) ** 2) / (2 * c ** 2)) + d

    def pixel(x, width=100, map=[], spread=1):
        width = float(width)
        r = sum(
            [
                gaussian(x, p[1][0], p[0] * width, width / (spread * len(map)))
                for p in map
            ]
        )
        g = sum(
            [
                gaussian(x, p[1][1], p[0] * width, width / (spread * len(map)))
                for p in map
            ]
        )
        b = sum(
            [
                gaussian(x, p[1][2], p[0] * width, width / (spread * len(map)))
                for p in map
            ]
        )
        return min(1.0, r), min(1.0, g), min(1.0, b)

    for x in range(im.size[0]):
        r, g, b = pixel(x, width=width, map=heatmap)
        r, g, b = [int(256 * v) for v in (r, g, b)]
        for y in range(im.size[1]):
            ld[x, y] = r, g, b

    if add_outline:
        draw = ImageDraw.Draw(im)
        draw.rectangle(
            [(0, 0), (width - 1, height - 1)], outline=check_color(outline_color)
        )
        del draw

    if add_ticks:
        tick_length = height * 0.1
        x = [key * width for key in keys]
        y_top = height - tick_length
        y_bottom = height
        draw = ImageDraw.Draw(im)
        for i in x:
            shape = [(i, y_top), (i, y_bottom)]
            draw.line(shape, fill="black", width=0)
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
            labels = [str(lowerbound + c * step) for c in range(0, len(palette))]
        except Exception as e:
            print(e)
            print("The labels are invalid.")
            return
    elif len(labels) == len(palette):
        labels = [str(c) for c in labels]
    else:
        print("The labels must have the same length as the palette.")
        return

    if add_labels:

        default_font = os.path.join(pkg_dir, "data/fonts/arial.ttf")
        if font_type == "arial.ttf":
            font = ImageFont.truetype(default_font, font_size)
        else:
            try:
                font_list = system_fonts(show_full_path=True)
                font_names = [os.path.basename(f) for f in font_list]
                if (font_type in font_list) or (font_type in font_names):
                    font = ImageFont.truetype(font_type, font_size)
                else:
                    print(
                        "The specified font type could not be found on your system. Using the default font instead."
                    )
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
        background = Image.new("RGBA", (W, H))
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


def save_colorbar(
    out_fig=None,
    width=6.0,
    height=0.4,
    vmin=0,
    vmax=1.0,
    palette=None,
    vis_params=None,
    cmap="gray",
    discrete=False,
    label=None,
    label_size=12,
    label_weight="normal",
    tick_size=10,
    bg_color=None,
    orientation="horizontal",
    dpi="figure",
    show_colorbar=True,
    **kwargs,
):
    """Create a standalone colorbar and save it as an image.

    Args:
        out_fig (str): Path to the output image.
        width (float): Width of the colorbar in inches. Default is 6.0.
        height (float): Height of the colorbar in inches. Default is 0.4.
        vmin (float): Minimum value of the colorbar. Default is 0.
        vmax (float): Maximum value of the colorbar. Default is 1.0.
        palette (list): List of colors to use for the colorbar. It can also be a cmap name, such as ndvi, ndwi, dem, coolwarm. Default is None.
        vis_params (dict): Visualization parameters as a dictionary. See https://developers.google.com/earth-engine/guides/image_visualization for options.
        cmap (str, optional): Matplotlib colormap. Defaults to "gray". See https://matplotlib.org/3.3.4/tutorials/colors/colormaps.html#sphx-glr-tutorials-colors-colormaps-py for options.
        discrete (bool, optional): Whether to create a discrete colorbar. Defaults to False.
        label (str, optional): Label for the colorbar. Defaults to None.
        label_size (int, optional): Font size for the colorbar label. Defaults to 12.
        label_weight (str, optional): Font weight for the colorbar label, can be "normal", "bold", etc. Defaults to "normal".
        tick_size (int, optional): Font size for the colorbar tick labels. Defaults to 10.
        bg_color (str, optional): Background color for the colorbar. Defaults to None.
        orientation (str, optional): Orientation of the colorbar, such as "vertical" and "horizontal". Defaults to "horizontal".
        dpi (float | str, optional): The resolution in dots per inch.  If 'figure', use the figure's dpi value.. Defaults to "figure".
        show_colorbar (bool, optional): Whether to show the colorbar. Defaults to True.

    Returns:
        str: Path to the output image.
    """
    import ipywidgets as widgets
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import numpy as np
    from .colormaps import palettes, get_palette

    if out_fig is None:
        out_fig = temp_file_path("png")
    else:
        out_fig = check_file_path(out_fig)

    if vis_params is None:
        vis_params = {}
    elif not isinstance(vis_params, dict):
        raise TypeError("The vis_params must be a dictionary.")

    if palette is not None:
        if palette in ["ndvi", "ndwi", "dem"]:
            palette = palettes[palette]
        elif palette in list(palettes.keys()):
            palette = get_palette(palette)
        vis_params["palette"] = palette

    orientation = orientation.lower()
    if orientation not in ["horizontal", "vertical"]:
        raise ValueError("The orientation must be either horizontal or vertical.")

    if "opacity" in vis_params:
        alpha = vis_params["opacity"]
        if type(alpha) not in (int, float):
            raise ValueError("The provided opacity value must be type scalar.")
    elif "alpha" in kwargs:
        alpha = kwargs["alpha"]
    else:
        alpha = 1

    if cmap is not None:

        cmap = mpl.pyplot.get_cmap(cmap)
        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    if "palette" in vis_params:
        hexcodes = to_hex_colors(vis_params["palette"])
        if discrete:
            cmap = mpl.colors.ListedColormap(hexcodes)
            vals = np.linspace(vmin, vmax, cmap.N + 1)
            norm = mpl.colors.BoundaryNorm(vals, cmap.N)

        else:
            cmap = mpl.colors.LinearSegmentedColormap.from_list(
                "custom", hexcodes, N=256
            )
            norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    elif cmap is not None:

        cmap = mpl.pyplot.get_cmap(cmap)
        norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    else:
        raise ValueError(
            'cmap keyword or "palette" key in vis_params must be provided.'
        )

    fig, ax = plt.subplots(figsize=(width, height))
    cb = mpl.colorbar.ColorbarBase(
        ax, norm=norm, alpha=alpha, cmap=cmap, orientation=orientation, **kwargs
    )
    if label is not None:
        cb.set_label(label=label, size=label_size, weight=label_weight)
    cb.ax.tick_params(labelsize=tick_size)
    fig.savefig(out_fig, dpi=dpi, facecolor=bg_color, bbox_inches="tight")
    if not show_colorbar:
        plt.close(fig)
    return out_fig


def minimum_bounding_box(geojson):
    """Gets the minimum bounding box for a geojson polygon.

    Args:
        geojson (dict): A geojson dictionary.

    Returns:
        tuple: Returns a tuple containing the minimum bounding box in the format of (lower_left(lat, lon), upper_right(lat, lon)), such as ((13, -130), (32, -120)).
    """
    coordinates = []
    try:
        if "geometry" in geojson.keys():
            coordinates = geojson["geometry"]["coordinates"][0]
        else:
            coordinates = geojson["coordinates"][0]
        lower_left = min([x[1] for x in coordinates]), min(
            [x[0] for x in coordinates]
        )  # (lat, lon)
        upper_right = max([x[1] for x in coordinates]), max(
            [x[0] for x in coordinates]
        )  # (lat, lon)
        bounds = (lower_left, upper_right)
        return bounds
    except Exception as e:
        raise Exception(e)


def geocode(location, max_rows=10, reverse=False):
    """Search location by address and lat/lon coordinates.

    Args:
        location (str): Place name or address
        max_rows (int, optional): Maximum number of records to return. Defaults to 10.
        reverse (bool, optional): Search place based on coordinates. Defaults to False.

    Returns:
        list: Returns a list of locations.
    """
    import geocoder

    if not isinstance(location, str):
        print("The location must be a string.")
        return None

    if not reverse:

        locations = []
        addresses = set()
        g = geocoder.arcgis(location, maxRows=max_rows)

        for result in g:
            address = result.address
            if address not in addresses:
                addresses.add(address)
                locations.append(result)

        if len(locations) > 0:
            return locations
        else:
            return None

    else:
        try:
            if "," in location:
                latlon = [float(x) for x in location.split(",")]
            elif " " in location:
                latlon = [float(x) for x in location.split(" ")]
            else:
                print(
                    "The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3"
                )
                return
            g = geocoder.arcgis(latlon, method="reverse")
            locations = []
            addresses = set()

            for result in g:
                address = result.address
                if address not in addresses:
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
    if "," in location:
        latlon = [float(x) for x in location.split(",")]
    elif " " in location:
        latlon = [float(x) for x in location.split(" ")]
    else:
        print(
            "The coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3"
        )
        return False

    try:
        lat, lon = float(latlon[0]), float(latlon[1])
        if lat >= -90 and lat <= 90 and lon >= -180 and lon <= 180:
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
        if "," in location:
            latlon = [float(x) for x in location.split(",")]
        elif " " in location:
            latlon = [float(x) for x in location.split(" ")]
        else:
            print(
                "The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3"
            )
            return None

        lat, lon = latlon[0], latlon[1]
        if lat >= -90 and lat <= 90 and lon >= -180 and lon <= 180:
            return lat, lon
        else:
            return None

    except Exception as e:
        print(e)
        print(
            "The lat-lon coordinates should be numbers only and separated by comma or space, such as 40.2, -100.3"
        )
        return None


def search_ee_data(keywords):
    """Searches Earth Engine data catalog.

    Args:
        keywords (str): Keywords to search for can be id, provider, tag and so on

    Returns:
        list: Returns a lit of assets.
    """
    try:
        cmd = f'geeadd search --keywords "{str(keywords)}"'
        output = os.popen(cmd).read()
        start_index = output.index("[")
        assets = eval(output[start_index:])

        results = []
        for asset in assets:
            asset_dates = asset["start_date"] + " - " + asset["end_date"]
            asset_snippet = asset["ee_id_snippet"]
            if "ee." in asset_snippet:
                start_index = asset_snippet.index("'") + 1
                end_index = asset_snippet.index("'", start_index)
                asset_id = asset_snippet[start_index:end_index]
            else:
                asset_id = asset_snippet

            asset["dates"] = asset_dates
            asset["id"] = asset_id
            asset["uid"] = asset_id.replace("/", "_")
            # asset['url'] = 'https://developers.google.com/earth-engine/datasets/catalog/' + asset['uid']
            # asset['thumbnail'] = 'https://mw1.google.com/ges/dd/images/{}_sample.png'.format(
            #     asset['uid'])
            results.append(asset)

        return results

    except Exception as e:
        print(e)


def ee_data_thumbnail(asset_id):
    """Retrieves the thumbnail URL of an Earth Engine asset.

    Args:
        asset_id (str): An Earth Engine asset id.

    Returns:
        str: An http url of the thumbnail.
    """
    import urllib

    import requests
    from bs4 import BeautifulSoup

    asset_uid = asset_id.replace("/", "_")
    asset_url = "https://developers.google.com/earth-engine/datasets/catalog/{}".format(
        asset_uid
    )
    thumbnail_url = "https://mw1.google.com/ges/dd/images/{}_sample.png".format(
        asset_uid
    )

    r = requests.get(thumbnail_url)

    try:
        if r.status_code != 200:
            html_page = urllib.request.urlopen(asset_url)
            soup = BeautifulSoup(html_page, features="html.parser")

            for img in soup.findAll("img"):
                if "sample.png" in img.get("src"):
                    thumbnail_url = img.get("src")
                    return thumbnail_url

        return thumbnail_url
    except Exception as e:
        print(e)


def ee_data_html(asset):
    """Generates HTML from an asset to be used in the HTML widget.

    Args:
        asset (dict): A dictionary containing an Earth Engine asset.

    Returns:
        str: A string containing HTML.
    """
    template = """
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
    """

    try:

        text = template.replace("asset_title", asset["title"])
        text = text.replace("asset_dates", asset["dates"])
        text = text.replace("ee_id_snippet", asset["ee_id_snippet"])
        text = text.replace("asset_id", asset["id"])
        text = text.replace("asset_url", asset["asset_url"])
        # asset['thumbnail'] = ee_data_thumbnail(asset['id'])
        text = text.replace("thumbnail_url", asset["thumbnail_url"])

        return text

    except Exception as e:
        print(e)


def create_code_cell(code="", where="below"):
    """Creates a code cell in the IPython Notebook.

    Args:
        code (str, optional): Code to fill the new code cell with. Defaults to ''.
        where (str, optional): Where to add the new code cell. It can be one of the following: above, below, at_bottom. Defaults to 'below'.
    """

    import base64

    from IPython.display import Javascript, display

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


def ee_api_to_csv(outfile=None):
    """Extracts Earth Engine API documentation from https://developers.google.com/earth-engine/api_docs as a csv file.

    Args:
        outfile (str, optional): The output file path to a csv file. Defaults to None.
    """
    import pkg_resources
    import requests
    from bs4 import BeautifulSoup

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    data_dir = os.path.join(pkg_dir, "data")
    template_dir = os.path.join(data_dir, "template")
    csv_file = os.path.join(template_dir, "ee_api_docs.csv")

    if outfile is None:
        outfile = csv_file
    else:
        if not outfile.endswith(".csv"):
            print("The output file must end with .csv")
            return
        else:
            out_dir = os.path.dirname(outfile)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

    url = "https://developers.google.com/earth-engine/api_docs"

    try:

        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")

        names = []
        descriptions = []
        functions = []
        returns = []
        arguments = []
        types = []
        details = []

        names = [h2.text for h2 in soup.find_all("h2")]
        descriptions = [h2.next_sibling.next_sibling.text for h2 in soup.find_all("h2")]
        func_tables = soup.find_all("table", class_="blue")
        functions = [func_table.find("code").text for func_table in func_tables]
        returns = [func_table.find_all("td")[1].text for func_table in func_tables]

        detail_tables = []
        tables = soup.find_all("table", class_="blue")

        for table in tables:
            item = table.next_sibling
            if item.attrs == {"class": ["details"]}:
                detail_tables.append(item)
            else:
                detail_tables.append("")

        for detail_table in detail_tables:
            if detail_table != "":
                items = [item.text for item in detail_table.find_all("code")]
            else:
                items = ""
            arguments.append(items)

        for detail_table in detail_tables:
            if detail_table != "":
                items = [item.text for item in detail_table.find_all("td")]
                items = items[1::3]
            else:
                items = ""
            types.append(items)

        for detail_table in detail_tables:
            if detail_table != "":
                items = [item.text for item in detail_table.find_all("p")]
            else:
                items = ""
            details.append(items)

        with open(outfile, "w", encoding="utf-8") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter="\t")

            csv_writer.writerow(
                [
                    "name",
                    "description",
                    "function",
                    "returns",
                    "argument",
                    "type",
                    "details",
                ]
            )

            for i in range(len(names)):
                name = names[i]
                description = descriptions[i]
                function = functions[i]
                return_type = returns[i]
                argument = "|".join(arguments[i])
                argu_type = "|".join(types[i])
                detail = "|".join(details[i])

                csv_writer.writerow(
                    [
                        name,
                        description,
                        function,
                        return_type,
                        argument,
                        argu_type,
                        detail,
                    ]
                )

    except Exception as e:
        print(e)


def read_api_csv():
    """Extracts Earth Engine API from a csv file and returns a dictionary containing information about each function.

    Returns:
        dict: The dictionary containing information about each function, including name, description, function form, return type, arguments, html.
    """
    import copy

    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    data_dir = os.path.join(pkg_dir, "data")
    template_dir = os.path.join(data_dir, "template")
    csv_file = os.path.join(template_dir, "ee_api_docs.csv")
    html_file = os.path.join(template_dir, "ee_api_docs.html")

    with open(html_file) as f:
        in_html_lines = f.readlines()

    api_dict = {}

    with open(csv_file, "r", encoding="utf-8") as f:
        csv_reader = csv.DictReader(f, delimiter="\t")

        for line in csv_reader:

            out_html_lines = copy.copy(in_html_lines)
            out_html_lines[65] = in_html_lines[65].replace(
                "function_name", line["name"]
            )
            out_html_lines[66] = in_html_lines[66].replace(
                "function_description", line.get("description")
            )
            out_html_lines[74] = in_html_lines[74].replace(
                "function_usage", line.get("function")
            )
            out_html_lines[75] = in_html_lines[75].replace(
                "function_returns", line.get("returns")
            )

            arguments = line.get("argument")
            types = line.get("type")
            details = line.get("details")

            if "|" in arguments:
                argument_items = arguments.split("|")
            else:
                argument_items = [arguments]

            if "|" in types:
                types_items = types.split("|")
            else:
                types_items = [types]

            if "|" in details:
                details_items = details.split("|")
            else:
                details_items = [details]

            out_argument_lines = []

            for index in range(len(argument_items)):
                in_argument_lines = in_html_lines[87:92]
                in_argument_lines[1] = in_argument_lines[1].replace(
                    "function_argument", argument_items[index]
                )
                in_argument_lines[2] = in_argument_lines[2].replace(
                    "function_type", types_items[index]
                )
                in_argument_lines[3] = in_argument_lines[3].replace(
                    "function_details", details_items[index]
                )
                out_argument_lines.append("".join(in_argument_lines))

            out_html_lines = (
                out_html_lines[:87] + out_argument_lines + out_html_lines[92:]
            )

            contents = "".join(out_html_lines)

            api_dict[line["name"]] = {
                "description": line.get("description"),
                "function": line.get("function"),
                "returns": line.get("returns"),
                "argument": line.get("argument"),
                "type": line.get("type"),
                "details": line.get("details"),
                "html": contents,
            }

    return api_dict


def ee_function_tree(name):
    """Construct the tree structure based on an Earth Engine function. For example, the function "ee.Algorithms.FMask.matchClouds" will return a list ["ee.Algorithms", "ee.Algorithms.FMask", "ee.Algorithms.FMask.matchClouds"]

    Args:
        name (str): The name of the Earth Engine function

    Returns:
        list: The list for parent functions.
    """
    func_list = []
    try:
        items = name.split(".")
        if items[0] == "ee":
            for i in range(2, len(items) + 1):
                func_list.append(".".join(items[0:i]))
        else:
            for i in range(1, len(items) + 1):
                func_list.append(".".join(items[0:i]))

        return func_list
    except Exception as e:
        print(e)
        print("The provided function name is invalid.")


def build_api_tree(api_dict, output_widget, layout_width="100%"):
    """Builds an Earth Engine API tree view.

    Args:
        api_dict (dict): The dictionary containing information about each Earth Engine API function.
        output_widget (object): An Output widget.
        layout_width (str, optional): The percentage width of the widget. Defaults to '100%'.

    Returns:
        tuple: Returns a tuple containing two items: a tree Output widget and a tree dictionary.
    """
    import warnings

    warnings.filterwarnings("ignore")

    tree = Tree()
    tree_dict = {}

    names = api_dict.keys()

    def handle_click(event):
        if event["new"]:
            name = event["owner"].name
            values = api_dict[name]

            with output_widget:
                output_widget.clear_output()
                html_widget = widgets.HTML(value=values["html"])
                display(html_widget)

    for name in names:
        func_list = ee_function_tree(name)
        first = func_list[0]

        if first not in tree_dict.keys():
            tree_dict[first] = Node(first)
            tree_dict[first].opened = False
            tree.add_node(tree_dict[first])

        for index, func in enumerate(func_list):
            if index > 0:
                if func not in tree_dict.keys():
                    node = tree_dict[func_list[index - 1]]
                    node.opened = False
                    tree_dict[func] = Node(func)
                    node.add_node(tree_dict[func])

                    if index == len(func_list) - 1:
                        node = tree_dict[func_list[index]]
                        node.icon = "file"
                        node.observe(handle_click, "selected")

    return tree, tree_dict


def search_api_tree(keywords, api_tree):
    """Search Earth Engine API and return functions containing the specified keywords

    Args:
        keywords (str): The keywords to search for.
        api_tree (dict): The dictionary containing the Earth Engine API tree.

    Returns:
        object: An ipytree object/widget.
    """
    import warnings

    warnings.filterwarnings("ignore")

    sub_tree = Tree()

    for key in api_tree.keys():
        if keywords.lower() in key.lower():
            sub_tree.add_node(api_tree[key])

    return sub_tree


def ee_search(asset_limit=100):
    """Search Earth Engine API and user assets. If you received a warning (IOPub message rate exceeded) in Jupyter notebook, you can relaunch Jupyter notebook using the following command:
        jupyter notebook --NotebookApp.iopub_msg_rate_limit=10000

    Args:
        asset_limit (int, optional): The number of assets to display for each asset type, i.e., Image, ImageCollection, and FeatureCollection. Defaults to 100.
    """

    import warnings

    warnings.filterwarnings("ignore")

    class Flags:
        def __init__(
            self,
            repos=None,
            docs=None,
            assets=None,
            docs_dict=None,
            asset_dict=None,
            asset_import=None,
        ):
            self.repos = repos
            self.docs = docs
            self.assets = assets
            self.docs_dict = docs_dict
            self.asset_dict = asset_dict
            self.asset_import = asset_import

    flags = Flags()

    search_type = widgets.ToggleButtons(
        options=["Scripts", "Docs", "Assets"],
        tooltips=[
            "Search Earth Engine Scripts",
            "Search Earth Engine API",
            "Search Earth Engine Assets",
        ],
        button_style="primary",
    )
    search_type.style.button_width = "100px"

    search_box = widgets.Text(placeholder="Filter scripts...", value="Loading...")
    search_box.layout.width = "310px"

    tree_widget = widgets.Output()

    left_widget = widgets.VBox()
    right_widget = widgets.VBox()
    output_widget = widgets.Output()
    output_widget.layout.max_width = "650px"

    search_widget = widgets.HBox()
    search_widget.children = [left_widget, right_widget]
    display(search_widget)

    repo_tree, repo_output, _ = build_repo_tree()
    left_widget.children = [search_type, repo_tree]
    right_widget.children = [repo_output]

    flags.repos = repo_tree
    search_box.value = ""

    def search_type_changed(change):
        search_box.value = ""

        output_widget.clear_output()
        tree_widget.clear_output()
        if change["new"] == "Scripts":
            search_box.placeholder = "Filter scripts..."
            left_widget.children = [search_type, repo_tree]
            right_widget.children = [repo_output]
        elif change["new"] == "Docs":
            search_box.placeholder = "Filter methods..."
            search_box.value = "Loading..."
            left_widget.children = [search_type, search_box, tree_widget]
            right_widget.children = [output_widget]
            if flags.docs is None:
                api_dict = read_api_csv()
                ee_api_tree, tree_dict = build_api_tree(api_dict, output_widget)
                flags.docs = ee_api_tree
                flags.docs_dict = tree_dict
            else:
                ee_api_tree = flags.docs
            with tree_widget:
                tree_widget.clear_output()
                display(ee_api_tree)
                right_widget.children = [output_widget]
            search_box.value = ""
        elif change["new"] == "Assets":
            search_box.placeholder = "Filter assets..."
            left_widget.children = [search_type, search_box, tree_widget]
            right_widget.children = [output_widget]
            search_box.value = "Loading..."
            if flags.assets is None:
                asset_tree, asset_widget, asset_dict = build_asset_tree(
                    limit=asset_limit
                )
                flags.assets = asset_tree
                flags.asset_dict = asset_dict
                flags.asset_import = asset_widget

            with tree_widget:
                tree_widget.clear_output()
                display(flags.assets)
            right_widget.children = [flags.asset_import]
            search_box.value = ""

    search_type.observe(search_type_changed, names="value")

    def search_box_callback(text):

        if search_type.value == "Docs":
            with tree_widget:
                if text.value == "":
                    print("Loading...")
                    tree_widget.clear_output(wait=True)
                    display(flags.docs)
                else:
                    tree_widget.clear_output()
                    print("Searching...")
                    tree_widget.clear_output(wait=True)
                    sub_tree = search_api_tree(text.value, flags.docs_dict)
                    display(sub_tree)
        elif search_type.value == "Assets":
            with tree_widget:
                if text.value == "":
                    print("Loading...")
                    tree_widget.clear_output(wait=True)
                    display(flags.assets)
                else:
                    tree_widget.clear_output()
                    print("Searching...")
                    tree_widget.clear_output(wait=True)
                    sub_tree = search_api_tree(text.value, flags.asset_dict)
                    display(sub_tree)

    search_box.on_submit(search_box_callback)


def ee_user_id():
    """Gets Earth Engine account user id.

    Returns:
        str: A string containing the user id.
    """
    # ee_initialize()
    roots = ee.data.getAssetRoots()
    if len(roots) == 0:
        return None
    else:
        root = ee.data.getAssetRoots()[0]
        user_id = root["id"].replace("projects/earthengine-legacy/assets/", "")
        return user_id


def build_asset_tree(limit=100):

    import warnings

    import geeadd.ee_report as geeadd

    warnings.filterwarnings("ignore")

    # ee_initialize()

    tree = Tree(multiple_selection=False)
    tree_dict = {}
    asset_types = {}

    asset_icons = {
        "FOLDER": "folder",
        "TABLE": "table",
        "IMAGE": "image",
        "IMAGE_COLLECTION": "file",
    }

    info_widget = widgets.HBox()

    import_btn = widgets.Button(
        description="import",
        button_style="primary",
        tooltip="Click to import the selected asset",
        disabled=True,
    )
    import_btn.layout.min_width = "57px"
    import_btn.layout.max_width = "57px"

    path_widget = widgets.Text()
    path_widget.layout.min_width = "500px"
    # path_widget.disabled = True

    info_widget.children = [import_btn, path_widget]

    user_id = ee_user_id()
    if user_id is None:
        print(
            "Your GEE account does not have any assets. Please create a repository at https://code.earthengine.google.com"
        )
        return

    user_path = "projects/earthengine-legacy/assets/" + user_id
    root_node = Node(user_id)
    root_node.opened = True
    tree_dict[user_id] = root_node
    tree.add_node(root_node)

    collection_list, table_list, image_list, folder_paths = geeadd.fparse(user_path)
    collection_list = collection_list[:limit]
    table_list = table_list[:limit]
    image_list = image_list[:limit]
    folder_paths = folder_paths[:limit]
    folders = [p[35:] for p in folder_paths[1:]]

    asset_type = "FOLDER"
    for folder in folders:
        bare_folder = folder.replace(user_id + "/", "")
        if folder not in tree_dict.keys():
            node = Node(bare_folder)
            node.opened = False
            node.icon = asset_icons[asset_type]
            root_node.add_node(node)
            tree_dict[folder] = node
            asset_types[folder] = asset_type

    def import_btn_clicked(b):
        if path_widget.value != "":
            dataset_uid = "dataset_" + random_string(string_length=3)
            layer_name = path_widget.value.split("/")[-1][:-2:]
            line1 = "{} = {}\n".format(dataset_uid, path_widget.value)
            line2 = "Map.addLayer(" + dataset_uid + ', {}, "' + layer_name + '")'
            contents = "".join([line1, line2])
            create_code_cell(contents)

    import_btn.on_click(import_btn_clicked)

    def handle_click(event):
        if event["new"]:
            cur_node = event["owner"]
            for key in tree_dict.keys():
                if cur_node is tree_dict[key]:
                    if asset_types[key] == "IMAGE":
                        path_widget.value = "ee.Image('{}')".format(key)
                    elif asset_types[key] == "IMAGE_COLLECTION":
                        path_widget.value = "ee.ImageCollection('{}')".format(key)
                    elif asset_types[key] == "TABLE":
                        path_widget.value = "ee.FeatureCollection('{}')".format(key)
                    if import_btn.disabled:
                        import_btn.disabled = False
                    break

    assets = [collection_list, image_list, table_list]
    for index, asset_list in enumerate(assets):
        if index == 0:
            asset_type = "IMAGE_COLLECTION"
        elif index == 1:
            asset_type = "IMAGE"
        else:
            asset_type = "TABLE"

        for asset in asset_list:
            items = asset.split("/")
            parent = "/".join(items[:-1])
            child = items[-1]
            parent_node = tree_dict[parent]
            child_node = Node(child)
            child_node.icon = asset_icons[asset_type]
            parent_node.add_node(child_node)
            tree_dict[asset] = child_node
            asset_types[asset] = asset_type
            child_node.observe(handle_click, "selected")

    return tree, info_widget, tree_dict


def build_repo_tree(out_dir=None, name="gee_repos"):
    """Builds a repo tree for GEE account.

    Args:
        out_dir (str): The output directory for the repos. Defaults to None.
        name (str, optional): The output name for the repo directory. Defaults to 'gee_repos'.

    Returns:
        tuple: Returns a tuple containing a tree widget, an output widget, and a tree dictionary containing nodes.
    """
    import warnings

    warnings.filterwarnings("ignore")

    if out_dir is None:
        out_dir = os.path.join(os.path.expanduser("~"))

    repo_dir = os.path.join(out_dir, name)
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)

    URLs = {
        # 'Owner': 'https://earthengine.googlesource.com/{ee_user_id()}/default',
        "Writer": "",
        "Reader": "https://github.com/giswqs/geemap",
        "Examples": "https://github.com/giswqs/earthengine-py-examples",
        "Archive": "https://earthengine.googlesource.com/EGU2017-EE101",
    }

    user_id = ee_user_id()
    if user_id is not None:
        URLs["Owner"] = f"https://earthengine.googlesource.com/{ee_user_id()}/default"

    path_widget = widgets.Text(placeholder="Enter the link to a Git repository here...")
    path_widget.layout.width = "475px"
    clone_widget = widgets.Button(
        description="Clone",
        button_style="primary",
        tooltip="Clone the repository to folder.",
    )
    info_widget = widgets.HBox()

    groups = ["Owner", "Writer", "Reader", "Examples", "Archive"]
    for group in groups:
        group_dir = os.path.join(repo_dir, group)
        if not os.path.exists(group_dir):
            os.makedirs(group_dir)

    example_dir = os.path.join(repo_dir, "Examples/earthengine-py-examples")
    if not os.path.exists(example_dir):
        clone_github_repo(URLs["Examples"], out_dir=example_dir)

    left_widget, right_widget, tree_dict = file_browser(
        in_dir=repo_dir,
        add_root_node=False,
        search_description="Filter scripts...",
        use_import=True,
        return_sep_widgets=True,
    )
    info_widget.children = [right_widget]

    def handle_folder_click(event):
        if event["new"]:
            url = ""
            selected = event["owner"]
            if selected.name in URLs.keys():
                url = URLs[selected.name]

            path_widget.value = url
            clone_widget.disabled = False
            info_widget.children = [path_widget, clone_widget]
        else:
            info_widget.children = [right_widget]

    for group in groups:
        dirname = os.path.join(repo_dir, group)
        node = tree_dict[dirname]
        node.observe(handle_folder_click, "selected")

    def handle_clone_click(b):

        url = path_widget.value
        default_dir = os.path.join(repo_dir, "Examples")
        if url == "":
            path_widget.value = "Please enter a valid URL to the repository."
        else:
            for group in groups:
                key = os.path.join(repo_dir, group)
                node = tree_dict[key]
                if node.selected:
                    default_dir = key
            try:
                path_widget.value = "Cloning..."
                clone_dir = os.path.join(default_dir, os.path.basename(url))
                if url.find("github.com") != -1:
                    clone_github_repo(url, out_dir=clone_dir)
                elif url.find("googlesource") != -1:
                    clone_google_repo(url, out_dir=clone_dir)
                path_widget.value = "Cloned to {}".format(clone_dir)
                clone_widget.disabled = True
            except Exception as e:
                path_widget.value = (
                    "An error occurred when trying to clone the repository " + str(e)
                )
                clone_widget.disabled = True

    clone_widget.on_click(handle_clone_click)

    return left_widget, info_widget, tree_dict


def file_browser(
    in_dir=None,
    show_hidden=False,
    add_root_node=True,
    search_description=None,
    use_import=False,
    return_sep_widgets=False,
    node_icon="file",
):
    """Creates a simple file browser and text editor.

    Args:
        in_dir (str, optional): The input directory. Defaults to None, which will use the current working directory.
        show_hidden (bool, optional): Whether to show hidden files/folders. Defaults to False.
        add_root_node (bool, optional): Whether to add the input directory as a root node. Defaults to True.
        search_description (str, optional): The description of the search box. Defaults to None.
        use_import (bool, optional): Whether to show the import button. Defaults to False.
        return_sep_widgets (bool, optional): Whether to return the results as separate widgets. Defaults to False.

    Returns:
        object: An ipywidget.
    """
    import platform

    if in_dir is None:
        in_dir = os.getcwd()

    if not os.path.exists(in_dir):
        print("The provided directory does not exist.")
        return
    elif not os.path.isdir(in_dir):
        print("The provided path is not a valid directory.")
        return

    sep = "/"
    if platform.system() == "Windows":
        sep = "\\"

    if in_dir.endswith(sep):
        in_dir = in_dir[:-1]

    full_widget = widgets.HBox()
    left_widget = widgets.VBox()

    right_widget = widgets.VBox()

    import_btn = widgets.Button(
        description="import",
        button_style="primary",
        tooltip="import the content to a new cell",
        disabled=True,
    )
    import_btn.layout.width = "70px"
    path_widget = widgets.Text()
    path_widget.layout.min_width = "400px"
    # path_widget.layout.max_width = '400px'
    save_widget = widgets.Button(
        description="Save",
        button_style="primary",
        tooltip="Save edits to file.",
        disabled=True,
    )
    info_widget = widgets.HBox()
    info_widget.children = [path_widget, save_widget]
    if use_import:
        info_widget.children = [import_btn, path_widget, save_widget]

    text_widget = widgets.Textarea()
    text_widget.layout.width = "630px"
    text_widget.layout.height = "600px"

    right_widget.children = [info_widget, text_widget]
    full_widget.children = [left_widget]

    if search_description is None:
        search_description = "Search files/folders..."
    search_box = widgets.Text(placeholder=search_description)
    search_box.layout.width = "310px"
    tree_widget = widgets.Output()
    tree_widget.layout.max_width = "310px"
    tree_widget.overflow = "auto"

    left_widget.children = [search_box, tree_widget]

    tree = Tree(multiple_selection=False)
    tree_dict = {}

    def on_button_clicked(b):
        content = text_widget.value
        out_file = path_widget.value

        out_dir = os.path.dirname(out_file)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        with open(out_file, "w") as f:
            f.write(content)

        text_widget.disabled = True
        text_widget.value = "The content has been saved successfully."
        save_widget.disabled = True
        path_widget.disabled = True

        if (out_file not in tree_dict.keys()) and (out_dir in tree_dict.keys()):
            node = Node(os.path.basename(out_file))
            tree_dict[out_file] = node
            parent_node = tree_dict[out_dir]
            parent_node.add_node(node)

    save_widget.on_click(on_button_clicked)

    def import_btn_clicked(b):
        if (text_widget.value != "") and (path_widget.value.endswith(".py")):
            create_code_cell(text_widget.value)

    import_btn.on_click(import_btn_clicked)

    def search_box_callback(text):

        with tree_widget:
            if text.value == "":
                print("Loading...")
                tree_widget.clear_output(wait=True)
                display(tree)
            else:
                tree_widget.clear_output()
                print("Searching...")
                tree_widget.clear_output(wait=True)
                sub_tree = search_api_tree(text.value, tree_dict)
                display(sub_tree)

    search_box.on_submit(search_box_callback)

    def handle_file_click(event):
        if event["new"]:
            cur_node = event["owner"]
            for key in tree_dict.keys():
                if (cur_node is tree_dict[key]) and (os.path.isfile(key)):
                    if key.endswith(".py"):
                        import_btn.disabled = False
                    else:
                        import_btn.disabled = True
                    try:
                        with open(key) as f:
                            content = f.read()
                            text_widget.value = content
                            text_widget.disabled = False
                            path_widget.value = key
                            path_widget.disabled = False
                            save_widget.disabled = False
                            full_widget.children = [left_widget, right_widget]
                    except Exception as e:
                        path_widget.value = key
                        path_widget.disabled = True
                        save_widget.disabled = True
                        text_widget.disabled = True
                        text_widget.value = (
                            "Failed to open {}.".format(cur_node.name) + "\n\n" + str(e)
                        )
                        full_widget.children = [left_widget, right_widget]
                        return
                    break

    def handle_folder_click(event):
        if event["new"]:
            full_widget.children = [left_widget]
            text_widget.value = ""

    if add_root_node:
        root_name = in_dir.split(sep)[-1]
        root_node = Node(root_name)
        tree_dict[in_dir] = root_node
        tree.add_node(root_node)
        root_node.observe(handle_folder_click, "selected")

    for root, d_names, f_names in os.walk(in_dir):

        if not show_hidden:
            folders = root.split(sep)
            for folder in folders:
                if folder.startswith("."):
                    continue
            for d_name in d_names:
                if d_name.startswith("."):
                    d_names.remove(d_name)
            for f_name in f_names:
                if f_name.startswith("."):
                    f_names.remove(f_name)

        d_names.sort()
        f_names.sort()

        if (not add_root_node) and (root == in_dir):
            for d_name in d_names:
                node = Node(d_name)
                tree_dict[os.path.join(in_dir, d_name)] = node
                tree.add_node(node)
                node.opened = False
                node.observe(handle_folder_click, "selected")

        if (root != in_dir) and (root not in tree_dict.keys()):
            name = root.split(sep)[-1]
            dir_name = os.path.dirname(root)
            parent_node = tree_dict[dir_name]
            node = Node(name)
            tree_dict[root] = node
            parent_node.add_node(node)
            node.observe(handle_folder_click, "selected")

        if len(f_names) > 0:
            parent_node = tree_dict[root]
            parent_node.opened = False
            for f_name in f_names:
                node = Node(f_name)
                node.icon = node_icon
                full_path = os.path.join(root, f_name)
                tree_dict[full_path] = node
                parent_node.add_node(node)
                node.observe(handle_file_click, "selected")

    with tree_widget:
        tree_widget.clear_output()
        display(tree)

    if return_sep_widgets:
        return left_widget, right_widget, tree_dict
    else:
        return full_widget


########################################
#             EE Utilities             #
########################################


def date_sequence(start, end, unit, date_format="YYYY-MM-dd"):
    """Creates a date sequence.

    Args:
        start (str): The start date, e.g., '2000-01-01'.
        end (str): The end date, e.g., '2000-12-31'.
        unit (str): One of 'year', 'quarter', 'month' 'week', 'day', 'hour', 'minute', or 'second'.
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html. Defaults to 'YYYY-MM-dd'.

    Returns:
        ee.List: A list of date sequence.
    """

    def get_quarter(d):
        return str((int(d[5:7]) - 1) // 3 * 3 + 1).zfill(2)

    def get_monday(d):
        date_obj = datetime.datetime.strptime(d, "%Y-%m-%d")
        start_of_week = date_obj - datetime.timedelta(days=date_obj.weekday())
        return start_of_week.strftime("%Y-%m-%d")

    if unit == "year":
        start = start[:4] + "-01-01"
    elif unit == "month":
        start = start[:7] + "-01"
    elif unit == "quarter":
        start = start[:5] + get_quarter(start) + "-01"
    elif unit == "week":
        start = get_monday(start)

    start_date = ee.Date(start)
    end_date = ee.Date(end)

    if unit != "quarter":
        count = ee.Number(end_date.difference(start_date, unit)).toInt()
        num_seq = ee.List.sequence(0, count)
        date_seq = num_seq.map(
            lambda d: start_date.advance(d, unit).format(date_format)
        )

    else:
        unit = "month"
        count = ee.Number(end_date.difference(start_date, unit)).divide(3).toInt()
        num_seq = ee.List.sequence(0, count.multiply(3), 3)
        date_seq = num_seq.map(
            lambda d: start_date.advance(d, unit).format(date_format)
        )

    return date_seq


def legend_from_ee(ee_class_table):
    """Extract legend from an Earth Engine class table on the Earth Engine Data Catalog page
    such as https://developers.google.com/earth-engine/datasets/catalog/MODIS_051_MCD12Q1

    Args:
        ee_class_table (str): An Earth Engine class table with triple quotes.

    Returns:
        dict: Returns a legend dictionary that can be used to create a legend.
    """
    try:
        ee_class_table = ee_class_table.strip()
        lines = ee_class_table.split("\n")[1:]

        if lines[0] == "Value\tColor\tDescription":
            lines = lines[1:]

        legend_dict = {}
        for _, line in enumerate(lines):
            items = line.split("\t")
            items = [item.strip() for item in items]
            color = items[1]
            key = items[0] + " " + items[2]
            legend_dict[key] = color

        return legend_dict

    except Exception as e:
        print(e)


def vis_to_qml(ee_class_table, out_qml):
    """Create a QGIS Layer Style (.qml) based on an Earth Engine class table from the Earth Engine Data Catalog page
    such as https://developers.google.com/earth-engine/datasets/catalog/MODIS_051_MCD12Q1

    Args:
        ee_class_table (str): An Earth Engine class table with triple quotes.
        out_qml (str): File path to the output QGIS Layer Style (.qml).
    """
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    data_dir = os.path.join(pkg_dir, "data")
    template_dir = os.path.join(data_dir, "template")
    qml_template = os.path.join(template_dir, "NLCD.qml")

    out_dir = os.path.dirname(out_qml)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(qml_template) as f:
        lines = f.readlines()
        header = lines[:31]
        footer = lines[51:]

    entries = []
    try:
        ee_class_table = ee_class_table.strip()
        lines = ee_class_table.split("\n")[1:]

        if lines[0] == "Value\tColor\tDescription":
            lines = lines[1:]

        for line in lines:
            items = line.split("\t")
            items = [item.strip() for item in items]
            value = items[0]
            color = items[1]
            label = items[2]
            entry = '        <paletteEntry alpha="255" color="#{}" value="{}" label="{}"/>\n'.format(
                color, value, label
            )
            entries.append(entry)

        out_lines = header + entries + footer
        with open(out_qml, "w") as f:
            f.writelines(out_lines)

    except Exception as e:
        print(e)


def create_nlcd_qml(out_qml):
    """Create a QGIS Layer Style (.qml) for NLCD data

    Args:
        out_qml (str): File path to the output qml.
    """
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    data_dir = os.path.join(pkg_dir, "data")
    template_dir = os.path.join(data_dir, "template")
    qml_template = os.path.join(template_dir, "NLCD.qml")

    out_dir = os.path.dirname(out_qml)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    shutil.copyfile(qml_template, out_qml)


def load_GeoTIFF(URL):
    """Loads a Cloud Optimized GeoTIFF (COG) as an Image. Only Google Cloud Storage is supported. The URL can be one of the following formats:
    Option 1: gs://pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 2: https://storage.googleapis.com/pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 3: https://storage.cloud.google.com/gcp-public-data-landsat/LC08/01/044/034/LC08_L1TP_044034_20131228_20170307_01_T1/LC08_L1TP_044034_20131228_20170307_01_T1_B5.TIF

    Args:
        URL (str): The Cloud Storage URL of the GeoTIFF to load.

    Returns:
        ee.Image: an Earth Engine image.
    """

    uri = URL.strip()

    if uri.startswith("https://storage.googleapis.com/"):
        uri = uri.replace("https://storage.googleapis.com/", "gs://")
    elif uri.startswith("https://storage.cloud.google.com/"):
        uri = uri.replace("https://storage.cloud.google.com/", "gs://")

    if not uri.startswith("gs://"):
        raise Exception(
            f'Invalid GCS URL: {uri}. Expected something of the form "gs://bucket/path/to/object.tif".'
        )

    if not uri.lower().endswith(".tif"):
        raise Exception(
            f'Invalid GCS URL: {uri}. Expected something of the form "gs://bucket/path/to/object.tif".'
        )

    cloud_image = ee.Image.loadGeoTIFF(uri)
    return cloud_image


def load_GeoTIFFs(URLs):
    """Loads a list of Cloud Optimized GeoTIFFs (COG) as an ImageCollection. URLs is a list of URL, which can be one of the following formats:
    Option 1: gs://pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 2: https://storage.googleapis.com/pdd-stac/disasters/hurricane-harvey/0831/20170831_172754_101c_3B_AnalyticMS.tif
    Option 3: https://storage.cloud.google.com/gcp-public-data-landsat/LC08/01/044/034/LC08_L1TP_044034_20131228_20170307_01_T1/LC08_L1TP_044034_20131228_20170307_01_T1_B5.TIF

    Args:
        URLs (list): A list of Cloud Storage URL of the GeoTIFF to load.

    Returns:
        ee.ImageCollection: An Earth Engine ImageCollection.
    """

    if not isinstance(URLs, list):
        raise Exception("The URLs argument must be a list.")

    URIs = []
    for URL in URLs:
        uri = URL.strip()

        if uri.startswith("https://storage.googleapis.com/"):
            uri = uri.replace("https://storage.googleapis.com/", "gs://")
        elif uri.startswith("https://storage.cloud.google.com/"):
            uri = uri.replace("https://storage.cloud.google.com/", "gs://")

        if not uri.startswith("gs://"):
            raise Exception(
                f'Invalid GCS URL: {uri}. Expected something of the form "gs://bucket/path/to/object.tif".'
            )

        if not uri.lower().endswith(".tif"):
            raise Exception(
                f'Invalid GCS URL: {uri}. Expected something of the form "gs://bucket/path/to/object.tif".'
            )

        URIs.append(uri)

    URIs = ee.List(URIs)
    collection = URIs.map(lambda uri: ee.Image.loadGeoTIFF(uri))
    return ee.ImageCollection(collection)


def cog_tile(url, bands=None, titiler_endpoint="https://titiler.xyz", **kwargs):
    """Get a tile layer from a Cloud Optimized GeoTIFF (COG).
        Source code adapted from https://developmentseed.org/titiler/examples/notebooks/Working_with_CloudOptimizedGeoTIFF_simple/

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        tuple: Returns the COG Tile layer URL and bounds.
    """

    kwargs["url"] = url

    band_names = cog_bands(url, titiler_endpoint)

    if bands is None and "bidx" not in kwargs:
        if len(band_names) >= 3:
            kwargs["bidx"] = [1, 2, 3]
    elif bands is not None and "bidx" not in kwargs:
        if all(isinstance(x, int) for x in bands):
            kwargs["bidx"] = bands
        elif all(isinstance(x, str) for x in bands):
            kwargs["bidx"] = [band_names.index(x) + 1 for x in bands]
        else:
            raise ValueError("Bands must be a list of integers or strings.")

    if "palette" in kwargs:
        kwargs["colormap_name"] = kwargs["palette"]
        del kwargs["palette"]

    if "rescale" not in kwargs:
        stats = cog_stats(url, titiler_endpoint)
        percentile_2 = min([stats[s]["percentile_2"] for s in stats])
        percentile_98 = max([stats[s]["percentile_98"] for s in stats])
        kwargs["rescale"] = f"{percentile_2},{percentile_98}"

    TileMatrixSetId = "WebMercatorQuad"
    if "TileMatrixSetId" in kwargs.keys():
        TileMatrixSetId = kwargs["TileMatrixSetId"]
        kwargs.pop("TileMatrixSetId")

    r = requests.get(
        f"{titiler_endpoint}/cog/{TileMatrixSetId}/tilejson.json", params=kwargs
    ).json()

    return r["tiles"][0]


def cog_mosaic(
    links,
    titiler_endpoint="https://titiler.xyz",
    username="anonymous",
    layername=None,
    overwrite=False,
    verbose=True,
    **kwargs,
):
    """Creates a COG mosaic from a list of COG URLs.

    Args:
        links (list): A list containing COG HTTP URLs.
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        username (str, optional): User name for the titiler endpoint. Defaults to "anonymous".
        layername ([type], optional): Layer name to use. Defaults to None.
        overwrite (bool, optional): Whether to overwrite the layer name if existing. Defaults to False.
        verbose (bool, optional): Whether to print out descriptive information. Defaults to True.

    Raises:
        Exception: If the COG mosaic fails to create.

    Returns:
        str: The tile URL for the COG mosaic.
    """

    if layername is None:
        layername = "layer_" + random_string(5)

    try:
        if verbose:
            print("Creating COG masaic ...")

        # Create token
        r = requests.post(
            f"{titiler_endpoint}/tokens/create",
            json={"username": username, "scope": ["mosaic:read", "mosaic:create"]},
        ).json()
        token = r["token"]

        # Create mosaic
        requests.post(
            f"{titiler_endpoint}/mosaicjson/create",
            json={
                "username": username,
                "layername": layername,
                "files": links,
                # "overwrite": overwrite
            },
            params={
                "access_token": token,
            },
        ).json()

        r2 = requests.get(
            f"{titiler_endpoint}/mosaicjson/{username}.{layername}/tilejson.json",
        ).json()

        return r2["tiles"][0]

    except Exception as e:
        raise Exception(e)


def cog_mosaic_from_file(
    filepath,
    skip_rows=0,
    titiler_endpoint="https://titiler.xyz",
    username="anonymous",
    layername=None,
    overwrite=False,
    verbose=True,
    **kwargs,
):
    """Creates a COG mosaic from a csv/txt file stored locally for through HTTP URL.

    Args:
        filepath (str): Local path or HTTP URL to the csv/txt file containing COG URLs.
        skip_rows (int, optional): The number of rows to skip in the file. Defaults to 0.
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".
        username (str, optional): User name for the titiler endpoint. Defaults to "anonymous".
        layername ([type], optional): Layer name to use. Defaults to None.
        overwrite (bool, optional): Whether to overwrite the layer name if existing. Defaults to False.
        verbose (bool, optional): Whether to print out descriptive information. Defaults to True.

    Returns:
        str: The tile URL for the COG mosaic.
    """
    import urllib

    links = []
    if filepath.startswith("http"):
        data = urllib.request.urlopen(filepath)
        for line in data:
            links.append(line.decode("utf-8").strip())

    else:
        with open(filepath) as f:
            links = [line.strip() for line in f.readlines()]

    links = links[skip_rows:]
    # print(links)
    mosaic = cog_mosaic(
        links, titiler_endpoint, username, layername, overwrite, verbose, **kwargs
    )
    return mosaic


def cog_bounds(url, titiler_endpoint="https://titiler.xyz"):
    """Get the bounding box of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A list of values representing [left, bottom, right, top]
    """

    r = requests.get(f"{titiler_endpoint}/cog/bounds", params={"url": url}).json()

    if "bounds" in r.keys():
        bounds = r["bounds"]
    else:
        bounds = None
    return bounds


def cog_center(url, titiler_endpoint="https://titiler.xyz"):
    """Get the centroid of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        tuple: A tuple representing (longitude, latitude)
    """
    bounds = cog_bounds(url, titiler_endpoint)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lat, lon)
    return center


def cog_bands(url, titiler_endpoint="https://titiler.xyz"):
    """Get band names of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A list of band names
    """

    r = requests.get(
        f"{titiler_endpoint}/cog/info",
        params={
            "url": url,
        },
    ).json()

    bands = [b[0] for b in r["band_descriptions"]]
    return bands


def cog_stats(url, titiler_endpoint="https://titiler.xyz"):
    """Get band statistics of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A dictionary of band statistics.
    """

    r = requests.get(
        f"{titiler_endpoint}/cog/statistics",
        params={
            "url": url,
        },
    ).json()

    return r


def cog_info(url, titiler_endpoint="https://titiler.xyz", return_geojson=False):
    """Get band statistics of a Cloud Optimized GeoTIFF (COG).

    Args:
        url (str): HTTP URL to a COG, e.g., https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif
        titiler_endpoint (str, optional): Titiler endpoint. Defaults to "https://titiler.xyz".

    Returns:
        list: A dictionary of band info.
    """

    info = "info"
    if return_geojson:
        info = "info.geojson"

    r = requests.get(
        f"{titiler_endpoint}/cog/{info}",
        params={
            "url": url,
        },
    ).json()

    return r


def cog_pixel_value(
    lon,
    lat,
    url,
    bidx=None,
    titiler_endpoint="https://titiler.xyz",
    **kwargs,
):
    """Get pixel value from COG.

    Args:
        lon (float): Longitude of the pixel.
        lat (float): Latitude of the pixel.
        url (str): HTTP URL to a COG, e.g., 'https://opendata.digitalglobe.com/events/california-fire-2020/pre-event/2018-02-16/pine-gulch-fire20/1030010076004E00.tif'
        bidx (str, optional): Dataset band indexes (e.g bidx=1, bidx=1&bidx=2&bidx=3). Defaults to None.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A dictionary of band info.
    """

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    kwargs["url"] = url
    if bidx is not None:
        kwargs["bidx"] = bidx

    r = requests.get(f"{titiler_endpoint}/cog/point/{lon},{lat}", params=kwargs).json()
    bands = cog_bands(url, titiler_endpoint)
    # if isinstance(titiler_endpoint, str):
    #     r = requests.get(f"{titiler_endpoint}/cog/point/{lon},{lat}", params=kwargs).json()
    # else:
    #     r = requests.get(
    #         titiler_endpoint.url_for_stac_pixel_value(lon, lat), params=kwargs
    #     ).json()

    if "detail" in r:
        print(r["detail"])
        return None
    else:
        values = r["values"]
        result = dict(zip(bands, values))
        return result


def stac_tile(
    url=None,
    collection=None,
    items=None,
    assets=None,
    bands=None,
    titiler_endpoint=None,
    **kwargs,
):
    """Get a tile layer from a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        items (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        bands (list): A list of band names, e.g., ["SR_B7", "SR_B5", "SR_B4"]
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "https://planetarycomputer.microsoft.com/api/data/v1", "planetary-computer", "pc". Defaults to None.

    Returns:
        str: Returns the STAC Tile layer URL.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if items is not None:
        kwargs["items"] = items

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)

    if isinstance(titiler_endpoint, PlanetaryComputerEndpoint):
        if isinstance(bands, list):
            bands = ",".join(bands)
        if isinstance(assets, list):
            assets = ",".join(assets)
        if assets is None and (bands is not None):
            assets = bands
        else:
            kwargs["bidx"] = bands

        kwargs["assets"] = assets

        if ("expression" in kwargs) and ("rescale" not in kwargs):
            stats = stac_stats(
                collection=collection,
                items=items,
                expression=kwargs["expression"],
                titiler_endpoint=titiler_endpoint,
            )
            kwargs[
                "rescale"
            ] = f"{stats[0]['percentile_2']},{stats[0]['percentile_98']}"

        if ("asset_expression" in kwargs) and ("rescale" not in kwargs):
            stats = stac_stats(
                collection=collection,
                items=items,
                expression=kwargs["asset_expression"],
                titiler_endpoint=titiler_endpoint,
            )
            kwargs[
                "rescale"
            ] = f"{stats[0]['percentile_2']},{stats[0]['percentile_98']}"

        if (
            (assets is not None)
            and ("asset_expression" not in kwargs)
            and ("expression" not in kwargs)
            and ("rescale" not in kwargs)
        ):
            stats = stac_stats(
                collection=collection,
                items=items,
                assets=assets,
                titiler_endpoint=titiler_endpoint,
            )
            percentile_2 = min([s["percentile_2"] for s in stats])
            percentile_98 = max([s["percentile_98"] for s in stats])
            kwargs["rescale"] = f"{percentile_2},{percentile_98}"

    else:
        if isinstance(bands, str):
            bands = bands.split(",")
        if isinstance(assets, str):
            assets = assets.split(",")

        if assets is None and (bands is not None):
            assets = bands
        else:
            kwargs["asset_bidx"] = bands
        kwargs["assets"] = assets

    TileMatrixSetId = "WebMercatorQuad"
    if "TileMatrixSetId" in kwargs.keys():
        TileMatrixSetId = kwargs["TileMatrixSetId"]
        kwargs.pop("TileMatrixSetId")

    if isinstance(titiler_endpoint, str):
        r = requests.get(
            f"{titiler_endpoint}/stac/{TileMatrixSetId}/tilejson.json",
            params=kwargs,
        ).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_item(), params=kwargs).json()

    return r["tiles"][0]


def stac_bounds(url=None, collection=None, items=None, titiler_endpoint=None, **kwargs):
    """Get the bounding box of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        items (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A list of values representing [left, bottom, right, top]
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if items is not None:
        kwargs["items"] = items

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/bounds", params=kwargs).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_bounds(), params=kwargs).json()

    bounds = r["bounds"]
    return bounds


def stac_center(url=None, collection=None, items=None, titiler_endpoint=None, **kwargs):
    """Get the centroid of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        items (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        tuple: A tuple representing (longitude, latitude)
    """
    bounds = stac_bounds(url, collection, items, titiler_endpoint, **kwargs)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lon, lat)
    return center


def stac_bands(url=None, collection=None, items=None, titiler_endpoint=None, **kwargs):
    """Get band names of a single SpatialTemporal Asset Catalog (STAC) item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        items (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A list of band names
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if items is not None:
        kwargs["items"] = items

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/assets", params=kwargs).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_assets(), params=kwargs).json()

    return r


def stac_stats(
    url=None, collection=None, items=None, assets=None, titiler_endpoint=None, **kwargs
):
    """Get band statistics of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        items (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A dictionary of band statistics.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if items is not None:
        kwargs["items"] = items
    if assets is not None:
        kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/statistics", params=kwargs).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_statistics(), params=kwargs
        ).json()

    return r


def stac_info(
    url=None, collection=None, items=None, assets=None, titiler_endpoint=None, **kwargs
):
    """Get band info of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        items (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A dictionary of band info.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if items is not None:
        kwargs["items"] = items
    if assets is not None:
        kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/info", params=kwargs).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_info(), params=kwargs).json()

    return r


def stac_info_geojson(
    url=None, collection=None, items=None, assets=None, titiler_endpoint=None, **kwargs
):
    """Get band info of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        items (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A dictionary of band info.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if items is not None:
        kwargs["items"] = items
    if assets is not None:
        kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/info.geojson", params=kwargs).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_info_geojson(), params=kwargs
        ).json()

    return r


def stac_assets(url=None, collection=None, items=None, titiler_endpoint=None, **kwargs):
    """Get all assets of a STAC item.

    Args:
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        items (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A list of assets.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if items is not None:
        kwargs["items"] = items

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/assets", params=kwargs).json()
    else:
        r = requests.get(titiler_endpoint.url_for_stac_assets(), params=kwargs).json()

    return r


def stac_pixel_value(
    lon,
    lat,
    url=None,
    collection=None,
    items=None,
    assets=None,
    titiler_endpoint=None,
    **kwargs,
):
    """Get pixel value from STAC assets.

    Args:
        lon (float): Longitude of the pixel.
        lat (float): Latitude of the pixel.
        url (str): HTTP URL to a STAC item, e.g., https://canada-spot-ortho.s3.amazonaws.com/canada_spot_orthoimages/canada_spot5_orthoimages/S5_2007/S5_11055_6057_20070622/S5_11055_6057_20070622.json
        collection (str): The Microsoft Planetary Computer STAC collection ID, e.g., landsat-8-c2-l2.
        items (str): The Microsoft Planetary Computer STAC item ID, e.g., LC08_L2SP_047027_20201204_02_T1.
        assets (str | list): The Microsoft Planetary Computer STAC asset ID, e.g., ["SR_B7", "SR_B5", "SR_B4"].
        titiler_endpoint (str, optional): Titiler endpoint, e.g., "https://titiler.xyz", "planetary-computer", "pc". Defaults to None.

    Returns:
        list: A dictionary of pixel values for each asset.
    """

    if url is None and collection is None:
        raise ValueError("Either url or collection must be specified.")

    if collection is not None and titiler_endpoint is None:
        titiler_endpoint = "planetary-computer"

    if url is not None:
        kwargs["url"] = url
    if collection is not None:
        kwargs["collection"] = collection
    if items is not None:
        kwargs["items"] = items

    if assets is None:
        assets = stac_assets(
            url=url,
            collection=collection,
            items=items,
            titiler_endpoint=titiler_endpoint,
        )
        assets = ",".join(assets)
    kwargs["assets"] = assets

    titiler_endpoint = check_titiler_endpoint(titiler_endpoint)
    if isinstance(titiler_endpoint, str):
        r = requests.get(f"{titiler_endpoint}/stac/{lon},{lat}", params=kwargs).json()
    else:
        r = requests.get(
            titiler_endpoint.url_for_stac_pixel_value(lon, lat), params=kwargs
        ).json()

    if "detail" in r:
        print(r["detail"])
        return None
    else:
        values = [v[0] for v in r["values"]]
        result = dict(zip(assets.split(","), values))
        return result


def bbox_to_geojson(bounds):
    """Convert coordinates of a bounding box to a geojson.

    Args:
        bounds (list): A list of coordinates representing [left, bottom, right, top].

    Returns:
        dict: A geojson feature.
    """
    return {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [bounds[0], bounds[3]],
                    [bounds[0], bounds[1]],
                    [bounds[2], bounds[1]],
                    [bounds[2], bounds[3]],
                    [bounds[0], bounds[3]],
                ]
            ],
        },
        "type": "Feature",
    }


def coords_to_geojson(coords):
    """Convert a list of bbox coordinates representing [left, bottom, right, top] to geojson FeatureCollection.

    Args:
        coords (list): A list of bbox coordinates representing [left, bottom, right, top].

    Returns:
        dict: A geojson FeatureCollection.
    """

    features = []
    for bbox in coords:
        features.append(bbox_to_geojson(bbox))
    return {"type": "FeatureCollection", "features": features}


def explode(coords):
    """Explode a GeoJSON geometry's coordinates object and yield
    coordinate tuples. As long as the input is conforming, the type of
    the geometry doesn't matter.  From Fiona 1.4.8

    Args:
        coords (list): A list of coordinates.

    Yields:
        [type]: [description]
    """

    for e in coords:
        if isinstance(e, (float, int)):
            yield coords
            break
        else:
            for f in explode(e):
                yield f


def get_bounds(geometry, north_up=True, transform=None):
    """Bounding box of a GeoJSON geometry, GeometryCollection, or FeatureCollection.
    left, bottom, right, top
    *not* xmin, ymin, xmax, ymax
    If not north_up, y will be switched to guarantee the above.
    Source code adapted from https://github.com/mapbox/rasterio/blob/master/rasterio/features.py#L361

    Args:
        geometry (dict): A GeoJSON dict.
        north_up (bool, optional): . Defaults to True.
        transform ([type], optional): . Defaults to None.

    Returns:
        list: A list of coordinates representing [left, bottom, right, top]
    """

    if "bbox" in geometry:
        return tuple(geometry["bbox"])

    geometry = geometry.get("geometry") or geometry

    # geometry must be a geometry, GeometryCollection, or FeatureCollection
    if not (
        "coordinates" in geometry or "geometries" in geometry or "features" in geometry
    ):
        raise ValueError(
            "geometry must be a GeoJSON-like geometry, GeometryCollection, "
            "or FeatureCollection"
        )

    if "features" in geometry:
        # Input is a FeatureCollection
        xmins = []
        ymins = []
        xmaxs = []
        ymaxs = []
        for feature in geometry["features"]:
            xmin, ymin, xmax, ymax = get_bounds(feature["geometry"])
            xmins.append(xmin)
            ymins.append(ymin)
            xmaxs.append(xmax)
            ymaxs.append(ymax)
        if north_up:
            return min(xmins), min(ymins), max(xmaxs), max(ymaxs)
        else:
            return min(xmins), max(ymaxs), max(xmaxs), min(ymins)

    elif "geometries" in geometry:
        # Input is a geometry collection
        xmins = []
        ymins = []
        xmaxs = []
        ymaxs = []
        for geometry in geometry["geometries"]:
            xmin, ymin, xmax, ymax = get_bounds(geometry)
            xmins.append(xmin)
            ymins.append(ymin)
            xmaxs.append(xmax)
            ymaxs.append(ymax)
        if north_up:
            return min(xmins), min(ymins), max(xmaxs), max(ymaxs)
        else:
            return min(xmins), max(ymaxs), max(xmaxs), min(ymins)

    elif "coordinates" in geometry:
        # Input is a singular geometry object
        if transform is not None:
            xyz = list(explode(geometry["coordinates"]))
            xyz_px = [transform * point for point in xyz]
            xyz = tuple(zip(*xyz_px))
            return min(xyz[0]), max(xyz[1]), max(xyz[0]), min(xyz[1])
        else:
            xyz = tuple(zip(*list(explode(geometry["coordinates"]))))
            if north_up:
                return min(xyz[0]), min(xyz[1]), max(xyz[0]), max(xyz[1])
            else:
                return min(xyz[0]), max(xyz[1]), max(xyz[0]), min(xyz[1])

    # all valid inputs returned above, so whatever falls through is an error
    raise ValueError(
        "geometry must be a GeoJSON-like geometry, GeometryCollection, "
        "or FeatureCollection"
    )


def get_center(geometry, north_up=True, transform=None):
    """Get the centroid of a GeoJSON.

    Args:
        geometry (dict): A GeoJSON dict.
        north_up (bool, optional): . Defaults to True.
        transform ([type], optional): . Defaults to None.

    Returns:
        list: [lon, lat]
    """
    bounds = get_bounds(geometry, north_up, transform)
    center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)  # (lat, lon)
    return center


def image_props(img, date_format="YYYY-MM-dd"):
    """Gets image properties.

    Args:
        img (ee.Image): The input image.
        date_format (str, optional): The output date format. Defaults to 'YYYY-MM-dd HH:mm:ss'.

    Returns:
        dd.Dictionary: The dictionary containing image properties.
    """
    if not isinstance(img, ee.Image):
        print("The input object must be an ee.Image")
        return

    keys = img.propertyNames().remove("system:footprint").remove("system:bands")
    values = keys.map(lambda p: img.get(p))

    bands = img.bandNames()
    scales = bands.map(lambda b: img.select([b]).projection().nominalScale())
    scale = ee.Algorithms.If(
        scales.distinct().size().gt(1),
        ee.Dictionary.fromLists(bands.getInfo(), scales),
        scales.get(0),
    )
    image_date = ee.Date(img.get("system:time_start")).format(date_format)
    time_start = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd HH:mm:ss")
    # time_end = ee.Date(img.get('system:time_end')).format('YYYY-MM-dd HH:mm:ss')
    time_end = ee.Algorithms.If(
        ee.List(img.propertyNames()).contains("system:time_end"),
        ee.Date(img.get("system:time_end")).format("YYYY-MM-dd HH:mm:ss"),
        time_start,
    )
    asset_size = (
        ee.Number(img.get("system:asset_size"))
        .divide(1e6)
        .format()
        .cat(ee.String(" MB"))
    )

    props = ee.Dictionary.fromLists(keys, values)
    props = props.set("system:time_start", time_start)
    props = props.set("system:time_end", time_end)
    props = props.set("system:asset_size", asset_size)
    props = props.set("NOMINAL_SCALE", scale)
    props = props.set("IMAGE_DATE", image_date)

    return props


def image_stats(img, region=None, scale=None):
    """Gets image descriptive statistics.

    Args:
        img (ee.Image): The input image to calculate descriptive statistics.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        ee.Dictionary: A dictionary containing the description statistics of the input image.
    """

    if not isinstance(img, ee.Image):
        print("The input object must be an ee.Image")
        return

    stat_types = ["min", "max", "mean", "std", "sum"]

    image_min = image_min_value(img, region, scale)
    image_max = image_max_value(img, region, scale)
    image_mean = image_mean_value(img, region, scale)
    image_std = image_std_value(img, region, scale)
    image_sum = image_sum_value(img, region, scale)

    stat_results = ee.List([image_min, image_max, image_mean, image_std, image_sum])

    stats = ee.Dictionary.fromLists(stat_types, stat_results)

    return stats


def adjust_longitude(in_fc):
    """Adjusts longitude if it is less than -180 or greater than 180.

    Args:
        in_fc (dict): The input dictionary containing coordinates.

    Returns:
        dict: A dictionary containing the converted longitudes
    """
    try:

        keys = in_fc.keys()

        if "geometry" in keys:

            coordinates = in_fc["geometry"]["coordinates"]

            if in_fc["geometry"]["type"] == "Point":
                longitude = coordinates[0]
                if longitude < -180:
                    longitude = 360 + longitude
                elif longitude > 180:
                    longitude = longitude - 360
                in_fc["geometry"]["coordinates"][0] = longitude

            elif in_fc["geometry"]["type"] == "Polygon":
                for index1, item in enumerate(coordinates):
                    for index2, element in enumerate(item):
                        longitude = element[0]
                        if longitude < -180:
                            longitude = 360 + longitude
                        elif longitude > 180:
                            longitude = longitude - 360
                        in_fc["geometry"]["coordinates"][index1][index2][0] = longitude

            elif in_fc["geometry"]["type"] == "LineString":
                for index, element in enumerate(coordinates):
                    longitude = element[0]
                    if longitude < -180:
                        longitude = 360 + longitude
                    elif longitude > 180:
                        longitude = longitude - 360
                    in_fc["geometry"]["coordinates"][index][0] = longitude

        elif "type" in keys:

            coordinates = in_fc["coordinates"]

            if in_fc["type"] == "Point":
                longitude = coordinates[0]
                if longitude < -180:
                    longitude = 360 + longitude
                elif longitude > 180:
                    longitude = longitude - 360
                in_fc["coordinates"][0] = longitude

            elif in_fc["type"] == "Polygon":
                for index1, item in enumerate(coordinates):
                    for index2, element in enumerate(item):
                        longitude = element[0]
                        if longitude < -180:
                            longitude = 360 + longitude
                        elif longitude > 180:
                            longitude = longitude - 360
                        in_fc["coordinates"][index1][index2][0] = longitude

            elif in_fc["type"] == "LineString":
                for index, element in enumerate(coordinates):
                    longitude = element[0]
                    if longitude < -180:
                        longitude = 360 + longitude
                    elif longitude > 180:
                        longitude = longitude - 360
                    in_fc["coordinates"][index][0] = longitude

        return in_fc

    except Exception as e:
        print(e)
        return None


def zonal_statistics(
    in_value_raster,
    in_zone_vector,
    out_file_path,
    statistics_type="MEAN",
    scale=None,
    crs=None,
    tile_scale=1.0,
    return_fc=False,
    verbose=True,
    **kwargs,
):
    """Summarizes the values of a raster within the zones of another dataset and exports the results as a csv, shp, json, kml, or kmz.

    Args:
        in_value_raster (object): An ee.Image or ee.ImageCollection that contains the values on which to calculate a statistic.
        in_zone_vector (object): An ee.FeatureCollection that defines the zones.
        out_file_path (str): Output file path that will contain the summary of the values in each zone. The file type can be: csv, shp, json, kml, kmz
        statistics_type (str, optional): Statistic type to be calculated. Defaults to 'MEAN'. For 'HIST', you can provide three parameters: max_buckets, min_bucket_width, and max_raw. For 'FIXED_HIST', you must provide three parameters: hist_min, hist_max, and hist_steps.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        crs (str, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        tile_scale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.0.
        verbose (bool, optional): Whether to print descriptive text when the programming is running. Default to True.
        return_fc (bool, optional): Whether to return the results as an ee.FeatureCollection. Defaults to False.
    """

    if isinstance(in_value_raster, ee.ImageCollection):
        in_value_raster = in_value_raster.toBands()

    if not isinstance(in_value_raster, ee.Image):
        print("The input raster must be an ee.Image.")
        return

    if not isinstance(in_zone_vector, ee.FeatureCollection):
        print("The input zone data must be an ee.FeatureCollection.")
        return

    allowed_formats = ["csv", "geojson", "kml", "kmz", "shp"]
    filename = os.path.abspath(out_file_path)
    basename = os.path.basename(filename)
    # name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:].lower()

    if not (filetype in allowed_formats):
        print(
            "The file type must be one of the following: {}".format(
                ", ".join(allowed_formats)
            )
        )
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

    if "max_buckets" in kwargs.keys():
        max_buckets = kwargs["max_buckets"]
    if "min_bucket_width" in kwargs.keys():
        min_bucket_width = kwargs["min_bucket"]
    if "max_raw" in kwargs.keys():
        max_raw = kwargs["max_raw"]

    if (
        statistics_type.upper() == "FIXED_HIST"
        and ("hist_min" in kwargs.keys())
        and ("hist_max" in kwargs.keys())
        and ("hist_steps" in kwargs.keys())
    ):
        hist_min = kwargs["hist_min"]
        hist_max = kwargs["hist_max"]
        hist_steps = kwargs["hist_steps"]
    elif statistics_type.upper() == "FIXED_HIST":
        print(
            "To use fixedHistogram, please provide these three parameters: hist_min, hist_max, and hist_steps."
        )
        return

    allowed_statistics = {
        "MEAN": ee.Reducer.mean(),
        "MAXIMUM": ee.Reducer.max(),
        "MEDIAN": ee.Reducer.median(),
        "MINIMUM": ee.Reducer.min(),
        "STD": ee.Reducer.stdDev(),
        "MIN_MAX": ee.Reducer.minMax(),
        "SUM": ee.Reducer.sum(),
        "VARIANCE": ee.Reducer.variance(),
        "HIST": ee.Reducer.histogram(
            maxBuckets=max_buckets, minBucketWidth=min_bucket_width, maxRaw=max_raw
        ),
        "FIXED_HIST": ee.Reducer.fixedHistogram(hist_min, hist_max, hist_steps),
    }

    if not (statistics_type.upper() in allowed_statistics.keys()):
        print(
            "The statistics type must be one of the following: {}".format(
                ", ".join(list(allowed_statistics.keys()))
            )
        )
        return

    if scale is None:
        scale = in_value_raster.projection().nominalScale().multiply(10)

    try:
        if verbose:
            print("Computing statistics ...")
        result = in_value_raster.reduceRegions(
            collection=in_zone_vector,
            reducer=allowed_statistics[statistics_type],
            scale=scale,
            crs=crs,
            tileScale=tile_scale,
        )
        if return_fc:
            return result
        else:
            ee_export_vector(result, filename)
    except Exception as e:
        raise Exception(e)


def zonal_statistics_by_group(
    in_value_raster,
    in_zone_vector,
    out_file_path,
    statistics_type="SUM",
    decimal_places=0,
    denominator=1.0,
    scale=None,
    crs=None,
    tile_scale=1.0,
    return_fc=False,
    verbose=True,
    **kwargs,
):
    """Summarizes the area or percentage of a raster by group within the zones of another dataset and exports the results as a csv, shp, json, kml, or kmz.

    Args:
        in_value_raster (object): An integer Image that contains the values on which to calculate area/percentage.
        in_zone_vector (object): An ee.FeatureCollection that defines the zones.
        out_file_path (str): Output file path that will contain the summary of the values in each zone. The file type can be: csv, shp, json, kml, kmz
        statistics_type (str, optional): Can be either 'SUM' or 'PERCENTAGE' . Defaults to 'SUM'.
        decimal_places (int, optional): The number of decimal places to use. Defaults to 0.
        denominator (float, optional): To convert area units (e.g., from square meters to square kilometers). Defaults to 1.0.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        crs (str, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        tile_scale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.0.
        verbose (bool, optional): Whether to print descriptive text when the programming is running. Default to True.
        return_fc (bool, optional): Whether to return the results as an ee.FeatureCollection. Defaults to False.

    """

    if isinstance(in_value_raster, ee.ImageCollection):
        in_value_raster = in_value_raster.toBands()

    if not isinstance(in_value_raster, ee.Image):
        print("The input raster must be an ee.Image.")
        return

    band_count = in_value_raster.bandNames().size().getInfo()

    band_name = ""
    if band_count == 1:
        band_name = in_value_raster.bandNames().get(0)
    else:
        print("The input image can only have one band.")
        return

    band_types = in_value_raster.bandTypes().get(band_name).getInfo()
    band_type = band_types.get("precision")
    if band_type != "int":
        print("The input image band must be integer type.")
        return

    if not isinstance(in_zone_vector, ee.FeatureCollection):
        print("The input zone data must be an ee.FeatureCollection.")
        return

    allowed_formats = ["csv", "geojson", "kml", "kmz", "shp"]
    filename = os.path.abspath(out_file_path)
    basename = os.path.basename(filename)
    # name = os.path.splitext(basename)[0]
    filetype = os.path.splitext(basename)[1][1:]

    if not (filetype.lower() in allowed_formats):
        print(
            "The file type must be one of the following: {}".format(
                ", ".join(allowed_formats)
            )
        )
        return

    out_dir = os.path.dirname(filename)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    allowed_statistics = ["SUM", "PERCENTAGE"]
    if not (statistics_type.upper() in allowed_statistics):
        print(
            "The statistics type can only be one of {}".format(
                ", ".join(allowed_statistics)
            )
        )
        return

    if scale is None:
        scale = in_value_raster.projection().nominalScale().multiply(10)

    try:

        if verbose:
            print("Computing ... ")
        geometry = in_zone_vector.geometry()

        hist = in_value_raster.reduceRegion(
            ee.Reducer.frequencyHistogram(),
            geometry=geometry,
            bestEffort=True,
            scale=scale,
        )
        class_values = (
            ee.Dictionary(hist.get(band_name))
            .keys()
            .map(lambda v: ee.Number.parse(v))
            .sort()
        )

        class_names = class_values.map(
            lambda c: ee.String("Class_").cat(ee.Number(c).format())
        )

        # class_count = class_values.size().getInfo()
        dataset = ee.Image.pixelArea().divide(denominator).addBands(in_value_raster)

        init_result = dataset.reduceRegions(
            **{
                "collection": in_zone_vector,
                "reducer": ee.Reducer.sum().group(
                    **{
                        "groupField": 1,
                        "groupName": "group",
                    }
                ),
                "scale": scale,
            }
        )

        # def build_dict(input_list):

        #     decimal_format = '%.{}f'.format(decimal_places)
        #     in_dict = input_list.map(lambda x: ee.Dictionary().set(ee.String('Class_').cat(
        #         ee.Number(ee.Dictionary(x).get('group')).format()), ee.Number.parse(ee.Number(ee.Dictionary(x).get('sum')).format(decimal_format))))
        #     return in_dict

        def get_keys(input_list):
            return input_list.map(
                lambda x: ee.String("Class_").cat(
                    ee.Number(ee.Dictionary(x).get("group")).format()
                )
            )

        def get_values(input_list):
            decimal_format = "%.{}f".format(decimal_places)
            return input_list.map(
                lambda x: ee.Number.parse(
                    ee.Number(ee.Dictionary(x).get("sum")).format(decimal_format)
                )
            )

        def set_attribute(f):
            groups = ee.List(f.get("groups"))
            keys = get_keys(groups)
            values = get_values(groups)
            total_area = ee.List(values).reduce(ee.Reducer.sum())

            def get_class_values(x):
                cls_value = ee.Algorithms.If(
                    keys.contains(x), values.get(keys.indexOf(x)), 0
                )
                cls_value = ee.Algorithms.If(
                    ee.String(statistics_type).compareTo(ee.String("SUM")),
                    ee.Number(cls_value).divide(ee.Number(total_area)),
                    cls_value,
                )
                return cls_value

            full_values = class_names.map(lambda x: get_class_values(x))
            attr_dict = ee.Dictionary.fromLists(class_names, full_values)
            attr_dict = attr_dict.set("Class_sum", total_area)

            return f.set(attr_dict).set("groups", None)

        final_result = init_result.map(set_attribute)
        if return_fc:
            return final_result
        else:
            ee_export_vector(final_result, filename)

    except Exception as e:
        raise Exception(e)


def vec_area(fc):
    """Calculate the area (m2) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({"area_m2": f.area(1).round()}))


def vec_area_km2(fc):
    """Calculate the area (km2) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({"area_km2": f.area(1).divide(1e6).round()}))


def vec_area_mi2(fc):
    """Calculate the area (square mile) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({"area_mi2": f.area(1).divide(2.59e6).round()}))


def vec_area_ha(fc):
    """Calculate the area (hectare) of each each feature in a feature collection.

    Args:
        fc (object): The feature collection to compute the area.

    Returns:
        object: ee.FeatureCollection
    """
    return fc.map(lambda f: f.set({"area_ha": f.area(1).divide(1e4).round()}))


def remove_geometry(fc):
    """Remove .geo coordinate field from a FeatureCollection

    Args:
        fc (object): The input FeatureCollection.

    Returns:
        object: The output FeatureCollection without the geometry field.
    """
    return fc.select([".*"], None, False)


def image_cell_size(img):
    """Retrieves the image cell size (e.g., spatial resolution)

    Args:
        img (object): ee.Image

    Returns:
        float: The nominal scale in meters.
    """
    bands = img.bandNames()
    scales = bands.map(lambda b: img.select([b]).projection().nominalScale())
    scale = ee.Algorithms.If(
        scales.distinct().size().gt(1),
        ee.Dictionary.fromLists(bands.getInfo(), scales),
        scales.get(0),
    )
    return scale


def image_scale(img):
    """Retrieves the image cell size (e.g., spatial resolution)

    Args:
        img (object): ee.Image

    Returns:
        float: The nominal scale in meters.
    """
    # bands = img.bandNames()
    # scales = bands.map(lambda b: img.select([b]).projection().nominalScale())
    # scale = ee.Algorithms.If(scales.distinct().size().gt(1), ee.Dictionary.fromLists(bands.getInfo(), scales), scales.get(0))
    return img.select(0).projection().nominalScale()


def image_band_names(img):
    """Gets image band names.

    Args:
        img (ee.Image): The input image.

    Returns:
        ee.List: The returned list of image band names.
    """
    return img.bandNames()


def image_date(img, date_format="YYYY-MM-dd"):
    """Retrieves the image acquisition date.

    Args:
        img (object): ee.Image
        date_format (str, optional): The date format to use. Defaults to 'YYYY-MM-dd'.

    Returns:
        str: A string representing the acquisition of the image.
    """
    return ee.Date(img.get("system:time_start")).format(date_format)


def image_dates(img_col, date_format="YYYY-MM-dd"):
    """Get image dates of all images in an ImageCollection.

    Args:
        img_col (object): ee.ImageCollection
        date_format (str, optional): A pattern, as described at http://joda-time.sourceforge.net/apidocs/org/joda/time/format/DateTimeFormat.html; if omitted will use ISO standard date formatting. Defaults to 'YYYY-MM-dd'.

    Returns:
        object: ee.List
    """
    dates = img_col.aggregate_array("system:time_start")
    new_dates = dates.map(lambda d: ee.Date(d).format(date_format))
    return new_dates


def image_area(img, region=None, scale=None, denominator=1.0):
    """Calculates the the area of an image.

    Args:
        img (object): ee.Image
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        denominator (float, optional): The denominator to use for converting size from square meters to other units. Defaults to 1.0.

    Returns:
        object: ee.Dictionary
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    pixel_area = (
        img.unmask().neq(ee.Image(0)).multiply(ee.Image.pixelArea()).divide(denominator)
    )
    img_area = pixel_area.reduceRegion(
        **{
            "geometry": region,
            "reducer": ee.Reducer.sum(),
            "scale": scale,
            "maxPixels": 1e12,
        }
    )
    return img_area


def image_max_value(img, region=None, scale=None):
    """Retrieves the maximum value of an image.

    Args:
        img (object): The image to calculate the maximum value.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    max_value = img.reduceRegion(
        **{
            "reducer": ee.Reducer.max(),
            "geometry": region,
            "scale": scale,
            "maxPixels": 1e12,
            "bestEffort": True,
        }
    )
    return max_value


def image_min_value(img, region=None, scale=None):
    """Retrieves the minimum value of an image.

    Args:
        img (object): The image to calculate the minimum value.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    min_value = img.reduceRegion(
        **{
            "reducer": ee.Reducer.min(),
            "geometry": region,
            "scale": scale,
            "maxPixels": 1e12,
            "bestEffort": True,
        }
    )
    return min_value


def image_mean_value(img, region=None, scale=None):
    """Retrieves the mean value of an image.

    Args:
        img (object): The image to calculate the mean value.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    mean_value = img.reduceRegion(
        **{
            "reducer": ee.Reducer.mean(),
            "geometry": region,
            "scale": scale,
            "maxPixels": 1e12,
            "bestEffort": True,
        }
    )
    return mean_value


def image_std_value(img, region=None, scale=None):
    """Retrieves the standard deviation of an image.

    Args:
        img (object): The image to calculate the standard deviation.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    std_value = img.reduceRegion(
        **{
            "reducer": ee.Reducer.stdDev(),
            "geometry": region,
            "scale": scale,
            "maxPixels": 1e12,
            "bestEffort": True,
        }
    )
    return std_value


def image_sum_value(img, region=None, scale=None):
    """Retrieves the sum of an image.

    Args:
        img (object): The image to calculate the standard deviation.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.

    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    sum_value = img.reduceRegion(
        **{
            "reducer": ee.Reducer.sum(),
            "geometry": region,
            "scale": scale,
            "maxPixels": 1e12,
            "bestEffort": True,
        }
    )
    return sum_value


def extract_values_to_points(
    in_fc,
    image,
    out_fc=None,
    scale=None,
    crs=None,
    crsTransform=None,
    tileScale=1,
    stats_type="FIRST",
    **kwargs,
):
    """Extracts image values to points.

    Args:
        in_fc (object): ee.FeatureCollection.
        image (object): The ee.Image to extract pixel values.
        out_fc (object, optional): The output feature collection. Defaults to None.
        scale (ee.Projectoin, optional): A nominal scale in meters of the projection to sample in. If unspecified,the scale of the image's first band is used.
        crs (str, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        crsTransform (list, optional): The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and will replace any transform already set on the projection.
        tile_scale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default.
        stats_type (str, optional): Statistic type to be calculated. Defaults to 'FIRST'.

    Returns:
        object: ee.FeatureCollection
    """

    if "tile_scale" in kwargs:
        tileScale = kwargs["tile_scale"]
    if "crs_transform" in kwargs:
        crsTransform = kwargs["crs_transform"]

    allowed_stats = {
        "FIRST": ee.Reducer.first(),
        "MEAN": ee.Reducer.mean(),
        "MAXIMUM": ee.Reducer.max(),
        "MEDIAN": ee.Reducer.median(),
        "MINIMUM": ee.Reducer.min(),
        "STD": ee.Reducer.stdDev(),
        "MIN_MAX": ee.Reducer.minMax(),
        "SUM": ee.Reducer.sum(),
        "VARIANCE": ee.Reducer.variance(),
    }

    if stats_type.upper() not in allowed_stats:
        raise ValueError(
            f"The statistics_type must be one of the following {', '.join(allowed_stats.keys())}"
        )

    if not isinstance(in_fc, ee.FeatureCollection):
        try:
            in_fc = shp_to_ee(in_fc)
        except Exception as e:
            print(e)
            return

    if not isinstance(image, ee.Image):
        print("The image must be an instance of ee.Image.")
        return

    result = image.reduceRegions(
        collection=in_fc,
        reducer=allowed_stats[stats_type.upper()],
        scale=scale,
        crs=crs,
        crsTransform=crsTransform,
        tileScale=tileScale,
    )

    if out_fc is not None:
        ee_export_vector(result, out_fc)
    else:
        return result


def image_reclassify(img, in_list, out_list):
    """Reclassify an image.

    Args:
        img (object): The image to which the remapping is applied.
        in_list (list): The source values (numbers or EEArrays). All values in this list will be mapped to the corresponding value in 'out_list'.
        out_list (list): The destination values (numbers or EEArrays). These are used to replace the corresponding values in 'from'. Must have the same number of values as 'in_list'.

    Returns:
        object: ee.Image
    """
    image = img.remap(in_list, out_list)
    return image


def image_smoothing(img, reducer, kernel):
    """Smooths an image.

    Args:
        img (object): The image to be smoothed.
        reducer (object): ee.Reducer
        kernel (object): ee.Kernel

    Returns:
        object: ee.Image
    """
    image = img.reduceNeighborhood(
        **{
            "reducer": reducer,
            "kernel": kernel,
        }
    )
    return image


def rename_bands(img, in_band_names, out_band_names):
    """Renames image bands.

    Args:
        img (object): The image to be renamed.
        in_band_names (list): The list of of input band names.
        out_band_names (list): The list of output band names.

    Returns:
        object: The output image with the renamed bands.
    """
    return img.select(in_band_names, out_band_names)


def bands_to_image_collection(img):
    """Converts all bands in an image to an image collection.

    Args:
        img (object): The image to convert.

    Returns:
        object: ee.ImageCollection
    """
    collection = ee.ImageCollection(img.bandNames().map(lambda b: img.select([b])))
    return collection


def find_landsat_by_path_row(landsat_col, path_num, row_num):
    """Finds Landsat images by WRS path number and row number.

    Args:
        landsat_col (str): The image collection id of Landsat.
        path_num (int): The WRS path number.
        row_num (int): the WRS row number.

    Returns:
        object: ee.ImageCollection
    """
    try:
        if isinstance(landsat_col, str):
            landsat_col = ee.ImageCollection(landsat_col)
            collection = landsat_col.filter(ee.Filter.eq("WRS_PATH", path_num)).filter(
                ee.Filter.eq("WRS_ROW", row_num)
            )
            return collection
    except Exception as e:
        print(e)


def str_to_num(in_str):
    """Converts a string to an ee.Number.

    Args:
        in_str (str): The string to convert to a number.

    Returns:
        object: ee.Number
    """
    return ee.Number.parse(str)


def array_sum(arr):
    """Accumulates elements of an array along the given axis.

    Args:
        arr (object): Array to accumulate.

    Returns:
        object: ee.Number
    """
    return ee.Array(arr).accum(0).get([-1])


def array_mean(arr):
    """Calculates the mean of an array along the given axis.

    Args:
        arr (object): Array to calculate mean.

    Returns:
        object: ee.Number
    """
    total = ee.Array(arr).accum(0).get([-1])
    size = arr.length()
    return ee.Number(total.divide(size))


def get_annual_NAIP(year, RGBN=True):
    """Filters NAIP ImageCollection by year.

    Args:
        year (int): The year to filter the NAIP ImageCollection.
        RGBN (bool, optional): Whether to retrieve 4-band NAIP imagery only. Defaults to True.

    Returns:
        object: ee.ImageCollection
    """
    try:
        collection = ee.ImageCollection("USDA/NAIP/DOQQ")
        start_date = str(year) + "-01-01"
        end_date = str(year) + "-12-31"
        naip = collection.filterDate(start_date, end_date)
        if RGBN:
            naip = naip.filter(ee.Filter.listContains("system:band_names", "N"))
        return naip
    except Exception as e:
        print(e)


def get_all_NAIP(start_year=2009, end_year=2019):
    """Creates annual NAIP imagery mosaic.

    Args:
        start_year (int, optional): The starting year. Defaults to 2009.
        end_year (int, optional): The ending year. Defaults to 2019.

    Returns:
        object: ee.ImageCollection
    """
    try:

        def get_annual_NAIP(year):
            try:
                collection = ee.ImageCollection("USDA/NAIP/DOQQ")
                start_date = ee.Date.fromYMD(year, 1, 1)
                end_date = ee.Date.fromYMD(year, 12, 31)
                naip = collection.filterDate(start_date, end_date).filter(
                    ee.Filter.listContains("system:band_names", "N")
                )
                return ee.ImageCollection(naip)
            except Exception as e:
                print(e)

        years = ee.List.sequence(start_year, end_year)
        collection = years.map(get_annual_NAIP)
        return collection

    except Exception as e:
        print(e)


def annual_NAIP(year, region):
    """Create an NAIP mosaic of a specified year for a specified region.

    Args:
        year (int): The specified year to create the mosaic for.
        region (object): ee.Geometry

    Returns:
        object: ee.Image
    """

    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = ee.Date.fromYMD(year, 12, 31)
    collection = (
        ee.ImageCollection("USDA/NAIP/DOQQ")
        .filterDate(start_date, end_date)
        .filterBounds(region)
    )

    time_start = ee.Date(
        ee.List(collection.aggregate_array("system:time_start")).sort().get(0)
    )
    time_end = ee.Date(
        ee.List(collection.aggregate_array("system:time_end")).sort().get(-1)
    )
    image = ee.Image(collection.mosaic().clip(region))
    NDWI = ee.Image(image).normalizedDifference(["G", "N"]).select(["nd"], ["ndwi"])
    NDVI = ee.Image(image).normalizedDifference(["N", "R"]).select(["nd"], ["ndvi"])
    image = image.addBands(NDWI)
    image = image.addBands(NDVI)
    return image.set({"system:time_start": time_start, "system:time_end": time_end})


def find_NAIP(region, add_NDVI=True, add_NDWI=True):
    """Create annual NAIP mosaic for a given region.

    Args:
        region (object): ee.Geometry
        add_NDVI (bool, optional): Whether to add the NDVI band. Defaults to True.
        add_NDWI (bool, optional): Whether to add the NDWI band. Defaults to True.

    Returns:
        object: ee.ImageCollection
    """

    init_collection = (
        ee.ImageCollection("USDA/NAIP/DOQQ")
        .filterBounds(region)
        .filterDate("2009-01-01", "2019-12-31")
        .filter(ee.Filter.listContains("system:band_names", "N"))
    )

    yearList = ee.List(
        init_collection.distinct(["system:time_start"]).aggregate_array(
            "system:time_start"
        )
    )
    init_years = yearList.map(lambda y: ee.Date(y).get("year"))

    # remove duplicates
    init_years = ee.Dictionary(
        init_years.reduce(ee.Reducer.frequencyHistogram())
    ).keys()
    years = init_years.map(lambda x: ee.Number.parse(x))
    # years = init_years.map(lambda x: x)

    # Available NAIP years with NIR band
    def NAIPAnnual(year):
        start_date = ee.Date.fromYMD(year, 1, 1)
        end_date = ee.Date.fromYMD(year, 12, 31)
        collection = init_collection.filterDate(start_date, end_date)
        # .filterBounds(geometry)
        # .filter(ee.Filter.listContains("system:band_names", "N"))
        time_start = ee.Date(
            ee.List(collection.aggregate_array("system:time_start")).sort().get(0)
        ).format("YYYY-MM-dd")
        time_end = ee.Date(
            ee.List(collection.aggregate_array("system:time_end")).sort().get(-1)
        ).format("YYYY-MM-dd")
        col_size = collection.size()
        image = ee.Image(collection.mosaic().clip(region))

        if add_NDVI:
            NDVI = (
                ee.Image(image)
                .normalizedDifference(["N", "R"])
                .select(["nd"], ["ndvi"])
            )
            image = image.addBands(NDVI)

        if add_NDWI:
            NDWI = (
                ee.Image(image)
                .normalizedDifference(["G", "N"])
                .select(["nd"], ["ndwi"])
            )
            image = image.addBands(NDWI)

        return image.set(
            {
                "system:time_start": time_start,
                "system:time_end": time_end,
                "tiles": col_size,
            }
        )

    # remove years with incomplete coverage
    naip = ee.ImageCollection(years.map(NAIPAnnual))
    mean_size = ee.Number(naip.aggregate_mean("tiles"))
    total_sd = ee.Number(naip.aggregate_total_sd("tiles"))
    threshold = mean_size.subtract(total_sd.multiply(1))
    naip = naip.filter(
        ee.Filter.Or(ee.Filter.gte("tiles", threshold), ee.Filter.gte("tiles", 15))
    )
    naip = naip.filter(ee.Filter.gte("tiles", 7))

    naip_count = naip.size()
    naip_seq = ee.List.sequence(0, naip_count.subtract(1))

    def set_index(index):
        img = ee.Image(naip.toList(naip_count).get(index))
        return img.set({"system:uid": ee.Number(index).toUint8()})

    naip = naip_seq.map(set_index)

    return ee.ImageCollection(naip)


def filter_NWI(HUC08_Id, region, exclude_riverine=True):
    """Retrieves NWI dataset for a given HUC8 watershed.

    Args:
        HUC08_Id (str): The HUC8 watershed id.
        region (object): ee.Geometry
        exclude_riverine (bool, optional): Whether to exclude riverine wetlands. Defaults to True.

    Returns:
        object: ee.FeatureCollection
    """
    nwi_asset_prefix = "users/wqs/NWI-HU8/HU8_"
    nwi_asset_suffix = "_Wetlands"
    nwi_asset_path = nwi_asset_prefix + HUC08_Id + nwi_asset_suffix
    nwi_huc = ee.FeatureCollection(nwi_asset_path).filterBounds(region)

    if exclude_riverine:
        nwi_huc = nwi_huc.filter(
            ee.Filter.notEquals(**{"leftField": "WETLAND_TY", "rightValue": "Riverine"})
        )
    return nwi_huc


def filter_HUC08(region):
    """Filters HUC08 watersheds intersecting a given region.

    Args:
        region (object): ee.Geometry

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC08 = ee.FeatureCollection("USGS/WBD/2017/HUC08")  # Subbasins
    HUC08 = USGS_HUC08.filterBounds(region)
    return HUC08


# Find HUC10 intersecting a geometry
def filter_HUC10(region):
    """Filters HUC10 watersheds intersecting a given region.

    Args:
        region (object): ee.Geometry

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC10 = ee.FeatureCollection("USGS/WBD/2017/HUC10")  # Watersheds
    HUC10 = USGS_HUC10.filterBounds(region)
    return HUC10


def find_HUC08(HUC08_Id):
    """Finds a HUC08 watershed based on a given HUC08 ID

    Args:
        HUC08_Id (str): The HUC08 ID.

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC08 = ee.FeatureCollection("USGS/WBD/2017/HUC08")  # Subbasins
    HUC08 = USGS_HUC08.filter(ee.Filter.eq("huc8", HUC08_Id))
    return HUC08


def find_HUC10(HUC10_Id):
    """Finds a HUC10 watershed based on a given HUC08 ID

    Args:
        HUC10_Id (str): The HUC10 ID.

    Returns:
        object: ee.FeatureCollection
    """

    USGS_HUC10 = ee.FeatureCollection("USGS/WBD/2017/HUC10")  # Watersheds
    HUC10 = USGS_HUC10.filter(ee.Filter.eq("huc10", HUC10_Id))
    return HUC10


# find NWI by HUC08
def find_NWI(HUC08_Id, exclude_riverine=True):
    """Finds NWI dataset for a given HUC08 watershed.

    Args:
        HUC08_Id (str): The HUC08 watershed ID.
        exclude_riverine (bool, optional): Whether to exclude riverine wetlands. Defaults to True.

    Returns:
        object: ee.FeatureCollection
    """

    nwi_asset_prefix = "users/wqs/NWI-HU8/HU8_"
    nwi_asset_suffix = "_Wetlands"
    nwi_asset_path = nwi_asset_prefix + HUC08_Id + nwi_asset_suffix
    nwi_huc = ee.FeatureCollection(nwi_asset_path)
    if exclude_riverine:
        nwi_huc = nwi_huc.filter(
            ee.Filter.notEquals(**{"leftField": "WETLAND_TY", "rightValue": "Riverine"})
        )
    return nwi_huc


def nwi_add_color(fc):
    """Converts NWI vector dataset to image and add color to it.

    Args:
        fc (object): ee.FeatureCollection

    Returns:
        object: ee.Image
    """
    emergent = ee.FeatureCollection(
        fc.filter(ee.Filter.eq("WETLAND_TY", "Freshwater Emergent Wetland"))
    )
    emergent = emergent.map(lambda f: f.set("R", 127).set("G", 195).set("B", 28))
    # print(emergent.first())

    forested = fc.filter(
        ee.Filter.eq("WETLAND_TY", "Freshwater Forested/Shrub Wetland")
    )
    forested = forested.map(lambda f: f.set("R", 0).set("G", 136).set("B", 55))

    pond = fc.filter(ee.Filter.eq("WETLAND_TY", "Freshwater Pond"))
    pond = pond.map(lambda f: f.set("R", 104).set("G", 140).set("B", 192))

    lake = fc.filter(ee.Filter.eq("WETLAND_TY", "Lake"))
    lake = lake.map(lambda f: f.set("R", 19).set("G", 0).set("B", 124))

    riverine = fc.filter(ee.Filter.eq("WETLAND_TY", "Riverine"))
    riverine = riverine.map(lambda f: f.set("R", 1).set("G", 144).set("B", 191))

    fc = ee.FeatureCollection(
        emergent.merge(forested).merge(pond).merge(lake).merge(riverine)
    )

    #   base = ee.Image(0).mask(0).toInt8()
    base = ee.Image().byte()
    img = base.paint(fc, "R").addBands(
        base.paint(fc, "G").addBands(base.paint(fc, "B"))
    )

    return img


def nwi_rename(names):

    name_dict = ee.Dictionary(
        {
            "Freshwater Emergent Wetland": "Emergent",
            "Freshwater Forested/Shrub Wetland": "Forested",
            "Estuarine and Marine Wetland": "Estuarine",
            "Freshwater Pond": "Pond",
            "Lake": "Lake",
            "Riverine": "Riverine",
            "Estuarine and Marine Deepwater": "Deepwater",
            "Other": "Other",
        }
    )

    new_names = ee.List(names).map(lambda name: name_dict.get(name))
    return new_names


def summarize_by_group(
    collection, column, group, group_name, stats_type, return_dict=True
):
    """Calculates summary statistics by group.

    Args:
        collection (object): The input feature collection
        column (str): The value column to calculate summary statistics.
        group (str): The name of the group column.
        group_name (str): The new group name to use.
        stats_type (str): The type of summary statistics.
        return_dict (bool): Whether to return the result as a dictionary.

    Returns:
        object: ee.Dictionary or ee.List
    """
    stats_type = stats_type.lower()
    allowed_stats = ["min", "max", "mean", "median", "sum", "stdDev", "variance"]
    if stats_type not in allowed_stats:
        print(
            "The stats type must be one of the following: {}".format(
                ",".join(allowed_stats)
            )
        )
        return

    stats_dict = {
        "min": ee.Reducer.min(),
        "max": ee.Reducer.max(),
        "mean": ee.Reducer.mean(),
        "median": ee.Reducer.median(),
        "sum": ee.Reducer.sum(),
        "stdDev": ee.Reducer.stdDev(),
        "variance": ee.Reducer.variance(),
    }

    selectors = [column, group]
    stats = collection.reduceColumns(
        **{
            "selectors": selectors,
            "reducer": stats_dict[stats_type].group(
                **{"groupField": 1, "groupName": group_name}
            ),
        }
    )
    results = ee.List(ee.Dictionary(stats).get("groups"))
    if return_dict:
        keys = results.map(lambda k: ee.Dictionary(k).get(group_name))
        values = results.map(lambda v: ee.Dictionary(v).get(stats_type))
        results = ee.Dictionary.fromLists(keys, values)

    return results


def summary_stats(collection, column):
    """Aggregates over a given property of the objects in a collection, calculating the sum, min, max, mean,
    sample standard deviation, sample variance, total standard deviation and total variance of the selected property.

    Args:
        collection (FeatureCollection): The input feature collection to calculate summary statistics.
        column (str): The name of the column to calculate summary statistics.

    Returns:
        dict: The dictionary containing information about the summary statistics.
    """
    stats = collection.aggregate_stats(column).getInfo()
    return eval(str(stats))


def column_stats(collection, column, stats_type):
    """Aggregates over a given property of the objects in a collection, calculating the sum, min, max, mean,
    sample standard deviation, sample variance, total standard deviation and total variance of the selected property.

    Args:
        collection (FeatureCollection): The input feature collection to calculate statistics.
        column (str): The name of the column to calculate statistics.
        stats_type (str): The type of statistics to calculate.

    Returns:
        dict: The dictionary containing information about the requested statistics.
    """
    stats_type = stats_type.lower()
    allowed_stats = ["min", "max", "mean", "median", "sum", "stdDev", "variance"]
    if stats_type not in allowed_stats:
        print(
            "The stats type must be one of the following: {}".format(
                ",".join(allowed_stats)
            )
        )
        return

    stats_dict = {
        "min": ee.Reducer.min(),
        "max": ee.Reducer.max(),
        "mean": ee.Reducer.mean(),
        "median": ee.Reducer.median(),
        "sum": ee.Reducer.sum(),
        "stdDev": ee.Reducer.stdDev(),
        "variance": ee.Reducer.variance(),
    }

    selectors = [column]
    stats = collection.reduceColumns(
        **{"selectors": selectors, "reducer": stats_dict[stats_type]}
    )

    return stats


def ee_num_round(num, decimal=2):
    """Rounds a number to a specified number of decimal places.

    Args:
        num (ee.Number): The number to round.
        decimal (int, optional): The number of decimal places to round. Defaults to 2.

    Returns:
        ee.Number: The number with the specified decimal places rounded.
    """
    format_str = "%.{}f".format(decimal)
    return ee.Number.parse(ee.Number(num).format(format_str))


def num_round(num, decimal=2):
    """Rounds a number to a specified number of decimal places.

    Args:
        num (float): The number to round.
        decimal (int, optional): The number of decimal places to round. Defaults to 2.

    Returns:
        float: The number with the specified decimal places rounded.
    """
    return round(num, decimal)


def png_to_gif(in_dir, out_gif, fps=10, loop=0):
    """Convert a list of png images to gif.

    Args:
        in_dir (str): The input directory containing png images.
        out_gif (str): The output file path to the gif.
        fps (int, optional): Frames per second. Defaults to 10.
        loop (bool, optional): controls how many times the animation repeats. 1 means that the animation will play once and then stop (displaying the last frame). A value of 0 means that the animation will repeat forever. Defaults to 0.

    Raises:
        FileNotFoundError: No png images could be found.
    """
    import glob

    from PIL import Image

    if not out_gif.endswith(".gif"):
        raise ValueError("The out_gif must be a gif file.")

    out_gif = os.path.abspath(out_gif)

    out_dir = os.path.dirname(out_gif)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Create the frames
    frames = []
    imgs = list(glob.glob(os.path.join(in_dir, "*.png")))
    imgs.sort()

    if len(imgs) == 0:
        raise FileNotFoundError(f"No png could be found in {in_dir}.")

    for i in imgs:
        new_frame = Image.open(i)
        frames.append(new_frame)

    # Save into a GIF file that loops forever
    frames[0].save(
        out_gif,
        format="GIF",
        append_images=frames[1:],
        save_all=True,
        duration=1000 / fps,
        loop=loop,
    )


def geometry_type(ee_object):
    """Get geometry type of an Earth Engine object.

    Args:
        ee_object (object): An Earth Engine object.

    Returns:
        str: Returns geometry type. One of Point, MultiPoint, LineString, LinearRing, MultiLineString, BBox, Rectangle, Polygon, MultiPolygon.
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


def vector_styling(ee_object, column, palette, **kwargs):
    """Add a new property to each feature containing a stylying dictionary.

    Args:
        ee_object (object): An ee.FeatureCollection.
        column (str): The column name to use for styling.
        palette (list | dict): The palette (e.g., list of colors or a dict containing label and color pairs) to use for styling.

    Raises:
        ValueError: The provided column name is invalid.
        TypeError: The provided palette is invalid.
        TypeError: The provided ee_object is not an ee.FeatureCollection.

    Returns:
        object: An ee.FeatureCollection containing the styling attribute.
    """
    from box import Box

    if isinstance(ee_object, ee.FeatureCollection):

        prop_names = ee.Feature(ee_object.first()).propertyNames().getInfo()
        arr = ee_object.aggregate_array(column).distinct().sort()

        if column not in prop_names:
            raise ValueError(f"The column name must of one of {', '.join(prop_names)}")

        if isinstance(palette, Box):
            try:
                palette = list(palette["default"])
            except Exception as e:
                print("The provided palette is invalid.")
                raise Exception(e)
        elif isinstance(palette, tuple):
            palette = list(palette)
        elif isinstance(palette, dict):
            values = list(arr.getInfo())
            labels = list(palette.keys())
            if not all(elem in values for elem in labels):
                raise ValueError(
                    f"The keys of the palette must contain the following elements: {', '.join(values)}"
                )
            else:
                colors = [palette[value] for value in values]
                palette = colors

        if not isinstance(palette, list):
            raise TypeError("The palette must be a list.")

        color = "000000"
        color_opacity = 1
        point_size = 3
        point_shape = "circle"
        line_width = 1
        line_type = "solid"
        fill_color_opacity = 0.66

        if "color" in kwargs.keys():
            color = kwargs["color"]
        if "colorOpacity" in kwargs.keys():
            color_opacity = kwargs["colorOpacity"]
        if "pointSize" in kwargs.keys():
            point_size = kwargs["pointSize"]
        if "pointShape" in kwargs.keys():
            point_shape = kwargs["pointShape"]
        if "width" in kwargs.keys():
            line_width = kwargs["width"]
        if "lineType" in kwargs.keys():
            line_type = kwargs["lineType"]
        if "fillColorOpacity" in kwargs.keys():
            fill_color_opacity = kwargs["fillColorOpacity"]

        colors = ee.List(
            [
                color.strip() + str(hex(int(fill_color_opacity * 255)))[2:].zfill(2)
                for color in palette
            ]
        )
        fc = ee_object.map(lambda f: f.set({"styleIndex": arr.indexOf(f.get(column))}))
        step = arr.size().divide(colors.size()).ceil()
        fc = fc.map(
            lambda f: f.set(
                {
                    "style": {
                        "color": color
                        + str(hex(int(color_opacity * 255)))[2:].zfill(2),
                        "pointSize": point_size,
                        "pointShape": point_shape,
                        "width": line_width,
                        "lineType": line_type,
                        "fillColor": colors.get(
                            ee.Number(
                                ee.Number(f.get("styleIndex")).divide(step)
                            ).floor()
                        ),
                    }
                }
            )
        )

        return fc

    else:
        raise TypeError("The ee_object must be an ee.FeatureCollection.")


def is_GCS(in_shp):

    import warnings

    import pycrs

    if not os.path.exists(in_shp):
        raise FileNotFoundError("The input shapefile could not be found.")

    if not in_shp.endswith(".shp"):
        raise TypeError("The input shapefile is invalid.")

    in_prj = in_shp.replace(".shp", ".prj")

    if not os.path.exists(in_prj):
        warnings.warn(
            f"The projection file {in_prj} could not be found. Assuming the dataset is in a geographic coordinate system (GCS)."
        )
        return True
    else:

        with open(in_prj) as f:
            esri_wkt = f.read()
        epsg4326 = pycrs.parse.from_epsg_code(4326).to_proj4()
        try:
            crs = pycrs.parse.from_esri_wkt(esri_wkt).to_proj4()
            return crs == epsg4326
            # if crs == epsg4326:
            #     return True
            # else:
            #     return False
        except Exception:
            return False


def kml_to_shp(in_kml, out_shp, **kwargs):
    """Converts a KML to shapefile.

    Args:
        in_kml (str): The file path to the input KML.
        out_shp (str): The file path to the output shapefile.

    Raises:
        FileNotFoundError: The input KML could not be found.
        TypeError: The output must be a shapefile.
    """
    import warnings

    warnings.filterwarnings("ignore")

    in_kml = os.path.abspath(in_kml)
    if not os.path.exists(in_kml):
        raise FileNotFoundError("The input KML could not be found.")

    out_shp = os.path.abspath(out_shp)
    if not out_shp.endswith(".shp"):
        raise TypeError("The output must be a shapefile.")

    out_dir = os.path.dirname(out_shp)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    # import fiona
    # print(fiona.supported_drivers)
    gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
    df = gpd.read_file(in_kml, driver="KML", **kwargs)
    df.to_file(out_shp, **kwargs)


def kml_to_geojson(in_kml, out_geojson=None, **kwargs):
    """Converts a KML to GeoJSON.

    Args:
        in_kml (str): The file path to the input KML.
        out_geojson (str): The file path to the output GeoJSON. Defaults to None.

    Raises:
        FileNotFoundError: The input KML could not be found.
        TypeError: The output must be a GeoJSON.
    """
    import warnings

    warnings.filterwarnings("ignore")

    in_kml = os.path.abspath(in_kml)
    if not os.path.exists(in_kml):
        raise FileNotFoundError("The input KML could not be found.")

    if out_geojson is not None:
        out_geojson = os.path.abspath(out_geojson)
        ext = os.path.splitext(out_geojson)[1].lower()
        if ext not in [".json", ".geojson"]:
            raise TypeError("The output file must be a GeoJSON.")

        out_dir = os.path.dirname(out_geojson)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    # import fiona
    # print(fiona.supported_drivers)
    gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
    gdf = gpd.read_file(in_kml, driver="KML", **kwargs)

    if out_geojson is not None:
        gdf.to_file(out_geojson, driver="GeoJSON", **kwargs)
    else:
        return gdf.__geo_interface__


def kml_to_ee(in_kml, **kwargs):
    """Converts a KML to ee.FeatureColleciton.

    Args:
        in_kml (str): The file path to the input KML.

    Raises:
        FileNotFoundError: The input KML could not be found.

    Returns:
        object: ee.FeatureCollection
    """
    import warnings

    warnings.filterwarnings("ignore")

    in_kml = os.path.abspath(in_kml)
    if not os.path.exists(in_kml):
        raise FileNotFoundError("The input KML could not be found.")

    out_json = os.path.join(os.getcwd(), "tmp.geojson")

    check_package(name="geopandas", URL="https://geopandas.org")

    kml_to_geojson(in_kml, out_json, **kwargs)
    ee_object = geojson_to_ee(out_json)
    os.remove(out_json)
    return ee_object


def kmz_to_ee(in_kmz, **kwargs):
    """Converts a KMZ to ee.FeatureColleciton.

    Args:
        in_kmz (str): The file path to the input KMZ.

    Raises:
        FileNotFoundError: The input KMZ could not be found.

    Returns:
        object: ee.FeatureCollection
    """
    in_kmz = os.path.abspath(in_kmz)
    if not os.path.exists(in_kmz):
        raise FileNotFoundError("The input KMZ could not be found.")

    out_dir = os.path.dirname(in_kmz)
    out_kml = os.path.join(out_dir, "doc.kml")
    with zipfile.ZipFile(in_kmz, "r") as zip_ref:
        zip_ref.extractall(out_dir)

    fc = kml_to_ee(out_kml, **kwargs)
    os.remove(out_kml)
    return fc


def csv_to_df(in_csv, **kwargs):
    """Converts a CSV file to pandas dataframe.

    Args:
        in_csv (str): File path to the input CSV.

    Returns:
        pd.DataFrame: pandas DataFrame
    """
    import pandas as pd

    try:
        return pd.read_csv(in_csv, **kwargs)
    except Exception as e:
        raise Exception(e)


csv_to_pandas = csv_to_df


def ee_to_df(ee_object, col_names=None, **kwargs):
    """Converts an ee.FeatureCollection to pandas dataframe.

    Args:
        ee_object (ee.FeatureCollection): ee.FeatureCollection.
        col_names (list): List of column names. Defaults to None.

    Raises:
        TypeError: ee_object must be an ee.FeatureCollection

    Returns:
        pd.DataFrame: pandas DataFrame
    """
    import pandas as pd

    if isinstance(ee_object, ee.Feature):
        ee_object = ee.FeatureCollection([ee_object])

    if not isinstance(ee_object, ee.FeatureCollection):
        raise TypeError("ee_object must be an ee.FeatureCollection")

    try:
        data = ee_object.map(lambda f: ee.Feature(None, f.toDictionary()))
        data = [x["properties"] for x in data.getInfo()["features"]]
        df = pd.DataFrame(data)

        if col_names is None:
            col_names = ee_object.first().propertyNames().getInfo()
            col_names.remove("system:index")
        elif not isinstance(col_names, list):
            raise TypeError("col_names must be a list")

        df = df[col_names]

        return df
    except Exception as e:
        raise Exception(e)


ee_to_pandas = ee_to_df


def shp_to_gdf(in_shp, **kwargs):
    """Converts a shapefile to Geopandas dataframe.

    Args:
        in_shp (str): File path to the input shapefile.

    Raises:
        FileNotFoundError: The provided shp could not be found.

    Returns:
        gpd.GeoDataFrame: geopandas.GeoDataFrame
    """
    import warnings

    warnings.filterwarnings("ignore")

    in_shp = os.path.abspath(in_shp)
    if not os.path.exists(in_shp):
        raise FileNotFoundError("The provided shp could not be found.")

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    try:
        return gpd.read_file(in_shp, **kwargs)
    except Exception as e:
        raise Exception(e)


shp_to_geopandas = shp_to_gdf


def ee_to_gdf(ee_object, selectors=None, verbose=False):
    """Converts an ee.FeatureCollection to Geopandas dataframe.

    Args:
        ee_object (ee.FeatureCollection): ee.FeatureCollection.
        selectors (list, optional): A list of attributes to export. Defaults to None.
        verbose (bool, optional): Whether to print out descriptive text. Defaults to False.

    Raises:
        TypeError: ee_object must be an ee.FeatureCollection.

    Returns:
        gpd.GeoDataFrame: geopandas.GeoDataFrame
    """
    from pathlib import Path

    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    if not isinstance(ee_object, ee.FeatureCollection):
        raise TypeError("ee_object must be an ee.FeatureCollection")

    collection = ee_to_geojson(ee_object)
    gdf = gpd.GeoDataFrame.from_features(collection["features"])

    return gdf


ee_to_geopandas = ee_to_gdf


def delete_shp(in_shp, verbose=False):
    """Deletes a shapefile.

    Args:
        in_shp (str): The input shapefile to delete.
        verbose (bool, optional): Whether to print out descriptive text. Defaults to False.
    """
    from pathlib import Path

    in_shp = os.path.abspath(in_shp)
    in_dir = os.path.dirname(in_shp)
    basename = os.path.basename(in_shp).replace(".shp", "")

    files = Path(in_dir).rglob(basename + ".*")

    for file in files:
        filepath = os.path.join(in_dir, str(file))
        try:
            os.remove(filepath)
            if verbose:
                print(f"Deleted {filepath}")
        except Exception as e:
            if verbose:
                print(e)


def df_to_ee(df, latitude="latitude", longitude="longitude", **kwargs):
    """Converts a pandas DataFrame to ee.FeatureCollection.

    Args:
        df (pandas.DataFrame): An input pandas.DataFrame.
        latitude (str, optional): Column name for the latitude column. Defaults to 'latitude'.
        longitude (str, optional): Column name for the longitude column. Defaults to 'longitude'.

    Raises:
        TypeError: The input data type must be pandas.DataFrame.

    Returns:
        ee.FeatureCollection: The ee.FeatureCollection converted from the input pandas DataFrame.
    """
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        raise TypeError("The input data type must be pandas.DataFrame.")

    geojson = pandas_to_geojson(df, latitude=latitude, longitude=longitude)
    fc = geojson_to_ee(geojson)

    return fc


pandas_to_ee = df_to_ee


def gdf_to_ee(gdf, geodesic=True):
    """Converts a GeoPandas GeoDataFrame to ee.FeatureCollection.

    Args:
        gdf (geopandas.GeoDataFrame): The input geopandas.GeoDataFrame to be converted ee.FeatureCollection.
        geodesic (bool, optional): Whether line segments should be interpreted as spherical geodesics. If false, indicates that line segments should be interpreted as planar lines in the specified CRS. If absent, defaults to true if the CRS is geographic (including the default EPSG:4326), or to false if the CRS is projected. Defaults to True.

    Raises:
        TypeError: The input data type must be geopandas.GeoDataFrame.

    Returns:
        ee.FeatureCollection: The output ee.FeatureCollection converted from the input geopandas.GeoDataFrame.
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("The input data type must be geopandas.GeoDataFrame.")

    out_json = os.path.join(os.getcwd(), random_string(6) + ".geojson")
    gdf = gdf.to_crs(4326)
    gdf.to_file(out_json, driver="GeoJSON")

    fc = geojson_to_ee(out_json, geodesic=geodesic)
    os.remove(out_json)

    return fc


geopandas_to_ee = gdf_to_ee


def vector_to_geojson(
    filename, out_geojson=None, bbox=None, mask=None, rows=None, epsg="4326", **kwargs
):
    """Converts any geopandas-supported vector dataset to GeoJSON.

    Args:
        filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
        out_geojson (str, optional): The file path to the output GeoJSON. Defaults to None.
        bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
        mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter for features that intersect with the given dict-like geojson geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox. Defaults to None.
        rows (int or slice, optional): Load in specific rows by passing an integer (first n rows) or a slice() object.. Defaults to None.
        epsg (str, optional): The EPSG number to convert to. Defaults to "4326".

    Raises:
        ValueError: When the output file path is invalid.

    Returns:
        dict: A dictionary containing the GeoJSON.
    """
    import warnings

    warnings.filterwarnings("ignore")
    check_package(name="geopandas", URL="https://geopandas.org")
    import geopandas as gpd

    if not filename.startswith("http"):
        filename = os.path.abspath(filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".kml":
        gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
        df = gpd.read_file(
            filename, bbox=bbox, mask=mask, rows=rows, driver="KML", **kwargs
        )
    else:
        df = gpd.read_file(filename, bbox=bbox, mask=mask, rows=rows, **kwargs)
    gdf = df.to_crs(epsg=epsg)

    if out_geojson is not None:

        if not out_geojson.lower().endswith(".geojson"):
            raise ValueError("The output file must have a geojson file extension.")

        out_geojson = os.path.abspath(out_geojson)
        out_dir = os.path.dirname(out_geojson)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        gdf.to_file(out_geojson, driver="GeoJSON")

    else:
        return gdf.__geo_interface__


def vector_to_ee(
    filename,
    bbox=None,
    mask=None,
    rows=None,
    geodesic=True,
    **kwargs,
):
    """Converts any geopandas-supported vector dataset to ee.FeatureCollection.

    Args:
        filename (str): Either the absolute or relative path to the file or URL to be opened, or any object with a read() method (such as an open file or StringIO).
        bbox (tuple | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter features by given bounding box, GeoSeries, GeoDataFrame or a shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with mask. Defaults to None.
        mask (dict | GeoDataFrame or GeoSeries | shapely Geometry, optional): Filter for features that intersect with the given dict-like geojson geometry, GeoSeries, GeoDataFrame or shapely geometry. CRS mis-matches are resolved if given a GeoSeries or GeoDataFrame. Cannot be used with bbox. Defaults to None.
        rows (int or slice, optional): Load in specific rows by passing an integer (first n rows) or a slice() object.. Defaults to None.
        geodesic (bool, optional): Whether line segments should be interpreted as spherical geodesics. If false, indicates that line segments should be interpreted as planar lines in the specified CRS. If absent, defaults to true if the CRS is geographic (including the default EPSG:4326), or to false if the CRS is projected.

    Returns:
        ee.FeatureCollection: Earth Engine FeatureCollection.
    """
    geojson = vector_to_geojson(
        filename, bbox=bbox, mask=mask, rows=rows, epsg="4326", **kwargs
    )

    return geojson_to_ee(geojson, geodesic=geodesic)


def extract_pixel_values(
    ee_object, region, scale=None, projection=None, tileScale=1, getInfo=False
):
    """Samples the pixels of an image, returning them as a ee.Dictionary.

    Args:
        ee_object (ee.Image | ee.ImageCollection): The ee.Image or ee.ImageCollection to sample.
        region (ee.Geometry): The region to sample from. If unspecified, uses the image's whole footprint.
        scale (float, optional): A nominal scale in meters of the projection to sample in. Defaults to None.
        projection (str, optional): The projection in which to sample. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        tileScale (int, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.
        getInfo (bool, optional): Whether to use getInfo with the results, i.e., returning the values a list. Default to False.

    Raises:
        TypeError: The image must be an instance of ee.Image.
        TypeError: Region must be an instance of ee.Geometry.

    Returns:
        ee.Dictionary: The dictionary containing band names and pixel values.
    """
    if isinstance(ee_object, ee.ImageCollection):
        ee_object = ee_object.toBands()

    if not isinstance(ee_object, ee.Image):
        raise TypeError("The image must be an instance of ee.Image.")

    if not isinstance(region, ee.Geometry):
        raise TypeError("Region must be an instance of ee.Geometry.")

    dict_values = (
        ee_object.sample(region, scale, projection, tileScale=tileScale)
        .first()
        .toDictionary()
    )

    if getInfo:
        band_names = ee_object.bandNames().getInfo()
        values_tmp = dict_values.getInfo()
        values = [values_tmp[i] for i in band_names]
        return dict(zip(band_names, values))
    else:
        return dict_values


def list_vars(var_type=None):
    """Lists all defined avariables.

    Args:
        var_type (object, optional): The object type of variables to list. Defaults to None.

    Returns:
        list: A list of all defined variables.
    """
    result = []

    for var in globals():

        reserved_vars = [
            "In",
            "Out",
            "get_ipython",
            "exit",
            "quit",
            "json",
            "getsizeof",
            "NamespaceMagics",
            "np",
            "var_dic_list",
            "list_vars",
            "ee",
            "geemap",
        ]

        if (not var.startswith("_")) and (var not in reserved_vars):
            if var_type is not None and isinstance(eval(var), var_type):
                result.append(var)
            elif var_type is None:
                result.append(var)

    return result


def extract_transect(
    image,
    line,
    reducer="mean",
    n_segments=100,
    dist_interval=None,
    scale=None,
    crs=None,
    crsTransform=None,
    tileScale=1.0,
    to_pandas=False,
    **kwargs,
):
    """Extracts transect from an image. Credits to Gena for providing the JavaScript example https://code.earthengine.google.com/b09759b8ac60366ee2ae4eccdd19e615.

    Args:
        image (ee.Image): The image to extract transect from.
        line (ee.Geometry.LineString): The LineString used to extract transect from an image.
        reducer (str, optional): The ee.Reducer to use, e.g., 'mean', 'median', 'min', 'max', 'stdDev'. Defaults to "mean".
        n_segments (int, optional): The number of segments that the LineString will be split into. Defaults to 100.
        dist_interval (float, optional): The distance interval used for splitting the LineString. If specified, the n_segments parameter will be ignored. Defaults to None.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
        crs (ee.Projection, optional): The projection to work in. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale. Defaults to None.
        crsTransform (list, optional): The list of CRS transform values. This is a row-major ordering of the 3x2 transform matrix. This option is mutually exclusive with 'scale', and will replace any transform already set on the projection. Defaults to None.
        tileScale (float, optional): A scaling factor used to reduce aggregation tile size; using a larger tileScale (e.g. 2 or 4) may enable computations that run out of memory with the default. Defaults to 1.
        to_pandas (bool, optional): Whether to convert the result to a pandas dataframe. Default to False.

    Raises:
        TypeError: If the geometry type is not LineString.
        Exception: If the program fails to compute.

    Returns:
        ee.FeatureCollection: The FeatureCollection containing the transect with distance and reducer values.
    """
    try:

        geom_type = line.type().getInfo()
        if geom_type != "LineString":
            raise TypeError("The geometry type must be LineString.")

        reducer = eval("ee.Reducer." + reducer + "()")
        maxError = image.projection().nominalScale().divide(5)

        length = line.length(maxError)
        if dist_interval is None:
            dist_interval = length.divide(n_segments)

        distances = ee.List.sequence(0, length, dist_interval)
        lines = line.cutLines(distances, maxError).geometries()

        def set_dist_attr(l):
            l = ee.List(l)
            geom = ee.Geometry(l.get(0))
            distance = ee.Number(l.get(1))
            geom = ee.Geometry.LineString(geom.coordinates())
            return ee.Feature(geom, {"distance": distance})

        lines = lines.zip(distances).map(set_dist_attr)
        lines = ee.FeatureCollection(lines)

        transect = image.reduceRegions(
            **{
                "collection": ee.FeatureCollection(lines),
                "reducer": reducer,
                "scale": scale,
                "crs": crs,
                "crsTransform": crsTransform,
                "tileScale": tileScale,
            }
        )

        if to_pandas:
            return ee_to_df(transect)
        return transect

    except Exception as e:
        raise Exception(e)


def random_sampling(
    image,
    region=None,
    scale=None,
    projection=None,
    factor=None,
    numPixels=None,
    seed=0,
    dropNulls=True,
    tileScale=1.0,
    geometries=True,
    to_pandas=False,
):
    """Samples the pixels of an image, returning them as a FeatureCollection. Each feature will have 1 property per band in the input image. Note that the default behavior is to drop features that intersect masked pixels, which result in null-valued properties (see dropNulls argument).

    Args:
        image (ee.Image): The image to sample.
        region (ee.Geometry, optional): The region to sample from. If unspecified, uses the image's whole footprint. Defaults to None.
        scale (float, optional): A nominal scale in meters of the projection to sample in.. Defaults to None.
        projection (ee.Projection, optional): The projection in which to sample. If unspecified, the projection of the image's first band is used. If specified in addition to scale, rescaled to the specified scale.. Defaults to None.
        factor (float, optional): A subsampling factor, within (0, 1]. If specified, 'numPixels' must not be specified. Defaults to no subsampling. Defaults to None.
        numPixels (int, optional): The approximate number of pixels to sample. If specified, 'factor' must not be specified. Defaults to None.
        seed (int, optional): A randomization seed to use for subsampling. Defaults to True. Defaults to 0.
        dropNulls (bool, optional): Post filter the result to drop features that have null-valued properties. Defaults to True.
        tileScale (float, optional): Post filter the result to drop features that have null-valued properties. Defaults to 1.
        geometries (bool, optional): If true, adds the center of the sampled pixel as the geometry property of the output feature. Otherwise, geometries will be omitted (saving memory). Defaults to True.
        to_pandas (bool, optional): Whether to return the result as a pandas dataframe. Defaults to False.

    Raises:
        TypeError: If the input image is not an ee.Image.

    Returns:
        ee.FeatureCollection: Random sampled points.
    """
    if not isinstance(image, ee.Image):
        raise TypeError("The image must be ee.Image")

    points = image.sample(
        **{
            "region": region,
            "scale": scale,
            "projection": projection,
            "factor": factor,
            "numPixels": numPixels,
            "seed": seed,
            "dropNulls": dropNulls,
            "tileScale": tileScale,
            "geometries": geometries,
        }
    )

    if to_pandas:
        return ee_to_df(points)
    else:
        return points


def osm_to_gdf(
    query,
    which_result=None,
    by_osmid=False,
    buffer_dist=None,
):
    """Retrieves place(s) by name or ID from the Nominatim API as a GeoDataFrame.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        which_result (INT, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.

    Returns:
        GeoDataFrame: A GeoPandas GeoDataFrame.
    """
    check_package(
        "geopandas", "https://geopandas.org/getting_started.html#installation"
    )
    check_package("osmnx", "https://osmnx.readthedocs.io/en/stable/")

    try:
        import osmnx as ox

        gdf = ox.geocode_to_gdf(query, which_result, by_osmid, buffer_dist)
        return gdf
    except Exception as e:
        raise Exception(e)


osm_to_geopandas = osm_to_gdf


def osm_to_ee(
    query, which_result=None, by_osmid=False, buffer_dist=None, geodesic=True
):
    """Retrieves place(s) by name or ID from the Nominatim API as an ee.FeatureCollection.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        which_result (INT, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.
        geodesic (bool, optional): Whether line segments should be interpreted as spherical geodesics. If false, indicates that line segments should be interpreted as planar lines in the specified CRS. If absent, defaults to true if the CRS is geographic (including the default EPSG:4326), or to false if the CRS is projected.

    Returns:
        ee.FeatureCollection: An Earth Engine FeatureCollection.
    """
    gdf = osm_to_gdf(query, which_result, by_osmid, buffer_dist)
    fc = gdf_to_ee(gdf, geodesic)
    return fc


def osm_to_geojson(query, which_result=None, by_osmid=False, buffer_dist=None):
    """Retrieves place(s) by name or ID from the Nominatim API as an ee.FeatureCollection.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        which_result (INT, optional): Which geocoding result to use. if None, auto-select the first (Multi)Polygon or raise an error if OSM doesn't return one. to get the top match regardless of geometry type, set which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather than text search. Defaults to False.
        buffer_dist (float, optional): Distance to buffer around the place geometry, in meters. Defaults to None.

    Returns:
        ee.FeatureCollection: An Earth Engine FeatureCollection.
    """
    gdf = osm_to_gdf(query, which_result, by_osmid, buffer_dist)
    return gdf.__geo_interface__


def get_api_key(token_name, m=None):
    """Retrieves an API key based on a system environmen variable.

    Args:
        token_name (str): The token name.
        m (ipyleaflet.Map | folium.Map, optional): A Map instance. Defaults to None.

    Returns:
        str: The API key.
    """
    api_key = os.environ.get(token_name)
    if m is not None and token_name in m.api_keys:
        api_key = m.api_keys[token_name]

    return api_key


def set_api_key(token_name, api_key, m=None):
    """Sets an API key as an environment variable.

    Args:
        token_name (str): The token name.
        api_key (str): The API key.
        m (ipyleaflet.Map | folium.Map, optional): A Map instance.. Defaults to None.
    """
    os.environ[token_name] = api_key
    if m is not None:
        m.api_keys[token_name] = api_key


def planet_monthly_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet monthly imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    # from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = datetime.date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))

    links = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/planet_medres_normalized_analytic_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2020, year_now + 1):

        for month in range(1, 13):
            m_str = str(year) + "-" + str(month).zfill(2)

            if year == 2020 and month < 9:
                continue
            if year == year_now and month >= month_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            links.append(url)

    return links


def planet_biannual_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    dates = [
        "2015-12_2016-05",
        "2016-06_2016-11",
        "2016-12_2017-05",
        "2017-06_2017-11",
        "2017-12_2018-05",
        "2018-06_2018-11",
        "2018-12_2019-05",
        "2019-06_2019-11",
        "2019-12_2020-05",
        "2020-06_2020-08",
    ]

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/planet_medres_normalized_analytic_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for d in dates:
        url = f"{prefix}{d}{subfix}{api_key}"
        link.append(url)

    return link


def planet_catalog_tropical(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual and monthly imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Returns:
        list: A list of tile URLs.
    """
    biannual = planet_biannual_tropical(api_key, token_name)
    monthly = planet_monthly_tropical(api_key, token_name)
    return biannual + monthly


def planet_monthly_tiles_tropical(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  monthly imagery TileLayer based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """
    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    link = planet_monthly_tropical(api_key, token_name)
    for url in link:
        index = url.find("20")
        name = "Planet_" + url[index: index + 7]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles


def planet_biannual_tiles_tropical(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  bi-annual imagery TileLayer based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    link = planet_biannual_tropical(api_key, token_name)
    for url in link:
        index = url.find("20")
        name = "Planet_" + url[index: index + 15]
        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )
        tiles[name] = tile

    return tiles


def planet_tiles_tropical(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  monthly imagery TileLayer based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    catalog = {}
    biannul = planet_biannual_tiles_tropical(api_key, token_name, tile_format)
    monthly = planet_monthly_tiles_tropical(api_key, token_name, tile_format)

    for key in biannul:
        catalog[key] = biannul[key]

    for key in monthly:
        catalog[key] = monthly[key]

    return catalog


def planet_monthly(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet monthly imagery URLs based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    # from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = datetime.date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_monthly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2016, year_now + 1):

        for month in range(1, 13):
            m_str = str(year) + "_" + str(month).zfill(2)

            if year == year_now and month >= month_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            link.append(url)

    return link


def planet_quarterly(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet quarterly imagery URLs based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: If the API key could not be found.

    Returns:
        list: A list of tile URLs.
    """
    # from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = datetime.date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))
    quarter_now = (month_now - 1) // 3 + 1

    link = []
    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_quarterly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    for year in range(2016, year_now + 1):

        for quarter in range(1, 5):
            m_str = str(year) + "q" + str(quarter)

            if year == year_now and quarter >= quarter_now:
                break

            url = f"{prefix}{m_str}{subfix}{api_key}"
            link.append(url)

    return link


def planet_catalog(api_key=None, token_name="PLANET_API_KEY"):
    """Generates Planet bi-annual and monthly imagery URLs based on an API key. See https://assets.planet.com/docs/NICFI_UserGuidesFAQ.pdf

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Returns:
        list: A list of tile URLs.
    """
    quarterly = planet_quarterly(api_key, token_name)
    monthly = planet_monthly(api_key, token_name)
    return quarterly + monthly


def planet_monthly_tiles(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  monthly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """
    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    link = planet_monthly(api_key, token_name)

    for url in link:
        index = url.find("20")
        name = "Planet_" + url[index: index + 7]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles


def planet_quarterly_tiles(
    api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"
):
    """Generates Planet  quarterly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """
    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    tiles = {}
    links = planet_quarterly(api_key, token_name)

    for url in links:
        index = url.find("20")
        name = "Planet_" + url[index: index + 6]

        if tile_format == "ipyleaflet":
            tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
        else:
            tile = folium.TileLayer(
                tiles=url,
                attr="Planet",
                name=name,
                overlay=True,
                control=True,
            )

        tiles[name] = tile

    return tiles


def planet_tiles(api_key=None, token_name="PLANET_API_KEY", tile_format="ipyleaflet"):
    """Generates Planet imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    catalog = {}
    quarterly = planet_quarterly_tiles(api_key, token_name, tile_format)
    monthly = planet_monthly_tiles(api_key, token_name, tile_format)

    for key in quarterly:
        catalog[key] = quarterly[key]

    for key in monthly:
        catalog[key] = monthly[key]

    return catalog


def planet_by_quarter(
    year=2016,
    quarter=1,
    api_key=None,
    token_name="PLANET_API_KEY",
):
    """Gets Planet global mosaic tile url by quarter. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        quarter (int, optional): The quarter of Planet global mosaic, must be 1-4. Defaults to 1.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: The Planet API key is not provided.
        ValueError: The year is invalid.
        ValueError: The quarter is invalid.
        ValueError: The quarter is invalid.

    Returns:
        str: A Planet global mosaic tile url.
    """
    # from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = datetime.date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))
    quarter_now = (month_now - 1) // 3 + 1

    if year > year_now:
        raise ValueError(f"Year must be between 2016 and {year_now}.")
    elif year == year_now and quarter >= quarter_now:
        raise ValueError(f"Quarter must be less than {quarter_now} for year {year_now}")

    if quarter < 1 or quarter > 4:
        raise ValueError("Quarter must be between 1 and 4.")

    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_quarterly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    m_str = str(year) + "q" + str(quarter)
    url = f"{prefix}{m_str}{subfix}{api_key}"

    return url


def planet_by_month(
    year=2016,
    month=1,
    api_key=None,
    token_name="PLANET_API_KEY",
):
    """Gets Planet global mosaic tile url by month. To get a Planet API key, see https://developers.planet.com/quickstart/apis/

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        month (int, optional): The month of Planet global mosaic, must be 1-12. Defaults to 1.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".

    Raises:
        ValueError: The Planet API key is not provided.
        ValueError: The year is invalid.
        ValueError: The month is invalid.
        ValueError: The month is invalid.

    Returns:
        str: A Planet global mosaic tile url.
    """
    # from datetime import date

    if api_key is None:
        api_key = os.environ.get(token_name)
        if api_key is None:
            raise ValueError("The Planet API Key must be provided.")

    today = datetime.date.today()
    year_now = int(today.strftime("%Y"))
    month_now = int(today.strftime("%m"))
    # quarter_now = (month_now - 1) // 3 + 1

    if year > year_now:
        raise ValueError(f"Year must be between 2016 and {year_now}.")
    elif year == year_now and month >= month_now:
        raise ValueError(f"Month must be less than {month_now} for year {year_now}")

    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")

    prefix = "https://tiles.planet.com/basemaps/v1/planet-tiles/global_monthly_"
    subfix = "_mosaic/gmap/{z}/{x}/{y}.png?api_key="

    m_str = str(year) + "_" + str(month).zfill(2)
    url = f"{prefix}{m_str}{subfix}{api_key}"

    return url


def planet_tile_by_quarter(
    year=2016,
    quarter=1,
    name=None,
    api_key=None,
    token_name="PLANET_API_KEY",
    tile_format="ipyleaflet",
):
    """Generates Planet quarterly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        quarter (int, optional): The quarter of Planet global mosaic, must be 1-4. Defaults to 1.
        name (str, optional): The layer name to use. Defaults to None.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """

    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    url = planet_by_quarter(year, quarter, api_key, token_name)

    if name is None:
        name = "Planet_" + str(year) + "_q" + str(quarter)

    if tile_format == "ipyleaflet":
        tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
    else:
        tile = folium.TileLayer(
            tiles=url,
            attr="Planet",
            name=name,
            overlay=True,
            control=True,
        )

    return tile


def planet_tile_by_month(
    year=2016,
    month=1,
    name=None,
    api_key=None,
    token_name="PLANET_API_KEY",
    tile_format="ipyleaflet",
):
    """Generates Planet monthly imagery TileLayer based on an API key. To get a Planet API key, see https://developers.planet.com/quickstart/apis

    Args:
        year (int, optional): The year of Planet global mosaic, must be >=2016. Defaults to 2016.
        month (int, optional): The month of Planet global mosaic, must be 1-12. Defaults to 1.
        name (str, optional): The layer name to use. Defaults to None.
        api_key (str, optional): The Planet API key. Defaults to None.
        token_name (str, optional): The environment variable name of the API key. Defaults to "PLANET_API_KEY".
        tile_format (str, optional): The TileLayer format, can be either ipyleaflet or folium. Defaults to "ipyleaflet".

    Raises:
        ValueError: If the tile layer format is invalid.

    Returns:
        dict: A dictionary of TileLayer.
    """
    import folium
    import ipyleaflet

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    url = planet_by_month(year, month, api_key, token_name)

    if name is None:
        name = "Planet_" + str(year) + "_" + str(month).zfill(2)

    if tile_format == "ipyleaflet":
        tile = ipyleaflet.TileLayer(url=url, attribution="Planet", name=name)
    else:
        tile = folium.TileLayer(
            tiles=url,
            attr="Planet",
            name=name,
            overlay=True,
            control=True,
        )

    return tile


def get_current_latlon():
    """Get the current latitude and longitude based on the user's location."""
    import geocoder

    g = geocoder.ip("me")
    props = g.geojson["features"][0]["properties"]
    lat = props["lat"]
    lon = props["lng"]
    return lat, lon


def get_census_dict(reset=False):
    """Returns a dictionary of Census data.

    Args:
        reset (bool, optional): Reset the dictionary. Defaults to False.

    Returns:
        dict: A dictionary of Census data.
    """
    import json
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    census_data = os.path.join(pkg_dir, "data/census_data.json")

    if reset:

        from owslib.wms import WebMapService

        census_dict = {}

        names = [
            "Current",
            "ACS 2021",
            "ACS 2019",
            "ACS 2018",
            "ACS 2017",
            "ACS 2016",
            "ACS 2015",
            "ACS 2014",
            "ACS 2013",
            "ACS 2012",
            "ECON 2012",
            "Census 2020",
            "Census 2010",
            "Physical Features",
            "Decennial Census 2020",
            "Decennial Census 2010",
            "Decennial Census 2000",
            "Decennial Physical Features",
        ]

        links = {}

        print("Retrieving data. Please wait ...")
        for name in names:
            if "Decennial" not in name:
                links[
                    name
                ] = f"https://tigerweb.geo.census.gov/arcgis/services/TIGERweb/tigerWMS_{name.replace(' ', '')}/MapServer/WMSServer"
            else:
                links[
                    name
                ] = f"https://tigerweb.geo.census.gov/arcgis/services/Census2020/tigerWMS_{name.replace('Decennial', '').replace(' ', '')}/MapServer/WMSServer"

            wms = WebMapService(links[name], timeout=300)
            layers = list(wms.contents)
            layers.sort()
            census_dict[name] = {
                "url": links[name],
                "layers": layers,
                # "title": wms.identification.title,
                # "abstract": wms.identification.abstract,
            }

        with open(census_data, "w") as f:
            json.dump(census_dict, f, indent=4)

    else:

        with open(census_data, "r") as f:
            census_dict = json.load(f)

    return census_dict


def search_xyz_services(keyword, name=None, list_only=True, add_prefix=True):
    """Search for XYZ tile providers from xyzservices.

    Args:
        keyword (str): The keyword to search for.
        name (str, optional): The name of the xyz tile. Defaults to None.
        list_only (bool, optional): If True, only the list of services will be returned. Defaults to True.
        add_prefix (bool, optional): If True, the prefix "xyz." will be added to the service name. Defaults to True.

    Returns:
        list: A list of XYZ tile providers.
    """

    import xyzservices.providers as xyz

    if name is None:
        providers = xyz.filter(keyword=keyword).flatten()
    else:
        providers = xyz.filter(name=name).flatten()

    if list_only:
        if add_prefix:
            return ["xyz." + provider for provider in providers]
        else:
            return [provider for provider in providers]
    else:
        return providers


def search_qms(keyword, limit=10, list_only=True, add_prefix=True):
    """Search for QMS tile providers from Quick Map Services.

    Args:
        keyword (str): The keyword to search for.
        limit (int, optional): The maximum number of results to return. Defaults to 10.
        list_only (bool, optional): If True, only the list of services will be returned. Defaults to True.
        add_prefix (bool, optional): If True, the prefix "qms." will be added to the service name. Defaults to True.

    Returns:
        list: A list of QMS tile providers.
    """

    import requests

    QMS_API = "https://qms.nextgis.com/api/v1/geoservices"
    services = requests.get(
        f"{QMS_API}/?search={keyword}&type=tms&epsg=3857&limit={limit}"
    )
    services = services.json()
    if services["results"]:
        providers = services["results"]
        if list_only:
            if add_prefix:
                return ["qms." + provider["name"] for provider in providers]
            else:
                return [provider["name"] for provider in providers]
        else:
            return providers
    else:
        return None


def get_wms_layers(url):
    """Returns a list of WMS layers from a WMS service.

    Args:
        url (str): The URL of the WMS service.

    Returns:
        list: A list of WMS layers.
    """
    from owslib.wms import WebMapService

    wms = WebMapService(url)
    layers = list(wms.contents)
    layers.sort()
    return layers


def read_file_from_url(url, return_type="list", encoding="utf-8"):
    """Reads a file from a URL.

    Args:
        url (str): The URL of the file.
        return_type (str, optional): The return type, can either be string or list. Defaults to "list".
        encoding (str, optional): The encoding of the file. Defaults to "utf-8".

    Raises:
        ValueError: The return type must be either list or string.

    Returns:
        str | list: The contents of the file.
    """
    from urllib.request import urlopen

    if return_type == "list":
        return [line.decode(encoding).rstrip() for line in urlopen(url).readlines()]
    elif return_type == "string":
        return urlopen(url).read().decode(encoding)
    else:
        raise ValueError("The return type must be either list or string.")


def create_download_button(
    label,
    data,
    file_name=None,
    mime=None,
    key=None,
    help=None,
    on_click=None,
    args=None,
    **kwargs,
):
    """Streamlit function to create a download button.

    Args:
        label (str): A short label explaining to the user what this button is for..
        data (str | list): The contents of the file to be downloaded. See example below for caching techniques to avoid recomputing this data unnecessarily.
        file_name (str, optional): An optional string to use as the name of the file to be downloaded, such as 'my_file.csv'. If not specified, the name will be automatically generated. Defaults to None.
        mime (str, optional): The MIME type of the data. If None, defaults to "text/plain" (if data is of type str or is a textual file) or "application/octet-stream" (if data is of type bytes or is a binary file). Defaults to None.
        key (str, optional): An optional string or integer to use as the unique key for the widget. If this is omitted, a key will be generated for the widget based on its content. Multiple widgets of the same type may not share the same key. Defaults to None.
        help (str, optional): An optional tooltip that gets displayed when the button is hovered over. Defaults to None.
        on_click (str, optional): An optional callback invoked when this button is clicked. Defaults to None.
        args (list, optional): An optional tuple of args to pass to the callback. Defaults to None.
        kwargs (dict, optional): An optional tuple of args to pass to the callback.

    """
    try:
        import streamlit as st
        import pandas as pd

        if isinstance(data, str):

            if file_name is None:
                file_name = data.split("/")[-1]

            if data.endswith(".csv"):
                data = pd.read_csv(data).to_csv()
                if mime is None:
                    mime = "text/csv"
                return st.download_button(
                    label, data, file_name, mime, key, help, on_click, args, **kwargs
                )
            elif (
                data.endswith(".gif") or data.endswith(".png") or data.endswith(".jpg")
            ):
                if mime is None:
                    mime = f"image/{os.path.splitext(data)[1][1:]}"

                with open(data, "rb") as file:
                    return st.download_button(
                        label,
                        file,
                        file_name,
                        mime,
                        key,
                        help,
                        on_click,
                        args,
                        **kwargs,
                    )

            else:
                return st.download_button(
                    label,
                    label,
                    data,
                    file_name,
                    mime,
                    key,
                    help,
                    on_click,
                    args,
                    **kwargs,
                )

    except ImportError:
        print("Streamlit is not installed. Please run 'pip install streamlit'.")
        return
    except Exception as e:
        raise Exception(e)


def gdf_to_geojson(gdf, out_geojson=None, epsg=None):
    """Converts a GeoDataFame to GeoJSON.

    Args:
        gdf (GeoDataFrame): A GeoPandas GeoDataFrame.
        out_geojson (str, optional): File path to he output GeoJSON. Defaults to None.
        epsg (str, optional): An EPSG string, e.g., "4326". Defaults to None.

    Raises:
        TypeError: When the output file extension is incorrect.
        Exception: When the conversion fails.

    Returns:
        dict: When the out_json is None returns a dict.
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    try:
        if epsg is not None:
            gdf = gdf.to_crs(epsg=epsg)
        geojson = gdf.__geo_interface__

        if out_geojson is None:
            return geojson
        else:
            ext = os.path.splitext(out_geojson)[1]
            if ext.lower() not in [".json", ".geojson"]:
                raise TypeError(
                    "The output file extension must be either .json or .geojson"
                )
            out_dir = os.path.dirname(out_geojson)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

            gdf.to_file(out_geojson, driver="GeoJSON")
    except Exception as e:
        raise Exception(e)


def temp_file_path(extension):
    """Returns a temporary file path.

    Args:
        extension (str): The file extension.

    Returns:
        str: The temporary file path.
    """

    import tempfile
    import os
    import uuid

    if not extension.startswith("."):
        extension = "." + extension
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{extension}")

    return file_path


def create_contours(
    image, min_value, max_value, interval, kernel=None, region=None, values=None
):
    """Creates contours from an image. Code adapted from https://mygeoblog.com/2017/01/28/contour-lines-in-gee. Credits to MyGeoBlog.

    Args:
        image (ee.Image): An image to create contours.
        min_value (float): The minimum value of contours.
        max_value (float): The maximum value of contours.
        interval (float):  The interval between contours.
        kernel (ee.Kernel, optional): The kernel to use for smoothing image. Defaults to None.
        region (ee.Geometry | ee.FeatureCollection, optional): The region of interest. Defaults to None.
        values (list, optional): A list of values to create contours for. Defaults to None.

    Raises:
        TypeError: The image must be an ee.Image.
        TypeError: The region must be an ee.Geometry or ee.FeatureCollection.

    Returns:
        ee.Image: The image containing contours.
    """
    if not isinstance(image, ee.Image):
        raise TypeError("The image must be an ee.Image.")
    if region is not None:
        if isinstance(region, ee.FeatureCollection) or isinstance(region, ee.Geometry):
            pass
        else:

            raise TypeError(
                "The region must be an ee.Geometry or ee.FeatureCollection."
            )

    if kernel is None:
        kernel = ee.Kernel.gaussian(5, 3)

    if isinstance(values, list):
        values = ee.List(values)
    elif isinstance(values, ee.List):
        pass

    if values is None:
        values = ee.List.sequence(min_value, max_value, interval)

    def contouring(value):
        mycountour = (
            image.convolve(kernel)
            .subtract(ee.Image.constant(value))
            .zeroCrossing()
            .multiply(ee.Image.constant(value).toFloat())
        )
        return mycountour.mask(mycountour)

    contours = values.map(contouring)

    if region is not None:
        if isinstance(region, ee.FeatureCollection):
            return ee.ImageCollection(contours).mosaic().clipToCollection(region)
        elif isinstance(region, ee.Geometry):
            return ee.ImageCollection(contours).mosaic().clip(region)
    else:
        return ee.ImageCollection(contours).mosaic()


def get_local_tile_layer(
    source,
    port="default",
    debug=False,
    projection="EPSG:3857",
    band=None,
    palette=None,
    vmin=None,
    vmax=None,
    nodata=None,
    attribution=None,
    tile_format="ipyleaflet",
    layer_name=None,
    get_center=False,
    get_bounds=False,
    **kwargs,
):
    """Generate an ipyleaflet/folium TileLayer from a local raster dataset or remote Cloud Optimized GeoTIFF (COG).

    Args:
        source (str): The path to the GeoTIFF file or the URL of the Cloud Optimized GeoTIFF.
        port (str, optional): The port to use for the server. Defaults to "default".
        debug (bool, optional): If True, the server will be started in debug mode. Defaults to False.
        projection (str, optional): The projection of the GeoTIFF. Defaults to "EPSG:3857".
        band (int, optional): The band to use. Band indexing starts at 1. Defaults to None.
        palette (str, optional): The name of the color palette from `palettable` to use when plotting a single band. See https://jiffyclub.github.io/palettable. Default is greyscale
        vmin (float, optional): The minimum value to use when colormapping the palette when plotting a single band. Defaults to None.
        vmax (float, optional): The maximum value to use when colormapping the palette when plotting a single band. Defaults to None.
        nodata (float, optional): The value from the band to use to interpret as not valid data. Defaults to None.
        attribution (str, optional): Attribution for the source raster. This defaults to a message about it being a local file.. Defaults to None.
        tile_format (str, optional): The tile layer format. Can be either ipyleaflet or folium. Defaults to "ipyleaflet".
        layer_name (str, optional): The layer name to use. Defaults to None.
        get_center (bool, optional): If True, the center of the layer will be returned. Defaults to False.
        get_bounds (bool, optional): If True, the bounds [minx, miny, maxx, maxy] of the layer will be returned. Defaults to False.

    Returns:
        ipyleaflet.TileLayer | folium.TileLayer: An ipyleaflet.TileLayer or folium.TileLayer.
    """

    check_package(
        "localtileserver", URL="https://github.com/banesullivan/localtileserver"
    )

    from localtileserver import (
        get_leaflet_tile_layer,
        get_folium_tile_layer,
        TileClient,
    )

    if isinstance(source, str):
        if not source.startswith("http"):
            source = os.path.abspath(source)
            if not os.path.exists(source):
                raise ValueError("The source path does not exist.")
    else:
        raise ValueError("The source must either be a string or TileClient")

    if isinstance(palette, str):
        from .colormaps import get_palette

        palette = get_palette(palette, hashtag=True)

    if tile_format not in ["ipyleaflet", "folium"]:
        raise ValueError("The tile format must be either ipyleaflet or folium.")

    if layer_name is None:
        if source.startswith("http"):
            layer_name = "RemoteTile_" + random_string(3)
        else:
            layer_name = "LocalTile_" + random_string(3)

    tile_client = TileClient(source, port=port, debug=debug)

    if tile_format == "ipyleaflet":
        tile_layer = get_leaflet_tile_layer(
            tile_client,
            port=port,
            debug=debug,
            projection=projection,
            band=band,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attribution=attribution,
            name=layer_name,
            **kwargs,
        )
    else:
        tile_layer = get_folium_tile_layer(
            tile_client,
            port=port,
            debug=debug,
            projection=projection,
            band=band,
            palette=palette,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            attr=attribution,
            overlay=True,
            name=layer_name,
            **kwargs,
        )

    center = tile_client.center()
    bounds = tile_client.bounds()  # [ymin, ymax, xmin, xmax]
    bounds = (bounds[2], bounds[0], bounds[3], bounds[1])  # [minx, miny, maxx, maxy]

    if get_center and get_bounds:
        return tile_layer, center, bounds
    elif get_center:
        return tile_layer, center
    elif get_bounds:
        return tile_layer, bounds
    else:
        return tile_layer


def get_palettable(types=None):
    """Get a list of palettable color palettes.

    Args:
        types (list, optional): A list of palettable types to return, e.g., types=['matplotlib', 'cartocolors']. Defaults to None.

    Returns:
        list: A list of palettable color palettes.
    """
    import palettable

    if types is not None and (not isinstance(types, list)):
        raise ValueError("The types must be a list.")

    allowed_palettes = [
        "cartocolors",
        "cmocean",
        "colorbrewer",
        "cubehelix",
        "lightbartlein",
        "matplotlib",
        "mycarta",
        "scientific",
        "tableau",
        "wesanderson",
    ]

    if types is None:
        types = allowed_palettes[:]

    if all(x in allowed_palettes for x in types):
        pass
    else:
        raise ValueError(
            "The types must be one of the following: " + ", ".join(allowed_palettes)
        )

    palettes = []

    if "cartocolors" in types:

        cartocolors_diverging = [
            f"cartocolors.diverging.{c}"
            for c in dir(palettable.cartocolors.diverging)[:-19]
        ]
        cartocolors_qualitative = [
            f"cartocolors.qualitative.{c}"
            for c in dir(palettable.cartocolors.qualitative)[:-19]
        ]
        cartocolors_sequential = [
            f"cartocolors.sequential.{c}"
            for c in dir(palettable.cartocolors.sequential)[:-41]
        ]

        palettes = (
            palettes
            + cartocolors_diverging
            + cartocolors_qualitative
            + cartocolors_sequential
        )

    if "cmocean" in types:

        cmocean_diverging = [
            f"cmocean.diverging.{c}" for c in dir(palettable.cmocean.diverging)[:-19]
        ]
        cmocean_sequential = [
            f"cmocean.sequential.{c}" for c in dir(palettable.cmocean.sequential)[:-19]
        ]

        palettes = palettes + cmocean_diverging + cmocean_sequential

    if "colorbrewer" in types:

        colorbrewer_diverging = [
            f"colorbrewer.diverging.{c}"
            for c in dir(palettable.colorbrewer.diverging)[:-19]
        ]
        colorbrewer_qualitative = [
            f"colorbrewer.qualitative.{c}"
            for c in dir(palettable.colorbrewer.qualitative)[:-19]
        ]
        colorbrewer_sequential = [
            f"colorbrewer.sequential.{c}"
            for c in dir(palettable.colorbrewer.sequential)[:-41]
        ]

        palettes = (
            palettes
            + colorbrewer_diverging
            + colorbrewer_qualitative
            + colorbrewer_sequential
        )

    if "cubehelix" in types:
        cubehelix = [
            "classic_16",
            "cubehelix1_16",
            "cubehelix2_16",
            "cubehelix3_16",
            "jim_special_16",
            "perceptual_rainbow_16",
            "purple_16",
            "red_16",
        ]
        cubehelix = [f"cubehelix.{c}" for c in cubehelix]
        palettes = palettes + cubehelix

    if "lightbartlein" in types:
        lightbartlein_diverging = [
            f"lightbartlein.diverging.{c}"
            for c in dir(palettable.lightbartlein.diverging)[:-19]
        ]
        lightbartlein_sequential = [
            f"lightbartlein.sequential.{c}"
            for c in dir(palettable.lightbartlein.sequential)[:-19]
        ]

        palettes = palettes + lightbartlein_diverging + lightbartlein_sequential

    if "matplotlib" in types:
        matplotlib_colors = [
            f"matplotlib.{c}" for c in dir(palettable.matplotlib)[:-16]
        ]
        palettes = palettes + matplotlib_colors

    if "mycarta" in types:
        mycarta = [f"mycarta.{c}" for c in dir(palettable.mycarta)[:-16]]
        palettes = palettes + mycarta

    if "scientific" in types:
        scientific_diverging = [
            f"scientific.diverging.{c}"
            for c in dir(palettable.scientific.diverging)[:-19]
        ]
        scientific_sequential = [
            f"scientific.sequential.{c}"
            for c in dir(palettable.scientific.sequential)[:-19]
        ]

        palettes = palettes + scientific_diverging + scientific_sequential

    if "tableau" in types:
        tableau = [f"tableau.{c}" for c in dir(palettable.tableau)[:-14]]
        palettes = palettes + tableau

    return palettes


def connect_postgis(
    database, host="localhost", user=None, password=None, port=5432, use_env_var=False
):
    """Connects to a PostGIS database.

    Args:
        database (str): Name of the database
        host (str, optional): Hosting server for the database. Defaults to "localhost".
        user (str, optional): User name to access the database. Defaults to None.
        password (str, optional): Password to access the database. Defaults to None.
        port (int, optional): Port number to connect to at the server host. Defaults to 5432.
        use_env_var (bool, optional): Whether to use environment variables. It set to True, user and password are treated as an environment variables with default values user="SQL_USER" and password="SQL_PASSWORD". Defaults to False.

    Raises:
        ValueError: If user is not specified.
        ValueError: If password is not specified.

    Returns:
        [type]: [description]
    """
    check_package(name="geopandas", URL="https://geopandas.org")
    check_package(
        name="sqlalchemy",
        URL="https://docs.sqlalchemy.org/en/14/intro.html#installation",
    )

    from sqlalchemy import create_engine

    if use_env_var:
        if user is not None:
            user = os.getenv(user)
        else:
            user = os.getenv("SQL_USER")

        if password is not None:
            password = os.getenv(password)
        else:
            password = os.getenv("SQL_PASSWORD")

        if user is None:
            raise ValueError("user is not specified.")
        if password is None:
            raise ValueError("password is not specified.")

    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(connection_string)

    return engine


def read_postgis(sql, con, geom_col="geom", crs=None, **kwargs):
    """Reads data from a PostGIS database and returns a GeoDataFrame.

    Args:
        sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
        con (sqlalchemy.engine.Engine): Active connection to the database to query.
        geom_col (str, optional): Column name to convert to shapely geometries. Defaults to "geom".
        crs (str | dict, optional): CRS to use for the returned GeoDataFrame; if not set, tries to determine CRS from the SRID associated with the first geometry in the database, and assigns that to all geometries. Defaults to None.

    Returns:
        [type]: [description]
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    import geopandas as gpd

    gdf = gpd.read_postgis(sql, con, geom_col, crs, **kwargs)
    return gdf


def postgis_to_ee(sql, con, geom_col="geom", crs=None, geodestic=False, **kwargs):
    """Reads data from a PostGIS database and returns a GeoDataFrame.

    Args:
        sql (str): SQL query to execute in selecting entries from database, or name of the table to read from the database.
        con (sqlalchemy.engine.Engine): Active connection to the database to query.
        geom_col (str, optional): Column name to convert to shapely geometries. Defaults to "geom".
        crs (str | dict, optional): CRS to use for the returned GeoDataFrame; if not set, tries to determine CRS from the SRID associated with the first geometry in the database, and assigns that to all geometries. Defaults to None.
        geodestic (bool, optional): Whether to use geodestic coordinates. Defaults to False.

    Returns:
        [type]: [description]
    """
    check_package(name="geopandas", URL="https://geopandas.org")

    gdf = read_postgis(sql, con, geom_col, crs=crs, **kwargs)
    fc = gdf_to_ee(gdf, geodesic=geodestic)
    return fc


def points_from_xy(data, x="longitude", y="latitude", z=None, crs=None, **kwargs):
    """Create a GeoPandas GeoDataFrame from a csv or Pandas DataFrame containing x, y, z values.

    Args:
        data (str | pd.DataFrame): A csv or Pandas DataFrame containing x, y, z values.
        x (str, optional): The column name for the x values. Defaults to "longitude".
        y (str, optional): The column name for the y values. Defaults to "latitude".
        z (str, optional): The column name for the z values. Defaults to None.
        crs (str | int, optional): The coordinate reference system for the GeoDataFrame. Defaults to None.

    Returns:
        geopandas.GeoDataFrame: A GeoPandas GeoDataFrame containing x, y, z values.
    """
    check_package(name="geopandas", URL="https://geopandas.org")
    import geopandas as gpd
    import pandas as pd

    if crs is None:
        crs = "epsg:4326"

    if isinstance(data, pd.DataFrame):
        df = data
    elif isinstance(data, str):
        if not data.startswith("http") and (not os.path.exists(data)):
            raise FileNotFoundError("The specified input csv does not exist.")
        else:
            df = pd.read_csv(data, **kwargs)
    else:
        raise TypeError("The data must be a pandas DataFrame or a csv file path.")

    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x], df[y], z=z, crs=crs))

    return gdf


def vector_centroids(ee_object):
    """Returns the centroids of an ee.FeatureCollection.

    Args:
        ee_object (ee.FeatureCollection): The ee.FeatureCollection to get the centroids of.

    Raises:
        TypeError: If the ee_object is not an ee.FeatureCollection.

    Returns:
        ee.FeatureCollection: The centroids of the ee_object.
    """
    if not isinstance(ee_object, ee.FeatureCollection):
        raise TypeError("The input must be an Earth Engine FeatureCollection.")

    centroids = ee_object.map(
        lambda f: ee.Feature(f.geometry().centroid(0.001), f.toDictionary())
    )

    centroids = centroids.map(
        lambda f: f.set(
            {
                "longitude": f.geometry().coordinates().get(0),
                "latitude": f.geometry().coordinates().get(1),
            }
        )
    )

    return centroids


def bbox_to_gdf(bbox, crs="EPSG:4326"):
    """Converts a bounding box to a GeoDataFrame.

    Args:
        bbox (tuple): A bounding box in the form of a tuple (minx, miny, maxx, maxy).
        crs (str, optional): The coordinate reference system of the bounding box to convert to. Defaults to "EPSG:4326".

    Returns:
        geopandas.GeoDataFrame: A GeoDataFrame containing the bounding box.
    """
    check_package(name="geopandas", URL="https://geopandas.org")
    from shapely.geometry import box
    from geopandas import GeoDataFrame

    minx, miny, maxx, maxy = bbox
    geometry = box(minx, miny, maxx, maxy)
    d = {"geometry": [geometry]}
    gdf = GeoDataFrame(d, crs="EPSG:4326")
    gdf.to_crs(crs=crs, inplace=True)
    return gdf


def check_dir(dir_path, make_dirs=True):
    """Checks if a directory exists and creates it if it does not.

    Args:
        dir_path ([str): The path to the directory.
        make_dirs (bool, optional): Whether to create the directory if it does not exist. Defaults to True.

    Raises:
        FileNotFoundError: If the directory could not be found.
        TypeError: If the input directory path is not a string.

    Returns:
        str: The path to the directory.
    """

    if isinstance(dir_path, str):
        if dir_path.startswith("~"):
            dir_path = os.path.expanduser(dir_path)
        else:
            dir_path = os.path.abspath(dir_path)

        if not os.path.exists(dir_path) and make_dirs:
            os.makedirs(dir_path)

        if os.path.exists(dir_path):
            return dir_path
        else:
            raise FileNotFoundError("The provided directory could not be found.")
    else:
        raise TypeError("The provided directory path must be a string.")


def check_file_path(file_path, make_dirs=True):
    """Gets the absolute file path.

    Args:
        file_path ([str): The path to the file.
        make_dirs (bool, optional): Whether to create the directory if it does not exist. Defaults to True.

    Raises:
        FileNotFoundError: If the directory could not be found.
        TypeError: If the input directory path is not a string.

    Returns:
        str: The absolute path to the file.
    """
    if isinstance(file_path, str):
        if file_path.startswith("~"):
            file_path = os.path.expanduser(file_path)
        else:
            file_path = os.path.abspath(file_path)

        file_dir = os.path.dirname(file_path)
        if not os.path.exists(file_dir) and make_dirs:
            os.makedirs(file_dir)

        return file_path

    else:
        raise TypeError("The provided file path must be a string.")


def image_to_cog(source, dst_path=None, profile="deflate", **kwargs):
    """Converts an image to a COG file.

    Args:
        source (str): A dataset path, URL or rasterio.io.DatasetReader object.
        dst_path (str, optional): An output dataset path or or PathLike object. Defaults to None.
        profile (str, optional): COG profile. More at https://cogeotiff.github.io/rio-cogeo/profile. Defaults to "deflate".

    Raises:
        ImportError: If rio-cogeo is not installed.
        FileNotFoundError: If the source file could not be found.
    """
    try:
        from rio_cogeo.cogeo import cog_translate
        from rio_cogeo.profiles import cog_profiles

    except ImportError:
        raise ImportError(
            "The rio-cogeo package is not installed. Please install it with `pip install rio-cogeo` or `conda install rio-cogeo -c conda-forge`."
        )

    if not source.startswith("http"):
        source = check_file_path(source)

        if not os.path.exists(source):
            raise FileNotFoundError("The provided input file could not be found.")

    if dst_path is None:
        if not source.startswith("http"):
            dst_path = os.path.splitext(source)[0] + "_cog.tif"
        else:
            dst_path = temp_file_path(extension=".tif")

    dst_path = check_file_path(dst_path)

    dst_profile = cog_profiles.get(profile)
    cog_translate(source, dst_path, dst_profile, **kwargs)


def cog_validate(source, verbose=False):
    """Validate Cloud Optimized Geotiff.

    Args:
        source (str): A dataset path or URL. Will be opened in "r" mode.
        verbose (bool, optional): Whether to print the output of the validation. Defaults to False.

    Raises:
        ImportError: If the rio-cogeo package is not installed.
        FileNotFoundError: If the provided file could not be found.

    Returns:
        tuple: A tuple containing the validation results (True is src_path is a valid COG, List of validation errors, and a list of validation warnings).
    """
    try:
        from rio_cogeo.cogeo import cog_validate, cog_info
    except ImportError:
        raise ImportError(
            "The rio-cogeo package is not installed. Please install it with `pip install rio-cogeo` or `conda install rio-cogeo -c conda-forge`."
        )

    if not source.startswith("http"):
        source = check_file_path(source)

        if not os.path.exists(source):
            raise FileNotFoundError("The provided input file could not be found.")

    if verbose:
        return cog_info(source)
    else:
        return cog_validate(source)
