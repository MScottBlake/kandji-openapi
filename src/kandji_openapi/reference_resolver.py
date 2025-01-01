from typing import Any


class ReferenceResolver:
    def __init__(self, openapi_spec: dict[str, Any]) -> None:
        self.openapi_spec = openapi_spec
        self.components_schemas = openapi_spec.setdefault("components", {}).setdefault(
            "schemas", {}
        )
        self.seen_schemas: dict[str, str] = {}

    def resolve_references(self):
        """Replace duplicate schemas with references across the OpenAPI spec."""
        for path, path_item in self.openapi_spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method in {"get", "post", "put", "delete", "patch"}:
                    self._resolve_operation_schemas(operation)

    def _resolve_operation_schemas(self, operation: dict[str, Any]) -> None:
        """Resolve schemas in requestBody and responses for each operation."""
        if "requestBody" in operation:
            self._resolve_schema_in_content(operation["requestBody"].get("content", {}))

        for response in operation.get("responses", {}).values():
            self._resolve_schema_in_content(response.get("content", {}))

    def _resolve_schema_in_content(self, content: dict[str, dict[str, Any]]) -> None:
        for media_type, media_obj in content.items():
            if "schema" in media_obj:
                schema = media_obj["schema"]
                schema_name = schema.get("title") or self._generate_schema_name(schema)
                ref = self._add_schema_to_components(schema_name, schema)
                media_obj["schema"] = ref

    def _add_schema_to_components(
        self, name: str, schema: dict[str, Any]
    ) -> dict[str, str]:
        """Adds schema to components.schemas if it doesn't exist, and returns a $ref."""
        if name not in self.components_schemas:
            self.components_schemas[name] = schema
        return {"$ref": f"#/components/schemas/{name}"}

    def _generate_schema_name(self, schema: dict[str, Any]) -> str:
        """Generates a unique schema name based on its structure."""
        schema_key = str(schema)
        if schema_key not in self.seen_schemas:
            schema_id = f"Schema{len(self.seen_schemas) + 1}"
            self.seen_schemas[schema_key] = schema_id
        return self.seen_schemas[schema_key]
