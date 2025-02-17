import json
from pathlib import Path

from models.postman_collection import PostmanCollection
from openapi_pydantic import OpenAPI
from ruamel.yaml import YAML


class OpenAPIGenerator:
    def __init__(self, collection: PostmanCollection) -> None:
        self.collection = collection
        self.openapi_spec = self._generate_openapi_spec()

    def _generate_openapi_spec(self) -> OpenAPI:
        """Generate OpenAPI spec with components"""
        spec = self.collection.to_openapi()
        return spec

    def to_json(self, file_path: Path) -> None:
        """Write OpenAPI spec to JSON file"""
        with open(file_path, "w") as temp:
            json.dump(
                json.loads(
                    self.openapi_spec.model_dump_json(by_alias=True, exclude_none=True)
                ),
                temp,
                indent=2,
            )

    def to_yaml(self, file_path: Path) -> None:
        """Write OpenAPI spec to YAML file"""
        yaml = YAML(typ="safe", pure=True)
        yaml.allow_unicode = True
        yaml.default_flow_style = False
        yaml.explicit_start = True
        yaml.preserve_quotes = True

        with open(file_path, "w") as temp:
            yaml.dump(
                json.loads(
                    self.openapi_spec.model_dump_json(by_alias=True, exclude_none=True)
                ),
                temp,
            )
