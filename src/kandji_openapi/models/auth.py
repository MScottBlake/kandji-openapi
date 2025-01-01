from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


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

    def to_openapi(self) -> dict[str, Any]:
        """Convert Postman auth to OpenAPI security scheme"""
        if self.type == AuthType.NOAUTH:
            return {}

        security_scheme: dict[str, Any] = {
            "type": "",
            "description": "Authentication information",
        }

        # if self.type == AuthType.APIKEY:
        #     # Not tested
        #     security_scheme.update(
        #         {
        #             "type": "apiKey",
        #             "in": self.data.get("in", "header"),
        #             "name": self.data.get("name", "X-API-Key"),
        #         }
        #     )
        # elif self.type == AuthType.BASIC:
        #     # Not tested
        #     security_scheme.update({"type": "http", "scheme": "basic"})
        # elif self.type == AuthType.BEARER:
        if self.type == AuthType.BEARER:
            security_scheme.update(
                {"type": "http", "scheme": "bearer", "bearerFormat": "API Token"}
            )

        return {self.type.value: security_scheme}
