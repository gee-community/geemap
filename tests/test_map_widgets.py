#!/usr/bin/env python

"""Tests for `map_widgets` module."""


import unittest
from unittest.mock import patch, MagicMock, ANY
from geemap import map_widgets


class TestColorbar(unittest.TestCase):
    """Tests for the Colorbar class in the `map_widgets` module."""

    TEST_COLORS = ["blue", "red", "green"]
    TEST_COLORS_HEX = ["#0000ff", "#ff0000", "#008000"]

    def setUp(self):
        self.fig_mock = MagicMock()
        self.ax_mock = MagicMock()
        self.subplots_mock = patch("matplotlib.pyplot.subplots").start()
        self.subplots_mock.return_value = (self.fig_mock, self.ax_mock)

        self.colorbar_base_mock = MagicMock()
        self.colorbar_base_class_mock = patch(
            "matplotlib.colorbar.ColorbarBase"
        ).start()
        self.colorbar_base_class_mock.return_value = self.colorbar_base_mock

        self.normalize_mock = MagicMock()
        self.normalize_class_mock = patch("matplotlib.colors.Normalize").start()
        self.normalize_class_mock.return_value = self.normalize_mock

        self.boundary_norm_mock = MagicMock()
        self.boundary_norm_class_mock = patch("matplotlib.colors.BoundaryNorm").start()
        self.boundary_norm_class_mock.return_value = self.boundary_norm_mock

        self.listed_colormap = MagicMock()
        self.listed_colormap_class_mock = patch(
            "matplotlib.colors.ListedColormap"
        ).start()
        self.listed_colormap_class_mock.return_value = self.listed_colormap

        self.linear_segmented_colormap_mock = MagicMock()
        self.colormap_from_list_mock = patch(
            "matplotlib.colors.LinearSegmentedColormap.from_list"
        ).start()
        self.colormap_from_list_mock.return_value = self.linear_segmented_colormap_mock

        check_cmap_mock = patch("geemap.common.check_cmap").start()
        check_cmap_mock.side_effect = lambda x: x

        self.cmap_mock = MagicMock()
        self.get_cmap_mock = patch("matplotlib.pyplot.get_cmap").start()
        self.get_cmap_mock.return_value = self.cmap_mock

    def tearDown(self):
        patch.stopall()

    def test_colorbar_no_args(self):
        map_widgets.Colorbar()
        self.normalize_class_mock.assert_called_with(vmin=0, vmax=1)
        self.get_cmap_mock.assert_called_with("gray")
        self.subplots_mock.assert_called_with(figsize=(3.0, 0.3))
        self.ax_mock.set_axis_off.assert_not_called()
        self.ax_mock.tick_params.assert_called_with(labelsize=9)
        self.fig_mock.patch.set_alpha.assert_not_called()
        self.colorbar_base_mock.set_label.assert_not_called()
        self.colorbar_base_class_mock.assert_called_with(
            self.ax_mock,
            norm=self.normalize_mock,
            alpha=1,
            cmap=self.cmap_mock,
            orientation="horizontal",
        )

    def test_colorbar_orientation_horizontal(self):
        map_widgets.Colorbar(orientation="horizontal")
        self.subplots_mock.assert_called_with(figsize=(3.0, 0.3))

    def test_colorbar_orientation_vertical(self):
        map_widgets.Colorbar(orientation="vertical")
        self.subplots_mock.assert_called_with(figsize=(0.3, 3.0))

    def test_colorbar_orientation_override(self):
        map_widgets.Colorbar(orientation="horizontal", width=2.0)
        self.subplots_mock.assert_called_with(figsize=(2.0, 0.3))

    def test_colorbar_invalid_orientation(self):
        with self.assertRaisesRegex(ValueError, "orientation must be one of"):
            map_widgets.Colorbar(orientation="not an orientation")

    def test_colorbar_label(self):
        map_widgets.Colorbar(label="Colorbar lbl", font_size=42)
        self.colorbar_base_mock.set_label.assert_called_with(
            "Colorbar lbl", fontsize=42
        )

    def test_colorbar_label_as_bands(self):
        map_widgets.Colorbar(vis_params={"bands": "b1"})
        self.colorbar_base_mock.set_label.assert_called_with("b1", fontsize=9)

    def test_colorbar_label_with_caption(self):
        map_widgets.Colorbar(caption="Colorbar caption")
        self.colorbar_base_mock.set_label.assert_called_with(
            "Colorbar caption", fontsize=9
        )

    def test_colorbar_label_precedence(self):
        map_widgets.Colorbar(
            label="Colorbar lbl",
            vis_params={"bands": "b1"},
            caption="Colorbar caption",
            font_size=21,
        )
        self.colorbar_base_mock.set_label.assert_called_with(
            "Colorbar lbl", fontsize=21
        )

    def test_colorbar_axis(self):
        map_widgets.Colorbar(axis_off=True, font_size=24)
        self.ax_mock.set_axis_off.assert_called()
        self.ax_mock.tick_params.assert_called_with(labelsize=24)

    def test_colorbar_transparent_bg(self):
        map_widgets.Colorbar(transparent_bg=True)
        self.fig_mock.patch.set_alpha.assert_called_with(0.0)

    def test_colorbar_vis_params_palette(self):
        map_widgets.Colorbar(
            vis_params={
                "palette": self.TEST_COLORS,
                "min": 11,
                "max": 21,
                "opacity": 0.2,
            }
        )
        self.normalize_class_mock.assert_called_with(vmin=11, vmax=21)
        self.colormap_from_list_mock.assert_called_with(
            "custom", self.TEST_COLORS_HEX, N=256
        )
        self.colorbar_base_class_mock.assert_called_with(
            self.ax_mock,
            norm=self.normalize_mock,
            alpha=0.2,
            cmap=self.linear_segmented_colormap_mock,
            orientation="horizontal",
        )

    def test_colorbar_vis_params_discrete_palette(self):
        map_widgets.Colorbar(
            vis_params={"palette": self.TEST_COLORS, "min": -1}, discrete=True
        )
        self.boundary_norm_class_mock.assert_called_with([-1], ANY)
        self.listed_colormap_class_mock.assert_called_with(self.TEST_COLORS_HEX)
        self.colorbar_base_class_mock.assert_called_with(
            self.ax_mock,
            norm=self.boundary_norm_mock,
            alpha=1,
            cmap=self.listed_colormap,
            orientation="horizontal",
        )

    def test_colorbar_vis_params_palette_as_list(self):
        map_widgets.Colorbar(vis_params=self.TEST_COLORS, discrete=True)
        self.boundary_norm_class_mock.assert_called_with([0], ANY)
        self.listed_colormap_class_mock.assert_called_with(self.TEST_COLORS_HEX)
        self.colorbar_base_class_mock.assert_called_with(
            self.ax_mock,
            norm=self.boundary_norm_mock,
            alpha=1,
            cmap=self.listed_colormap,
            orientation="horizontal",
        )

    def test_colorbar_kwargs_colors(self):
        map_widgets.Colorbar(colors=self.TEST_COLORS, discrete=True)
        self.boundary_norm_class_mock.assert_called_with([0], ANY)
        self.listed_colormap_class_mock.assert_called_with(self.TEST_COLORS_HEX)
        self.colorbar_base_class_mock.assert_called_with(
            self.ax_mock,
            norm=self.boundary_norm_mock,
            alpha=1,
            cmap=self.listed_colormap,
            orientation="horizontal",
            colors=self.TEST_COLORS,
        )

    def test_colorbar_min_max(self):
        map_widgets.Colorbar(
            vis_params={"palette": self.TEST_COLORS, "min": -1.5}, vmin=-1, vmax=2
        )
        self.normalize_class_mock.assert_called_with(vmin=-1.5, vmax=1)

    def test_colorbar_invalid_min(self):
        with self.assertRaisesRegex(TypeError, "min value must be scalar type"):
            map_widgets.Colorbar(vis_params={"min": "invalid_min"})

    def test_colorbar_invalid_max(self):
        with self.assertRaisesRegex(TypeError, "max value must be scalar type"):
            map_widgets.Colorbar(vis_params={"max": "invalid_max"})

    def test_colorbar_opacity(self):
        map_widgets.Colorbar(vis_params={"opacity": 0.5}, colors=self.TEST_COLORS)
        self.colorbar_base_class_mock.assert_called_with(
            ANY, norm=ANY, alpha=0.5, cmap=ANY, orientation=ANY, colors=ANY
        )

    def test_colorbar_alpha(self):
        map_widgets.Colorbar(alpha=0.5, colors=self.TEST_COLORS)
        self.colorbar_base_class_mock.assert_called_with(
            ANY, norm=ANY, alpha=0.5, cmap=ANY, orientation=ANY, colors=ANY
        )

    def test_colorbar_invalid_alpha(self):
        with self.assertRaisesRegex(
            TypeError, "opacity or alpha value must be type scalar"
        ):
            map_widgets.Colorbar(alpha="invalid_alpha", colors=self.TEST_COLORS)

    def test_colorbar_vis_params_throws_for_not_dict(self):
        with self.assertRaisesRegex(TypeError, "vis_params must be a dictionary"):
            map_widgets.Colorbar(vis_params="NOT a dict")
