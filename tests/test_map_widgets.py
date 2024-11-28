#!/usr/bin/env python

"""Tests for `map_widgets` module."""
import unittest
from unittest.mock import patch, MagicMock, Mock, ANY

import ipywidgets
import ee
from matplotlib import pyplot

from geemap import coreutils, map_widgets
from tests import fake_ee, fake_map, utils
from geemap.legends import builtin_legends


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
        self.normalize_class_mock.assert_called_with(vmin=-1.5, vmax=2)

    def test_colorbar_invalid_min(self):
        with self.assertRaisesRegex(ValueError, "min value must be scalar type"):
            map_widgets.Colorbar(vis_params={"min": "invalid_min"})

    def test_colorbar_invalid_max(self):
        with self.assertRaisesRegex(ValueError, "max value must be scalar type"):
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
            ValueError, "opacity or alpha value must be scalar type"
        ):
            map_widgets.Colorbar(alpha="invalid_alpha", colors=self.TEST_COLORS)

    def test_colorbar_vis_params_throws_for_not_dict(self):
        with self.assertRaisesRegex(TypeError, "vis_params must be a dictionary"):
            map_widgets.Colorbar(vis_params="NOT a dict")


class TestLegend(unittest.TestCase):
    """Tests for the Legend class in the `map_widgets` module."""

    TEST_COLORS_HEX = ["#ff0000", "#00ff00", "#0000ff"]
    TEST_COLORS_RGB = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    TEST_KEYS = ["developed", "forest", "open water"]

    def test_legend_unable_to_convert_rgb_to_hex(self):
        with self.assertRaisesRegex(ValueError, "Unable to convert rgb value to hex."):
            test_keys = ["Key 1"]
            test_colors = [("invalid", "invalid")]
            map_widgets.Legend(keys=test_keys, colors=test_colors)

    def test_legend_keys_and_colors_not_same_length(self):
        with self.assertRaisesRegex(
            ValueError, ("The legend keys and colors must be the " + "same length.")
        ):
            test_keys = ["one", "two", "three", "four"]
            map_widgets.Legend(keys=test_keys, colors=TestLegend.TEST_COLORS_HEX)

    def test_legend_builtin_legend_not_allowed(self):
        expected_regex = "The builtin legend must be one of the following: {}".format(
            ", ".join(builtin_legends)
        )
        with self.assertRaisesRegex(ValueError, expected_regex):
            map_widgets.Legend(builtin_legend="invalid_builtin_legend")

    def test_legend_position_not_allowed(self):
        expected_regex = (
            "The position must be one of the following: "
            + "topleft, topright, bottomleft, bottomright"
        )
        with self.assertRaisesRegex(ValueError, expected_regex):
            map_widgets.Legend(position="invalid_position")

    def test_legend_keys_not_a_dict(self):
        with self.assertRaisesRegex(TypeError, "The legend keys must be a list."):
            map_widgets.Legend(keys="invalid_keys")

    def test_legend_colors_not_a_list(self):
        with self.assertRaisesRegex(TypeError, "The legend colors must be a list."):
            map_widgets.Legend(colors="invalid_colors")

    def test_legend_colors_not_a_list_of_tuples(self):
        with self.assertRaisesRegex(
            TypeError, ("The legend colors must be a list of " + "tuples.")
        ):
            map_widgets.Legend(colors=["invalid_tuple"])


@patch.object(ee, "Algorithms", fake_ee.Algorithms)
@patch.object(ee, "FeatureCollection", fake_ee.FeatureCollection)
@patch.object(ee, "Feature", fake_ee.Feature)
@patch.object(ee, "Geometry", fake_ee.Geometry)
@patch.object(ee, "Image", fake_ee.Image)
@patch.object(ee, "String", fake_ee.String)
class TestInspector(unittest.TestCase):
    """Tests for the Inspector class in the `map_widgets` module."""

    def setUp(self):
        # ee.Reducer is dynamically initialized (can't use @patch.object).
        ee.Reducer = fake_ee.Reducer

        self.map_fake = fake_map.FakeMap()
        self.inspector = map_widgets.Inspector(self.map_fake)

    def tearDown(self):
        pass

    def test_inspector_no_map(self):
        """Tests that a valid map must be passed in."""
        with self.assertRaisesRegex(ValueError, "valid map"):
            map_widgets.Inspector(None)

    def test_inspector(self):
        """Tests that the inspector's initial UI is set up properly."""
        self.assertEqual(self.map_fake.cursor_style, "crosshair")
        self.assertFalse(self.inspector.hide_close_button)

        self.assertFalse(self.inspector.expand_points)
        self.assertTrue(self.inspector.expand_pixels)
        self.assertFalse(self.inspector.expand_objects)

        self.assertEqual(self.inspector.point_info, {})
        self.assertEqual(self.inspector.pixel_info, {})
        self.assertEqual(self.inspector.object_info, {})

    def test_map_empty_click(self):
        """Tests that clicking the map triggers inspection."""
        self.map_fake.click((1, 2), "click")

        self.assertEqual(self.map_fake.cursor_style, "crosshair")

        expected_point_info = coreutils.new_tree_node(
            "Point (2.00, 1.00) at 1024m/px",
            [
                coreutils.new_tree_node("Longitude: 2"),
                coreutils.new_tree_node("Latitude: 1"),
                coreutils.new_tree_node("Zoom Level: 7"),
                coreutils.new_tree_node("Scale (approx. m/px): 1024"),
            ],
            top_level=True,
        )
        self.assertEqual(self.inspector.point_info, expected_point_info)

        expected_pixel_info = coreutils.new_tree_node(
            "Pixels", top_level=True, expanded=True
        )
        self.assertEqual(self.inspector.pixel_info, expected_pixel_info)

        expected_object_info = coreutils.new_tree_node(
            "Objects", top_level=True, expanded=True
        )
        self.assertEqual(self.inspector.object_info, expected_object_info)

    def test_map_click(self):
        """Tests that clicking the map triggers inspection."""
        self.map_fake.ee_layers = {
            "test-map-1": {
                "ee_object": ee.Image(1),
                "ee_layer": fake_map.FakeEeTileLayer(visible=True),
                "vis_params": None,
            },
            "test-map-2": {
                "ee_object": ee.Image(2),
                "ee_layer": fake_map.FakeEeTileLayer(visible=False),
                "vis_params": None,
            },
            "test-map-3": {
                "ee_object": ee.FeatureCollection([]),
                "ee_layer": fake_map.FakeEeTileLayer(visible=True),
                "vis_params": None,
            },
        }
        self.map_fake.click((1, 2), "click")

        expected_point_info = coreutils.new_tree_node(
            "Point (2.00, 1.00) at 1024m/px",
            [
                coreutils.new_tree_node("Longitude: 2"),
                coreutils.new_tree_node("Latitude: 1"),
                coreutils.new_tree_node("Zoom Level: 7"),
                coreutils.new_tree_node("Scale (approx. m/px): 1024"),
            ],
            top_level=True,
        )
        self.assertEqual(self.inspector.point_info, expected_point_info)

        expected_pixel_info = coreutils.new_tree_node(
            "Pixels",
            [
                coreutils.new_tree_node(
                    "test-map-1: Image (2 bands)",
                    [
                        coreutils.new_tree_node("B1: 42", expanded=True),
                        coreutils.new_tree_node("B2: 3.14", expanded=True),
                    ],
                    expanded=True,
                ),
            ],
            top_level=True,
            expanded=True,
        )
        self.assertEqual(self.inspector.pixel_info, expected_pixel_info)

        expected_object_info = coreutils.new_tree_node(
            "Objects",
            [
                coreutils.new_tree_node(
                    "test-map-3: Feature",
                    [
                        coreutils.new_tree_node("type: Feature"),
                        coreutils.new_tree_node("id: 00000000000000000001"),
                        coreutils.new_tree_node(
                            "properties: Object (4 properties)",
                            [
                                coreutils.new_tree_node("fullname: some-full-name"),
                                coreutils.new_tree_node("linearid: 110469267091"),
                                coreutils.new_tree_node("mtfcc: S1400"),
                                coreutils.new_tree_node("rttyp: some-rttyp"),
                            ],
                        ),
                    ],
                ),
            ],
            top_level=True,
            expanded=True,
        )
        self.assertEqual(self.inspector.object_info, expected_object_info)

    def test_map_click_twice(self):
        """Tests that clicking the map a second time resets the point info."""
        self.map_fake.ee_layers = {
            "test-map-1": {
                "ee_object": ee.Image(1),
                "ee_layer": fake_map.FakeEeTileLayer(visible=True),
                "vis_params": None,
            },
        }
        self.map_fake.scale = 32
        self.map_fake.click((1, 2), "click")
        self.map_fake.click((4, 1), "click")

        expected_point_info = coreutils.new_tree_node(
            "Point (1.00, 4.00) at 32m/px",
            [
                coreutils.new_tree_node("Longitude: 1"),
                coreutils.new_tree_node("Latitude: 4"),
                coreutils.new_tree_node("Zoom Level: 7"),
                coreutils.new_tree_node("Scale (approx. m/px): 32"),
            ],
            top_level=True,
        )
        self.assertEqual(self.inspector.point_info, expected_point_info)

    def test_map_click_expanded(self):
        """Tests that nodes are expanded when the expand boolean is true."""
        self.inspector.expand_points = True

        self.map_fake.click((4, 1), "click")

        expected_point_info = coreutils.new_tree_node(
            "Point (1.00, 4.00) at 1024m/px",
            [
                coreutils.new_tree_node("Longitude: 1"),
                coreutils.new_tree_node("Latitude: 4"),
                coreutils.new_tree_node("Zoom Level: 7"),
                coreutils.new_tree_node("Scale (approx. m/px): 1024"),
            ],
            top_level=True,
            expanded=True,
        )
        self.assertEqual(self.inspector.point_info, expected_point_info)


def _create_fake_map() -> fake_map.FakeMap:
    ret = fake_map.FakeMap()
    ret.layers = [
        fake_map.FakeTileLayer("OpenStreetMap"),  # Basemap
        fake_map.FakeTileLayer("GMaps", False, 0.5),  # Extra basemap
        fake_map.FakeEeTileLayer("test-layer", True, 0.8),
        fake_map.FakeGeoJSONLayer(
            "test-geojson-layer",
            False,
            {"some-style": "red", "opacity": 0.3, "fillOpacity": 0.2},
        ),
    ]
    ret.ee_layers = {
        "test-layer": {"ee_object": None, "ee_layer": ret.layers[2], "vis_params": None}
    }
    ret.geojson_layers = [ret.layers[3]]
    return ret


@unittest.mock.patch(
    "geemap.map_widgets.LayerManagerRow._traitlet_link_type",
    new=unittest.mock.Mock(return_value=ipywidgets.link),
)  # jslink isn't supported in ipywidgets
class TestLayerManagerRow(unittest.TestCase):
    """Tests for the LayerManagerRow class in the `layer_manager` module."""

    def setUp(self):
        self.fake_map = _create_fake_map()

    def test_row_invalid_map_or_layer(self):
        """Tests that a valid map and layer must be passed in."""
        with self.assertRaisesRegex(ValueError, "valid map and layer"):
            map_widgets.LayerManagerRow(None, None)

    def test_row(self):
        """Tests LayerManagerRow is initialized correctly for a standard layer."""
        layer = fake_map.FakeTileLayer(name="layer-name", visible=False, opacity=0.2)
        row = map_widgets.LayerManagerRow(self.fake_map, layer)

        self.assertFalse(row.is_loading)
        self.assertEqual(row.name, layer.name)
        self.assertEqual(row.visible, layer.visible)
        self.assertEqual(row.opacity, layer.opacity)

    def test_geojson_row(self):
        """Tests LayerManagerRow is initialized correctly for a GeoJSON layer."""
        layer = fake_map.FakeGeoJSONLayer(
            name="layer-name", visible=True, style={"opacity": 0.2, "fillOpacity": 0.4}
        )
        self.fake_map.geojson_layers.append(layer)
        row = map_widgets.LayerManagerRow(self.fake_map, layer)

        self.assertEqual(row.name, layer.name)
        self.assertTrue(row.visible)
        self.assertEqual(row.opacity, 0.4)

    def test_layer_update_row_properties(self):
        """Tests layer updates update row traitlets."""
        layer = fake_map.FakeTileLayer(name="layer-name", visible=False, opacity=0.2)
        row = map_widgets.LayerManagerRow(self.fake_map, layer)

        layer.loading = True
        layer.opacity = 0.42
        layer.visible = True
        self.assertTrue(row.is_loading)
        self.assertEqual(row.opacity, 0.42)
        self.assertTrue(row.visible)

    def test_row_update_layer_properties(self):
        """Tests row updates update layer traitlets."""
        layer = fake_map.FakeTileLayer(name="layer-name", visible=False, opacity=0.2)
        row = map_widgets.LayerManagerRow(self.fake_map, layer)

        row.opacity = 0.42
        row.visible = True
        self.assertEqual(layer.opacity, 0.42)
        self.assertTrue(layer.visible)

    def test_geojson_row_update_layer_properties(self):
        """Tests GeoJSON row updates update layer traitlets."""
        layer = fake_map.FakeGeoJSONLayer(
            name="layer-name", visible=True, style={"opacity": 0.2, "fillOpacity": 0.4}
        )
        self.fake_map.geojson_layers.append(layer)
        row = map_widgets.LayerManagerRow(self.fake_map, layer)

        row.opacity = 0.42
        row.visible = True
        self.assertEqual(layer.style["opacity"], 0.42)
        self.assertEqual(layer.style["fillOpacity"], 0.42)
        self.assertTrue(layer.visible)

    def test_settings_button_clicked_non_ee_layer(self):
        """Tests that the layer vis editor is opened when settings is clicked."""
        row = map_widgets.LayerManagerRow(self.fake_map, self.fake_map.layers[0])

        msg = {"type": "click", "id": "settings"}
        row._handle_custom_msg(msg, [])  # pylint: disable=protected-access

        self.fake_map.add.assert_called_once_with(
            "layer_editor", position="bottomright", layer_dict=None
        )

    def test_settings_button_clicked_ee_layer(self):
        """Tests that the layer vis editor is opened when settings is clicked."""
        row = map_widgets.LayerManagerRow(self.fake_map, self.fake_map.layers[2])

        msg = {"type": "click", "id": "settings"}
        row._handle_custom_msg(msg, [])  # pylint: disable=protected-access

        self.fake_map.add.assert_called_once_with(
            "layer_editor",
            position="bottomright",
            layer_dict={
                "ee_object": None,
                "ee_layer": self.fake_map.layers[2],
                "vis_params": None,
            },
        )

    def test_delete_button_clicked(self):
        """Tests that the layer is removed when delete is clicked."""
        row = map_widgets.LayerManagerRow(self.fake_map, self.fake_map.layers[0])

        msg = {"type": "click", "id": "delete"}
        row._handle_custom_msg(msg, [])  # pylint: disable=protected-access

        self.assertEqual(len(self.fake_map.layers), 3)
        self.assertEqual(self.fake_map.layers[0].name, "GMaps")
        self.assertEqual(self.fake_map.layers[1].name, "test-layer")
        self.assertEqual(self.fake_map.layers[2].name, "test-geojson-layer")


class TestLayerManager(unittest.TestCase):
    """Tests for the LayerManager class in the `layer_manager` module."""

    def setUp(self):
        self.fake_map = _create_fake_map()
        self.layer_manager = map_widgets.LayerManager(self.fake_map)

    def test_layer_manager_no_map(self):
        """Tests that a valid map must be passed in."""
        with self.assertRaisesRegex(ValueError, "valid map"):
            map_widgets.LayerManager(None)

    def _validate_row(
        self, index: int, name: str, visible: bool, opacity: float
    ) -> None:
        child = self.layer_manager.children[index]
        self.assertEqual(child.host_map, self.fake_map)
        self.assertEqual(child.layer, self.fake_map.layers[index])
        self.assertEqual(child.name, name)
        self.assertEqual(child.visible, visible)
        self.assertAlmostEqual(child.opacity, opacity)

    def test_refresh_layers_updates_children(self):
        """Tests that refresh layers updates children."""
        self.layer_manager.refresh_layers()

        self.assertEqual(len(self.layer_manager.children), len(self.fake_map.layers))
        self._validate_row(0, name="OpenStreetMap", visible=True, opacity=1.0)
        self._validate_row(1, name="GMaps", visible=False, opacity=0.5)
        self._validate_row(2, name="test-layer", visible=True, opacity=0.8)
        self._validate_row(3, name="test-geojson-layer", visible=False, opacity=0.3)

    def test_visibility_updates_children(self):
        """Tests that tweaking the visibility updates children visibilities."""
        self.layer_manager.refresh_layers()
        self.assertTrue(self.layer_manager.visible)

        self.layer_manager.visible = False
        for child in self.layer_manager.children:
            self.assertFalse(child.visible)

        self.layer_manager.visible = True
        for child in self.layer_manager.children:
            self.assertTrue(child.visible)


class TestBasemapSelector(unittest.TestCase):
    """Tests for the BasemapSelector class in the `map_widgets` module."""

    def setUp(self):
        self.basemaps = ["first", "default", "bounded"]
        self.default = "default"
        self.basemap_widget = map_widgets.BasemapSelector(self.basemaps, self.default)

    def test_basemap_default(self):
        """Tests that the default value is set."""
        self.assertEqual(self.basemap_widget.value, "default")

    def test_basemap_close(self):
        """Tests that triggering the closing button fires the close callback."""
        on_close_mock = Mock()
        self.basemap_widget.on_close = on_close_mock
        msg = {"type": "click", "id": "close"}
        self.basemap_widget._handle_custom_msg(
            msg, []
        )  # pylint: disable=protected-access
        on_close_mock.assert_called_once()

    def test_basemap_change(self):
        """Tests that value change fires the basemap_changed callback."""
        on_change_mock = Mock()
        self.basemap_widget.on_basemap_changed = on_change_mock
        self.basemap_widget.value = "ROADMAP"
        on_change_mock.assert_called_once_with("ROADMAP")


class LayerEditorTestHarness:
    """A wrapper around LayerEditor to expose widgets for testing."""

    def __init__(self, layer_editor: map_widgets.LayerEditor):
        self._layer_editor = layer_editor

    def _query_checkbox(self, description):
        return utils.query_widget(
            self._layer_editor,
            ipywidgets.Checkbox,
            lambda c: c.description == description,
        )

    @property
    def legend_checkbox(self):
        return self._query_checkbox("Legend")

    @property
    def linear_colormap_checkbox(self):
        return self._query_checkbox("Linear colormap")

    @property
    def step_colormap_checkbox(self):
        return self._query_checkbox("Step colormap")

    @property
    def classes_dropdown(self):
        return utils.query_widget(
            self._layer_editor,
            ipywidgets.Dropdown,
            lambda c: c.description == "Classes:",
        )

    @property
    def colormap_dropdown(self):
        return utils.query_widget(
            self._layer_editor,
            ipywidgets.Dropdown,
            lambda c: c.description == "Colormap:",
        )

    @property
    def apply_button(self):
        return utils.query_widget(
            self._layer_editor, ipywidgets.Button, lambda c: c.description == "Apply"
        )


@patch.object(ee, "Feature", fake_ee.Feature)
@patch.object(ee, "FeatureCollection", fake_ee.FeatureCollection)
@patch.object(ee, "Geometry", fake_ee.Geometry)
@patch.object(ee, "Image", fake_ee.Image)
class TestLayerEditor(unittest.TestCase):
    """Tests for the `LayerEditor` class in the `map_widgets` module."""

    def _fake_layer_dict(self, ee_object):
        return {
            "ee_object": ee_object,
            "ee_layer": fake_map.FakeEeTileLayer(name="fake-ee-layer-name"),
            "vis_params": {},
        }

    def setUp(self):
        self._fake_map = fake_map.FakeMap()
        pyplot.show = Mock()  # Plotting isn't captured by output widgets.

    def test_layer_editor_no_map(self):
        """Tests that a valid map must be passed in."""
        with self.assertRaisesRegex(
            ValueError, "valid map when creating a LayerEditor widget"
        ):
            map_widgets.LayerEditor(None, {})

    def test_layer_editor_feature(self):
        """Tests that an ee.Feature can be passed in."""
        widget = map_widgets.LayerEditor(
            self._fake_map, self._fake_layer_dict(ee.Feature())
        )
        self.assertIsNotNone(
            utils.query_widget(widget, map_widgets._VectorLayerEditor, lambda _: True)
        )

    def test_layer_editor_geometry(self):
        """Tests that an ee.Geometry can be passed in."""
        widget = map_widgets.LayerEditor(
            self._fake_map, self._fake_layer_dict(ee.Geometry())
        )
        self.assertIsNotNone(
            utils.query_widget(widget, map_widgets._VectorLayerEditor, lambda _: True)
        )

    def test_layer_editor_feature_collection(self):
        """Tests that an ee.FeatureCollection can be passed in."""
        widget = map_widgets.LayerEditor(
            self._fake_map, self._fake_layer_dict(ee.FeatureCollection())
        )
        self.assertIsNotNone(
            utils.query_widget(widget, map_widgets._VectorLayerEditor, lambda _: True)
        )

    def test_layer_editor_image(self):
        """Tests that an ee.Image can be passed in."""
        widget = map_widgets.LayerEditor(
            self._fake_map, self._fake_layer_dict(ee.Image())
        )
        self.assertIsNotNone(
            utils.query_widget(widget, map_widgets._RasterLayerEditor, lambda _: True)
        )

    def test_layer_editor_colorbar(self):
        """Tests that linear legends checkbox changes the UI."""
        fake_dict = self._fake_layer_dict(ee.Image())
        self._fake_map.ee_layers["fake-ee-layer-name"] = fake_dict
        widget = map_widgets.LayerEditor(self._fake_map, fake_dict)
        harness = LayerEditorTestHarness(widget)

        legend_checkbox = harness.legend_checkbox
        self.assertIsNotNone(legend_checkbox)
        self.assertIsNone(harness.linear_colormap_checkbox)
        self.assertIsNone(harness.step_colormap_checkbox)

        legend_checkbox.value = True
        self.assertTrue(harness.linear_colormap_checkbox.value)
        self.assertFalse(harness.step_colormap_checkbox.value)

        harness.classes_dropdown.value = "3"
        harness.colormap_dropdown.value = "Blues"
        harness.apply_button.click()

        self.assertIsNotNone(self._fake_map.ee_layers["fake-ee-layer-name"]["colorbar"])
        self.assertNotIn("legend", self._fake_map.ee_layers["fake-ee-layer-name"])

    def test_layer_editor_legend(self):
        """Tests that linear legends checkbox changes the UI."""
        fake_dict = self._fake_layer_dict(ee.Image())
        self._fake_map.ee_layers["fake-ee-layer-name"] = fake_dict
        widget = map_widgets.LayerEditor(self._fake_map, fake_dict)
        harness = LayerEditorTestHarness(widget)

        legend_checkbox = harness.legend_checkbox
        self.assertIsNotNone(legend_checkbox)
        self.assertIsNone(harness.linear_colormap_checkbox)
        self.assertIsNone(harness.step_colormap_checkbox)

        legend_checkbox.value = True
        harness.step_colormap_checkbox.value = True
        self.assertFalse(harness.linear_colormap_checkbox.value)
        self.assertTrue(harness.step_colormap_checkbox.value)

        harness.classes_dropdown.value = "3"
        harness.colormap_dropdown.value = "Blues"
        harness.apply_button.click()

        self.assertNotIn("colorbar", self._fake_map.ee_layers["fake-ee-layer-name"])
        self.assertIsNotNone(self._fake_map.ee_layers["fake-ee-layer-name"]["legend"])
