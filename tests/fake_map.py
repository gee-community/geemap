class FakeMap:
    """A fake map used for initializing widgets."""

    def __init__(self):
        self.default_style = {}
        self.interaction_handlers = set()
        self.scale = 1024
        self.zoom = 7
        self.ee_layer_dict = {}

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

    @property
    def cursor_style(self):
        return self.default_style.get("cursor")


class FakeEeTileLayer:
    def __init__(self, visible):
        self.visible = visible
