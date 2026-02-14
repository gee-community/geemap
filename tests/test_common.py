"""Tests for the common module."""

import base64
import builtins
import io
import math
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

import ee
from geemap import colormaps
from geemap import common
import ipywidgets
from PIL import Image
import psutil
import requests

from tests import fake_ee


class CommonTest(unittest.TestCase):

    def _create_zip_with_tif(self, tif_name: str, content: bytes):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(tif_name, content)
        return zip_buffer.getvalue()

    @mock.patch.object(requests, "get")
    def test_ee_export_image_unzip(self, mock_get):
        """Tests ee_export_image with unzip=True."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        zip_content = self._create_zip_with_tif("test.tif", b"tif content")
        mock_response.iter_content.return_value = [zip_content]
        mock_get.return_value = mock_response

        image_mock = mock.MagicMock(spec=ee.Image)
        image_mock.getDownloadURL.return_value = "http://example.com/image.zip"
        image_mock.geometry.return_value = fake_ee.Geometry()

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = str(pathlib.Path(tmpdir) / "test.tif")
            common.ee_export_image(image_mock, filename, unzip=True, verbose=False)

            image_mock.getDownloadURL.assert_called_once()
            mock_get.assert_called_once_with(
                "http://example.com/image.zip", stream=True, timeout=300, proxies=None
            )
            filename_path = pathlib.Path(filename)
            self.assertTrue(filename_path.exists())
            with open(filename_path, "rb") as f:
                self.assertEqual(f.read(), b"tif content")
            filename_zip_path = pathlib.Path(tmpdir) / "test.zip"
            self.assertFalse(filename_zip_path.exists())

    @mock.patch.object(requests, "get")
    def test_ee_export_image_no_unzip(self, mock_get):
        """Tests ee_export_image with unzip=False."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        zip_content = self._create_zip_with_tif("test.tif", b"tif content")
        mock_response.iter_content.return_value = [zip_content]
        mock_get.return_value = mock_response

        image_mock = mock.MagicMock(spec=ee.Image)
        image_mock.getDownloadURL.return_value = "http://example.com/image.zip"
        image_mock.geometry.return_value = fake_ee.Geometry()

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = str(pathlib.Path(tmpdir) / "test.tif")
            common.ee_export_image(image_mock, filename, unzip=False, verbose=False)

            image_mock.getDownloadURL.assert_called_once()
            mock_get.assert_called_once_with(
                "http://example.com/image.zip", stream=True, timeout=300, proxies=None
            )
            filename_path = pathlib.Path(filename)
            filename_zip_path = pathlib.Path(tmpdir) / "test.zip"
            self.assertTrue(filename_zip_path.exists())
            with open(filename_zip_path, "rb") as f:
                self.assertEqual(f.read(), zip_content)
            self.assertFalse(filename_path.exists())

    # TODO: test_ee_export_image_collection
    # TODO: test_ee_export_image_to_drive
    # TODO: test_ee_export_image_to_asset
    # TODO: test_ee_export_image_to_cloud_storage
    # TODO: test_ee_export_image_collection_to_drive
    # TODO: test_ee_export_image_collection_to_asset
    # TODO: test_ee_export_image_collection_to_cloud_storage
    # TODO: test_ee_export_geojson
    # TODO: test_ee_export_vector
    # TODO: test_ee_export_vector_to_drive
    # TODO: test_ee_export_vector_to_asset
    # TODO: test_ee_export_vector_to_cloud_storage
    # TODO: test_ee_export_vector_to_feature_view
    # TODO: test_ee_export_video_to_drive
    # TODO: test_ee_export_video_to_cloud_storage
    # TODO: test_ee_export_map_to_cloud_storage
    # TODO: test_TitilerEndpoint
    # TODO: test_PlanetaryComputerEndpoint

    def test_check_titiler_endpoint(self):
        """Tests check_titiler_endpoint."""
        self.assertEqual(
            common.check_titiler_endpoint(None),
            "https://giswqs-titiler-endpoint.hf.space",
        )
        self.assertEqual(common.check_titiler_endpoint("some_url"), "some_url")
        self.assertIsInstance(
            common.check_titiler_endpoint("pc"),
            common.PlanetaryComputerEndpoint,
        )
        self.assertIsInstance(
            common.check_titiler_endpoint("planetary-computer"),
            common.PlanetaryComputerEndpoint,
        )
        with mock.patch.dict(os.environ, {"TITILER_ENDPOINT": "planetary-computer"}):
            self.assertIsInstance(
                common.check_titiler_endpoint(None),
                common.PlanetaryComputerEndpoint,
            )
        with mock.patch.dict(os.environ, {"TITILER_ENDPOINT": "some_other_url"}):
            self.assertEqual(common.check_titiler_endpoint(None), "some_other_url")

    @mock.patch.object(requests, "get")
    def test_set_proxy(self, mock_get):
        """Tests set_proxy."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        common.set_proxy(port=8080, ip="192.168.1.1")
        self.assertEqual(os.environ["HTTP_PROXY"], "http://192.168.1.1:8080")
        self.assertEqual(os.environ["HTTPS_PROXY"], "http://192.168.1.1:8080")
        mock_get.assert_called_with("https://earthengine.google.com/", timeout=300)

        # Test ip without http prefix.
        common.set_proxy(port=8080, ip="192.168.1.2")
        self.assertEqual(os.environ["HTTP_PROXY"], "http://192.168.1.2:8080")
        self.assertEqual(os.environ["HTTPS_PROXY"], "http://192.168.1.2:8080")

        # Test default values.
        common.set_proxy()
        self.assertEqual(os.environ["HTTP_PROXY"], "http://127.0.0.1:1080")
        self.assertEqual(os.environ["HTTPS_PROXY"], "http://127.0.0.1:1080")

        # Test connection failure.
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            common.set_proxy()
            self.assertIn("Failed to connect", mock_stdout.getvalue())

        del os.environ["HTTP_PROXY"]
        del os.environ["HTTPS_PROXY"]

    @mock.patch.object(os.path, "exists")
    def test_is_drive_mounted(self, mock_exists):
        """Tests is_drive_mounted."""
        mock_exists.return_value = True
        self.assertTrue(common.is_drive_mounted())
        mock_exists.assert_called_with("/content/drive/My Drive")

        mock_exists.return_value = False
        self.assertFalse(common.is_drive_mounted())
        mock_exists.assert_called_with("/content/drive/My Drive")

    @mock.patch.object(os.path, "exists")
    def test_credentials_in_drive(self, mock_exists):
        """Tests credentials_in_drive."""
        mock_exists.return_value = True
        self.assertTrue(common.credentials_in_drive())
        mock_exists.assert_called_with(
            "/content/drive/My Drive/.config/earthengine/credentials"
        )

        mock_exists.return_value = False
        self.assertFalse(common.credentials_in_drive())
        mock_exists.assert_called_with(
            "/content/drive/My Drive/.config/earthengine/credentials"
        )

    @mock.patch.object(os.path, "exists")
    def test_credentials_in_colab(self, mock_exists):
        """Tests credentials_in_colab."""
        mock_exists.return_value = True
        self.assertTrue(common.credentials_in_colab())
        mock_exists.assert_called_with("/root/.config/earthengine/credentials")

        mock_exists.return_value = False
        self.assertFalse(common.credentials_in_colab())
        mock_exists.assert_called_with("/root/.config/earthengine/credentials")

    @mock.patch.object(shutil, "copyfile")
    @mock.patch.object(os, "makedirs")
    @mock.patch.object(os.path, "exists")
    def test_copy_credentials_to_drive_exists(
        self, mock_exists, mock_makedirs, mock_copyfile
    ):
        """Tests copy_credentials_to_drive."""
        src = "/root/.config/earthengine/credentials"
        dst = "/content/drive/My Drive/.config/earthengine/credentials"
        dst_dir = "/content/drive/My Drive/.config/earthengine"

        # Case 1: Destination directory exists.
        mock_exists.return_value = True
        common.copy_credentials_to_drive()
        mock_exists.assert_called_with(dst_dir)
        mock_makedirs.assert_not_called()
        mock_copyfile.assert_called_with(src, dst)

    @mock.patch.object(shutil, "copyfile")
    @mock.patch.object(os, "makedirs")
    @mock.patch.object(os.path, "exists")
    def test_copy_credentials_to_drive_does_not_exist(
        self, mock_exists, mock_makedirs, mock_copyfile
    ):
        """Tests copy_credentials_to_drive."""
        src = "/root/.config/earthengine/credentials"
        dst = "/content/drive/My Drive/.config/earthengine/credentials"
        dst_dir = "/content/drive/My Drive/.config/earthengine"

        # Case 2: Destination directory does not exist.
        mock_exists.return_value = False
        common.copy_credentials_to_drive()
        mock_exists.assert_called_with(dst_dir)
        mock_makedirs.assert_called_once_with(dst_dir)
        mock_copyfile.assert_called_with(src, dst)

    @mock.patch.object(shutil, "copyfile")
    @mock.patch.object(os, "makedirs")
    @mock.patch.object(os.path, "exists")
    def test_copy_credentials_to_colab_exists(
        self, mock_exists, mock_makedirs, mock_copyfile
    ):
        """Tests copy_credentials_to_colab."""
        src = "/content/drive/My Drive/.config/earthengine/credentials"
        dst = "/root/.config/earthengine/credentials"
        dst_dir = "/root/.config/earthengine"

        # Case 1: Destination directory exists.
        mock_exists.return_value = True
        common.copy_credentials_to_colab()
        mock_exists.assert_called_with(dst_dir)
        mock_makedirs.assert_not_called()
        mock_copyfile.assert_called_with(src, dst)

    @mock.patch.object(shutil, "copyfile")
    @mock.patch.object(os, "makedirs")
    @mock.patch.object(os.path, "exists")
    def test_copy_credentials_to_colab_does_not_exist(
        self, mock_exists, mock_makedirs, mock_copyfile
    ):
        """Tests copy_credentials_to_colab."""
        src = "/content/drive/My Drive/.config/earthengine/credentials"
        dst = "/root/.config/earthengine/credentials"
        dst_dir = "/root/.config/earthengine"

        # Case 2: Destination directory does not exist.
        mock_exists.return_value = False
        common.copy_credentials_to_colab()
        mock_exists.assert_called_with(dst_dir)
        mock_makedirs.assert_called_once_with(dst_dir)
        mock_copyfile.assert_called_with(src, dst)

    # TODO: test_check_install
    # TODO: test_update_package
    # TODO: test_check_package
    # TODO: test_install_package
    # TODO: test_clone_repo
    # TODO: test_install_from_github
    # TODO: test_check_git_install
    # TODO: test_clone_github_repo
    # TODO: test_clone_google_repo
    # TODO: test_open_github
    # TODO: test_open_youtube
    # TODO: test_is_tool
    # TODO: test_open_image_from_url
    # TODO: test_show_image
    # TODO: test_show_html
    # TODO: test_has_transparency
    # TODO: test_upload_to_imgur
    # TODO: test_system_fonts
    # TODO: test_download_from_url
    # TODO: test_download_from_gdrive
    # TODO: test_create_download_link
    # TODO: test_edit_download_html
    # TODO: test_xy_to_points
    # TODO: test_csv_points_to_shp
    # TODO: test_csv_to_shp
    # TODO: test_csv_to_geojson
    # TODO: test_df_to_geojson
    # TODO: test_csv_to_ee
    # TODO: test_csv_to_gdf
    # TODO: test_csv_to_vector
    # TODO: test_ee_to_geojson
    # TODO: test_ee_to_bbox
    # TODO: test_shp_to_geojson
    # TODO: test_shp_to_ee
    # TODO: test_filter_polygons
    # TODO: test_ee_to_shp
    # TODO: test_ee_to_csv
    # TODO: test_dict_to_csv
    # TODO: test_get_image_thumbnail
    # TODO: test_get_image_collection_thumbnails
    # TODO: test_netcdf_to_ee
    # TODO: test_numpy_to_ee
    # TODO: test_ee_to_numpy
    # TODO: test_ee_to_xarray
    # TODO: test_download_ee_video
    # TODO: test_screen_capture
    # TODO: test_api_docs
    # TODO: test_show_youtube
    # TODO: test_create_colorbar
    # TODO: test_save_colorbar
    # TODO: test_minimum_bounding_box
    # TODO: test_geocode
    # TODO: test_is_latlon_valid
    # TODO: test_latlon_from_text
    # TODO: test_search_ee_data
    # TODO: test_ee_data_thumbnail
    # TODO: test_ee_data_html
    # TODO: test_ee_api_to_csv
    # TODO: test_read_api_csv
    # TODO: test_ee_function_tree
    # TODO: test_build_api_tree
    # TODO: test_search_api_tree
    # TODO: test_ee_search
    # TODO: test_ee_user_id
    # TODO: test_build_asset_tree
    # TODO: test_build_repo_tree
    # TODO: test_file_browser
    # TODO: test_date_sequence
    # TODO: test_legend_from_ee
    # TODO: test_vis_to_qml
    # TODO: test_create_nlcd_qml
    # TODO: test_load_GeoTIFF
    # TODO: test_load_GeoTIFFs
    # TODO: test_cog_tile
    # TODO: test_cog_mosaic
    # TODO: test_cog_mosaic_from_file
    # TODO: test_cog_bounds
    # TODO: test_cog_center
    # TODO: test_cog_bands
    # TODO: test_cog_stats
    # TODO: test_cog_info
    # TODO: test_cog_pixel_value
    # TODO: test_stac_tile
    # TODO: test_stac_bounds
    # TODO: test_stac_center
    # TODO: test_stac_bands
    # TODO: test_stac_stats
    # TODO: test_stac_info
    # TODO: test_stac_info_geojson
    # TODO: test_stac_assets
    # TODO: test_stac_pixel_value
    # TODO: test_local_tile_pixel_value
    # TODO: test_local_tile_vmin_vmax
    # TODO: test_local_tile_bands
    def test_bbox_to_geojson(self):
        """Tests bbox_to_geojson."""
        bounds = [-10, -20, 10, 20]
        expected_geojson = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-10, 20],
                        [-10, -20],
                        [10, -20],
                        [10, 20],
                        [-10, 20],
                    ]
                ],
            },
            "type": "Feature",
        }
        self.assertEqual(common.bbox_to_geojson(bounds), expected_geojson)
        self.assertEqual(common.bbox_to_geojson(tuple(bounds)), expected_geojson)

    def test_coords_to_geojson(self):
        """Tests coords_to_geojson."""
        coords = [[-10, -20, 10, 20], [-100, -80, 100, 80]]
        expected_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-10, 20],
                                [-10, -20],
                                [10, -20],
                                [10, 20],
                                [-10, 20],
                            ]
                        ],
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-100, 80],
                                [-100, -80],
                                [100, -80],
                                [100, 80],
                                [-100, 80],
                            ]
                        ],
                    },
                    "type": "Feature",
                },
            ],
        }
        self.assertEqual(common.coords_to_geojson(coords), expected_geojson)

    def test_explode(self):
        """Tests explode."""
        self.assertEqual(list(common.explode([1.0, 2.0])), [[1.0, 2.0]])
        self.assertEqual(
            list(common.explode([[1.0, 2.0], [3.0, 4.0]])), [[1.0, 2.0], [3.0, 4.0]]
        )
        self.assertEqual(
            list(common.explode([[[1.0, 2.0], [3.0, 4.0]]])), [[1.0, 2.0], [3.0, 4.0]]
        )

    # TODO: test_get_bounds
    # TODO: test_get_center
    # TODO: test_image_props
    # TODO: test_image_stats
    # TODO: test_adjust_longitude
    # TODO: test_zonal_stats
    # TODO: test_zonal_stats_by_group
    # TODO: test_vec_area
    # TODO: test_vec_area_km2
    # TODO: test_vec_area_mi2
    # TODO: test_vec_area_ha
    # TODO: test_remove_geometry
    # TODO: test_image_cell_size
    # TODO: test_image_scale
    # TODO: test_image_band_names
    # TODO: test_image_date
    # TODO: test_image_dates
    # TODO: test_image_area
    # TODO: test_image_area_by_group
    # TODO: test_image_max_value
    # TODO: test_image_min_value
    # TODO: test_image_mean_value
    # TODO: test_image_std_value
    # TODO: test_image_sum_value
    # TODO: test_image_value_list
    # TODO: test_image_histogram
    # TODO: test_image_stats_by_zone
    # TODO: test_latitude_grid
    # TODO: test_longitude_grid
    # TODO: test_latlon_grid
    # TODO: test_fishnet
    # TODO: test_extract_values_to_points
    # TODO: test_extract_timeseries_to_point
    # TODO: test_image_reclassify
    # TODO: test_image_smoothing
    # TODO: test_rename_bands
    # TODO: test_bands_to_image_collection
    # TODO: test_find_landsat_by_path_row
    # TODO: test_str_to_num
    # TODO: test_array_sum
    # TODO: test_array_mean
    # TODO: test_get_annual_NAIP
    # TODO: test_get_all_NAIP
    # TODO: test_annual_NAIP
    # TODO: test_find_NAIP
    # TODO: test_filter_NWI
    # TODO: test_filter_HUC08
    # TODO: test_filter_HUC10
    # TODO: test_find_HUC08
    # TODO: test_find_HUC10
    # TODO: test_find_NWI
    # TODO: test_nwi_add_color
    # TODO: test_nwi_rename
    # TODO: test_summarize_by_group
    # TODO: test_summary_stats
    # TODO: test_column_stats
    # TODO: test_ee_num_round

    def test_num_round(self):
        self.assertEqual(common.num_round(1.2345), 1.23)
        self.assertEqual(common.num_round(1.2345, 3), 1.234)
        self.assertEqual(common.num_round(-1.2, 3), -1.2)

    # TODO: test_png_to_gif
    # TODO: test_jpg_to_gif
    # TODO: test_vector_styling
    # TODO: test_is_GCS
    # TODO: test_kml_to_shp
    # TODO: test_kml_to_geojson
    # TODO: test_kml_to_ee
    # TODO: test_kmz_to_ee
    # TODO: test_csv_to_df
    # TODO: test_ee_to_df
    # TODO: test_shp_to_gdf
    # TODO: test_ee_to_gdf

    def test_delete_shp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shp_path = os.path.join(tmpdir, "test.shp")
            extensions = [".shp", ".shx", ".dbf", ".prj"]
            for ext in extensions:
                with open(os.path.join(tmpdir, "test" + ext), "w") as f:
                    f.write("test")

            common.delete_shp(shp_path)

            for ext in extensions:
                self.assertFalse(os.path.exists(os.path.join(tmpdir, "test" + ext)))

    # TODO: test_df_to_ee
    # TODO: test_gdf_to_ee
    # TODO: test_vector_to_geojson
    # TODO: test_vector_to_ee
    # TODO: test_extract_pixel_values

    def test_list_vars(self):
        """Tests list_vars function."""
        common.list_vars_test_int = 1
        common.list_vars_test_str = "test"
        vars_all = common.list_vars()
        vars_int = common.list_vars(var_type=int)
        vars_str = common.list_vars(var_type=str)
        del common.list_vars_test_int
        del common.list_vars_test_str

        self.assertIn("list_vars_test_int", vars_all)
        self.assertIn("list_vars_test_str", vars_all)
        self.assertIn("list_vars_test_int", vars_int)
        self.assertNotIn("list_vars_test_str", vars_int)
        self.assertIn("list_vars_test_str", vars_str)
        self.assertNotIn("list_vars_test_int", vars_str)

    # TODO: test_extract_transect
    # TODO: test_random_sampling
    # TODO: test_osm_to_gdf
    # TODO: test_osm_to_ee
    # TODO: test_osm_to_geojson
    # TODO: test_planet_monthly_tropical
    # TODO: test_planet_biannual_tropical
    # TODO: test_planet_catalog_tropical
    # TODO: test_planet_monthly_tiles_tropical
    # TODO: test_planet_biannual_tiles_tropical
    # TODO: test_planet_tiles_tropical
    # TODO: test_planet_monthly
    # TODO: test_planet_quarterly
    # TODO: test_planet_catalog
    # TODO: test_planet_monthly_tiles
    # TODO: test_planet_quarterly_tiles
    # TODO: test_planet_tiles
    # TODO: test_planet_by_quarter
    # TODO: test_planet_by_month
    # TODO: test_planet_tile_by_quarter
    # TODO: test_planet_tile_by_month
    # TODO: test_get_current_latlon
    # TODO: test_get_census_dict
    # TODO: test_search_xyz_services
    # TODO: test_search_qms
    # TODO: test_get_wms_layers
    # TODO: test_read_file_from_url
    # TODO: test_create_download_button
    # TODO: test_gdf_to_geojson
    # TODO: test_get_temp_dir
    # TODO: test_create_contours
    # TODO: test_get_local_tile_layer
    # TODO: test_get_palettable
    # TODO: test_connect_postgis
    # TODO: test_read_postgis
    # TODO: test_postgis_to_ee
    # TODO: test_points_from_xy
    # TODO: test_vector_centroids
    # TODO: test_bbox_to_gdf

    def test_check_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with make_dirs=True.
            dir_path_1 = os.path.join(tmpdir, "subdir1")
            abs_path_1 = common.check_dir(dir_path_1, make_dirs=True)
            self.assertTrue(os.path.exists(abs_path_1))
            self.assertEqual(abs_path_1, os.path.abspath(dir_path_1))

            # Test with make_dirs=False and dir does not exist.
            dir_path_2 = os.path.join(tmpdir, "subdir2")
            with self.assertRaises(FileNotFoundError):
                common.check_dir(dir_path_2, make_dirs=False)

            # Test with make_dirs=False and dir exists.
            os.makedirs(dir_path_2)
            abs_path_2 = common.check_dir(dir_path_2, make_dirs=False)
            self.assertTrue(os.path.exists(abs_path_2))
            self.assertEqual(abs_path_2, os.path.abspath(dir_path_2))

            # Test with invalid type.
            with self.assertRaises(TypeError):
                common.check_dir(123)  # pytype: disable=wrong-arg-types

    def test_check_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with make_dirs=True.
            file_path_1 = os.path.join(tmpdir, "subdir1", "file1.txt")
            abs_path_1 = common.check_file_path(file_path_1, make_dirs=True)
            self.assertTrue(os.path.exists(os.path.dirname(abs_path_1)))
            self.assertEqual(abs_path_1, os.path.abspath(file_path_1))

            # Test with make_dirs=False.
            file_path_2 = os.path.join(tmpdir, "subdir2", "file2.txt")
            abs_path_2 = common.check_file_path(file_path_2, make_dirs=False)
            self.assertFalse(os.path.exists(os.path.dirname(abs_path_2)))
            self.assertEqual(abs_path_2, os.path.abspath(file_path_2))

            # Test with home directory character ~.
            file_path_3 = "~/some_dir/file3.txt"
            abs_path_3 = common.check_file_path(file_path_3, make_dirs=False)
            self.assertEqual(
                abs_path_3, os.path.abspath(os.path.expanduser(file_path_3))
            )

            # Test with invalid type.
            with self.assertRaises(TypeError):
                common.check_file_path(123)  # pytype: disable=wrong-arg-types

    # TODO: test_image_to_cog
    # TODO: test_cog_validate
    # TODO: test_gdf_to_df
    # TODO: test_geojson_to_df
    # TODO: test_ee_join_table
    # TODO: test_gdf_bounds
    # TODO: test_gdf_centroid
    # TODO: test_gdf_geom_type
    # TODO: test_image_to_numpy
    # TODO: test_numpy_to_cog
    # TODO: test_view_lidar
    # TODO: test_read_lidar
    # TODO: test_convert_lidar
    # TODO: test_write_lidar
    # TODO: test_download_folder
    # TODO: test_blend
    # TODO: test_clip_image
    # TODO: test_netcdf_to_tif
    # TODO: test_read_netcdf
    # TODO: test_netcdf_tile_layer
    # TODO: test_classify
    # TODO: test_image_count
    # TODO: test_dynamic_world
    # TODO: test_dynamic_world_s2
    # TODO: test_download_ee_image
    # TODO: test_download_ee_image_tiles
    # TODO: test_download_ee_image_tiles_parallel
    # TODO: test_download_ee_image_collection

    def test_get_palette_colors(self):
        # Test with n_class.
        colors = common.get_palette_colors("viridis", n_class=5)
        self.assertEqual(len(colors), 5)
        self.assertTrue(all(isinstance(c, str) and len(c) == 6 for c in colors))
        self.assertEqual(colors, ["440154", "3b528b", "21918c", "5ec962", "fde725"])

        # Test with hashtag=True.
        colors_hashtag = common.get_palette_colors("viridis", 5, hashtag=True)
        self.assertTrue(all(c.startswith("#") for c in colors_hashtag))
        self.assertEqual(
            colors_hashtag, ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"]
        )

        # Test with no n_class (should default to a reasonable number, e.g., 256 for continuous).
        colors_default = common.get_palette_colors("viridis")
        self.assertGreater(len(colors_default), 1)
        self.assertTrue(all(isinstance(c, str) and len(c) == 6 for c in colors_default))

        # Test invalid cmap name.
        with self.assertRaises(ValueError):
            common.get_palette_colors("invalid_cmap_name")

    # TODO: test_plot_raster
    # TODO: test_plot_raster_3d

    @mock.patch("geemap.common.IFrame")
    @mock.patch("geemap.common.display")
    def test_display_html(self, mock_display, mock_iframe):
        mock_iframe.return_value = "iframe_object"
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as fp:
            html_file = fp.name
        try:
            common.display_html(html_file, width=800, height=400)
            mock_iframe.assert_called_once_with(src=html_file, width=800, height=400)
            mock_display.assert_called_once_with(mock_iframe.return_value)
        finally:
            os.remove(html_file)

        with self.assertRaisesRegex(ValueError, "is not a valid file path"):
            common.display_html("non_existent_file.html")

    # TODO: test_bbox_coords
    # TODO: test_requireJS
    # TODO: test_setupJS
    # TODO: test_change_require
    # TODO: test_ee_vector_style

    @mock.patch("geemap.common.requests.head")
    def test_get_direct_url(self, mock_head):
        mock_response = mock.Mock()
        mock_response.url = "https://example.com/direct_url"
        mock_head.return_value = mock_response

        # Test with a URL that redirects.
        self.assertEqual(
            common.get_direct_url("https://example.com/redirect"),
            "https://example.com/direct_url",
        )
        mock_head.assert_called_with(
            "https://example.com/redirect", allow_redirects=True
        )

        # Test with a direct URL.
        self.assertEqual(
            common.get_direct_url("https://example.com/direct_url"),
            "https://example.com/direct_url",
        )
        mock_head.assert_called_with(
            "https://example.com/direct_url", allow_redirects=True
        )

        # Test with non-http URL.
        with self.assertRaisesRegex(ValueError, "url must start with http."):
            common.get_direct_url("ftp://example.com/file")

        # Test with non-string URL.
        with self.assertRaisesRegex(ValueError, "url must be a string."):
            common.get_direct_url(123)  # pytype: disable=wrong-arg-types

    # TODO: test_add_crs
    # TODO: test_jrc_hist_monthly_history
    # TODO: test_html_to_streamlit
    # TODO: test_image_convolution
    # TODO: test_download_ned
    # TODO: test_mosaic
    # TODO: test_reproject
    # TODO: test_download_3dep_lidar

    @mock.patch.dict(os.environ, {"USE_MKDOCS": "true"})
    def test_use_mkdocs_true(self):
        self.assertTrue(common.use_mkdocs())

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_use_mkdocs_false(self):
        self.assertFalse(common.use_mkdocs())

    # TODO: test_create_legend
    # TODO: test_is_arcpy
    # TODO: test_arc_active_map
    # TODO: test_arc_active_view
    # TODO: test_arc_add_layer
    # TODO: test_arc_zoom_to_extent
    # TODO: test_get_current_year

    def test_html_to_gradio(self):
        html_list = [
            "<!DOCTYPE html>",
            "<html>",
            "<body>",
            "    <script>",
            '        L.tileLayer("url", {',
            '            "attribution": "..."',
            "        }).addTo(map);",
            '       function(e) { console.log("foo"); }',
            '       "should be kept";',
            "    </script>",
            "</body>",
            "</html>",
        ]
        gradio_html = common.html_to_gradio(html_list, width="800px", height="400px")
        self.assertIn('<iframe style="width: 800px; height: 400px"', gradio_html)
        self.assertNotIn('function(e) { console.log("foo"); }', gradio_html)
        self.assertIn('"should be kept";', gradio_html)

    # TODO: test_image_check
    # TODO: test_image_client
    # TODO: test_image_center
    # TODO: test_image_bounds
    # TODO: test_image_metadata
    # TODO: test_image_bandcount
    # TODO: test_image_size
    # TODO: test_image_projection
    # TODO: test_image_set_crs
    # TODO: test_image_geotransform
    # TODO: test_image_resolution

    def test_find_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = pathlib.Path(tmpdir)
            f1 = dir_path / "file1.txt"
            f2 = dir_path / "file2.csv"
            f1.touch()
            f2.touch()
            subdir = dir_path / "subdir"
            subdir.mkdir()
            f3 = subdir / "file3.txt"
            f4 = subdir / "file4.py"
            f3.touch()
            f4.touch()

            # Test recursive search, full path, no extension.
            result = common.find_files(tmpdir, fullpath=True, recursive=True)
            expected = [str(f1), str(f2), str(f3), str(f4)]
            self.assertCountEqual(result, expected)

            # Test recursive search, full path, with extension "txt".
            result = common.find_files(
                tmpdir, ext=".txt", fullpath=True, recursive=True
            )
            expected = [str(f1), str(f3)]
            self.assertCountEqual(result, expected)

            result = common.find_files(tmpdir, ext="txt", fullpath=True, recursive=True)
            expected = [str(f1), str(f3)]
            self.assertCountEqual(result, expected)

            # Test non-recursive search, full path, with extension "txt".
            result = common.find_files(
                tmpdir, ext="txt", fullpath=True, recursive=False
            )
            expected = [str(f1)]
            self.assertCountEqual(result, expected)

            # Test recursive search, no full path, with extension "txt".
            result = common.find_files(
                tmpdir, ext="txt", fullpath=False, recursive=True
            )
            expected = ["file1.txt", "file3.txt"]
            self.assertCountEqual(result, expected)

            # Test non-recursive search, no full path, no extension.
            result = common.find_files(tmpdir, fullpath=False, recursive=False)
            expected = ["file1.txt", "file2.csv"]
            self.assertCountEqual(result, expected)

    def test_zoom_level_resolution(self):
        self.assertAlmostEqual(
            common.zoom_level_resolution(zoom=0, latitude=0), 156543.04, places=4
        )
        self.assertAlmostEqual(
            common.zoom_level_resolution(zoom=10, latitude=0), 152.8740625, places=4
        )
        self.assertAlmostEqual(
            common.zoom_level_resolution(zoom=10, latitude=math.pi / 3),
            76.43703125,
            places=4,
        )
        self.assertAlmostEqual(
            common.zoom_level_resolution(zoom=10, latitude=-math.pi / 3),
            76.43703125,
            places=4,
        )

    def test_lnglat_to_meters(self):
        x, y = common.lnglat_to_meters(longitude=0, latitude=0)
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, 0)

        x, y = common.lnglat_to_meters(longitude=1, latitude=2)
        self.assertAlmostEqual(x, 111319.4908, places=4)
        self.assertAlmostEqual(y, 222684.2085, places=4)

        x, y = common.lnglat_to_meters(10, 20)
        lng, lat = common.meters_to_lnglat(x, y)
        self.assertAlmostEqual(lng, 10, places=4)
        self.assertAlmostEqual(lat, 20, places=4)

    def test_meters_to_lnglat(self):
        lng, lat = common.meters_to_lnglat(x=0, y=0)
        self.assertAlmostEqual(lng, 0)
        self.assertAlmostEqual(lat, 0)

        lng, lat = common.meters_to_lnglat(x=111319.4908, y=222684.2085)
        self.assertAlmostEqual(lng, 1.0, places=4)
        self.assertAlmostEqual(lat, 2.0, places=4)

        x, y = common.lnglat_to_meters(10, 20)
        lng, lat = common.meters_to_lnglat(x, y)
        self.assertAlmostEqual(lng, 10, places=4)
        self.assertAlmostEqual(lat, 20, places=4)

    # TODO: test_bounds_to_xy_range

    def test_center_zoom_to_xy_range(self):
        x_range, y_range = common.center_zoom_to_xy_range(center=(0, 0), zoom=2)
        self.assertAlmostEqual(x_range[0], -19926188.8520, places=4)
        self.assertAlmostEqual(x_range[1], 19926188.8520, places=4)
        self.assertAlmostEqual(y_range[0], -11068715.6594, places=4)
        self.assertAlmostEqual(y_range[1], 11068715.6594, places=4)

        x_range, y_range = common.center_zoom_to_xy_range(center=(0, 0), zoom=3)
        self.assertAlmostEqual(x_range[0], -9963094.4260, places=4)
        self.assertAlmostEqual(x_range[1], 9963094.4260, places=4)
        self.assertAlmostEqual(y_range[0], -4163881.1441, places=4)
        self.assertAlmostEqual(y_range[1], 4163881.1441, places=4)

    # TODO: test_get_geometry_coords

    def test_landsat_scaling(self):
        image = mock.MagicMock(spec=ee.Image)
        optical_bands_mock = mock.MagicMock(name="optical_bands_mock")
        thermal_bands_mock = mock.MagicMock(name="thermal_bands_mock")
        qa_pixel_mock = mock.MagicMock(name="qa_pixel_mock")

        def select_side_effect(band_selector):
            if band_selector == "SR_B.":
                return optical_bands_mock
            elif band_selector == "ST_B.*":
                return thermal_bands_mock
            elif band_selector == "QA_PIXEL":
                return qa_pixel_mock
            else:
                raise ValueError(f"Unexpected band selector: {band_selector}")

        image.select.side_effect = select_side_effect

        scaled_optical = mock.MagicMock(name="scaled_optical")
        optical_bands_mock.multiply.return_value.add.return_value = scaled_optical

        scaled_thermal = mock.MagicMock(name="scaled_thermal")
        thermal_bands_mock.multiply.return_value.add.return_value = scaled_thermal

        qa_mask = mock.MagicMock(name="qa_mask")
        qa_pixel_mock.bitwiseAnd.return_value.eq.return_value = qa_mask

        # To allow chaining addBands().addBands().updateMask().
        image.addBands.return_value = image

        # Test case 1: thermal_bands=True, apply_fmask=False.
        image.reset_mock()
        optical_bands_mock.reset_mock()
        thermal_bands_mock.reset_mock()
        qa_pixel_mock.reset_mock()
        common.landsat_scaling(image, thermal_bands=True, apply_fmask=False)
        image.select.assert_has_calls([mock.call("SR_B."), mock.call("ST_B.*")])
        self.assertEqual(image.select.call_count, 2)
        optical_bands_mock.multiply.assert_called_with(0.0000275)
        optical_bands_mock.multiply().add.assert_called_with(-0.2)
        thermal_bands_mock.multiply.assert_called_with(0.00341802)
        thermal_bands_mock.multiply().add.assert_called_with(149)
        image.addBands.assert_has_calls(
            [
                mock.call(scaled_thermal, None, True),
                mock.call(scaled_optical, None, True),
            ]
        )
        image.updateMask.assert_not_called()

        # Test case 2: thermal_bands=False, apply_fmask=False.
        image.reset_mock()
        optical_bands_mock.reset_mock()
        thermal_bands_mock.reset_mock()
        qa_pixel_mock.reset_mock()
        common.landsat_scaling(image, thermal_bands=False, apply_fmask=False)
        image.select.assert_called_once_with("SR_B.")
        optical_bands_mock.multiply.assert_called_with(0.0000275)
        optical_bands_mock.multiply().add.assert_called_with(-0.2)
        thermal_bands_mock.multiply.assert_not_called()
        image.addBands.assert_called_once_with(scaled_optical, None, True)
        image.updateMask.assert_not_called()

        # Test case 3: thermal_bands=True, apply_fmask=True.
        image.reset_mock()
        optical_bands_mock.reset_mock()
        thermal_bands_mock.reset_mock()
        qa_pixel_mock.reset_mock()
        common.landsat_scaling(image, thermal_bands=True, apply_fmask=True)
        image.select.assert_has_calls(
            [mock.call("SR_B."), mock.call("ST_B.*"), mock.call("QA_PIXEL")],
            any_order=True,
        )
        self.assertEqual(image.select.call_count, 3)
        optical_bands_mock.multiply.assert_called_with(0.0000275)
        optical_bands_mock.multiply().add.assert_called_with(-0.2)
        thermal_bands_mock.multiply.assert_called_with(0.00341802)
        thermal_bands_mock.multiply().add.assert_called_with(149)
        qa_pixel_mock.bitwiseAnd.assert_called_once_with(31)
        qa_pixel_mock.bitwiseAnd().eq.assert_called_once_with(0)
        image.addBands.assert_has_calls(
            [
                mock.call(scaled_thermal, None, True),
                mock.call(scaled_optical, None, True),
            ]
        )
        image.updateMask.assert_called_once_with(qa_mask)

        # Test case 4: thermal_bands=False, apply_fmask=True.
        image.reset_mock()
        optical_bands_mock.reset_mock()
        thermal_bands_mock.reset_mock()
        qa_pixel_mock.reset_mock()
        common.landsat_scaling(image, thermal_bands=False, apply_fmask=True)
        image.select.assert_has_calls(
            [mock.call("SR_B."), mock.call("QA_PIXEL")], any_order=True
        )
        self.assertEqual(image.select.call_count, 2)
        optical_bands_mock.multiply.assert_called_with(0.0000275)
        optical_bands_mock.multiply().add.assert_called_with(-0.2)
        thermal_bands_mock.multiply.assert_not_called()
        qa_pixel_mock.bitwiseAnd.assert_called_once_with(31)
        qa_pixel_mock.bitwiseAnd().eq.assert_called_once_with(0)
        image.addBands.assert_called_once_with(scaled_optical, None, True)
        image.updateMask.assert_called_once_with(qa_mask)

    # TODO: test_tms_to_geotiff
    # TODO: test_tif_to_jp2
    # TODO: test_ee_to_geotiff
    # TODO: test_create_grid

    def test_jslink_slider_label(self):
        int_slider = ipywidgets.IntSlider(value=5)
        int_label = ipywidgets.Label(value="0")
        common.jslink_slider_label(int_slider, int_label)
        int_slider.value = 10
        self.assertEqual(int_label.value, "10")

        float_slider = ipywidgets.FloatSlider(value=5.5)
        float_label = ipywidgets.Label(value="0.0")
        common.jslink_slider_label(float_slider, float_label)
        float_slider.value = 10.1
        self.assertEqual(float_label.value, "10.1")

    def test_check_basemap(self):
        self.assertEqual(common.check_basemap("ROADMAP"), "Google Maps")
        self.assertEqual(common.check_basemap("SATELLITE"), "Google Satellite")
        self.assertEqual(common.check_basemap("TERRAIN"), "Google Terrain")
        self.assertEqual(common.check_basemap("HYBRID"), "Google Hybrid")
        self.assertEqual(common.check_basemap("roadmap"), "Google Maps")
        self.assertEqual(common.check_basemap("satellite"), "Google Satellite")
        self.assertEqual(common.check_basemap("terrain"), "Google Terrain")
        self.assertEqual(common.check_basemap("hybrid"), "Google Hybrid")
        self.assertEqual(common.check_basemap("OpenStreetMap"), "OpenStreetMap")

        # pytype: disable=wrong-arg-types
        self.assertIsNone(common.check_basemap(None))
        self.assertEqual(common.check_basemap(123), 123)
        # pytype: enable=wrong-arg-types

    @mock.patch.object(os.path, "exists")
    @mock.patch.object(
        builtins,
        "open",
        new_callable=mock.mock_open,
        read_data='{"access_token": "TOKEN"}',
    )
    def test_get_ee_token_exists(self, mock_file, mock_exists):
        del mock_file  # Unused.
        mock_exists.return_value = True
        token = common.get_ee_token()
        self.assertEqual(token, {"access_token": "TOKEN"})

    @mock.patch.object(os.path, "exists")
    @mock.patch.object(sys, "stdout", new_callable=io.StringIO)
    def test_get_ee_token_not_exists(self, mock_stdout, mock_exists):
        mock_exists.return_value = False
        token = common.get_ee_token()
        self.assertIsNone(token)
        self.assertIn("credentials not found", mock_stdout.getvalue())

    # TODO: test_geotiff_to_image
    # TODO: test_xee_to_image
    # TODO: test_array_to_memory_file
    # TODO: test_array_to_image

    @mock.patch.object(psutil, "Process")
    def test_is_studio_lab(self, mock_process):
        mock_process.return_value.parent.return_value.cmdline.return_value = [
            "python",
            "/path/to/studiolab/bin/jupyter",
        ]
        self.assertTrue(common.is_studio_lab())

        mock_process.return_value.parent.return_value.cmdline.return_value = [
            "python",
            "/home/user/run.py",
        ]
        self.assertFalse(common.is_studio_lab())

    @mock.patch.object(psutil, "Process")
    def test_is_on_aws(self, mock_process):
        mock_process.return_value.parent.return_value.cmdline.return_value = [
            "python",
            "/home/ec2-user/run.py",
        ]
        self.assertTrue(common.is_on_aws())

        mock_process.return_value.parent.return_value.cmdline.return_value = [
            "python",
            "script.aws",
        ]
        self.assertTrue(common.is_on_aws())

        mock_process.return_value.parent.return_value.cmdline.return_value = [
            "python",
            "/home/user/run.py",
        ]
        self.assertFalse(common.is_on_aws())

    # TODO: test_xarray_to_raster

    def test_hex_to_rgba(self):
        self.assertEqual(common.hex_to_rgba("#000000", 1.0), "rgba(0,0,0,1.0)")
        self.assertEqual(common.hex_to_rgba("000000", 1.0), "rgba(0,0,0,1.0)")
        self.assertEqual(common.hex_to_rgba("#FF0000", 0.5), "rgba(255,0,0,0.5)")
        self.assertEqual(common.hex_to_rgba("00FF00", 0.0), "rgba(0,255,0,0.0)")
        self.assertEqual(common.hex_to_rgba("0000FF", 1.0), "rgba(0,0,255,1.0)")
        self.assertEqual(common.hex_to_rgba("#FFFFFF", 0.7), "rgba(255,255,255,0.7)")

    def test_replace_top_level_hyphens(self):
        self.assertEqual(
            common.replace_top_level_hyphens({"a-b": 1, "c": 2}), {"a_b": 1, "c": 2}
        )
        self.assertEqual(
            common.replace_top_level_hyphens({"a-b": {"c-d": 1}}),
            {"a_b": {"c-d": 1}},
        )
        self.assertEqual(
            common.replace_top_level_hyphens([{"a-b": 1}, {"c-d": 2}]),
            [{"a-b": 1}, {"c-d": 2}],
        )
        self.assertEqual(common.replace_top_level_hyphens(1), 1)
        self.assertEqual(common.replace_top_level_hyphens("test"), "test")
        self.assertEqual(common.replace_top_level_hyphens({"a_b": 1}), {"a_b": 1})

    def test_replace_hyphens_in_keys(self):
        self.assertEqual(
            common.replace_hyphens_in_keys({"a-b": 1, "c": 2}), {"a_b": 1, "c": 2}
        )
        self.assertEqual(
            common.replace_hyphens_in_keys({"a-b": {"c-d": 1}}), {"a_b": {"c_d": 1}}
        )
        self.assertEqual(
            common.replace_hyphens_in_keys([{"a-b": 1}, {"c-d": 2}]),
            [{"a_b": 1}, {"c_d": 2}],
        )
        self.assertEqual(common.replace_hyphens_in_keys(1), 1)
        self.assertEqual(common.replace_hyphens_in_keys("test"), "test")
        self.assertEqual(common.replace_hyphens_in_keys({"a_b": 1}), {"a_b": 1})

    def test_remove_port_from_string(self):
        self.assertEqual(
            common.remove_port_from_string("http://127.0.0.1:8080"),
            "http://127.0.0.1",
        )
        self.assertEqual(
            common.remove_port_from_string("http://127.0.0.1"), "http://127.0.0.1"
        )
        self.assertEqual(
            common.remove_port_from_string("https://127.0.0.1:8080"),
            "https://127.0.0.1:8080",
        )
        self.assertEqual(
            common.remove_port_from_string("ABCD http://10.0.0.1:1234 EFGH"),
            "ABCD http://10.0.0.1 EFGH",
        )
        self.assertEqual(common.remove_port_from_string("no url"), "no url")
        self.assertEqual(
            common.remove_port_from_string('{"url": "http://127.0.0.1:8000/tile"}'),
            '{"url": "http://127.0.0.1/tile"}',
        )

    # TODO: test_pmtiles_metadata

    @mock.patch.object(common, "pmtiles_metadata")
    def test_pmtiles_style(self, mock_pmtiles_metadata):
        mock_pmtiles_metadata.return_value = {
            "layer_names": ["layer1", "layer2"],
            "center": [0, 0, 0],
            "bounds": [0, 0, 0, 0],
        }
        style = common.pmtiles_style("some_url")
        self.assertIn("layers", style)
        self.assertEqual(6, len(style["layers"]))

    @mock.patch.object(common, "pmtiles_metadata")
    def test_pmtiles_style_cmap_list(self, mock_pmtiles_metadata):
        mock_pmtiles_metadata.return_value = {
            "layer_names": ["layer1", "layer2"],
            "center": [0, 0, 0],
            "bounds": [0, 0, 0, 0],
        }
        # pytype: disable=wrong-arg-types
        style = common.pmtiles_style("some_url", cmap=["#1a9850", "#91cf60"])
        # pytype: enable=wrong-arg-types
        self.assertEqual(style["layers"][0]["paint"]["circle-color"], "#1a9850")
        self.assertEqual(style["layers"][1]["paint"]["line-color"], "#1a9850")
        self.assertEqual(style["layers"][2]["paint"]["fill-color"], "#1a9850")
        self.assertEqual(style["layers"][3]["paint"]["circle-color"], "#91cf60")
        self.assertEqual(style["layers"][4]["paint"]["line-color"], "#91cf60")
        self.assertEqual(style["layers"][5]["paint"]["fill-color"], "#91cf60")

    @mock.patch.object(common, "pmtiles_metadata")
    @mock.patch.object(colormaps, "get_palette")
    def test_pmtiles_style_cmap_palette(self, mock_get_palette, mock_pmtiles_metadata):
        mock_pmtiles_metadata.return_value = {
            "layer_names": ["layer1", "layer2"],
            "center": [0, 0, 0],
            "bounds": [0, 0, 0, 0],
        }
        mock_get_palette.return_value = ["440154", "414287"]
        style = common.pmtiles_style("some_url", cmap="viridis")
        self.assertEqual(style["layers"][0]["paint"]["circle-color"], "#440154")
        self.assertEqual(style["layers"][1]["paint"]["line-color"], "#440154")
        self.assertEqual(style["layers"][2]["paint"]["fill-color"], "#440154")
        self.assertEqual(style["layers"][3]["paint"]["circle-color"], "#414287")
        self.assertEqual(style["layers"][4]["paint"]["line-color"], "#414287")
        self.assertEqual(style["layers"][5]["paint"]["fill-color"], "#414287")

    @mock.patch.object(common, "pmtiles_metadata")
    def test_pmtiles_style_layers_str(self, mock_pmtiles_metadata):
        mock_pmtiles_metadata.return_value = {
            "layer_names": ["layer1", "layer2"],
            "center": [0, 0, 0],
            "bounds": [0, 0, 0, 0],
        }
        style = common.pmtiles_style("some_url", layers="layer1")
        self.assertEqual(3, len(style["layers"]))
        self.assertEqual(style["layers"][0]["id"], "layer1_point")

    @mock.patch.object(common, "pmtiles_metadata")
    def test_pmtiles_style_layers_list(self, mock_pmtiles_metadata):
        mock_pmtiles_metadata.return_value = {
            "layer_names": ["layer1", "layer2"],
            "center": [0, 0, 0],
            "bounds": [0, 0, 0, 0],
        }
        style = common.pmtiles_style("some_url", layers=["layer2"])
        self.assertEqual(3, len(style["layers"]))
        self.assertEqual(style["layers"][0]["id"], "layer2_point")

    @mock.patch.object(common, "pmtiles_metadata")
    def test_pmtiles_style_layers_invalid_list(self, mock_pmtiles_metadata):
        mock_pmtiles_metadata.return_value = {
            "layer_names": ["layer1", "layer2"],
            "center": [0, 0, 0],
            "bounds": [0, 0, 0, 0],
        }
        with self.assertRaises(ValueError):
            common.pmtiles_style("some_url", layers=["layer1", "invalid_layer"])

    @mock.patch.object(common, "pmtiles_metadata")
    def test_pmtiles_style_layers_invalid_type(self, mock_pmtiles_metadata):
        mock_pmtiles_metadata.return_value = {
            "layer_names": ["layer1", "layer2"],
            "center": [0, 0, 0],
            "bounds": [0, 0, 0, 0],
        }
        with self.assertRaises(ValueError):
            common.pmtiles_style(
                "some_url", layers=123
            )  # pytype: disable=wrong-arg-types

    def test_check_html_string(self):
        with tempfile.TemporaryDirectory() as root_dir:
            root = pathlib.Path(root_dir)

            # Create a dummy image file.
            temp_file = root / "test_image.png"
            img = Image.new("RGB", (1, 1), color="red")
            img.save(temp_file)

            img_data = temp_file.read_bytes()
            base64_data = base64.b64encode(img_data).decode("utf-8")
            expected_base64_src = f"data:image/png;base64,{base64_data}"

            html_string = f'<html><body><img src="{temp_file}"></body></html>'

            result_html = common.check_html_string(html_string)

            self.assertIn(expected_base64_src, result_html)
            self.assertNotIn(str(temp_file), result_html)


if __name__ == "__main__":
    unittest.main()
