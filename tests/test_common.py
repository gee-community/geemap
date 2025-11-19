"""Tests for `common` module."""

import base64
import builtins
import io
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

from geemap import colormaps
from geemap import common
import ipywidgets
from PIL import Image
import psutil


class CommonTest(unittest.TestCase):

    # TODO: test_ee_export_image
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
    # TODO: test_check_titiler_endpoint
    # TODO: test_set_proxy
    # TODO: test_is_drive_mounted
    # TODO: test_credentials_in_drive
    # TODO: test_credentials_in_colab
    # TODO: test_copy_credentials_to_drive
    # TODO: test_copy_credentials_to_colab
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
    # TODO: test_bbox_to_geojson
    # TODO: test_coords_to_geojson
    # TODO: test_explode
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
    # TODO: test_num_round
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
    # TODO: test_delete_shp
    # TODO: test_df_to_ee
    # TODO: test_gdf_to_ee
    # TODO: test_vector_to_geojson
    # TODO: test_vector_to_ee
    # TODO: test_extract_pixel_values
    # TODO: test_list_vars
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
    # TODO: test_check_dir
    # TODO: test_check_file_path
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
    # TODO: test_get_palette_colors
    # TODO: test_plot_raster
    # TODO: test_plot_raster_3d
    # TODO: test_display_html
    # TODO: test_bbox_coords
    # TODO: test_requireJS
    # TODO: test_setupJS
    # TODO: test_change_require
    # TODO: test_ee_vector_style
    # TODO: test_get_direct_url
    # TODO: test_add_crs
    # TODO: test_jrc_hist_monthly_history
    # TODO: test_html_to_streamlit
    # TODO: test_image_convolution
    # TODO: test_download_ned
    # TODO: test_mosaic
    # TODO: test_reproject
    # TODO: test_download_3dep_lidar
    # TODO: test_use_mkdocs
    # TODO: test_create_legend
    # TODO: test_is_arcpy
    # TODO: test_arc_active_map
    # TODO: test_arc_active_view
    # TODO: test_arc_add_layer
    # TODO: test_arc_zoom_to_extent
    # TODO: test_get_current_year
    # TODO: test_html_to_gradio
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
    # TODO: test_find_files
    # TODO: test_zoom_level_resolution
    # TODO: test_lnglat_to_meters
    # TODO: test_meters_to_lnglat
    # TODO: test_bounds_to_xy_range
    # TODO: test_center_zoom_to_xy_range
    # TODO: test_get_geometry_coords
    # TODO: test_landsat_scaling
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
