"""Tests for the timelapse module."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from tests.mocks import mock_ee


class MockPILImage:

    def __init__(self, size: tuple[int, int] = (100, 100), mode: str = "RGB") -> None:
        self._size = size
        self._mode = mode
        self.n_frames = 5

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    def save(self, *args, **kwargs) -> None:
        pass

    def convert(self, mode: str) -> "MockPILImage":
        return MockPILImage(size=self._size, mode=mode)

    @classmethod
    def open(cls, path: str) -> "MockPILImage":
        return MockPILImage()


class MockImageDraw:

    def __init__(self, image: MockPILImage) -> None:
        self.image = image

    def text(self, *args, **kwargs) -> None:
        pass

    def rectangle(self, *args, **kwargs) -> None:
        pass


class MockImageFont:

    @staticmethod
    def truetype(font: str, size: int) -> "MockImageFont":
        return MockImageFont()


class MockImageSequence:

    class Iterator:
        def __init__(self, image: MockPILImage) -> None:
            self.image = image
            self.index = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.index < self.image.n_frames:
                self.index += 1
                return self.image
            raise StopIteration


class TestMakeGif(unittest.TestCase):

    def test_make_gif_invalid_images_type_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(ValueError):
            timelapse.make_gif(12345, "out.gif")

    def test_make_gif_empty_directory_raises(self) -> None:
        from geemap import timelapse

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                timelapse.make_gif(tmpdir, "out.gif")

    @mock.patch("geemap.timelapse.Image")
    def test_make_gif_from_directory(self, mock_image: mock.Mock) -> None:
        from geemap import timelapse

        mock_frame = mock.MagicMock()
        mock_image.open.return_value = mock_frame

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                with open(os.path.join(tmpdir, f"frame{i}.jpg"), "w") as f:
                    f.write("test")

            out_gif = os.path.join(tmpdir, "out.gif")
            timelapse.make_gif(tmpdir, out_gif, ext="jpg")

            self.assertTrue(mock_image.open.called)

    @mock.patch("geemap.timelapse.Image")
    def test_make_gif_from_list(self, mock_image: mock.Mock) -> None:
        from geemap import timelapse

        mock_frame = mock.MagicMock()
        mock_image.open.return_value = mock_frame

        with tempfile.TemporaryDirectory() as tmpdir:
            images = []
            for i in range(3):
                path = os.path.join(tmpdir, f"frame{i}.jpg")
                with open(path, "w") as f:
                    f.write("test")
                images.append(path)

            out_gif = os.path.join(tmpdir, "out.gif")
            timelapse.make_gif(images, out_gif)

            self.assertTrue(mock_image.open.called)


class TestGifToMp4(unittest.TestCase):

    def test_gif_to_mp4_missing_file_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(FileNotFoundError):
            timelapse.gif_to_mp4("/nonexistent/file.gif", "out.mp4")

    @mock.patch("geemap.timelapse.is_tool", return_value=False)
    @mock.patch("geemap.timelapse.Image")
    def test_gif_to_mp4_no_ffmpeg(
        self, mock_image: mock.Mock, mock_is_tool: mock.Mock
    ) -> None:
        from geemap import timelapse

        mock_image.open.return_value = MockPILImage()

        with tempfile.TemporaryDirectory() as tmpdir:
            in_gif = os.path.join(tmpdir, "test.gif")
            with open(in_gif, "w") as f:
                f.write("test")
            out_mp4 = os.path.join(tmpdir, "test.mp4")

            timelapse.gif_to_mp4(in_gif, out_mp4)

            mock_is_tool.assert_called_with("ffmpeg")


class TestMergeGifs(unittest.TestCase):

    def test_merge_gifs_invalid_type_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(Exception):
            timelapse.merge_gifs(12345, "out.gif")

    @mock.patch("os.system")
    def test_merge_gifs_from_list(self, mock_system: mock.Mock) -> None:
        from geemap import timelapse

        in_gifs = ["gif1.gif", "gif2.gif"]
        out_gif = "merged.gif"

        timelapse.merge_gifs(in_gifs, out_gif)

        mock_system.assert_called_once()
        call_args = mock_system.call_args[0][0]
        self.assertIn("gifsicle", call_args)

    @mock.patch("os.system")
    @mock.patch("glob.glob", return_value=["gif1.gif", "gif2.gif"])
    def test_merge_gifs_from_directory(
        self, mock_glob: mock.Mock, mock_system: mock.Mock
    ) -> None:
        from geemap import timelapse

        with tempfile.TemporaryDirectory() as tmpdir:
            timelapse.merge_gifs(tmpdir, "merged.gif")

            mock_glob.assert_called_once()


class TestGifToPng(unittest.TestCase):

    def test_gif_to_png_missing_file_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(FileNotFoundError):
            timelapse.gif_to_png("/nonexistent/file.gif")

    def test_gif_to_png_spaces_in_path_raises(self) -> None:
        from geemap import timelapse

        with tempfile.TemporaryDirectory() as tmpdir:
            in_gif = os.path.join(tmpdir, "test file.gif")
            with open(in_gif, "w") as f:
                f.write("test")

            with self.assertRaises(Exception):
                timelapse.gif_to_png(in_gif)

    def test_gif_to_png_invalid_out_dir_raises(self) -> None:
        from geemap import timelapse

        with tempfile.TemporaryDirectory() as tmpdir:
            in_gif = os.path.join(tmpdir, "test.gif")
            with open(in_gif, "w") as f:
                f.write("test")

            with self.assertRaises(Exception):
                timelapse.gif_to_png(in_gif, out_dir=12345)


class TestGifFading(unittest.TestCase):

    def test_gif_fading_invalid_input_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(Exception):
            timelapse.gif_fading("not_a_gif.txt", "out.gif")

    def test_gif_fading_missing_file_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(FileNotFoundError):
            timelapse.gif_fading("/nonexistent/file.gif", "out.gif")

    def test_gif_fading_spaces_in_path_raises(self) -> None:
        from geemap import timelapse

        with tempfile.TemporaryDirectory() as tmpdir:
            in_gif = os.path.join(tmpdir, "test file.gif")
            with open(in_gif, "w") as f:
                f.write("test")

            with self.assertRaises(Exception):
                timelapse.gif_fading(in_gif, "out.gif")


class TestAddTextToGif(unittest.TestCase):

    def test_add_text_to_gif_missing_file_returns(self) -> None:
        from geemap import timelapse

        result = timelapse.add_text_to_gif("/nonexistent.gif", "out.gif")

        self.assertIsNone(result)

    @mock.patch("geemap.timelapse.Image")
    @mock.patch("geemap.timelapse.ImageDraw")
    @mock.patch("geemap.timelapse.ImageFont")
    @mock.patch("geemap.timelapse.ImageSequence")
    def test_add_text_to_gif_invalid_xy_tuple_returns(
        self,
        mock_seq: mock.Mock,
        mock_font: mock.Mock,
        mock_draw: mock.Mock,
        mock_image: mock.Mock,
    ) -> None:
        from geemap import timelapse

        mock_img = MockPILImage()
        mock_image.open.return_value = mock_img

        with tempfile.TemporaryDirectory() as tmpdir:
            in_gif = os.path.join(tmpdir, "test.gif")
            with open(in_gif, "w") as f:
                f.write("test")
            out_gif = os.path.join(tmpdir, "out.gif")

            result = timelapse.add_text_to_gif(in_gif, out_gif, xy="invalid")

            self.assertIsNone(result)


class TestReduceGifSize(unittest.TestCase):

    @mock.patch("geemap.timelapse.is_tool", return_value=False)
    def test_reduce_gif_size_no_gifsicle_raises(self, mock_is_tool: mock.Mock) -> None:
        from geemap import timelapse

        with self.assertRaises(Exception):
            timelapse.reduce_gif_size("test.gif")


class TestValidRoi(unittest.TestCase):

    @mock.patch("geemap.timelapse.ee", mock_ee)
    @mock.patch("geemap.timelapse.ee_to_geojson")
    @mock.patch("geemap.timelapse.adjust_longitude")
    def test_valid_roi_with_geometry(
        self, mock_adjust: mock.Mock, mock_to_geojson: mock.Mock
    ) -> None:
        from geemap import timelapse

        mock_to_geojson.return_value = {"type": "Polygon", "coordinates": []}
        mock_adjust.return_value = {"type": "Polygon", "coordinates": []}

        roi = mock_ee.Geometry.Polygon()
        result = timelapse.valid_roi(roi)

        self.assertIsNotNone(result)

    @mock.patch("geemap.timelapse.ee", mock_ee)
    @mock.patch("geemap.timelapse.ee_to_geojson")
    @mock.patch("geemap.timelapse.adjust_longitude")
    def test_valid_roi_with_feature_collection(
        self, mock_adjust: mock.Mock, mock_to_geojson: mock.Mock
    ) -> None:
        from geemap import timelapse

        mock_to_geojson.return_value = {"type": "Polygon", "coordinates": []}
        mock_adjust.return_value = {"type": "Polygon", "coordinates": []}

        fc = mock_ee.FeatureCollection()
        result = timelapse.valid_roi(fc)

        self.assertIsNotNone(result)


class TestSentinel1Defaults(unittest.TestCase):

    @mock.patch("geemap.timelapse.ee", mock_ee)
    def test_sentinel1_defaults_returns_tuple(self) -> None:
        from geemap import timelapse

        result = timelapse.sentinel1_defaults()

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    @mock.patch("geemap.timelapse.ee", mock_ee)
    def test_sentinel1_defaults_year_is_current(self) -> None:
        import datetime

        from geemap import timelapse

        year, _ = timelapse.sentinel1_defaults()

        self.assertEqual(year, datetime.date.today().year)


class TestCreateTimeseries(unittest.TestCase):

    @mock.patch("geemap.timelapse.ee", mock_ee)
    @mock.patch("geemap.timelapse.date_sequence")
    def test_create_timeseries_with_string_collection(
        self, mock_date_seq: mock.Mock
    ) -> None:
        from geemap import timelapse

        mock_dates = mock_ee.List(["2020-01-01", "2020-02-01"])
        mock_dates.map = mock.MagicMock(return_value=mock_ee.ImageCollection())
        mock_date_seq.return_value = mock_dates

        result = timelapse.create_timeseries(
            "LANDSAT/LC08/C02/T1_L2",
            "2020-01-01",
            "2020-12-31",
        )

        self.assertIsNotNone(result)

    def test_create_timeseries_invalid_collection_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(Exception):
            timelapse.create_timeseries(12345, "2020-01-01", "2020-12-31")

    @mock.patch("geemap.timelapse.ee", mock_ee)
    @mock.patch("geemap.timelapse.date_sequence")
    def test_create_timeseries_with_bands(self, mock_date_seq: mock.Mock) -> None:
        from geemap import timelapse

        mock_dates = mock_ee.List(["2020-01-01"])
        mock_dates.map = mock.MagicMock(return_value=mock_ee.ImageCollection())
        mock_date_seq.return_value = mock_dates

        collection = mock_ee.ImageCollection()
        result = timelapse.create_timeseries(
            collection,
            "2020-01-01",
            "2020-12-31",
            bands=["B1", "B2"],
        )

        self.assertIsNotNone(result)


class TestSentinel1Filtering(unittest.TestCase):

    @mock.patch("geemap.timelapse.ee", mock_ee)
    def test_sentinel1_filtering_default_band(self) -> None:
        from geemap import timelapse

        collection = mock_ee.ImageCollection()
        result = timelapse.sentinel1_filtering(collection)

        self.assertIsNotNone(result)

    @mock.patch("geemap.timelapse.ee", mock_ee)
    def test_sentinel1_filtering_custom_band(self) -> None:
        from geemap import timelapse

        collection = mock_ee.ImageCollection()
        result = timelapse.sentinel1_filtering(collection, band="VH")

        self.assertIsNotNone(result)

    @mock.patch("geemap.timelapse.ee", mock_ee)
    def test_sentinel1_filtering_with_orbit(self) -> None:
        from geemap import timelapse

        collection = mock_ee.ImageCollection()
        result = timelapse.sentinel1_filtering(
            collection, orbitProperties_pass="ASCENDING"
        )

        self.assertIsNotNone(result)


class TestAddOverlay(unittest.TestCase):

    def test_add_overlay_invalid_collection_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(Exception):
            timelapse.add_overlay("not_a_collection", "overlay")


class TestAddProgressBarToGif(unittest.TestCase):

    def test_add_progress_bar_to_gif_missing_file_returns(self) -> None:
        from geemap import timelapse

        result = timelapse.add_progress_bar_to_gif("/nonexistent.gif", "out.gif")

        self.assertIsNone(result)


class TestDrawMarkers(unittest.TestCase):

    def test_draw_cross_marker(self) -> None:
        from geemap import timelapse

        mock_draw = mock.MagicMock()
        timelapse.draw_cross_marker(mock_draw, 50, 50, 10, "red")

        self.assertTrue(mock_draw.line.called)

    def test_draw_circle_marker(self) -> None:
        from geemap import timelapse

        mock_draw = mock.MagicMock()
        timelapse.draw_circle_marker(mock_draw, 50, 50, 10, "blue")

        self.assertTrue(mock_draw.ellipse.called)

    def test_draw_square_marker(self) -> None:
        from geemap import timelapse

        mock_draw = mock.MagicMock()
        timelapse.draw_square_marker(mock_draw, 50, 50, 10, "green")

        self.assertTrue(mock_draw.rectangle.called)


class TestGetPixelCoordinates(unittest.TestCase):

    def test_get_pixel_coordinates_from_geo(self) -> None:
        from geemap import timelapse

        roi_bounds = [-115.5, 35.9, -114.3, 36.4]
        x, y = timelapse.get_pixel_coordinates_from_geo(
            lon=-115.0,
            lat=36.1,
            roi_bounds=roi_bounds,
            gif_width=800,
            gif_height=600,
        )

        self.assertIsInstance(x, int)
        self.assertIsInstance(y, int)
        self.assertGreaterEqual(x, 0)
        self.assertLess(x, 800)
        self.assertGreaterEqual(y, 0)
        self.assertLess(y, 600)


class TestCalculateIndices(unittest.TestCase):

    @mock.patch("geemap.timelapse.ee", mock_ee)
    def test_calculate_sentinel2_indices(self) -> None:
        from geemap import timelapse

        image = mock_ee.Image()
        result = timelapse.calculate_sentinel2_indices(image)

        self.assertIsInstance(result, mock_ee.Image)

    @mock.patch("geemap.timelapse.ee", mock_ee)
    def test_calculate_landsat_indices(self) -> None:
        from geemap import timelapse

        image = mock_ee.Image()
        result = timelapse.calculate_landsat_indices(image)

        self.assertIsInstance(result, mock_ee.Image)


class TestGetVisParams(unittest.TestCase):

    def test_get_default_index_vis_params(self) -> None:
        from geemap import timelapse

        result = timelapse.get_default_index_vis_params()

        self.assertIsInstance(result, dict)
        self.assertIn("NDVI", result)

    def test_get_index_chart_labels(self) -> None:
        from geemap import timelapse

        result = timelapse.get_index_chart_labels()

        self.assertIsInstance(result, dict)

    def test_get_default_landsat_index_vis_params(self) -> None:
        from geemap import timelapse

        result = timelapse.get_default_landsat_index_vis_params()

        self.assertIsInstance(result, dict)

    def test_get_default_landsat_band_labels(self) -> None:
        from geemap import timelapse

        result = timelapse.get_default_landsat_band_labels()

        self.assertIsInstance(result, dict)

    def test_get_landsat_index_chart_labels(self) -> None:
        from geemap import timelapse

        result = timelapse.get_landsat_index_chart_labels()

        self.assertIsInstance(result, dict)


class TestAddImageToGif(unittest.TestCase):

    def test_add_image_to_gif_missing_gif_returns(self) -> None:
        from geemap import timelapse

        result = timelapse.add_image_to_gif("/nonexistent.gif", "/image.png", "out.gif")

        self.assertIsNone(result)

    def test_add_image_to_gif_missing_image_returns(self) -> None:
        from geemap import timelapse

        with tempfile.TemporaryDirectory() as tmpdir:
            in_gif = os.path.join(tmpdir, "test.gif")
            with open(in_gif, "w") as f:
                f.write("test")

            result = timelapse.add_image_to_gif(
                in_gif, "/nonexistent_image.png", "out.gif"
            )

            self.assertIsNone(result)


class TestGoesTimeseries(unittest.TestCase):

    @mock.patch("geemap.timelapse.ee", mock_ee)
    def test_goes_timeseries_invalid_data_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(ValueError):
            timelapse.goes_timeseries(
                start_date="2020-01-01T14:00:00",
                end_date="2020-01-02T01:00:00",
                data="GOES-99",
            )


class TestModisNdviDoyTs(unittest.TestCase):

    @mock.patch("geemap.timelapse.ee", mock_ee)
    def test_modis_ndvi_doy_ts_invalid_data_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(Exception):
            timelapse.modis_ndvi_doy_ts(data="Invalid")


class TestGoesFireTimeseries(unittest.TestCase):

    @mock.patch("geemap.timelapse.ee", mock_ee)
    def test_goes_fire_timeseries_invalid_data_raises(self) -> None:
        from geemap import timelapse

        with self.assertRaises(ValueError):
            timelapse.goes_fire_timeseries(
                start_date="2020-01-01T14:00:00",
                end_date="2020-01-02T01:00:00",
                data="GOES-99",
            )


if __name__ == "__main__":
    unittest.main()
