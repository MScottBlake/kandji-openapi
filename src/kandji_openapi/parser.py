import json
import os
from typing import Any

from kandji_openapi.models.postman_collection import PostmanCollection


class PostmanParser:
    """Parser for Postman Collection JSON files"""

    def __init__(self, json_data: dict[str, Any]) -> None:
        self.json_data = json_data
        self._validate_collection()

    def _validate_collection(self) -> None:
        """Validate basic collection structure"""
        if not isinstance(self.json_data, dict):
            raise ValueError("Collection data must be a JSON object")
        if "info" not in self.json_data:
            raise ValueError("Collection must have 'info' field")
        if not isinstance(self.json_data.get("item", []), list):
            raise ValueError("Collection 'item' field must be an array of items.")

    def parse(self) -> PostmanCollection:
        """Parse the collection JSON data into a PostmanCollection object"""
        return PostmanCollection.from_data(self.json_data)

    @classmethod
    def from_file(cls, file_path: str) -> "PostmanParser":
        """Create a parser instance from a JSON file path"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Collection file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in collection file: {e}")
        except Exception as e:
            raise IOError(f"Error reading collection file: {e}")

        return cls(json_data)
