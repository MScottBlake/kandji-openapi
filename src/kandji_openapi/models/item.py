import re
from dataclasses import dataclass, field
from typing import Any, Optional

from openapi_pydantic import Operation

from kandji_openapi.configurations import KANDJI_API_DOCS_URL
from kandji_openapi.models.auth import Auth
from kandji_openapi.models.request import PostmanRequest
from kandji_openapi.strings import string_formatting


@dataclass
class PostmanItem:
    name: str
    id: str
    request: Optional[PostmanRequest] = None
    description: Optional[str] = None
    url: str = ""
    auth: Optional[Auth] = None
    proxy_config: Optional[dict[str, Any]] = None
    items: list["PostmanItem"] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: dict[str, Any], tag: str = "") -> Optional["PostmanItem"]:
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
            request=PostmanRequest.from_data(
                data=data.get("request", {}),
                name=data.get("name", ""),
                responses=data.get("response", []),
                tag=tag,
                url=url,
            ),
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

    def get_items(self) -> list["PostmanItem"]:
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

    def get_request(self) -> Optional[PostmanRequest]:
        return self.request if self.request else None

    def get_tag(self) -> str:
        if self.request:
            return ""
        return self.name

    def get_url(self) -> str:
        return self.url

    def is_folder(self) -> bool:
        return not isinstance(self.request, PostmanRequest)

    def to_openapi(self) -> dict[str, Operation]:
        """Convert to OpenAPI path object"""
        return self.request.to_openapi() if self.request else {}
