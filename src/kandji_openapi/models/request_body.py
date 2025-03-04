import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from openapi_pydantic import DataType, MediaType, RequestBody, Schema

from kandji_openapi.strings import string_formatting


@dataclass
class PostmanRequestBody:
    mode: str
    raw: Optional[str] = None
    formdata: list[dict[str, Any]] = field(default_factory=list)
    urlencoded: list[dict[str, Any]] = field(default_factory=list)
    file: Optional[dict[str, Any]] = None
    options: dict[str, Any] = field(default_factory=dict)
    disabled: bool = False
    graphql: Optional[dict[str, Any]] = None

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> Optional["PostmanRequestBody"]:
        if not data:
            return None

        # Remove comments - find // and remove all remaining text on that line
        raw = re.sub(r"//.*$", "", data.get("raw", ""), flags=re.MULTILINE)

        return cls(
            mode=data.get("mode", "raw"),
            raw=raw,
            formdata=data.get("formdata", []),
            urlencoded=data.get("urlencoded", []),
            file=data.get("file"),
            options=data.get("options", {}),
            disabled=data.get("disabled", False),
            graphql=data.get("graphql"),
        )

    def get_content_type(self) -> str:
        """Determine content type based on body mode and options"""
        if self.mode == "raw":
            language = self.options.get("raw", {}).get("language", "")
            content_types = {
                "json": "application/json",
                "xml": "application/xml",
                "javascript": "application/javascript",
                "html": "text/html",
            }
            return content_types.get(language, "text/plain")
        elif self.mode == "formdata":
            return "multipart/form-data"
        elif self.mode == "urlencoded":
            return "application/x-www-form-urlencoded"
        elif self.mode == "graphql":
            return "application/json"
        elif self.mode == "file":
            return (
                self.file.get("content-type", "application/octet-stream")
                if self.file
                else "application/octet-stream"
            )
        return "application/octet-stream"

    def to_openapi(self) -> Optional[RequestBody]:
        """Convert body to OpenAPI schema"""
        content_type = self.get_content_type()

        if self.mode == "raw":
            example = string_formatting(self.raw or "{}")
            if "json" in content_type.lower():
                try:
                    example = json.loads(self.raw or "{}")
                except json.JSONDecodeError:
                    example = self.raw or "{}"

            return RequestBody(
                content={
                    content_type: MediaType(
                        example=example,
                        schema=Schema(type=DataType(value="string")),
                    )
                }
            )

        elif self.mode in ["formdata", "urlencoded"]:
            properties = {}
            required = []
            data_list = self.formdata if self.mode == "formdata" else self.urlencoded

            for item in data_list:
                if item.get("disabled", False):
                    continue

                if key := item.get("key"):
                    properties[key] = {"type": "string"}
                    if description := item.get("description"):
                        properties[key]["description"] = string_formatting(description)
                    if item.get("type") == "file":
                        properties[key]["format"] = "binary"
                    if item.get("value"):
                        properties[key]["example"] = item["value"]

                    required.append(key)

            schema = Schema(type=DataType(value="object"), properties=properties)
            if required:
                schema.required = required

            return RequestBody(content={content_type: MediaType(schema=schema)})

        elif self.mode == "graphql":
            if self.graphql:
                return RequestBody(
                    content={
                        "application/json": MediaType(
                            schema=Schema(
                                type=DataType(value="object"),
                                properties={
                                    "query": Schema(
                                        type=DataType(value="string"),
                                        example=self.graphql.get("query", ""),
                                    ),
                                    "variables": Schema(
                                        type=DataType(value="object"),
                                        example=self.graphql.get("variables", {}),
                                    ),
                                },
                                required=["query"],
                            ),
                        )
                    }
                )

        return None
