import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from openapi_pydantic import (
    DataType,
    Example,
    Header,
    MediaType,
    Response,
    Responses,
    Schema,
)
from strings import string_formatting


@dataclass
class PostmanResponse:
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
    def from_data(cls, data: dict[str, Any]) -> "PostmanResponse":
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

    def to_openapi(self) -> Responses:
        """Convert response to OpenAPI response object"""
        response = Response(description=self.status_text)

        content_type = self.get_content_type()
        if content_type and self.body:
            if "json" in content_type.lower():
                modified_body = self.body

                # Remove escaped newline characters
                modified_body = re.sub(r"[\n\t]|\.{3}", "", modified_body)

                # Replace smart quotes with regular quotes
                modified_body = re.sub(r"[“”‘’]", "'", modified_body)

                # Remove comments
                modified_body = re.sub(r"// [^\n}]*", "", modified_body)

                # Remove trailing commas
                modified_body = re.sub(r",\s*}", "}", modified_body)
                modified_body = re.sub(r",\s*]", "]", modified_body)

                # Remove extraneous characters like ",s"
                modified_body = re.sub(r",s", ",", modified_body)

                try:
                    body = json.loads(modified_body)
                except json.JSONDecodeError:
                    body = modified_body

                schema_type = "object"
                example = Example(value=body)
            else:
                schema_type = "string"
                example = Example(value=string_formatting(self.body))

            response.content = {
                content_type: MediaType(
                    example=example,
                    schema=Schema(type=DataType(value=schema_type)),
                )
            }

        headers = {}
        for header in self.headers:
            if not header:
                continue
            if key := header.get("key"):
                headers[key] = Header(schema=Schema(type=DataType(value="string")))

                if description := header.get("description"):
                    headers[key].description = string_formatting(description)
                if value := header.get("value"):
                    headers[key].example = Example(value=value)

        if headers:
            response.headers = headers

        return {str(self.status_code): response}
