"""All draw control implementations for each type of map."""

import enum

import ee
import ipyleaflet
import ipywidgets

from . import common
from .ee_tile_layers import EELeafletTileLayer


class DrawActions(enum.Enum):
    """Action types for the draw control.

    Args:
        enum (str): Action type.
    """

    CREATED = "created"
    EDITED = "edited"
    DELETED = "deleted"
    REMOVED_LAST = "removed-last"


class AbstractDrawControl(object):
    """Abstract class for the draw control."""

    host_map = None
    layer = None
    geometries = []
    properties = []
    last_geometry = None
    last_draw_action = None
    _geometry_create_dispatcher = ipywidgets.CallbackDispatcher()
    _geometry_edit_dispatcher = ipywidgets.CallbackDispatcher()
    _geometry_delete_dispatcher = ipywidgets.CallbackDispatcher()

    def __init__(self, host_map):
        """Initialize the draw control.

        Args:
            host_map (geemap.Map): The geemap.Map instance to be linked with the draw control.
        """

        self.host_map = host_map
        self.layer = None
        self.geometries = []
        self.properties = []
        self.last_geometry = None
        self.last_draw_action = None
        self._geometry_create_dispatcher = ipywidgets.CallbackDispatcher()
        self._geometry_edit_dispatcher = ipywidgets.CallbackDispatcher()
        self._geometry_delete_dispatcher = ipywidgets.CallbackDispatcher()
        self._bind_to_draw_control()

    @property
    def features(self):
        if self.count:
            features = []
            for i, geometry in enumerate(self.geometries):
                if i < len(self.properties):
                    property = self.properties[i]
                else:
                    property = None
                features.append(ee.Feature(geometry, property))
            return features
        else:
            return []

    @property
    def collection(self):
        return ee.FeatureCollection(self.features if self.count else [])

    @property
    def last_feature(self):
        property = self.get_geometry_properties(self.last_geometry)
        return ee.Feature(self.last_geometry, property) if self.last_geometry else None

    @property
    def count(self):
        return len(self.geometries)

    def reset(self, clear_draw_control=True):
        """Resets the draw controls."""
        if self.layer is not None:
            self.host_map.remove_layer(self.layer)
        self.geometries = []
        self.properties = []
        self.last_geometry = None
        self.layer = None
        if clear_draw_control:
            self._clear_draw_control()

    def remove_geometry(self, geometry):
        """Removes a geometry from the draw control."""
        if not geometry:
            return
        try:
            index = self.geometries.index(geometry)
        except ValueError:
            return
        if index >= 0:
            del self.geometries[index]
            del self.properties[index]
            self._remove_geometry_at_index_on_draw_control(index)
            if index == self.count and geometry == self.last_geometry:
                # Treat this like an "undo" of the last drawn geometry.
                if len(self.geometries):
                    self.last_geometry = self.geometries[-1]
                else:
                    self.last_geometry = geometry
                self.last_draw_action = DrawActions.REMOVED_LAST
            if self.layer is not None:
                self._redraw_layer()

    def get_geometry_properties(self, geometry):
        """Gets the properties of a geometry."""
        if not geometry:
            return None
        try:
            index = self.geometries.index(geometry)
        except ValueError:
            return None
        if index >= 0:
            return self.properties[index]
        else:
            return None

    def set_geometry_properties(self, geometry, property):
        """Sets the properties of a geometry."""
        if not geometry:
            return
        try:
            index = self.geometries.index(geometry)
        except ValueError:
            return
        if index >= 0:
            self.properties[index] = property

    def on_geometry_create(self, callback, remove=False):
        self._geometry_create_dispatcher.register_callback(callback, remove=remove)

    def on_geometry_edit(self, callback, remove=False):
        self._geometry_edit_dispatcher.register_callback(callback, remove=remove)

    def on_geometry_delete(self, callback, remove=False):
        self._geometry_delete_dispatcher.register_callback(callback, remove=remove)

    def _bind_to_draw_control(self):
        """Set up draw control event handling like create, edit, and delete."""
        raise NotImplementedError()

    def _remove_geometry_at_index_on_draw_control(self):
        """Remove the geometry at the given index on the draw control."""
        raise NotImplementedError()

    def _clear_draw_control(self):
        """Clears the geometries from the draw control."""
        raise NotImplementedError()

    def _get_synced_geojson_from_draw_control(self):
        """Returns an up-to-date list of GeoJSON from the draw control."""
        raise NotImplementedError()

    def _sync_geometries(self):
        """Sync the local geometries with those from the draw control."""
        if not self.count:
            return
        # The current geometries from the draw_control.
        test_geojsons = self._get_synced_geojson_from_draw_control()
        i = 0
        while i < self.count and i < len(test_geojsons):
            local_geometry = None
            test_geometry = None
            while i < self.count and i < len(test_geojsons):
                local_geometry = self.geometries[i]
                test_geometry = common.geojson_to_ee(test_geojsons[i], False)
                if test_geometry == local_geometry:
                    i += 1
                else:
                    break
            if i < self.count and test_geometry is not None:
                self.geometries[i] = test_geometry
        if self.layer is not None:
            self._redraw_layer()

    def _redraw_layer(self):
        if self.host_map:
            self.host_map.add_layer(
                self.collection, {"color": "blue"}, "Drawn Features", False, 0.5
            )
            self.layer = self.host_map.ee_layers.get("Drawn Features").get("ee_layer")

    def _handle_geometry_created(self, geo_json):
        geometry = common.geojson_to_ee(geo_json, False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.CREATED
        self.geometries.append(geometry)
        self.properties.append(None)
        self._redraw_layer()
        self._geometry_create_dispatcher(self, geometry=geometry)

    def _handle_geometry_edited(self, geo_json):
        geometry = common.geojson_to_ee(geo_json, False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.EDITED
        self._sync_geometries()
        self._redraw_layer()
        self._geometry_edit_dispatcher(self, geometry=geometry)

    def _handle_geometry_deleted(self, geo_json):
        geometry = common.geojson_to_ee(geo_json, False)
        self.last_geometry = geometry
        self.last_draw_action = DrawActions.DELETED
        try:
            index = self.geometries.index(geometry)
        except ValueError:
            return
        if index >= 0:
            del self.geometries[index]
            del self.properties[index]
            self._redraw_layer()
            self._geometry_delete_dispatcher(self, geometry=geometry)


class MapDrawControl(ipyleaflet.DrawControl, AbstractDrawControl):
    """Implements the AbstractDrawControl for ipleaflet Map."""

    def __init__(self, host_map, **kwargs):
        """Initialize the map draw control.

        Args:
            host_map (geemap.Map): The geemap.Map object that the control will be added to.
        """
        super(MapDrawControl, self).__init__(host_map=host_map, **kwargs)

    # NOTE: Overridden for backwards compatibility, where edited geometries are
    # added to the layer instead of modified in place. Remove when
    # https://github.com/jupyter-widgets/ipyleaflet/issues/1119 is fixed to
    # allow geometry edits to be reflected on the tile layer.
    def _handle_geometry_edited(self, geo_json):
        return self._handle_geometry_created(geo_json)

    def _get_synced_geojson_from_draw_control(self):
        return [data.copy() for data in self.data]

    def _bind_to_draw_control(self):
        # Handles draw events
        def handle_draw(_, action, geo_json):
            try:
                if action == "created":
                    self._handle_geometry_created(geo_json)
                elif action == "edited":
                    self._handle_geometry_edited(geo_json)
                elif action == "deleted":
                    self._handle_geometry_deleted(geo_json)
            except Exception as e:
                self.reset(clear_draw_control=False)
                print("There was an error creating Earth Engine Feature.")
                raise Exception(e)

        self.on_draw(handle_draw)
        # NOTE: Uncomment the following code once
        # https://github.com/jupyter-widgets/ipyleaflet/issues/1119 is fixed
        # to allow edited geometries to be reflected instead of added.
        # def handle_data_update(_):
        #     self._sync_geometries()
        # self.observe(handle_data_update, 'data')

    def _remove_geometry_at_index_on_draw_control(self, index):
        # NOTE: Uncomment the following code once
        # https://github.com/jupyter-widgets/ipyleaflet/issues/1119 is fixed to
        # remove drawn geometries with `remove_last_drawn()`.
        # del self.data[index]
        # self.send_state(key='data')
        pass

    def _clear_draw_control(self):
        self.data = []  # Remove all drawn features from the map.
        return self.clear()
