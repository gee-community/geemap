"""Tests for the deck module."""

import unittest

try:
    import pydeck
    from geemap import deck

    PYDECK_AVAILABLE = True
except ImportError:
    PYDECK_AVAILABLE = False


@unittest.skipUnless(PYDECK_AVAILABLE, "pydeck not available")
class DeckTest(unittest.TestCase):

    def test_map_init_default_params(self):
        m = deck.Map(ee_initialize=False)
        self.assertIsNotNone(m)

    def test_map_init_custom_center(self):
        m = deck.Map(ee_initialize=False, center=(40, -100))
        self.assertIsNotNone(m)
        self.assertEqual(m.initial_view_state.latitude, 40)
        self.assertEqual(m.initial_view_state.longitude, -100)

    def test_map_init_custom_zoom(self):
        m = deck.Map(ee_initialize=False, zoom=10)
        self.assertIsNotNone(m)
        self.assertEqual(m.initial_view_state.zoom, 10)

    def test_map_init_custom_height(self):
        m = deck.Map(ee_initialize=False, height=600)
        self.assertIsNotNone(m)
        self.assertEqual(m.initial_view_state.height, 600)

    def test_map_default_center(self):
        m = deck.Map(ee_initialize=False)
        self.assertEqual(m.initial_view_state.latitude, 20)
        self.assertEqual(m.initial_view_state.longitude, 0)

    def test_map_default_zoom(self):
        m = deck.Map(ee_initialize=False)
        self.assertEqual(m.initial_view_state.zoom, 1.2)

    def test_map_default_height(self):
        m = deck.Map(ee_initialize=False)
        self.assertEqual(m.initial_view_state.height, 800)

    def test_map_default_map_style(self):
        m = deck.Map(ee_initialize=False)
        self.assertIn("positron", m.map_style)

    def test_map_custom_map_style(self):
        m = deck.Map(ee_initialize=False, map_style="dark")
        self.assertIn("dark", m.map_style)

    def test_map_layers_initially_empty(self):
        m = deck.Map(ee_initialize=False)
        self.assertEqual(len(m.layers), 0)

    def test_add_layer_url(self):
        m = deck.Map(ee_initialize=False)
        m.add_layer("https://example.com/tiles/{z}/{x}/{y}.png", layer_name="test")
        self.assertEqual(len(m.layers), 1)

    def test_add_layer_pydeck_layer(self):
        m = deck.Map(ee_initialize=False)
        layer = pydeck.Layer("ScatterplotLayer", data=[], get_position="[0, 0]")
        m.add_layer(layer)
        self.assertEqual(len(m.layers), 1)

    def test_add_multiple_layers(self):
        m = deck.Map(ee_initialize=False)
        m.add_layer("https://example.com/tiles/{z}/{x}/{y}.png", layer_name="layer1")
        m.add_layer("https://example.com/tiles2/{z}/{x}/{y}.png", layer_name="layer2")
        self.assertEqual(len(m.layers), 2)

    def test_layer_class_exists(self):
        self.assertTrue(hasattr(deck, "Layer"))

    def test_layer_inherits_from_pydeck(self):
        self.assertTrue(issubclass(deck.Layer, pydeck.Layer))

    def test_map_inherits_from_pydeck_deck(self):
        self.assertTrue(issubclass(deck.Map, pydeck.Deck))

    def test_map_has_add_basemap(self):
        m = deck.Map(ee_initialize=False)
        self.assertTrue(hasattr(m, "add_basemap"))

    def test_map_has_add_gdf(self):
        m = deck.Map(ee_initialize=False)
        self.assertTrue(hasattr(m, "add_gdf"))

    def test_map_has_add_vector(self):
        m = deck.Map(ee_initialize=False)
        self.assertTrue(hasattr(m, "add_vector"))


if __name__ == "__main__":
    unittest.main()
