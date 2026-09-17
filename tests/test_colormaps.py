"""Tests for `colormaps` module."""

import unittest
from unittest import mock

import matplotlib as mpl
import matplotlib.pyplot as plt

from geemap import colormaps


class ColormapsTest(unittest.TestCase):
    """Tests for `colormaps` module."""

    def tearDown(self):
        """Close figures created by colorbar tests."""
        plt.close("all")

    def test_get_palette_ndvi(self):
        """Test get_palette with ndvi."""
        palette = colormaps.get_palette("ndvi")
        self.assertEqual(len(palette), 17)
        self.assertEqual(palette[0], "FFFFFF")

    def test_get_palette_ndwi_hashtag(self):
        """Test get_palette with ndwi and hashtag."""
        palette = colormaps.get_palette("ndwi", hashtag=True)
        expect = [
            "#ece7f2",
            "#d0d1e6",
            "#a6bddb",
            "#74a9cf",
            "#3690c0",
            "#0570b0",
            "#045a8d",
            "#023858",
        ]
        self.assertEqual(expect, palette)

    def test_get_palette_dem(self):
        """Test get_palette with dem."""
        palette = colormaps.get_palette("dem")
        self.assertEqual(len(palette), 5)
        self.assertEqual(palette[0], "006633")

    def test_get_palette_dw(self):
        """Test get_palette with dw."""
        palette = colormaps.get_palette("dw")
        self.assertEqual(len(palette), 9)
        self.assertEqual(palette[0], "#419BDF")

    def test_get_palette_esri_lulc(self):
        """Test get_palette with esri_lulc."""
        palette = colormaps.get_palette("esri_lulc")
        self.assertEqual(len(palette), 11)
        self.assertEqual(palette[0], "#1A5BAB")

    def test_get_palette_viridis_nclass(self):
        """Test get_palette with viridis and n_class."""
        palette = colormaps.get_palette("viridis", n_class=5)
        self.assertEqual(len(palette), 5)
        self.assertEqual(palette[0], "440154")
        self.assertEqual(palette[4], "fde725")

    def test_get_palette_terrain_nclass_hashtag(self):
        """Test get_palette with terrain and n_class and hashtag."""
        palette = colormaps.get_palette("terrain", n_class=3, hashtag=True)
        self.assertEqual(len(palette), 3)
        self.assertEqual(palette[0], "#333399")
        self.assertEqual(palette[1], "#fefe98")
        self.assertEqual(palette[2], "#ffffff")

    def test_get_palette_no_nclass(self):
        """Test get_palette with no n_class."""
        palette = colormaps.get_palette("plasma")
        self.assertEqual(len(palette), 256)
        self.assertEqual(palette[0], "0d0887")
        self.assertEqual(palette[255], "f0f921")

    def test_get_colorbar_continuous(self):
        """Test a continuous colorbar returned as a figure."""
        with mock.patch.object(colormaps.mpl.colorbar, "ColorbarBase") as colorbar:
            fig = colormaps.get_colorbar(
                ["000000", "#ffffff"],
                vmin=-2,
                vmax=4,
                width=4,
                height=0.5,
                orientation="vertical",
                return_fig=True,
            )

        self.assertIsInstance(fig, mpl.figure.Figure)
        self.assertEqual(tuple(fig.get_size_inches()), (4.0, 0.5))
        args, kwargs = colorbar.call_args
        self.assertIs(args[0], fig.axes[0])
        self.assertIsInstance(kwargs["cmap"], mpl.colors.LinearSegmentedColormap)
        self.assertIsInstance(kwargs["norm"], mpl.colors.Normalize)
        self.assertNotIsInstance(kwargs["norm"], mpl.colors.BoundaryNorm)
        self.assertEqual(kwargs["norm"].vmin, -2)
        self.assertEqual(kwargs["norm"].vmax, 4)
        self.assertEqual(kwargs["orientation"], "vertical")

    def test_get_colorbar_discrete(self):
        """Test a discrete colorbar and hex color normalization."""
        with mock.patch.object(colormaps.mpl.colorbar, "ColorbarBase") as colorbar:
            fig = colormaps.get_colorbar(
                ["000000", "#ffffff"], discrete=True, return_fig=True
            )

        self.assertIsInstance(fig, mpl.figure.Figure)
        args, kwargs = colorbar.call_args
        self.assertIs(args[0], fig.axes[0])
        self.assertIsInstance(kwargs["cmap"], mpl.colors.ListedColormap)
        self.assertEqual(kwargs["cmap"].colors, ["#000000", "#ffffff"])
        self.assertIsInstance(kwargs["norm"], mpl.colors.BoundaryNorm)
        self.assertEqual(kwargs["orientation"], "horizontal")

    def test_get_colorbar_shows_by_default(self):
        """Test that a colorbar is shown when no figure is requested."""
        with mock.patch.object(colormaps.plt, "show") as show:
            result = colormaps.get_colorbar(["000000", "ffffff"])

        self.assertIsNone(result)
        show.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
