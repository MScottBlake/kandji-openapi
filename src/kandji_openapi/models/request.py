import re
from dataclasses import dataclass, field
from typing import Any, Optional

from models.auth import Auth
from models.request_body import RequestBody
from models.url import URL
from strings import string_formatting


@dataclass
class Request:
    method: str
    url: URL
    summary: str = ""
    headers: list[dict[str, Any]] = field(default_factory=list)
    body: Optional[RequestBody] = None
    description: Optional[str] = None
    auth: Optional[Auth] = None
    proxy: Optional[dict[str, Any]] = None
    certificate: Optional[dict[str, Any]] = None
    tag: str = ""
    external_docs: str = ""

    @classmethod
    def from_data(
        cls, data: dict[str, Any], name: str, tag: str = "", url: str = ""
    ) -> Optional["Request"]:
        if not data:
            return None

        if data.get("urlObject"):
            url_data = data.get("urlObject", {})
        else:
            url_data = data.get("url", {})
            if isinstance(url_data, str):
                url_data = {"raw": url_data}

        return cls(
            method=data.get("method", "GET"),
            url=URL.from_data(url_data),
            summary=name,
            headers=data.get("header", []),
            body=RequestBody.from_data(data.get("body", {})),
            description=string_formatting(data.get("description", "")),
            auth=Auth.from_data(data.get("auth", {})),
            proxy=data.get("proxy"),
            certificate=data.get("certificate"),
            tag=tag,
            external_docs=url,
        )

    def _to_camel_case(self, input_string: str) -> str:
        # Remove any non-alphanumeric characters (optional based on needs)
        input_string = re.sub(r"[^a-zA-Z0-9\s_]", "", input_string)

        # Split the string by spaces or underscores
        words = re.split(r"[_\s]+", input_string)

        # Capitalize each word except the first one, and join them together
        return words[0].lower() + "".join(word.capitalize() for word in words[1:])

    def get_auth(self) -> Optional[Auth]:
        return self.auth

    def get_description(self) -> Optional[str]:
        return self.description

    def get_host(self) -> str:
        return self.url.get_base_url()

    def get_method(self) -> str:
        return self.method

    def get_parameters(self) -> list[dict[str, Any]]:
        """Extract all parameters from request"""
        parameters = []

        # Path parameters
        parameters.extend(self.url.get_path_parameters())

        # Query parameters
        for query in self.url.query:
            description = string_formatting(
                query.get("description", {}).get("content", "")
            )
            parameters.append(
                {
                    "name": query.get("key", ""),
                    "in": "query",
                    "required": not query.get("disabled", False),
                    "schema": {"type": "string"},
                    "description": string_formatting(description),
                    "example": query.get("value"),
                }
            )

        # Header parameters
        for header in self.headers:
            if header.get("disabled", False):
                continue

            parameters.append(
                {
                    "name": header.get("key", ""),
                    "in": "header",
                    "schema": {"type": "string"},
                    "required": True,
                    "description": string_formatting(header.get("description", "")),
                    "example": header.get("value"),
                }
            )

        return parameters

    def get_path(self) -> str:
        return self.url.get_path_string()

    def get_tag(self) -> str:
        return self.tag

    def to_openapi(self) -> dict[str, dict[str, Any]]:
        """Convert to OpenAPI request object"""
        method = self.method.lower()

        tag_camel_case = self._to_camel_case(self.get_tag())
        summary_camel_case = self._to_camel_case(self.summary)

        request_obj: dict[str, dict[str, Any]] = {
            method: {
                "summary": self.summary,
                "operationId": f"{tag_camel_case}_{summary_camel_case}",
            }
        }
        if tag := self.get_tag():
            request_obj[method]["tags"] = [tag]
        if self.description:
            request_obj[method]["description"] = self.description
        if parameters := self.get_parameters():
            request_obj[method]["parameters"] = parameters
        if self.body:
            request_obj[method]["requestBody"] = self.body.to_openapi()
        if self.auth:
            request_obj[method]["security"] = [{self.auth.get_type(): []}]

        if self.url:
            request_obj[method]["externalDocs"] = {"url": self.external_docs}

        return request_obj
