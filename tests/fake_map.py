import ee

from geemap import ee_tile_layers


class FakeMap:
    """A fake map used for initializing widgets."""

    def __init__(self):
        self.default_style = {}
        self.interaction_handlers = set()
        self.scale = 1024
        self.zoom = 7
        self.layers = []
        self.ee_layers = {}
        self.geojson_layers = []
        self.controls = []

        self._recognized_attrs = self.__dict__.keys()

    def __setattr__(self, k, v):
        if hasattr(self, "_recognized_attrs") and k not in self._recognized_attrs:
            raise AttributeError(f"{k} is not a recognized attr")
        super(FakeMap, self).__setattr__(k, v)

    def on_interaction(self, func, remove=False):
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

    def click(self, coordinates, event_type):
        for handler in self.interaction_handlers:
            handler(coordinates=coordinates, type=event_type)

    def get_scale(self):
        return self.scale

    def find_layer_index(self, name):
        layers = self.layers

        for index, layer in enumerate(layers):
            if layer.name == name:
                return index

        return -1

    def add_layer(
        self,
        ee_object,
        vis_params=None,
        name=None,
        shown=True,
        opacity=1.0,
    ):
        layer = ee_object
        if isinstance(
            ee_object,
            (
                ee.FeatureCollection,
                ee.Feature,
                ee.Geometry,
                ee.Image,
            ),
        ):
            layer = ee_tile_layers.EELeafletTileLayer(
                ee_object, vis_params, name, shown, opacity
            )
            self.ee_layers[name] = {
                "ee_object": ee_object,
                "ee_layer": layer,
                "vis_params": vis_params,
            }
        self.layers.append(layer)

    def add(self, obj):
        del obj  # Unused.

    def remove_layer(self, layer):
        if isinstance(layer, str):
            layer = self.ee_layers[layer]["ee_layer"]
        self.layers.remove(layer)
        del self.ee_layers[layer.name]

    def get_layer_names(self):
        return [layer.name for layer in self.layers]

    def zoom_to_bounds(self, _):
        pass

    def substitute(self, old_layer, new_layer):
        i = self.find_layer_index(old_layer)
        if i >= 0:
            self.layers[i] = new_layer

    def add_basemap(self, basemap="HYBRID", show=True, **kwargs):
        self.add_layer(FakeTileLayer(name=basemap, visible=show))

    def _add_legend(
        self,
        title=None,
        keys=None,
        colors=None,
        position=None,
        builtin_legend=None,
        layer_name=None,
        add_header=None,
        widget_args=None,
        **kwargs,
    ):
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
        vis_params=None,
        cmap=None,
        discrete=None,
        label=None,
        orientation=None,
        position=None,
        transparent_bg=None,
        layer_name=None,
        font_size=None,
        axis_off=None,
        max_width=None,
        **kwargs,
    ):
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
    def cursor_style(self):
        return self.default_style.get("cursor")


class FakeEeTileLayer:
    def __init__(self, name="test-layer", visible=True, opacity=1.0):
        self.name = name
        self.visible = visible
        self.opacity = opacity

    def observe(self, func, names):
        pass


class FakeTileLayer:
    def __init__(self, name="test-layer", visible=True, opacity=1.0):
        self.name = name
        self.visible = visible
        self.opacity = opacity

    def observe(self, func, names):
        pass


class FakeGeoJSONLayer:
    def __init__(self, name="test-layer", visible=True, style=None):
        self.name = name
        self.visible = visible
        self.style = style or {}

    def observe(self, func, names):
        pass
