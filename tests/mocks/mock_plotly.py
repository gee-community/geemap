from __future__ import annotations


class MockFigure:

    def __init__(
        self,
        data: list | None = None,
        layout: dict | None = None,
    ) -> None:
        self.data = data or []
        self.layout = layout or {}

    def update_layout(self, **kwargs) -> "MockFigure":
        self.layout.update(kwargs)
        return self

    def show(self) -> None:
        pass

    def to_json(self) -> str:
        return '{"data": [], "layout": {}}'

    def write_html(self, file: str, **kwargs) -> None:
        pass

    def write_image(self, file: str, **kwargs) -> None:
        pass


class MockPlotlyExpress:

    @staticmethod
    def bar(*args, **kwargs) -> MockFigure:
        return MockFigure(data=[{"type": "bar"}])

    @staticmethod
    def line(*args, **kwargs) -> MockFigure:
        return MockFigure(data=[{"type": "line"}])

    @staticmethod
    def histogram(*args, **kwargs) -> MockFigure:
        return MockFigure(data=[{"type": "histogram"}])

    @staticmethod
    def pie(*args, **kwargs) -> MockFigure:
        return MockFigure(data=[{"type": "pie"}])

    @staticmethod
    def scatter(*args, **kwargs) -> MockFigure:
        return MockFigure(data=[{"type": "scatter"}])

    @staticmethod
    def scatter_mapbox(*args, **kwargs) -> MockFigure:
        return MockFigure(data=[{"type": "scattermapbox"}])

    @staticmethod
    def choropleth_mapbox(*args, **kwargs) -> MockFigure:
        return MockFigure(data=[{"type": "choroplethmapbox"}])
