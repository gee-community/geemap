"""Module for basemaps.

Each basemap is defined as an item in the `basemaps` dictionary.

More WMS basemaps can be found at the following websites:

  1. USGS National Map: https://viewer.nationalmap.gov/services/
  2. MRLC NLCD Land Cover data: https://viewer.nationalmap.gov/services/
  3. FWS NWI Wetlands data: https://www.fws.gov/wetlands/Data/Web-Map-Services.html

"""

# *******************************************************************************#
# This module contains core features and extra features of the geemap package.   #
# The Earth Engine team and the geemap community will maintain the core features.#
# The geemap community will maintain the extra features.                         #
# The core features include classes and functions below until the line # ******* #
# *******************************************************************************#

# pylint: disable=line-too-long

import collections
import os
from typing import Any
import urllib.parse

import folium
import ipyleaflet
import requests
import traitlets
import xyzservices

from . import common
from . import coreutils

OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_ATTRIBUTION = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">'
    "OpenStreetMap</a> contributors"
)
OSM_MAX_NATIVE_ZOOM = 19
OSM_REFERRER_POLICY = "strict-origin-when-cross-origin"

XYZ_TILES = {
    "OpenStreetMap": {
        "url": OSM_URL,
        "attribution": OSM_ATTRIBUTION,
        "name": "OpenStreetMap",
        "max_native_zoom": OSM_MAX_NATIVE_ZOOM,
    },
    "ROADMAP": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        "attribution": "Esri",
        "name": "Esri.WorldStreetMap",
    },
    "SATELLITE": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attribution": "Esri",
        "name": "Esri.WorldImagery",
        "max_zoom": 30,
    },
    "TERRAIN": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        "attribution": "Esri",
        "name": "Esri.WorldTopoMap",
        "max_zoom": 30,
    },
    "HYBRID": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attribution": "Esri",
        "name": "Esri.WorldImagery",
        "max_zoom": 30,
    },
}


# Custom WMS tile services.
WMS_TILES = {
    "FWS NWI Wetlands": {
        "url": "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/services/Wetlands/MapServer/WMSServer?",
        "layers": "1",
        "name": "FWS NWI Wetlands",
        "attribution": "FWS",
        "format": "image/png",
        "transparent": True,
    },
    "FWS NWI Wetlands Raster": {
        "url": "https://www.fws.gov/wetlands/arcgis/services/Wetlands_Raster/ImageServer/WMSServer?",
        "layers": "0",
        "name": "FWS NWI Wetlands Raster",
        "attribution": "FWS",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2021 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2021_Land_Cover_L48/wms?",
        "layers": "NLCD_2021_Land_Cover_L48",
        "name": "NLCD 2021 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2019 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2019_Land_Cover_L48/wms?",
        "layers": "NLCD_2019_Land_Cover_L48",
        "name": "NLCD 2019 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2016 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2016_Land_Cover_L48/wms?",
        "layers": "NLCD_2016_Land_Cover_L48",
        "name": "NLCD 2016 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2013 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2013_Land_Cover_L48/wms?",
        "layers": "NLCD_2013_Land_Cover_L48",
        "name": "NLCD 2013 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2011 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2011_Land_Cover_L48/wms?",
        "layers": "NLCD_2011_Land_Cover_L48",
        "name": "NLCD 2011 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2008 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2008_Land_Cover_L48/wms?",
        "layers": "NLCD_2008_Land_Cover_L48",
        "name": "NLCD 2008 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2006 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2006_Land_Cover_L48/wms?",
        "layers": "NLCD_2006_Land_Cover_L48",
        "name": "NLCD 2006 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2004 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2004_Land_Cover_L48/wms?",
        "layers": "NLCD_2004_Land_Cover_L48",
        "name": "NLCD 2004 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "NLCD 2001 CONUS Land Cover": {
        "url": "https://www.mrlc.gov/geoserver/mrlc_display/NLCD_2001_Land_Cover_L48/wms?",
        "layers": "NLCD_2001_Land_Cover_L48",
        "name": "NLCD 2001 CONUS Land Cover",
        "attribution": "MRLC",
        "format": "image/png",
        "transparent": True,
    },
    "USGS NAIP Imagery": {
        "url": "https://imagery.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?",
        "layers": "USGSNAIPImagery:NaturalColor",
        "name": "USGS NAIP Imagery",
        "attribution": "USGS",
        "format": "image/png",
        "transparent": True,
        "max_zoom": 30,
    },
    "USGS NAIP Imagery False Color": {
        "url": "https://imagery.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?",
        "layers": "USGSNAIPImagery:FalseColorComposite",
        "name": "USGS NAIP Imagery False Color",
        "attribution": "USGS",
        "format": "image/png",
        "transparent": True,
    },
    "USGS NAIP Imagery NDVI": {
        "url": "https://imagery.nationalmap.gov/arcgis/services/USGSNAIPImagery/ImageServer/WMSServer?",
        "layers": "USGSNAIPImagery:NDVI_Color",
        "name": "USGS NAIP Imagery NDVI",
        "attribution": "USGS",
        "format": "image/png",
        "transparent": True,
    },
    "USGS Hydrography": {
        "url": "https://basemap.nationalmap.gov/arcgis/services/USGSHydroCached/MapServer/WMSServer?",
        "layers": "0",
        "name": "USGS Hydrography",
        "attribution": "USGS",
        "format": "image/png",
        "transparent": True,
    },
    "USGS 3DEP Elevation": {
        "url": "https://elevation.nationalmap.gov/arcgis/services/3DEPElevation/ImageServer/WMSServer?",
        "layers": "33DEPElevation:Hillshade Elevation Tinted",
        "name": "USGS 3DEP Elevation",
        "attribution": "USGS",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2020": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2020_MAP",
        "name": "ESA Worldcover 2020",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2020 S2 FCC": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2020_S2_FCC",
        "name": "ESA Worldcover 2020 S2 FCC",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2020 S2 TCC": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2020_S2_TCC",
        "name": "ESA Worldcover 2020 S2 TCC",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2021": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2021_MAP",
        "name": "ESA Worldcover 2021",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2021 S2 FCC": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2021_S2_FCC",
        "name": "ESA Worldcover 2021 S2 FCC",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
    "ESA WorldCover 2021 S2 TCC": {
        "url": "https://services.terrascope.be/wms/v2",
        "layers": "WORLDCOVER_2021_S2_TCC",
        "name": "ESA Worldcover 2021 S2 TCC",
        "attribution": "ESA",
        "format": "image/png",
        "transparent": True,
    },
}

custom_tiles = {"xyz": XYZ_TILES, "wms": WMS_TILES}


class GoogleMapsTileProvider(xyzservices.TileProvider):
    """Google Maps TileProvider."""

    MAP_TYPE_CONFIG = {
        "roadmap": {"mapType": "roadmap"},
        "satellite": {"mapType": "satellite"},
        "terrain": {
            "mapType": "terrain",
            "layerTypes": ["layerRoadmap"],
        },
        "hybrid": {
            "mapType": "satellite",
            "layerTypes": ["layerRoadmap"],
        },
    }

    def __init__(
        self,
        map_type: str = "roadmap",
        language: str = "en-Us",
        region: str = "US",
        api_key: str | None = None,
        **kwargs,
    ):
        """Generates Google Map tiles using the provided parameters.

        To get an API key and enable Map Tiles API, visit
        https://developers.google.com/maps/get-started#create-project.  You can set the
        API key using the environment variable `GOOGLE_MAPS_API_KEY` or by passing it as
        an argument.

        Args:
            map_type: The type of map to generate. Options are 'roadmap', 'satellite',
                'terrain', 'hybrid', 'traffic', 'streetview'.
            language: An IETF language tag that specifies the language used to display
                information on the tiles, such as 'zh-Cn'.
            region: A Common Locale Data Repository region identifier (two uppercase
                letters) that represents the physical location of the user.
            api_key: The API key to use for the Google Maps API.  If not provided, it
                will try to get it from the environment or Colab user data with the key
                'GOOGLE_MAPS_API_KEY'.
            **kwargs: Additional parameters to pass to the map generation. For more
                info, visit https://bit.ly/3UhbZKU

        Raises:
            ValueError: If the API key is not provided and cannot be found in the
                environment or Colab user data.
            ValueError: If the map_type is not one of the allowed types.

        Example:
            >>> from geemap.basemaps import GoogleMapsTileProvider
            >>> m = geemap.Map()
            >>> basemap = GoogleMapsTileProvider(map_type='roadmap',
                language="en-Us", region="US", scale="scaleFactor2x", highDpi=True)
            >>> m.add_basemap(basemap)
        """
        key = api_key or coreutils.get_google_maps_api_key()
        if key is None:
            raise ValueError(
                "API key is required to access Google Maps API. To get an API "
                "key and enable Map Tiles API, visit "
                "https://developers.google.com/maps/get-started#create-project"
            )

        if map_type not in self.MAP_TYPE_CONFIG:
            raise ValueError(f"map_type must be one of: {self.MAP_TYPE_CONFIG.keys()}")

        request_url = f"https://tile.googleapis.com/v1/createSession?key={key}"
        response = requests.post(
            url=request_url,
            headers={"Content-Type": "application/json"},
            json={
                **self.MAP_TYPE_CONFIG[map_type],
                "language": language,
                "region": region,
                **kwargs,
            },
            timeout=3,
        )

        if (
            response.status_code == requests.codes.ok
        ):  # pyrefly: ignore[missing-attribute]
            json = response.json()
            map_name = map_type.capitalize()
            super().__init__(
                {
                    "url": f"https://tile.googleapis.com/v1/2dtiles/{{z}}/{{x}}/{{y}}?session={json['session']}&key={{accessToken}}",
                    "attribution": f"© Google {map_name}",
                    "accessToken": key,
                    "name": f"Google.{map_name}",
                    "ext": json["imageFormat"],
                    "tileSize": json["tileWidth"],
                }
            )
        else:
            raise RuntimeError(
                f"Error creating a Maps API session:\n{response.json()}."
            )


def get_google_map_tile_providers(
    language: str = "en-Us",
    region: str = "US",
    api_key: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Generates a dictionary of Google Map tile providers for different map types.

    Args:
        language: An IETF language tag that specifies the language used to display
            information on the tiles, such as 'zh-Cn'.
        region: A Common Locale Data Repository region identifier (two uppercase
            letters) that represents the physical location of the user.
        api_key: The API key to use for the Google Maps API. If not provided, it will
            try to get it from the environment or Colab user data with the key
            'GOOGLE_MAPS_API_KEY'.
        **kwargs: Additional parameters to pass to the map generation. For more info,
            visit https://bit.ly/3UhbZKU

    Returns:
        A dictionary where the keys are the map types ('roadmap', 'satellite',
        'terrain', 'hybrid') and the values are the corresponding GoogleMapsTileProvider
        objects.
    """
    gmap_providers = {}

    for m_type in GoogleMapsTileProvider.MAP_TYPE_CONFIG:
        gmap_providers[m_type] = GoogleMapsTileProvider(
            map_type=m_type, language=language, region=region, api_key=api_key, **kwargs
        )

    return gmap_providers


def get_xyz_dict(free_only: bool = True, france: bool = False) -> dict[str, Any]:
    """Returns a dictionary of xyz services.

    Args:
        free_only: Whether to return only free xyz tile services that do not require an
            access token.
        france: Whether to include Geoportail France basemaps.

    Returns:
        dict: A dictionary of xyz services.
    """
    xyz_bunch = xyzservices.providers

    if free_only:
        xyz_bunch = xyz_bunch.filter(requires_token=False)
    if not france:
        xyz_bunch = xyz_bunch.filter(
            function=lambda tile: "france" not in dict(tile)["name"].lower()
        )

    xyz_dict = xyz_bunch.flatten()

    for key, value in xyz_dict.items():
        tile = xyzservices.TileProvider(value)
        if "type" not in tile:
            tile["type"] = "xyz"
        xyz_dict[key] = tile

    xyz_dict = collections.OrderedDict(sorted(xyz_dict.items()))
    return xyz_dict


def get_default_referrer_policy(url: str) -> str | None:
    """Returns the default referrer policy required for a tile URL, if any.

    OpenStreetMap's tile servers block browser tile requests that omit the HTTP
    Referer header (such as cells rendered inside no-referrer sandboxed iframes).
    Using strict-origin-when-cross-origin sends only the origin over HTTPS
    without exposing URL paths or query parameters.
    """
    if not isinstance(url, str) or not url:
        return None
    if url.strip().lower() == "openstreetmap":
        return OSM_REFERRER_POLICY
    hostname = urllib.parse.urlparse(url.replace("{s}.", "")).hostname or ""
    hostname = hostname.lower()
    if hostname == "openstreetmap.org" or hostname.endswith(".openstreetmap.org"):
        return OSM_REFERRER_POLICY
    return None


class TileLayer(ipyleaflet.TileLayer):
    """An ipyleaflet TileLayer with referrerPolicy support."""

    referrer_policy = traitlets.Unicode(default_value=None, allow_none=True).tag(
        sync=True, o=True
    )

    def __init__(self, **kwargs: Any) -> None:
        url = kwargs.setdefault("url", OSM_URL)
        if "referrer_policy" not in kwargs:
            policy = get_default_referrer_policy(url)
            if policy is not None:
                kwargs["referrer_policy"] = policy
        super().__init__(**kwargs)


def configure_leaflet_tile_layer(layer: Any) -> None:
    """Ensures an ipyleaflet TileLayer sets referrerPolicy when required."""
    if not isinstance(layer, ipyleaflet.TileLayer):
        return
    policy = get_default_referrer_policy(getattr(layer, "url", ""))
    if policy is None:
        return
    if not layer.has_trait("referrer_policy"):
        layer.add_traits(
            referrer_policy=traitlets.Unicode(default_value=None, allow_none=True).tag(
                sync=True, o=True
            )
        )
    if getattr(layer, "referrer_policy", None) is None:
        layer.referrer_policy = policy  # pyrefly: ignore[missing-attribute]
    if "referrer_policy" not in layer.options:
        layer.options = list(layer.options) + ["referrer_policy"]


def configure_folium_tile_layer(layer: Any) -> None:
    """Ensures a Folium TileLayer sets referrerPolicy when required."""
    if not isinstance(layer, folium.raster_layers.TileLayer):
        return
    policy = get_default_referrer_policy(getattr(layer, "tiles", ""))
    if policy is None:
        return
    if "referrer_policy" not in layer.options and "referrerPolicy" not in layer.options:
        layer.options["referrer_policy"] = policy


def basemap_to_tiles(basemap: Any, **kwargs: Any) -> TileLayer:
    """Converts a basemap TileProvider or dictionary into a TileLayer."""
    if isinstance(basemap, xyzservices.TileProvider):
        url = basemap.build_url()
    elif isinstance(basemap, dict):
        url = basemap.get("url", "")
    else:
        raise ValueError(f"Invalid basemap type: {type(basemap)}")

    if "attribution" in kwargs and kwargs["attribution"] is not None:
        attribution = kwargs.pop("attribution")
    else:
        kwargs.pop("attribution", None)
        attribution = (
            basemap.get("html_attribution") or basemap.get("attribution") or ""
        )

    if "name" in kwargs and kwargs["name"] is not None:
        name = kwargs.pop("name")
    else:
        kwargs.pop("name", None)
        name = basemap.get("name", "")

    max_zoom = kwargs.pop("max_zoom", None)
    if max_zoom is None:
        max_zoom = basemap.get("max_zoom")
    if max_zoom is None:
        max_zoom = 24

    min_zoom = kwargs.pop("min_zoom", None)
    if min_zoom is None:
        min_zoom = basemap.get("min_zoom")
    if min_zoom is None:
        min_zoom = 0

    max_native_zoom = kwargs.pop("max_native_zoom", basemap.get("max_native_zoom"))
    if (
        max_native_zoom is None
        and "max_zoom" in basemap
        and basemap["max_zoom"] is not None
        and max_zoom > basemap["max_zoom"]
    ):
        max_native_zoom = basemap["max_zoom"]

    return TileLayer(
        url=url,
        name=name,
        attribution=attribution,
        max_zoom=max_zoom,
        min_zoom=min_zoom,
        max_native_zoom=max_native_zoom,
        **kwargs,
    )


def xyz_to_leaflet() -> dict[str, Any]:
    """Convert xyz tile services to ipyleaflet tile layers.

    Returns:
        A dictionary of ipyleaflet tile layers.
    """
    leaflet_dict = {}
    # Ignore Esri basemaps if they are already in the custom XYZ_TILES.
    ignore_list = [XYZ_TILES[tile]["name"] for tile in XYZ_TILES]

    # Add custom tiles.
    for tile_type, tile_dict in custom_tiles.items():
        for tile_provider, tile_info in tile_dict.items():
            del tile_provider  # Unused.
            tile_info["type"] = tile_type
            if "max_zoom" in tile_info and "max_native_zoom" not in tile_info:
                tile_info["max_native_zoom"] = tile_info[
                    "max_zoom"
                ]  # pyrefly: ignore[unsupported-operation]
            tile_info["max_zoom"] = 30  # pyrefly: ignore[unsupported-operation]
            leaflet_dict[tile_info["name"]] = tile_info

    # Add xyzservices.provider tiles.
    for tile_provider, tile_info in get_xyz_dict().items():
        del tile_provider  # Unused.
        if tile_info["name"] in ignore_list:
            continue
        tile_info["url"] = tile_info.build_url()
        if "html_attribution" in tile_info:
            tile_info["attribution"] = tile_info["html_attribution"]
        if "max_zoom" in tile_info and "max_native_zoom" not in tile_info:
            tile_info["max_native_zoom"] = tile_info["max_zoom"]
        tile_info["max_zoom"] = 30
        leaflet_dict[tile_info["name"]] = tile_info

    return leaflet_dict


def xyz_to_folium() -> dict[str, Any]:
    """Convert xyz tile services to folium tile layers.

    Returns:
        A dictionary of folium tile layers.
    """
    folium_dict = {}
    # Ignore Esri basemaps if they are already in the custom XYZ_TILES.
    ignore_list = [XYZ_TILES[tile]["name"] for tile in XYZ_TILES]

    for key, tile in custom_tiles["xyz"].items():
        tile_kwargs: dict[str, Any] = {}
        if "max_native_zoom" in tile:
            tile_kwargs["max_native_zoom"] = tile["max_native_zoom"]
        policy = get_default_referrer_policy(str(tile["url"]))
        if policy is not None:
            tile_kwargs["referrer_policy"] = policy
        folium_dict[key] = folium.TileLayer(
            tiles=tile["url"],
            attr=tile["attribution"],
            name=tile["name"],
            overlay=True,
            control=True,
            max_zoom=30,
            **tile_kwargs,
        )

    for key, tile in custom_tiles["wms"].items():
        folium_dict[key] = folium.WmsTileLayer(
            url=tile["url"],  # pyrefly: ignore[bad-argument-type]
            layers=tile["layers"],  # pyrefly: ignore[bad-argument-type]
            name=tile["name"],  # pyrefly: ignore[bad-argument-type]
            attr=tile["attribution"],  # pyrefly: ignore[bad-argument-type]
            fmt=tile["format"],  # pyrefly: ignore[bad-argument-type]
            transparent=tile["transparent"],  # pyrefly: ignore[bad-argument-type]
            overlay=True,
            control=True,
            max_zoom=30,
        )

    for item in get_xyz_dict().values():
        if item["name"] in ignore_list:
            continue
        url = item.build_url()
        tile_kwargs = {}
        if "max_native_zoom" in item:
            tile_kwargs["max_native_zoom"] = item["max_native_zoom"]
        elif "max_zoom" in item:
            tile_kwargs["max_native_zoom"] = item["max_zoom"]
        policy = get_default_referrer_policy(url)
        if policy is not None:
            tile_kwargs["referrer_policy"] = policy
        folium_dict[item.name] = folium.TileLayer(
            tiles=url,
            attr=item.get("html_attribution") or item.attribution,
            name=item.name,
            max_zoom=max(item.get("max_zoom", 30), 30),
            overlay=True,
            control=True,
            **tile_kwargs,
        )

    if os.environ.get("PLANET_API_KEY") is not None:
        planet_dict = common.planet_tiles(tile_format="folium")
        folium_dict.update(planet_dict)

    return folium_dict


# ******************************************************************************#
# The classes and functions above are the core features of the geemap package.  #
# The Earth Engine team and the geemap community will maintain these features.  #
# ******************************************************************************#

# ******************************************************************************#
# The classes and functions below are the extra features of the geemap package. #
# The geemap community will maintain these features.                            #
# ******************************************************************************#


def xyz_to_pydeck() -> dict[str, Any]:
    """Convert xyz tile services to pydeck custom tile layers.

    Returns:
        A dictionary of pydeck tile layers.
    """
    import pydeck as pdk

    pydeck_dict = {}
    # Ignore Esri basemaps if they are already in the custom XYZ_TILES.
    ignore_list = [XYZ_TILES[tile]["name"] for tile in XYZ_TILES]

    for key, tile in custom_tiles["xyz"].items():
        url = tile["url"]
        pydeck_dict[key] = url

    for key, item in get_xyz_dict().items():
        if item["name"] in ignore_list:
            continue
        url = item.build_url()
        pydeck_dict[key] = url

        if os.environ.get("PLANET_API_KEY") is not None:
            planet_dict = common.planet_tiles(tile_format="ipyleaflet")
            for id_, tile in planet_dict.items():
                pydeck_dict[id_] = tile.url

    pdk.settings.custom_libraries = [
        {
            "libraryName": "MyTileLayerLibrary",
            "resourceUri": "https://cdn.jsdelivr.net/gh/giswqs/pydeck_myTileLayer@master/dist/bundle.js",
        }
    ]

    for key in pydeck_dict:
        pydeck_dict[key] = pdk.Layer("MyTileLayer", pydeck_dict[key], key)

    return pydeck_dict


def xyz_to_plotly() -> dict[str, Any]:
    """Convert xyz tile services to plotly tile layers.

    Returns:
        A dictionary of plotly tile layers.
    """
    plotly_dict = {}
    # Ignore Esri basemaps if they are already in the custom XYZ_TILES.
    ignore_list = [XYZ_TILES[tile]["name"] for tile in XYZ_TILES]

    for key, tile in custom_tiles["xyz"].items():
        plotly_dict[key] = {
            "below": "traces",
            "sourcetype": "raster",
            "sourceattribution": tile["attribution"],
            "source": [tile["url"]],
            "name": key,
        }

    for item in get_xyz_dict().values():
        if item["name"] in ignore_list:
            continue
        plotly_dict[item.name] = {
            "below": "traces",
            "sourcetype": "raster",
            "sourceattribution": item.get("html_attribution") or item.attribution,
            "source": [item.build_url()],
            "name": item.name,
        }

    return plotly_dict


def search_qms(keywords: str, limit: int = 10) -> list[Any] | None:
    """Search qms files for keywords.

    Reference: https://github.com/geopandas/xyzservices/issues/65

    Args:
        keywords: Keywords to search for.
        limit: Number of results to return.
    """
    qms_api = "https://qms.nextgis.com/api/v1/geoservices"

    services = requests.get(
        f"{qms_api}/?search={keywords}&type=tms&epsg=3857&limit={limit}"
    )
    services = services.json()
    if services["count"] == 0:
        return None

    if services["count"] <= limit:
        return services["results"]

    return services["results"][:limit]


def get_qms(service_id: str):
    qms_api = "https://qms.nextgis.com/api/v1/geoservices"
    service_details = requests.get(f"{qms_api}/{service_id}")
    return service_details.json()


def qms_to_geemap(service_id: str) -> ipyleaflet.TileLayer:
    """Convert a qms service to an ipyleaflet tile layer.

    Args:
        service_id: Service ID.

    Returns:
        An ipyleaflet tile layer.
    """
    service_details = get_qms(service_id)
    name = service_details["name"]
    url = service_details["url"]
    attribution = service_details["copyright_text"]

    layer = TileLayer(url=url, name=name, attribution=attribution)
    return layer
