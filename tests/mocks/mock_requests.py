from __future__ import annotations


class RequestError(Exception):
    pass


class MockResponse:

    def __init__(
        self,
        json_data: dict | None = None,
        status_code: int = 200,
        text: str = "",
        content: bytes = b"",
    ) -> None:
        self._json_data = json_data
        self.status_code = status_code
        self.text = text
        self.content = content
        self.ok = status_code < 400

    def json(self) -> dict | None:
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RequestError(f"HTTP {self.status_code}")


def create_mock_response(
    json_data: dict | None = None,
    status_code: int = 200,
    text: str = "",
    content: bytes = b"",
) -> MockResponse:
    return MockResponse(
        json_data=json_data,
        status_code=status_code,
        text=text,
        content=content,
    )
