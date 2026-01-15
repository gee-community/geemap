"""The module contains functions for downloading OpenStreetMap data.

It wraps the geometries module of the osmnx package (see
https://osmnx.readthedocs.io/en/stable/osmnx.html#module-osmnx.geometries). Credits to
Geoff Boeing, the developer of the osmnx package.  Most functions for downloading
OpenStreetMap data require tags of map features. The list of commonly used tags can be
found at https://wiki.openstreetmap.org/wiki/Map_features
"""

# *******************************************************************************#
# This module contains extra features of the geemap package.                     #
# The geemap community will maintain the extra features.                         #
# *******************************************************************************#

from typing import Any


def osm_gdf_from_address(address: str, tags: dict[str, Any], dist: int = 1000):
    """Create GeoDataFrame of OSM entities within some distance N, S, E, W of address.

    Args:
        address: The address to geocode and use as the central point around which to get
            the geometries.
        tags: Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        dist: Distance in meters. Defaults to 1000.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    import osmnx as ox

    gdf = ox.features.features_from_address(address, tags, dist)
    return gdf


def osm_shp_from_address(
    address: str, tags: dict[str, Any], filepath: str, dist: int = 1000
) -> None:
    """Download OSM entities within some distance N, S, E, W of address as a shapefile.

    Args:
        address: The address to geocode and use as the central point around which to get
            the geometries.
        tags: Tags used for finding objects in the selected area. Results returned are
            the union, not intersection of each individual tag. Each result matches at
            least one given tag. The dict keys should be OSM tags, (e.g., building,
            landuse, highway, etc) and the dict values should be either True to retrieve
            all items with the given tag, or a string to get a single tag-value
            combination, or a list of strings to get multiple values for the given
            tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath: File path to the output shapefile.
        dist: Distance in meters. Defaults to 1000.
    """
    gdf = osm_gdf_from_address(address, tags, dist)
    gdf.to_file(filepath)


def osm_geojson_from_address(
    address: str, tags: dict[str, Any], filepath: str | None = None, dist: int = 1000
):
    """Download OSM entities within some distance N, S, E, W of address as a GeoJSON.

    Args:
        address: The address to geocode and use as the central point around which to get
            the geometries.
        tags: Tags used for finding objects in the selected area. Results returned are
            the union, not intersection of each individual tag. Each result matches at
            least one given tag. The dict keys should be OSM tags, (e.g., building,
            landuse, highway, etc) and the dict values should be either True to retrieve
            all items with the given tag, or a string to get a single tag-value
            combination, or a list of strings to get multiple values for the given
            tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath: File path to the output GeoJSON. Defaults to None.
        dist: Distance in meters. Defaults to 1000.

    Returns:
       A GeoJSON dictionary of OSM entities.
    """
    gdf = osm_gdf_from_address(address, tags, dist)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_gdf_from_place(query, tags: dict[str, Any], which_result: int | None = None):
    """Create GeoDataFrame of OSM entities within boundaries of geocodable place(s).

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        tags: Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        which_result: Which geocoding result to use. if None, auto-select the first
            (Multi)Polygon or raise an error if OSM doesn't return one. to get the top
            match regardless of geometry type, set which_result=1. Defaults to None.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    import osmnx as ox

    ox.config(use_cache=True, log_console=True)  # pytype: disable=module-attr

    gdf = ox.features.features_from_place(query, tags, which_result=which_result)
    return gdf


def osm_shp_from_place(query, tags, filepath, which_result=None):
    """Download OSM entities within boundaries of geocodable place(s) as a shapefile.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        tags (dict): Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
        which_result (int, optional): Which geocoding result to use. if None,
            auto-select the first (Multi)Polygon or raise an error if OSM doesn't return
            one. to get the top match regardless of geometry type, set
            which_result=1. Defaults to None.
    """
    gdf = osm_gdf_from_place(query, tags, which_result)
    gdf.to_file(filepath)


def osm_geojson_from_place(query, tags, filepath=None, which_result=None):
    """Download OSM entities within boundaries of geocodable place(s) as a GeoJSON.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        tags (dict): Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
        which_result (int, optional): Which geocoding result to use. if None,
            auto-select the first (Multi)Polygon or raise an error if OSM doesn't return
            one. to get the top match regardless of geometry type, set
            which_result=1. Defaults to None.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """

    gdf = osm_gdf_from_place(query, tags, which_result)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_gdf_from_point(center_point, tags, dist=1000):
    """Create GeoDataFrame of OSM entities within some distance N, S, E, W of a point.

    Args:
        center_point (tuple): The (lat, lng) center point around which to get the geometries.
        tags (dict): Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        dist (int, optional): Distance in meters. Defaults to 1000.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    import osmnx as ox

    gdf = ox.features.features_from_point(center_point, tags, dist)
    return gdf


def osm_shp_from_point(
    center_point: tuple[float, float],
    tags: dict[str, Any],
    filepath: str,
    dist: int = 1000,
) -> None:
    """Download OSM entities within some distance N, S, E, W of point as a shapefile.

    Args:
        center_point: The (lat, lng) center point around which to get the geometries.
        tags: Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath: File path to the output shapefile.
        dist: Distance in meters. Defaults to 1000.
    """
    gdf = osm_gdf_from_point(center_point, tags, dist)
    gdf.to_file(filepath)


def osm_geojson_from_point(center_point, tags, filepath=None, dist=1000):
    """Download OSM entities within some distance N, S, E, W of point as a GeoJSON.

    Args:
        center_point (tuple): The (lat, lng) center point around which to get the
            geometries.
        tags (dict): Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
        dist (int, optional): Distance in meters. Defaults to 1000.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """
    gdf = osm_gdf_from_point(center_point, tags, dist)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_gdf_from_polygon(polygon, tags):
    """Create GeoDataFrame of OSM entities within boundaries of a (multi)polygon.

    Args:
        polygon (shapely.geometry.Polygon | shapely.geometry.MultiPolygon): Geographic
          boundaries to fetch geometries within
        tags (dict): Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    import osmnx as ox

    gdf = ox.features.features_from_polygon(polygon, tags)
    return gdf


def osm_shp_from_polygon(polygon, tags, filepath):
    """Download OSM entities within boundaries of a (multi)polygon as a shapefile.

    Args:
        polygon (shapely.geometry.Polygon | shapely.geometry.MultiPolygon): Geographic
            boundaries to fetch geometries within
        tags (dict): Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
    """
    gdf = osm_gdf_from_polygon(polygon, tags)
    gdf.to_file(filepath)


def osm_geojson_from_polygon(polygon, tags, filepath=None):
    """Download OSM entities within boundaries of a (multi)polygon as a GeoJSON.

    Args:
        polygon (shapely.geometry.Polygon | shapely.geometry.MultiPolygon): Geographic
            boundaries to fetch geometries within
        tags (dict): Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str, optional): File path to the output GeoJSON.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """
    gdf = osm_gdf_from_polygon(polygon, tags)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_gdf_from_bbox(north, south, east, west, tags):
    """Create a GeoDataFrame of OSM entities within a N, S, E, W bounding box.

    Args:
        north (float): Northern latitude of bounding box.
        south (float): Southern latitude of bounding box.
        east (float): Eastern longitude of bounding box.
        west (float): Western longitude of bounding box.
        tags (dict): Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    import osmnx as ox

    gdf = ox.features.features_from_bbox(
        north, south, east, west, tags
    )  # pytype: disable=wrong-arg-count
    return gdf


def osm_shp_from_bbox(north, south, east, west, tags, filepath):
    """Download OSM entities within a N, S, E, W bounding box as a shapefile.

    Args:
        north (float): Northern latitude of bounding box.
        south (float): Southern latitude of bounding box.
        east (float): Eastern longitude of bounding box.
        west (float): Western longitude of bounding box.
        tags (dict): Dict of tags used for finding objects in the selected area. Results returned are the union, not intersection of each individual tag. Each result matches at least one given tag. The dict keys should be OSM tags, (e.g., building, landuse, highway, etc) and the dict values should be either True to retrieve all items with the given tag, or a string to get a single tag-value combination, or a list of strings to get multiple values for the given tag. For example, tags = {‘building’: True} would return all building footprints in the area. tags = {‘amenity’:True, ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str): File path to the output shapefile.
    """
    gdf = osm_gdf_from_bbox(north, south, east, west, tags)
    gdf.to_file(filepath)


def osm_geojson_from_bbox(north, south, east, west, tags, filepath=None):
    """Download OSM entities within a N, S, E, W bounding box as a GeoJSON.

    Args:
        north (float): Northern latitude of bounding box.
        south (float): Southern latitude of bounding box.
        east (float): Eastern longitude of bounding box.
        west (float): Western longitude of bounding box.
        tags (dict): Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.
        filepath (str, optional): File path to the output GeoJSON.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """
    gdf = osm_gdf_from_bbox(north, south, east, west, tags)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_gdf_from_xml(filepath, polygon=None, tags=None):
    """Create a GeoDataFrame of OSM entities in an OSM-formatted XML file.

    Args:
        filepath (str): File path to file containing OSM XML data
        polygon (shapely.geometry.Polygon, optional): Optional geographic boundary to
            filter objects. Defaults to None.
        tags (dict): Dict of tags used for finding objects in the selected area. Results
            returned are the union, not intersection of each individual tag. Each result
            matches at least one given tag. The dict keys should be OSM tags, (e.g.,
            building, landuse, highway, etc) and the dict values should be either True
            to retrieve all items with the given tag, or a string to get a single
            tag-value combination, or a list of strings to get multiple values for the
            given tag. For example, tags = {‘building’: True} would return all building
            footprints in the area. tags = {‘amenity’:True,
            ‘landuse’:[‘retail’,’commercial’], ‘highway’:’bus_stop’} would return all
            amenities, landuse=retail, landuse=commercial, and highway=bus_stop.

    Returns:
        GeoDataFrame: A GeoDataFrame of OSM entities.
    """
    import osmnx as ox

    gdf = ox.features.features_from_xml(
        filepath, polygon, tags
    )  # pytype: disable=wrong-arg-count
    return gdf


def osm_gdf_from_geocode(
    query,
    which_result=None,
    by_osmid=False,
):
    """Retrieves place(s) by name or ID from the Nominatim API as a GeoDataFrame.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        which_result (int, optional): Which geocoding result to use. if None,
            auto-select the first (Multi)Polygon or raise an error if OSM doesn't return
            one. to get the top match regardless of geometry type, set
            which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather
            than text search. Defaults to False.

    Returns:
        GeoDataFrame: A GeoPandas GeoDataFrame.
    """
    import osmnx as ox

    gdf = ox.geocoder.geocode_to_gdf(
        query, which_result=which_result, by_osmid=by_osmid
    )
    return gdf


def osm_shp_from_geocode(
    query,
    filepath,
    which_result=None,
    by_osmid=False,
):
    """Download place(s) by name or ID from the Nominatim API as a shapefile.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        filepath (str): File path to the output shapefile.
        which_result (int, optional): Which geocoding result to use. if None,
            auto-select the first (Multi)Polygon or raise an error if OSM doesn't return
            one. to get the top match regardless of geometry type, set
            which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather
            than text search. Defaults to False.
    """
    gdf = osm_gdf_from_geocode(query, which_result, by_osmid)
    gdf.to_file(filepath)


def osm_geojson_from_geocode(
    query,
    filepath=None,
    which_result=None,
    by_osmid=False,
):
    """Download place(s) by name or ID from the Nominatim API as a GeoJSON.

    Args:
        query (str | dict | list): Query string(s) or structured dict(s) to geocode.
        filepath (str): File path to the output GeoJSON.
        which_result (int, optional): Which geocoding result to use. if None,
            auto-select the first (Multi)Polygon or raise an error if OSM doesn't return
            one. to get the top match regardless of geometry type, set
            which_result=1. Defaults to None.
        by_osmid (bool, optional): If True, handle query as an OSM ID for lookup rather
            than text search. Defaults to False.

    Returns:
        dict: A GeoJSON dictionary of OSM entities.
    """
    gdf = osm_gdf_from_geocode(query, which_result, by_osmid)
    if filepath is not None:
        gdf.to_file(filepath, driver="GeoJSON")
    else:
        return gdf.__geo_interface__


def osm_tags_list() -> None:
    """Open a browser to see all tags of OSM features."""
    import webbrowser

    webbrowser.open_new_tab("https://wiki.openstreetmap.org/wiki/Map_features")
