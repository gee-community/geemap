from __future__ import annotations

import box


class Image:

    def __init__(self, *_, **__) -> None:
        self._bands: list[str] = ["B1", "B2", "B3"]
        self._crs: str = "EPSG:4326"

    @classmethod
    def constant(cls, *_, **__) -> "Image":
        return Image()

    def getMapId(self, *_, **__) -> box.Box:
        return box.Box({"tile_fetcher": {"url_format": "url-format"}})

    def updateMask(self, *_, **__) -> "Image":
        return self

    def blend(self, *_, **__) -> "Image":
        return self

    def bandNames(self, *_, **__) -> "List":
        return List(self._bands)

    def reduceRegion(self, *_, **__) -> "Dictionary":
        return Dictionary({"B1": 42, "B2": 3.14})

    def select(self, *args, **__) -> "Image":
        if args:
            self._bands = list(args[0]) if isinstance(args[0], (list, tuple)) else [args[0]]
        return self

    def clip(self, *_, **__) -> "Image":
        return self

    def rename(self, *args, **__) -> "Image":
        if args:
            self._bands = list(args[0]) if isinstance(args[0], (list, tuple)) else [args[0]]
        return self

    def multiply(self, *_, **__) -> "Image":
        return self

    def add(self, *_, **__) -> "Image":
        return self

    def divide(self, *_, **__) -> "Image":
        return self

    def subtract(self, *_, **__) -> "Image":
        return self

    def normalizedDifference(self, bands: list[str] | None = None, *_, **__) -> "Image":
        return self

    def expression(self, *_, **__) -> "Image":
        return self

    def abs(self, *_, **__) -> "Image":
        return self

    def sqrt(self, *_, **__) -> "Image":
        return self

    def log(self, *_, **__) -> "Image":
        return self

    def log10(self, *_, **__) -> "Image":
        return self

    def pow(self, *_, **__) -> "Image":
        return self

    def addBands(self, *_, **__) -> "Image":
        return self

    def getInfo(self) -> dict:
        return {
            "type": "Image",
            "bands": [
                {
                    "id": "band-1",
                    "data_type": {
                        "type": "PixelType",
                        "precision": "int",
                        "min": -2,
                        "max": 2,
                    },
                    "dimensions": [4, 2],
                    "crs": "EPSG:4326",
                    "crs_transform": [1, 0, -180, 0, -1, 84],
                },
            ],
            "version": 42,
            "id": "some/image/id",
            "properties": {
                "type_name": "Image",
                "keywords": ["keyword-1", "keyword-2"],
                "thumb": "https://some-thumbnail.png",
            },
        }


class List:

    def __init__(self, items: list | None = None, *_, **__) -> None:
        self.items = items or []

    def getInfo(self, *_, **__) -> list:
        return self.items

    def size(self, *_, **__) -> "Number":
        return Number(len(self.items))

    def get(self, index: int, *_, **__):
        return self.items[index] if index < len(self.items) else None

    def map(self, func, *_, **__) -> "List":
        return List([func(item) for item in self.items])


class Number:

    def __init__(self, value: int | float = 0) -> None:
        self.value = value

    def getInfo(self, *_, **__) -> int | float:
        return self.value


class Dictionary:

    def __init__(self, data: dict | None = None) -> None:
        self.data = data or {}

    def getInfo(self) -> dict:
        return self.data

    def get(self, key: str, *_, **__):
        return self.data.get(key)

    def keys(self, *_, **__) -> List:
        return List(list(self.data.keys()))


class ReduceRegionResult:

    def getInfo(self) -> None:
        return None


class Geometry:

    geometry = None

    def __init__(self, *args, **kwargs) -> None:
        if len(args):
            self.geometry = args[0]
        if kwargs.get("type"):
            self.geom_type = kwargs.get("type")
        else:
            self.geom_type = None

    @classmethod
    def Point(cls, coords: list | None = None, *_, **__) -> "Geometry":
        geom = Geometry(type=String("Point"))
        geom._coords = coords or [0, 0]
        return geom

    @classmethod
    def BBox(cls, *_, **__) -> "Geometry":
        return Geometry(type=String("BBox"))

    @classmethod
    def Polygon(cls, coords: list | None = None, *_, **__) -> "Geometry":
        geom = Geometry(type=String("Polygon"))
        geom._coords = coords
        return geom

    @classmethod
    def Rectangle(cls, coords: list | None = None, *_, **__) -> "Geometry":
        geom = Geometry(type=String("Polygon"))
        geom._coords = coords
        return geom

    @classmethod
    def LineString(cls, coords: list | None = None, *_, **__) -> "Geometry":
        geom = Geometry(type=String("LineString"))
        geom._coords = coords
        return geom

    @classmethod
    def MultiPoint(cls, coords: list | None = None, *_, **__) -> "Geometry":
        geom = Geometry(type=String("MultiPoint"))
        geom._coords = coords
        return geom

    def transform(self, *_, **__) -> "Geometry":
        return Geometry(type=self.geom_type)

    def bounds(self, *_, **__) -> "Geometry":
        return Geometry.Polygon()

    def centroid(self, *_, **__) -> "Geometry":
        return Geometry.Point()

    def buffer(self, *_, **__) -> "Geometry":
        return Geometry.Polygon()

    def type(self, *_, **__) -> "String":
        return self.geom_type

    def coordinates(self, *_, **__) -> List:
        return List(getattr(self, "_coords", []))

    def getInfo(self, *_, **__) -> dict:
        the_type = self.type()
        if the_type is None:
            return {"type": "Unknown"}
        type_value = the_type.value
        if type_value == "Polygon":
            return {
                "geodesic": False,
                "type": "Polygon",
                "coordinates": [
                    [[-178, -76], [179, -76], [179, 80], [-178, 80], [-178, -76]]
                ],
            }
        if type_value == "Point":
            return {
                "geodesic": False,
                "type": "Point",
                "coordinates": [120, -70],
            }
        if type_value == "BBox":
            return {
                "geodesic": False,
                "type": "Polygon",
                "coordinates": [[0, 1], [1, 2], [0, 1]],
            }
        if type_value == "LineString":
            return {
                "geodesic": False,
                "type": "LineString",
                "coordinates": [[0, 0], [1, 1]],
            }
        if type_value == "MultiPoint":
            return {
                "geodesic": False,
                "type": "MultiPoint",
                "coordinates": [[0, 0], [1, 1]],
            }
        return {"type": type_value}

    def __eq__(self, other: object) -> bool:
        return self.geometry == getattr(other, "geometry", None)


class String:

    def __init__(self, value: str = "") -> None:
        self.value = value

    def compareTo(self, other_str: "String") -> bool:
        return self.value == other_str.value

    def getInfo(self, *_, **__) -> str:
        return self.value

    def replace(self, pattern: str, replacement: str, flags: str = "") -> "String":
        return String(self.value.replace(pattern, replacement))


class FeatureCollection:

    features: list = []

    def __init__(self, *args, **_) -> None:
        if len(args):
            self.features = args[0] if isinstance(args[0], list) else []
        else:
            self.features = []

    def style(self, *_, **__) -> Image:
        return Image()

    def first(self, *_, **__) -> "Feature":
        return Feature()

    def filterBounds(self, *_, **__) -> "FeatureCollection":
        return FeatureCollection()

    def filter(self, *_, **__) -> "FeatureCollection":
        return FeatureCollection(self.features)

    def geometry(self, *_, **__) -> Geometry:
        return Geometry.Polygon()

    def aggregate_array(self, *_, **__) -> List:
        return List(["aggregation-one", "aggregation-two"])

    def size(self, *_, **__) -> Number:
        return Number(len(self.features))

    def toList(self, *_, **__) -> List:
        return List(self.features)

    def getInfo(self, *_, **__) -> dict:
        return {
            "type": "FeatureCollection",
            "features": [f.getInfo() if hasattr(f, "getInfo") else f for f in self.features],
        }

    def __eq__(self, other: object) -> bool:
        return self.features == getattr(other, "features", None)


class Feature:

    feature = None
    properties = None

    def __init__(self, *args, **_) -> None:
        if len(args) > 0:
            self.feature = args[0]
        if len(args) >= 2:
            self.properties = args[1]

    def geometry(self, *_, **__) -> Geometry:
        return Geometry(type=String("Polygon"))

    def get(self, key: str, *_, **__):
        if self.properties:
            return self.properties.get(key)
        return None

    def set(self, key: str, value, *_, **__) -> "Feature":
        if self.properties is None:
            self.properties = {}
        self.properties[key] = value
        return self

    def getInfo(self, *_, **__) -> dict:
        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-67.1, 46.2], [-67.3, 46.4], [-67.5, 46.6]],
            },
            "id": "00000000000000000001",
            "properties": {
                "fullname": "some-full-name",
                "linearid": "110469267091",
                "mtfcc": "S1400",
                "rttyp": "some-rttyp",
            },
        }

    def __eq__(self, other: object) -> bool:
        features_equal = self.feature == getattr(other, "feature", None)
        properties_equal = self.properties == getattr(other, "properties", None)
        return features_equal and properties_equal

    def propertyNames(self, *_, **__) -> List:
        return List(["prop-1", "prop-2"])


class ImageCollection:

    def __init__(self, images: list | str | None = None, *_, **__) -> None:
        if isinstance(images, str):
            self.images = [Image()]
        elif images is None:
            self.images = []
        else:
            self.images = images

    def mosaic(self, *_, **__) -> Image:
        return Image()

    def median(self, *_, **__) -> Image:
        return Image()

    def mean(self, *_, **__) -> Image:
        return Image()

    def first(self, *_, **__) -> Image:
        return Image() if self.images else Image()

    def filterDate(self, *_, **__) -> "ImageCollection":
        return ImageCollection(self.images)

    def filterBounds(self, *_, **__) -> "ImageCollection":
        return ImageCollection(self.images)

    def filter(self, *_, **__) -> "ImageCollection":
        return ImageCollection(self.images)

    def filterMetadata(self, *_, **__) -> "ImageCollection":
        return ImageCollection(self.images)

    def select(self, *args, **__) -> "ImageCollection":
        return ImageCollection(self.images)

    def map(self, func, *_, **__) -> "ImageCollection":
        return ImageCollection(self.images)

    def size(self, *_, **__) -> Number:
        return Number(len(self.images))

    def toList(self, *_, **__) -> List:
        return List(self.images)

    def getInfo(self) -> dict:
        return {
            "type": "ImageCollection",
            "bands": [],
            "features": [f.getInfo() for f in self.images],
        }


class Reducer:

    @classmethod
    def first(cls, *_, **__) -> "Reducer":
        return Reducer()

    @classmethod
    def mean(cls, *_, **__) -> "Reducer":
        return Reducer()

    @classmethod
    def median(cls, *_, **__) -> "Reducer":
        return Reducer()

    @classmethod
    def sum(cls, *_, **__) -> "Reducer":
        return Reducer()

    @classmethod
    def min(cls, *_, **__) -> "Reducer":
        return Reducer()

    @classmethod
    def max(cls, *_, **__) -> "Reducer":
        return Reducer()

    @classmethod
    def count(cls, *_, **__) -> "Reducer":
        return Reducer()

    @classmethod
    def stdDev(cls, *_, **__) -> "Reducer":
        return Reducer()


class Algorithms:

    @classmethod
    def If(cls, *_, **__) -> "Algorithms":
        return Algorithms()


class Filter:

    @classmethod
    def eq(cls, *_, **__) -> "Filter":
        return Filter()

    @classmethod
    def lt(cls, *_, **__) -> "Filter":
        return Filter()

    @classmethod
    def lte(cls, *_, **__) -> "Filter":
        return Filter()

    @classmethod
    def gt(cls, *_, **__) -> "Filter":
        return Filter()

    @classmethod
    def gte(cls, *_, **__) -> "Filter":
        return Filter()

    @classmethod
    def date(cls, *_, **__) -> "Filter":
        return Filter()

    @classmethod
    def bounds(cls, *_, **__) -> "Filter":
        return Filter()

    @classmethod
    def And(cls, *_, **__) -> "Filter":
        return Filter()

    @classmethod
    def Or(cls, *_, **__) -> "Filter":
        return Filter()

    @classmethod
    def listContains(cls, *_, **__) -> "Filter":
        return Filter()

    @classmethod
    def inList(cls, *_, **__) -> "Filter":
        return Filter()


class Date:

    def __init__(self, date_str: str | None = None, *_, **__) -> None:
        self._date = date_str or "2020-01-01"

    def getInfo(self, *_, **__) -> dict:
        return {"type": "Date", "value": self._date}

    def format(self, *_, **__) -> String:
        return String(self._date)

    @classmethod
    def fromYMD(cls, year: int, month: int, day: int, *_, **__) -> "Date":
        return Date(f"{year}-{month:02d}-{day:02d}")


class Projection:

    def __init__(self, crs: str = "EPSG:4326", *_, **__) -> None:
        self._crs = crs

    def getInfo(self, *_, **__) -> dict:
        return {"type": "Projection", "crs": self._crs}


class Classifier:

    def __init__(self, *_, **__) -> None:
        self._trees = []

    @classmethod
    def decisionTreeEnsemble(cls, trees, *_, **__) -> "Classifier":
        clf = Classifier()
        clf._trees = trees
        return clf

    def getInfo(self, *_, **__) -> dict:
        return {"type": "Classifier", "trees": len(self._trees)}


class _ExportTable:

    @staticmethod
    def toAsset(collection, description: str = "", assetId: str = "", *_, **__):
        return _Task(description=description, assetId=assetId)


class _Export:

    table = _ExportTable()


class _Task:

    def __init__(self, description: str = "", assetId: str = "") -> None:
        self.description = description
        self.assetId = assetId
        self._started = False

    def start(self) -> None:
        self._started = True


class _Batch:

    Export = _Export()


batch = _Batch()


def Initialize(*_, **__) -> None:
    pass


def Authenticate(*_, **__) -> None:
    pass
