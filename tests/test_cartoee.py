import pathlib
import tempfile
import unittest

from geemap import cartoee
import matplotlib.pyplot as plt

try:
    import cartopy.crs as ccrs

    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False


@unittest.skipIf(not CARTOPY_AVAILABLE, "cartopy is not installed")
class TestCartoee(unittest.TestCase):

    def test_build_palette(self):
        palette = cartoee.build_palette("viridis", 5)
        self.assertEqual(len(palette), 5)
        self.assertEqual(palette[0], "#440154")
        self.assertEqual(palette[-1], "#fde725")

    def test_add_colorbar(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
        vis_params = {"min": 0, "max": 10, "palette": ["#440154", "#fde725"]}
        cartoee.add_colorbar(ax, vis_params, loc="right")
        self.assertEqual(len(fig.axes), 2)

    def test__buffer_box(self):
        bbox = [1.1, 2.9, 3.1, 4.9]
        interval = 1
        self.assertEqual(cartoee._buffer_box(bbox, interval), (1.0, 3.0, 3.0, 5.0))
        bbox = [1.0, 3.0, 3.0, 5.0]
        self.assertEqual(cartoee._buffer_box(bbox, interval), (1.0, 3.0, 3.0, 5.0))

    def test_bbox_to_extent(self):
        self.assertEqual(cartoee.bbox_to_extent([1, 2, 3, 4]), (1, 3, 2, 4))

    def test_add_gridlines(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
        ax.set_extent([-180, 180, -90, 90])
        cartoee.add_gridlines(ax, interval=60)
        self.assertEqual(len(ax.get_xticks()), 7)

    def test_pad_view(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
        ax.set_extent([-10, 10, -10, 10])
        cartoee.pad_view(ax, factor=0.1)
        result = ax.get_xlim()
        self.assertAlmostEqual(result[0], -12.0)
        self.assertAlmostEqual(result[1], 12.0)
        result = ax.get_ylim()
        self.assertAlmostEqual(result[0], -12.0)
        self.assertAlmostEqual(result[1], 12.0)

    def test_add_north_arrow(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection=ccrs.PlateCarree())
        cartoee.add_north_arrow(ax)
        self.assertEqual(len(ax.texts), 1)

    def test_convert_si(self):
        self.assertEqual(cartoee.convert_SI(1, "km", "m"), 1000.0)

    def test_savefig(self):
        fig = plt.figure()
        fig.add_subplot(111, projection=ccrs.PlateCarree())
        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = pathlib.Path(tmpdir) / "test.png"
            cartoee.savefig(fig, str(outfile))
            self.assertTrue(outfile.exists())


if __name__ == "__main__":
    unittest.main()
