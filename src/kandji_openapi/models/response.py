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
from strings import string_formatting, to_camel_case


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

    def generate_properties_from_example(self, example: dict) -> dict:
        """Generates a properties dictionary for an OpenAPI schema from an example."""
        properties = {}
        for key, value in example.items():
            properties[key] = self.infer_schema_from_value(value)
        return properties

    def infer_schema_from_value(self, value: Any) -> Schema:
        """Infers the schema for a single value."""
        if isinstance(value, str):
            return Schema(type=DataType(value="string"))
        elif isinstance(value, int):
            return Schema(type=DataType(value="integer"))
        elif isinstance(value, float):
            return Schema(type=DataType(value="number"))
        elif isinstance(value, bool):
            return Schema(type=DataType(value="boolean"))
        elif isinstance(value, dict):
            return Schema(
                type=DataType(value="object"),
                properties=self.generate_properties_from_example(value),
            )
        else:
            # Handle other types or return a default schema
            return Schema()  # Generic schema

    def to_openapi(self) -> Responses:
        """Convert response to OpenAPI response object"""
        response = Response(description=self.status_text)
        properties = {}
        title = "".join(
            [to_camel_case(str(self.name)), str(self.status_code), "Response"]
        )

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
                    if isinstance(body, dict):
                        properties = self.generate_properties_from_example(body)
                except json.JSONDecodeError:
                    body = modified_body

                example = Example(value=body)
                schema = Schema(title=title, type=DataType(value="object"))
                if properties:
                    schema.properties = properties
            else:
                example = Example(value=string_formatting(self.body))
                schema = Schema(title=title, type=DataType(value="string"))

            response.content = {content_type: MediaType(example=example, schema=schema)}

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
