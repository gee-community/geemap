"""Fake ee module for use with testing."""

import box


class Image:
    def __init__(self, *_, **__):
        pass

    @classmethod
    def constant(self, *_, **__):
        return Image()

    def getMapId(self, *_, **__):
        return box.Box({"tile_fetcher": {"url_format": "url-format"}})

    def updateMask(self, *_, **__):
        return self

    def blend(self, *_, **__):
        return self


class Geometry:
    def __init__(self, *_, **__):
        pass


class FeatureCollection:
    def __init__(self, *_, **__):
        pass

    def style(self, *_, **__):
        return Image()


class Feature:
    def __init__(self, *_, **__):
        pass


class ImageCollection:
    def __init__(self, *_, **__):
        pass

    def mosaic(self, *_, **__):
        return Image()
