"""This module contains some common functions for both folium and ipyleaflet to interact with the Earth Engine Python API.
"""

import csv
import os
import subprocess
import tarfile
import urllib.request
import zipfile
from collections import deque
from pathlib import Path
import ee


#################
# Data Download #
#################
def download_from_url(url, out_file_name=None, out_dir='.', unzip=True):
    """Download a file from a URL (e.g., https://github.com/giswqs/whitebox/raw/master/examples/testdata.zip)

    Args:
        url (str): The HTTP URL to download.
        out_file_name (str, optional): The output file name to use. Defaults to None.
        out_dir (str, optional): The output directory to use. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the downloaded file if it is a zip file. Defaults to True.
    """
    in_file_name = os.path.basename(url)

    if out_file_name is None:
        out_file_name = in_file_name
    out_file_path = os.path.join(os.path.abspath(out_dir), out_file_name)

    print('Downloading {} ...'.format(url))

    try:
        urllib.request.urlretrieve(url, out_file_path)
    except:
        print("The URL is invalid. Please double check the URL.")
        return

    final_path = out_file_path

    if unzip:
        # if it is a zip file
        if '.zip' in out_file_name:
            print("Unzipping {} ...".format(out_file_name))
            with zipfile.ZipFile(out_file_path, "r") as zip_ref:
                zip_ref.extractall(out_dir)
            final_path = os.path.join(os.path.abspath(
                out_dir), out_file_name.replace('.zip', ''))

        # if it is a tar file
        if '.tar' in out_file_name:
            print("Unzipping {} ...".format(out_file_name))
            with tarfile.open(out_file_path, "r") as tar_ref:
                tar_ref.extractall(out_dir)
            final_path = os.path.join(os.path.abspath(
                out_dir), out_file_name.replace('.tart', ''))

    print('Data downloaded to: {}'.format(final_path))


def download_from_gdrive(gfile_url, file_name, out_dir='.', unzip=True):
    """Download a file shared via Google Drive 
       (e.g., https://drive.google.com/file/d/18SUo_HcDGltuWYZs1s7PpOmOq_FvFn04/view?usp=sharing)

    Args:
        gfile_url (str): The Google Drive shared file URL
        file_name (str): The output file name to use.
        out_dir (str, optional): The output directory. Defaults to '.'.
        unzip (bool, optional): Whether to unzip the output file if it is a zip file. Defaults to True.
    """
    try:
        from google_drive_downloader import GoogleDriveDownloader as gdd
    except ImportError:
        print('GoogleDriveDownloader package not installed. Installing ...')
        subprocess.check_call(
            ["python", '-m', 'pip', 'install', 'googledrivedownloader'])
        from google_drive_downloader import GoogleDriveDownloader as gdd

    file_id = gfile_url.split('/')[5]
    print('Google Drive file id: {}'.format(file_id))

    dest_path = os.path.join(out_dir, file_name)
    gdd.download_file_from_google_drive(file_id, dest_path, True, unzip)


###################
# Data Conversion #
###################

def xy_to_points(in_csv, latitude='latitude', longitude='longitude'):
    """Converts a csv containing points (latitude and longitude) into an ee.FeatureCollection.

    Args:
        in_csv (str): File path or HTTP URL to the input csv file. For example, https://raw.githubusercontent.com/giswqs/data/main/world/world_cities.csv
        latitude (str, optional): Column name for the latitude column. Defaults to 'latitude'.
        longitude (str, optional): Column name for the longitude column. Defaults to 'longitude'.

    Returns:
        ee.FeatureCollection: The ee.FeatureCollection containing the points converted from the input csv.
    """

    if in_csv.startswith('http') and in_csv.endswith('.csv'):
        out_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        out_name = os.path.basename(in_csv)
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        download_from_url(in_csv, out_dir=out_dir)
        in_csv = os.path.join(out_dir, out_name)

    in_csv = os.path.abspath(in_csv)
    if not os.path.exists(in_csv):
        raise Exception('The provided csv file does not exist.')

    points = []
    with open(in_csv) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            lat, lon = float(row[latitude]), float(row[longitude])
            points.append([lon, lat])

    ee_list = ee.List(points)
    ee_points = ee_list.map(lambda xy: ee.Feature(ee.Geometry.Point(xy)))
    return ee.FeatureCollection(ee_points)


def csv_to_shp(in_csv, out_shp, latitude='latitude', longitude='longitude'):
    """Converts a csv file containing points (latitude, longitude) into a shapefile.

    Args:
        in_csv (str): File path or HTTP URL to the input csv file. For example, https://raw.githubusercontent.com/giswqs/data/main/world/world_cities.csv
        out_shp (str): File path to the output shapefile.
        latitude (str, optional): Column name for the latitude column. Defaults to 'latitude'.
        longitude (str, optional): Column name for the longitude column. Defaults to 'longitude'.

    """
    import whitebox
    
    if in_csv.startswith('http') and in_csv.endswith('.csv'):
        out_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        out_name = os.path.basename(in_csv)
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        download_from_url(in_csv, out_dir=out_dir)
        in_csv = os.path.join(out_dir, out_name)

    wbt = whitebox.WhiteboxTools()
    in_csv = os.path.abspath(in_csv)
    out_shp = os.path.abspath(out_shp)

    if not os.path.exists(in_csv):
        raise Exception('The provided csv file does not exist.')

    with open(in_csv) as csv_file:
        reader = csv.DictReader(csv_file)
        fields = reader.fieldnames
        xfield = fields.index(longitude)
        yfield  = fields.index(latitude)

    wbt.csv_points_to_vector(in_csv, out_shp, xfield=xfield, yfield=yfield, epsg=4326)
    