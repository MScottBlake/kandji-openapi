from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Sequence


@dataclass
class URL:
    raw: Optional[str] = None
    protocol: Optional[str] = None
    host: Sequence[str] = field(default_factory=list)
    path: Iterable[str] = field(default_factory=list)
    port: Optional[str] = None
    query: list[dict[str, Any]] = field(default_factory=list)
    hash: Optional[str] = None

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "URL":
        if "raw" in data:
            # Parse raw URL string to extract protocol, host, etc
            if "://" in data["raw"]:
                protocol, rest = data["raw"].split("://", 1)
                data["protocol"] = protocol
                if "/" in rest:
                    host_part, path_part = rest.split("/", 1)
                    data["host"] = host_part.split(".")
                    data["path"] = path_part.split("/")
                else:
                    data["host"] = rest.split(".")

        # Handle full URL object
        return cls(
            raw=data.get("raw"),
            protocol=data.get("protocol"),
            host=data.get("host", []),
            path=data.get("path", []),
            port=data.get("port"),
            query=data.get("query", []),
            hash=data.get("hash"),
        )

    def get_path_parameters(self) -> list[dict[str, Any]]:
        path_params = []
        for path_var in self.path:
            if path_var.startswith("{") and path_var.endswith("}"):
                path_params.append(
                    {
                        "name": path_var.strip("{}"),
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                )
        return path_params

    def get_path_string(self) -> str:
        """Convert path components to OpenAPI path string with parameters"""
        path = "/" + "/".join(self.path)
        return path.replace("{{", "{").replace("}}", "}")

    def get_base_url(self) -> str:
        """Get the base URL without path, query parameters, etc."""
        if "://" in self.host:
            protocol = ""
        else:
            protocol = self.protocol or ""

        host = ".".join(self.host) if self.host else ""
        port = f":{self.port}" if self.port else ""

        base_url = f"{protocol}{host}{port}"
        if base_url == "https://":
            return ""

        return base_url