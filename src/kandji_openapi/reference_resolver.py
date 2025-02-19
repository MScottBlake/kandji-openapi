from typing import Any, Optional

from openapi_pydantic import (
    Components,
    Header,
    OpenAPI,
    Operation,
    Parameter,
    PathItem,
    Reference,
    RequestBody,
    Response,
)


class ReferenceResolver:
    def __init__(self, spec: OpenAPI) -> None:
        self.spec = spec

    def resolve_references(self) -> OpenAPI:
        """Replace duplicate components with references across the OpenAPI spec."""
        if not self.spec.paths:
            return self.spec

        if not self.spec.components:
            self.spec.components = Components()

        for path, path_item in self.spec.paths.items():
            self._resolve_path_item(path_item)

        return self.spec

    def _resolve_path_item(self, path_item: PathItem) -> None:
        """Resolve references within a PathItem."""
        for method in {"get", "put", "post", "delete", "patch"}:
            operation: Operation = getattr(path_item, method, Operation())
            if operation:
                self._resolve_operation(operation)

    def _resolve_operation(self, operation: Operation) -> None:
        """Resolve references within an Operation."""
        self._resolve_parameters(operation)
        self._resolve_request_body(operation)
        self._resolve_responses(operation)

    def _resolve_headers(self, response: Response) -> None:
        if not response.headers:
            return

        for header_name, header in response.headers.items():
            if not isinstance(header, Header):
                continue

            reference = self._create_reference(
                "headers", header_name, header, check_content=True
            )
            response.headers[header_name] = reference

    def _resolve_parameters(self, operation: Operation) -> None:
        """Resolve references for Parameters."""
        if not operation.parameters:
            return

        for index, parameter in enumerate(operation.parameters):
            if not isinstance(parameter, Parameter):
                continue

            reference = self._create_reference(
                "parameters", parameter.name, parameter, check_content=True
            )
            operation.parameters[index] = reference

    def _resolve_request_body(self, operation: Operation) -> None:
        """Resolve references for RequestBody."""
        if not operation.requestBody:
            return

        if not isinstance(operation.requestBody, RequestBody):
            return

        name = f"{operation.summary}_RequestBody"

        reference = self._create_reference("requestBodies", name, operation.requestBody)
        operation.requestBody = reference

    def _resolve_responses(self, operation: Operation) -> None:
        """Resolve references for Responses."""
        if not operation.responses:
            return

        for return_code, response in operation.responses.items():
            if not isinstance(response, Response):
                continue

            self._resolve_headers(response)

            reference = self._create_reference(
                "responses", f"{operation.summary}_{return_code}_Response", response
            )
            operation.responses[return_code] = reference

    def _component_exists(
        self,
        component_type: str,
        name: str,
        component: Any = None,
        check_content: bool = False,
    ) -> bool:
        if not self.spec.components:
            return False

        components_dict: Optional[dict] = getattr(
            self.spec.components, component_type, None
        )
        if not components_dict:
            return False

        existing_component = components_dict.get(name)
        if not existing_component:
            return False

        if check_content and component:
            if existing_component.model_dump(
                by_alias=True, exclude_none=True
            ) != component.model_dump(by_alias=True, exclude_none=True):
                return False

        return True

    def _create_reference(
        self,
        component_type: str,
        name: str,
        component: Any,
        check_content: bool = False,
    ) -> Reference:
        """Create a reference for a component if it doesn't already exist."""
        name = name.replace(" ", "_")

        components_dict = getattr(self.spec.components, component_type, {})
        if not components_dict:
            components_dict = {}
            setattr(self.spec.components, component_type, components_dict)

        # Set a unique name
        counter = 0
        new_name = name
        while self._component_exists(component_type, new_name):
            # Check if a component with the same content already exists
            if check_content and self._component_exists(
                component_type, new_name, component, check_content
            ):
                ref_name = f"#/components/{component_type}/{new_name}"
                return Reference(ref=ref_name)  # type: ignore

            counter += 1
            new_name = f"{name}_{counter}"

        name = new_name

        ref_name = f"#/components/{component_type}/{name}"

        if ref_name not in components_dict:
            components_dict[name] = component

        return Reference(ref=ref_name)  # type: ignore
