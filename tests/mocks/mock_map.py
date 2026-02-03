from __future__ import annotations

import unittest.mock

import ipywidgets
import traitlets

from tests.mocks import mock_ee


class FakeMap:

    def __init__(self) -> None:
        self.default_style: dict = {}
        self.interaction_handlers: set = set()
        self.scale: int = 1024
        self.zoom: int = 7
        self.center: list = [0, 0]
        self.layers: list = []
        self.ee_layers: dict = {}
        self.geojson_layers: list = []
        self.controls: list = []
        self.add = unittest.mock.MagicMock()

        self._recognized_attrs = set(self.__dict__.keys())

    def __setattr__(self, k: str, v) -> None:
        if hasattr(self, "_recognized_attrs") and k not in self._recognized_attrs:
            raise AttributeError(f"{k} is not a recognized attr")
        super().__setattr__(k, v)

    def on_interaction(self, func, remove: bool = False) -> None:
        if remove:
            if func in self.interaction_handlers:
                self.interaction_handlers.remove(func)
            else:
                raise ValueError("Removing an unknown on_interaction func.")
        else:
            if func in self.interaction_handlers:
                raise ValueError("This on_interaction func already exists.")
            else:
                self.interaction_handlers.add(func)

    def click(self, coordinates: tuple, event_type: str) -> None:
        for handler in self.interaction_handlers:
            handler(coordinates=coordinates, type=event_type)

    def get_scale(self) -> int:
        return self.scale

    @property
    def bounds(self) -> tuple:
        return ((1, 2), (3, 4))

    def find_layer_index(self, name: str) -> int:
        layers = self.layers
        for index, layer in enumerate(layers):
            if layer.name == name:
                return index
        return -1

    def add_layer(
        self,
        ee_object,
        vis_params: dict | None = None,
        name: str | None = None,
        shown: bool = True,
        opacity: float = 1.0,
    ) -> None:
        layer = ee_object
        if isinstance(
            ee_object,
            (
                mock_ee.FeatureCollection,
                mock_ee.Feature,
                mock_ee.Geometry,
                mock_ee.Image,
            ),
        ):
            layer = FakeEeTileLayer(
                name=name or "layer", visible=shown, opacity=opacity
            )
            self.ee_layers[name] = {
                "ee_object": ee_object,
                "ee_layer": layer,
                "vis_params": vis_params,
            }
        self.layers.append(layer)

    def remove_layer(self, layer) -> None:
        if isinstance(layer, str):
            layer = self.ee_layers[layer]["ee_layer"]
        self.layers.remove(layer)
        del self.ee_layers[layer.name]

    def get_layer_names(self) -> list[str]:
        return [layer.name for layer in self.layers]

    def zoom_to_bounds(self, _) -> None:
        pass

    def substitute(self, old_layer: str, new_layer) -> None:
        i = self.find_layer_index(old_layer)
        if i >= 0:
            self.layers[i] = new_layer

    def add_basemap(self, basemap: str = "HYBRID", show: bool = True, **kwargs) -> None:
        self.add_layer(FakeTileLayer(name=basemap, visible=show))

    def _add_legend(
        self,
        title: str | None = None,
        keys: list | None = None,
        colors: list | None = None,
        position: str | None = None,
        builtin_legend: str | None = None,
        layer_name: str | None = None,
        add_header: bool | None = None,
        widget_args: dict | None = None,
        **kwargs,
    ) -> None:
        del (
            title,
            keys,
            colors,
            position,
            builtin_legend,
            add_header,
            widget_args,
            kwargs,
        )
        if layer := self.ee_layers.get(layer_name):
            layer["legend"] = {}

    def _add_colorbar(
        self,
        vis_params: dict | None = None,
        cmap: str | None = None,
        discrete: bool | None = None,
        label: str | None = None,
        orientation: str | None = None,
        position: str | None = None,
        transparent_bg: bool | None = None,
        layer_name: str | None = None,
        font_size: int | None = None,
        axis_off: bool | None = None,
        max_width: str | None = None,
        **kwargs,
    ) -> None:
        del (
            vis_params,
            cmap,
            discrete,
            label,
            orientation,
            position,
            transparent_bg,
            font_size,
            axis_off,
            max_width,
            kwargs,
        )
        if layer := self.ee_layers.get(layer_name):
            layer["colorbar"] = {}

    @property
    def cursor_style(self) -> str | None:
        return self.default_style.get("cursor")

    def set_center(self, lon: float, lat: float, zoom: int | None = None) -> None:
        self.center = [lat, lon]
        if zoom is not None:
            self.zoom = zoom


class FakeEeTileLayer:

    def __init__(
        self,
        name: str = "test-layer",
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        self.name = name
        self.visible = visible
        self.opacity = opacity

    def observe(self, func, names) -> None:
        pass

    def calculate_vis_minmax(
        self,
        *,
        bounds,
        bands: list[str] | None = None,
        percent: float | None = None,
        sigma: float | None = None,
    ) -> tuple[float, float]:
        return (21, 42)


class FakeTileLayer(ipywidgets.Widget):

    name = traitlets.Unicode("").tag(sync=True)
    visible = traitlets.Bool(True).tag(sync=True)
    opacity = traitlets.Float(1).tag(sync=True)
    loading = traitlets.Bool(False).tag(sync=True)

    def __init__(
        self,
        name: str = "test-layer",
        visible: bool = True,
        opacity: float = 1.0,
    ) -> None:
        super().__init__()
        self.name = name
        self.visible = visible
        self.opacity = opacity


class FakeGeoJSONLayer:

    def __init__(
        self,
        name: str = "test-layer",
        visible: bool = True,
        style: dict | None = None,
    ) -> None:
        self.name = name
        self.visible = visible
        self.style = style or {}

    def observe(self, func, names) -> None:
        pass
