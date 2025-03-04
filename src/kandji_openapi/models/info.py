from dataclasses import dataclass
from typing import Any, Optional

from openapi_pydantic import Contact, Info, License

from kandji_openapi.strings import string_formatting


@dataclass
class PostmanInfo:
    name: str
    version: str
    description: Optional[str] = None
    schema: Optional[str] = None
    contact: Optional[Contact] = None
    license: Optional[License] = None

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "PostmanInfo":
        contact = Contact(
            name="Scott Blake",
            email="mitchelsblake@gmail.com",
            url="https://github.com/MScottBlake/kandji-openapi",
        )

        license = License(name="MIT License", identifier="MIT")

        return cls(
            name=data.get("name", "API"),
            version=data.get("version", "1.0.0"),
            description=data.get("description"),
            schema=data.get("schema"),
            contact=contact,
            license=license,
        )

    def to_openapi(self) -> Info:
        """Convert to OpenAPI info object"""
        info = Info(title=self.name, version=self.version or "1.0.0")
        if self.description:
            info.description = string_formatting(self.description)
        if self.contact:
            info.contact = self.contact
        if self.license:
            info.license = self.license
        return info
