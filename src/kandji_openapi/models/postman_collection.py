import re
from dataclasses import dataclass, field
from typing import Any, Optional

from configurations import KANDJI_API_DOCS_URL
from models.auth import Auth
from models.item import Item
from openapi_pydantic import (
    ExternalDocumentation,
    SecurityScheme,
    Server,
    ServerVariable,
    Tag,
)


@dataclass
class PostmanCollection:
    info: PostmanInfo
    items: list[Item] = field(default_factory=list)
    auth: Optional[Auth] = None

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "PostmanCollection":
        return cls(
            info=PostmanInfo.from_data(data.get("info", {})),
            auth=Auth.from_data(data.get("auth", {})),
            items=cls._process_items(data.get("item", [])),
        )

    @classmethod
    def _process_items(
        cls, items_data: list[dict[str, Any]], parent: Optional[Item] = None
    ) -> list[Item]:
        """Process collection items recursively"""
        processed_items: list[Item] = []

        tag = ""
        if parent and parent.is_folder():
            tag = parent.name

        for item_data in items_data:
            if item := Item.from_data(item_data, tag):
                processed_items.append(item)

        return processed_items

    def _hosts_to_openapi(self) -> list[Server]:
        """Extract unique hosts from all items' requests."""
        hosts: set[str] = set()
        for item in self.items:
            if item.get_host():
                hosts.add(item.get_host())

            for subitem in item.get_items():
                if subitem.get_host():
                    hosts.add(subitem.get_host())

        variable_pattern = re.compile(r"\{([^}]+)\}")

        output = []
        for host in hosts:
            variables: dict[str, ServerVariable] = {}
            for match in variable_pattern.finditer(host):
                var_name = match.group(1)
                variables[var_name] = ServerVariable(default=f"<{var_name}>")

            host_dict = Server(url=host)
            if variables:
                host_dict.variables = variables

            output.append(host_dict)
        return output

    def _paths_to_openapi(self, items: Optional[list[Item]] = None) -> dict[str, Any]:
        output: dict[str, dict[str, Any]] = {}
        if items is None:
            items = self.items

        for item in items:
            if path := item.get_path():
                item_dict = item.to_openapi()

                if path not in output:
                    output[path] = {}
                output[path].update(item_dict[path])

            output.update(self._paths_to_openapi(item.get_items()))
        return output

    def _tags_to_openapi(self, items: Optional[list[Item]] = None) -> list[Tag]:
        """List of tags from all items' requests."""
        all_tags: list[Tag] = []
        if items is None:
            items = self.items

        for item in items:
            if item.is_folder():
                tag_dict = Tag(name=item.name)

                if description := item.get_description():
                    tag_dict.description = description
                if url := item.get_url():
                    tag_dict.externalDocs = ExternalDocumentation(url=url)

                all_tags.append(tag_dict)

            all_tags.extend(self._tags_to_openapi(item.get_items()))
        return all_tags

    def get_security_schemes(self) -> dict[str, SecurityScheme]:
        """Compile all unique security schemes"""
        schemes = {}

        # Add collection-level auth if present
        if self.auth:
            schemes.update(self.auth.to_openapi())

        # Add auth from items
        for item in self.items:
            if item_auth := item.get_auth():
                schemes.update(item_auth.to_openapi())

            if request := item.get_request():
                if request_auth := request.get_auth():
                    schemes.update(request_auth.to_openapi())

        return schemes

    def to_openapi(self) -> dict[str, Any]:
        """Convert the collection to an OpenAPI specification"""
        openapi: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": self.info.to_openapi(),
            "servers": self._hosts_to_openapi(),
            "tags": self._tags_to_openapi(),
            "paths": self._paths_to_openapi(),
        }

        if self.auth:
            openapi["security"] = [{self.auth.get_type(): []}]

        # Add security schemes if present
        if security_schemes := self.get_security_schemes():
            if "components" not in openapi:
                openapi["components"] = {}
            openapi["components"]["securitySchemes"] = security_schemes

        if KANDJI_API_DOCS_URL:
            openapi["externalDocs"] = ExternalDocumentation(url=KANDJI_API_DOCS_URL)

        return openapi
