import json
import os
import tempfile
from pathlib import Path

from openapi_pydantic import parse_obj
from openapi_pydantic.v3.parser import OpenAPIv3
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError
from openapi_spec_validator.versions.shortcuts import get_spec_version
from ruamel.yaml import YAML

from kandji_openapi.models.postman_collection import PostmanCollection


class OpenAPIGenerator:
    def __init__(self, collection: PostmanCollection) -> None:
        self.collection = collection
        self.openapi_spec = self._generate_spec()

    def _generate_spec(self) -> OpenAPIv3:
        """Generate OpenAPI specification from Postman collection"""
        return parse_obj(data=self.collection.to_openapi())

    def _write_json_file(self, file_path: Path) -> None:
        with open(file_path, "w") as temp:
            json.dump(
                self.openapi_spec.model_dump_json(
                    by_alias=True, exclude_none=True, indent=2
                ),
                temp,
            )

    def _write_yaml_file(self, file_path: Path) -> None:
        yaml = YAML(typ="safe", pure=True)
        yaml.allow_unicode = True
        yaml.default_flow_style = False
        yaml.explicit_start = True
        yaml.preserve_quotes = True

        with open(file_path, "w") as temp:
            yaml_model = self.openapi_spec.model_dump(by_alias=True, exclude_none=True)
            yaml.dump(yaml_model, temp)

    def validate_spec(self) -> bool:
        """Validate the generated OpenAPI spec, providing detailed feedback if invalid."""
        temp_json_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        with open(temp_json_file.name, "w") as _:
            self._write_json_file(Path(temp_json_file.name))

        temp_yaml_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        with open(temp_yaml_file.name, "w") as _:
            self._write_yaml_file(Path(temp_yaml_file.name))

        try:
            spec_dict, _ = read_from_filename(temp_json_file.name)
            validate(spec_dict)

            spec_dict, _ = read_from_filename(temp_yaml_file.name)
            validate(spec_dict)

            print(f"Successfully validated as {get_spec_version(spec_dict)}.")
            return True
        except OpenAPIValidationError as error:
            print(f"Validation failed: {error}")
            return False
        finally:
            os.remove(temp_json_file.name)
            os.remove(temp_yaml_file.name)

    def to_json(self, output_path: Path) -> None:
        """Write OpenAPI spec to YAML file"""
        self._write_json_file(output_path)

    def to_yaml(self, output_path: Path) -> None:
        """Write OpenAPI spec to YAML file"""
        self._write_yaml_file(output_path)
