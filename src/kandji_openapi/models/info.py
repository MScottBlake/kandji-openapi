from dataclasses import dataclass
from typing import Any, Optional, cast

from openapi_types import ContactObject, InfoObject, LicenseObject
from strings import string_formatting


@dataclass
class Info:
    name: str
    version: str
    description: Optional[str] = None
    schema: Optional[str] = None
    contact: Optional[ContactObject] = None
    license: Optional[LicenseObject] = None

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "Info":
        contact: ContactObject = {
            "name": "Scott Blake",
            "email": "mitchelsblake@gmail.com",
            "url": "https://github.com/MScottBlake/kandji-openapi",
        }

        license: LicenseObject = {"name": "MIT License", "identifier": "MIT"}

        return cls(
            name=data.get("name", "API"),
            version=data.get("version", "1.0.0"),
            description=data.get("description"),
            schema=data.get("schema"),
            contact=contact,
            license=license,
        )

    def to_openapi(self) -> InfoObject:
        """Convert to OpenAPI info object"""
        info: InfoObject = {"title": self.name, "version": self.version or "1.0.0"}
        if self.description:
            info["description"] = string_formatting(self.description)
        if self.contact:
            info["contact"] = cast(ContactObject, self.contact)
        if self.license:
            info["license"] = cast(LicenseObject, self.license)
        return info
