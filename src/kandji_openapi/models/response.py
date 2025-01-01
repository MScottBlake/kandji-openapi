import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from kandji_openapi.strings import string_formatting


@dataclass
class Response:
    id: Optional[str]
    name: Optional[str]
    status_code: int
    status_text: str
    headers: list[dict[str, str]] = field(default_factory=list)
    body: Optional[str] = None
    cookies: list[dict[str, Any]] = field(default_factory=list)
    time: Optional[int] = None
    timestamp: Optional[datetime] = None

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "Response":
        headers = data.get("header", [])
        if headers is None:
            headers = []
        elif not isinstance(headers, list):
            headers = []

        return cls(
            id=data.get("id"),
            name=data.get("name"),
            status_code=data.get("code", 200),
            status_text=data.get("status", "OK"),
            headers=headers,
            body=data.get("body"),
            cookies=data.get("cookie", []),
            time=data.get("responseTime"),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else None
            ),
        )

    def get_content_type(self) -> Optional[str]:
        """Extract content type from response headers"""
        for header in self.headers:
            if not header:
                continue
            if header.get("key", "").lower() == "content-type":
                return header.get("value") or None
        return None

    def to_openapi(self) -> dict[str, Any]:
        """Convert response to OpenAPI response object"""
        response: dict[str, Any] = {"description": self.status_text}

        content_type = self.get_content_type()
        if content_type and self.body:
            try:
                if "json" in content_type.lower():
                    schema_type = "object"
                    example = json.loads(self.body)
                else:
                    schema_type = "string"
                    example = string_formatting(self.body)

                response["content"] = {
                    content_type: {"schema": {"type": schema_type, "example": example}}
                }
            except json.JSONDecodeError:
                pass  # If JSON parsing fails, skip body schema

        headers: dict[str, dict[str, str | dict[str, str]]] = {}
        for header in self.headers:
            if not header:
                continue
            if key := header.get("key"):
                headers[key] = {"schema": {"type": "string"}}

                if description := header.get("description"):
                    headers[key]["description"] = string_formatting(description)
                if value := header.get("value"):
                    headers[key]["example"] = value

        if headers:
            response["headers"] = headers

        return {str(self.status_code): response}
