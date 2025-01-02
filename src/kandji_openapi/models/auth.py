from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from openapi_pydantic import SecurityScheme


class AuthType(Enum):
    NOAUTH = "noauth"
    APIKEY = "apikeyauth"
    BASIC = "basic"
    BEARER = "bearer"


@dataclass
class Auth:
    type: AuthType
    data: dict[str, list[dict[str, str]]]

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> Optional["Auth"]:
        if not data or "type" not in data:
            return None

        try:
            auth_type = AuthType(data.get("type", "noauth"))
        except ValueError:
            auth_type = AuthType.NOAUTH
        return cls(type=auth_type, data=data)

    def get_type(self) -> str:
        return self.type.value

    def to_openapi(self) -> dict[str, Optional[SecurityScheme]]:
        """Convert Postman auth to OpenAPI security scheme"""
        if self.type == AuthType.NOAUTH:
            return {}

        security_scheme = None
        if self.type == AuthType.APIKEY:
            security_scheme = SecurityScheme(
                type="apiKey",
                description="Authentication information",
                security_scheme_in=self.data.get("in", "header"),  # type: ignore
                name=self.data.get("name", "X-API-Key"),
            )
        elif self.type == AuthType.BASIC:
            security_scheme = SecurityScheme(
                type="http",
                description="Authentication information",
                scheme="basic",
            )
        elif self.type == AuthType.BEARER:
            security_scheme = SecurityScheme(
                type="http",
                description="Authentication information",
                scheme="bearer",
                bearerFormat="API Token",
            )

        return {self.type.value: security_scheme}
