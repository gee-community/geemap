from __future__ import annotations

from shapely.geometry import Point, Polygon


class MockGeoDataFrame:

    def __init__(
        self,
        data: dict | None = None,
        geometry: list | None = None,
        crs: str = "EPSG:4326",
    ) -> None:
        self.data = data or {}
        self.geometry = geometry or []
        self.crs = crs
        self.empty = len(self.geometry) == 0
        self.__geo_interface__ = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"name": "Test"},
                }
            ],
        }

    def to_file(self, filepath: str, driver: str | None = None) -> None:
        pass

    def to_json(self) -> str:
        return '{"type": "FeatureCollection", "features": []}'

    def __len__(self) -> int:
        return len(self.geometry)


def mock_features_from_address(
    address: str,
    tags: dict,
    dist: int = 1000,
) -> MockGeoDataFrame:
    return MockGeoDataFrame(
        geometry=[Point(0, 0)],
        data={"name": ["Test Feature"]},
    )


def mock_features_from_point(
    center_point: tuple[float, float],
    tags: dict,
    dist: int = 1000,
) -> MockGeoDataFrame:
    return MockGeoDataFrame(
        geometry=[Point(center_point[0], center_point[1])],
        data={"name": ["Test Point Feature"]},
    )


def mock_features_from_bbox(
    bbox: tuple[float, float, float, float],
    tags: dict,
) -> MockGeoDataFrame:
    west, south, east, north = bbox
    return MockGeoDataFrame(
        geometry=[
            Polygon([(west, south), (east, south), (east, north), (west, north)])
        ],
        data={"name": ["Test BBox Feature"]},
    )


def mock_features_from_polygon(
    polygon,
    tags: dict,
) -> MockGeoDataFrame:
    return MockGeoDataFrame(
        geometry=[polygon],
        data={"name": ["Test Polygon Feature"]},
    )


def mock_features_from_place(
    query: str | dict | list,
    tags: dict,
    which_result: int | None = None,
) -> MockGeoDataFrame:
    return MockGeoDataFrame(
        geometry=[Point(0, 0)],
        data={"name": ["Test Place Feature"]},
    )


def mock_features_from_xml(
    filepath: str,
    polygon=None,
    tags: dict | None = None,
) -> MockGeoDataFrame:
    return MockGeoDataFrame(
        geometry=[Point(0, 0)],
        data={"name": ["Test XML Feature"]},
    )


def mock_geocode_to_gdf(
    query: str | dict | list,
    which_result: int | None = None,
    by_osmid: bool = False,
) -> MockGeoDataFrame:
    return MockGeoDataFrame(
        geometry=[Point(0, 0)],
        data={"name": ["Test Geocode Feature"]},
    )
