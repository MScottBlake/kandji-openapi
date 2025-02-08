import re
from dataclasses import dataclass, field
from typing import Any, Optional

from configurations import KANDJI_API_DOCS_URL
from models.auth import Auth
from models.request import Request
from models.response import Response
from strings import string_formatting


@dataclass
class Item:
    name: str
    id: str
    request: Optional[Request] = None
    description: Optional[str] = None
    url: str = ""
    responses: list[Response] = field(default_factory=list)
    auth: Optional[Auth] = None
    proxy_config: Optional[dict[str, Any]] = None
    items: list["Item"] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: dict[str, Any], tag: str = "") -> Optional["Item"]:
        """Create an Item from dictionary data"""
        url = ""
        if "id" in data:
            url = f"{KANDJI_API_DOCS_URL}/#{data['id']}"

        # Don't create if the entire url is a variable
        if bool(re.fullmatch(r"^\{[^{}]+\}$", data.get("request", {}).get("url", ""))):
            return None

        items = []
        for item_data in data.get("item", []):
            if item := cls.from_data(item_data, tag=data.get("name", "")):
                items.append(item)

        return cls(
            name=data.get("name", ""),
            id=data.get("id", ""),
            description=string_formatting(data.get("description", "")),
            request=Request.from_data(
                data.get("request", {}), data.get("name", ""), tag, url
            ),
            responses=[Response.from_data(r) for r in data.get("response", [])],
            auth=Auth.from_data(data.get("auth", {})),
            proxy_config=data.get("protocolProfileBehavior"),
            url=url,
            items=items,
        )

    def get_auth(self) -> Optional[Auth]:
        return self.auth

    def get_description(self) -> str:
        return self.description or ""

    def get_host(self) -> str:
        """Extracts the host from the Request."""
        if self.request:
            return self.request.get_host()
        return ""

    def get_items(self) -> list["Item"]:
        return self.items

    def get_path(self) -> str:
        """Get the endpoint path"""
        if self.request:
            return self.request.get_path()
        return ""

    def get_method(self) -> str:
        """Get HTTP method in lowercase"""
        if self.request:
            return self.request.get_method()
        return "get"

    def get_request(self) -> Optional[Request]:
        return self.request if self.request else None

    def get_tag(self) -> str:
        if self.request:
            return ""
        return self.name

    def get_url(self) -> str:
        return self.url

    def is_folder(self) -> bool:
        return not isinstance(self.request, Request)

    def to_openapi(self) -> dict[str, dict[str, Any]]:
        """Convert to OpenAPI path object"""
        if self.is_folder():
            output: dict[str, dict[str, Any]] = {}
            for item in self.items:
                path = item.get_path()
                item_dict = item.to_openapi()

                if path not in output:
                    output[path] = {}
                output[path].update(item_dict[path])
            return output

        path = self.get_path()
        method = self.get_method().lower()

        path_obj: dict[str, dict[str, Any]] = {}
        path_obj[path] = self.request.to_openapi() if self.request else {}

        if self.auth:
            path_obj[path]["security"] = [{self.auth.get_type(): []}]

        if self.responses:
            for response in self.responses:
                if "responses" not in path_obj[path][method]:
                    path_obj[path][method]["responses"] = {}
                path_obj[path][method]["responses"].update(response.to_openapi())
        else:
            path_obj[path][method]["responses"] = {"200": {"description": "OK"}}

        return path_obj
