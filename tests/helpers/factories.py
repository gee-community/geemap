from __future__ import annotations

import pandas as pd

from tests.mocks import mock_ee


def create_ee_image(
    bands: list[str] | None = None,
    crs: str = "EPSG:4326",
) -> mock_ee.Image:
    img = mock_ee.Image()
    img._bands = bands or ["B1", "B2", "B3"]
    img._crs = crs
    return img


def create_ee_feature_collection(
    features: list | None = None,
) -> mock_ee.FeatureCollection:
    fc = mock_ee.FeatureCollection(features or [])
    return fc


def create_ee_geometry(
    geom_type: str = "Point",
    coords: list | None = None,
) -> mock_ee.Geometry:
    coords = coords or [0, 0]
    if geom_type == "Point":
        return mock_ee.Geometry.Point(coords)
    elif geom_type == "Polygon":
        return mock_ee.Geometry.Polygon(coords)
    elif geom_type == "LineString":
        return mock_ee.Geometry.LineString(coords)
    elif geom_type == "Rectangle":
        return mock_ee.Geometry.Rectangle(coords)
    else:
        geom = mock_ee.Geometry(type=mock_ee.String(geom_type))
        geom._coords = coords
        return geom


def create_ee_feature(
    geometry: mock_ee.Geometry | None = None,
    properties: dict | None = None,
) -> mock_ee.Feature:
    geom = geometry or create_ee_geometry("Point", [0, 0])
    return mock_ee.Feature(geom, properties)


def create_ee_image_collection(
    images: list[mock_ee.Image] | None = None,
    count: int = 3,
) -> mock_ee.ImageCollection:
    if images is None:
        images = [create_ee_image() for _ in range(count)]
    return mock_ee.ImageCollection(images)


def create_sample_dataframe(
    rows: int = 5,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    columns = columns or ["x", "y", "value"]
    data = {col: list(range(rows)) for col in columns}
    return pd.DataFrame(data)


def create_sample_geodataframe(
    rows: int = 5,
    crs: str = "EPSG:4326",
):
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        return None

    data = {
        "name": [f"feature_{i}" for i in range(rows)],
        "value": list(range(rows)),
        "geometry": [Point(i, i) for i in range(rows)],
    }
    return gpd.GeoDataFrame(data, crs=crs)


def create_sample_geojson(
    num_features: int = 3,
    geom_type: str = "Point",
) -> dict:
    features = []
    for i in range(num_features):
        if geom_type == "Point":
            coordinates = [i, i]
        elif geom_type == "Polygon":
            coordinates = [[[i, i], [i + 1, i], [i + 1, i + 1], [i, i + 1], [i, i]]]
        elif geom_type == "LineString":
            coordinates = [[i, i], [i + 1, i + 1]]
        else:
            coordinates = [i, i]

        features.append(
            {
                "type": "Feature",
                "properties": {"id": i, "name": f"feature_{i}"},
                "geometry": {"type": geom_type, "coordinates": coordinates},
            }
        )

    return {"type": "FeatureCollection", "features": features}
