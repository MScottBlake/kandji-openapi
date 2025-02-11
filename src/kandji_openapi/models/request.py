from dataclasses import dataclass, field
from typing import Any, Optional

from models.auth import Auth
from models.request_body import PostmanRequestBody
from models.response import PostmanResponse
from models.url import URL
from openapi_pydantic import (
    DataType,
    ExternalDocumentation,
    Operation,
    Parameter,
    ParameterLocation,
    Reference,
    Response,
    Responses,
    Schema,
)
from strings import string_formatting, to_camel_case


@dataclass
class PostmanRequest:
    method: str
    url: URL
    summary: str = ""
    headers: list[dict[str, Any]] = field(default_factory=list)
    body: Optional[PostmanRequestBody] = None
    description: Optional[str] = None
    auth: Optional[Auth] = None
    proxy: Optional[dict[str, Any]] = None
    certificate: Optional[dict[str, Any]] = None
    tag: str = ""
    external_docs: str = ""
    responses: list[PostmanResponse] = field(default_factory=list)

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        name: str,
        responses: list[dict[str, Any]],
        tag: str = "",
        url: str = "",
    ) -> Optional["PostmanRequest"]:
        if not data:
            return None

        if data.get("urlObject"):
            url_data = data.get("urlObject", {})
        else:
            url_data = data.get("url", {})
            if isinstance(url_data, str):
                url_data = {"raw": url_data}

        return cls(
            method=data.get("method", "GET"),
            url=URL.from_data(url_data),
            summary=name,
            headers=data.get("header", []),
            body=PostmanRequestBody.from_data(data.get("body", {})),
            description=string_formatting(data.get("description", "")),
            auth=Auth.from_data(data.get("auth", {})),
            proxy=data.get("proxy"),
            certificate=data.get("certificate"),
            tag=tag,
            external_docs=url,
            responses=[PostmanResponse.from_data(r) for r in responses],
        )

    def get_auth(self) -> Optional[Auth]:
        return self.auth

    def get_description(self) -> Optional[str]:
        return self.description

    def get_host(self) -> str:
        return self.url.get_base_url()

    def get_method(self) -> str:
        return self.method

    def get_parameters(self) -> Optional[list[Parameter | Reference]]:
        """Extract all parameters from request"""
        parameters: list[Parameter | Reference] = []

        # Path parameters
        parameters.extend(self.url.get_path_parameters())

        # Query parameters
        for query in self.url.query:
            description = string_formatting(
                query.get("description", {}).get("content", "")
            )

            parameters.append(
                Parameter(
                    name=query.get("key", ""),
                    param_in=ParameterLocation.QUERY,  # type: ignore
                    schema=Schema(type=DataType("string")),
                    required=not query.get("disabled", False),
                    description=string_formatting(description),
                    example=query.get("value"),
                )
            )
        # Header parameters
        for header in self.headers:
            if header.get("disabled", False):
                continue

            parameters.append(
                Parameter(
                    name=header.get("key", ""),
                    param_in=ParameterLocation.HEADER,  # type: ignore
                    schema=Schema(type=DataType("string")),
                    required=True,
                    description=string_formatting(header.get("description", "")),
                    example=header.get("value"),
                )
            )

        return parameters

    def get_path(self) -> str:
        return self.url.get_path_string()

    def get_responses(self) -> Responses:
        responses: Responses = {}
        for response in self.responses:
            responses.update(response.to_openapi())

        if not responses:
            responses = {"204": Response(description="No Content")}

        return responses

    def get_tag(self) -> str:
        return self.tag

    def to_openapi(self) -> dict[str, Operation]:
        """Convert to OpenAPI request object"""
        method = self.method.lower()

        tag_camel_case = to_camel_case(self.get_tag())
        summary_camel_case = to_camel_case(self.summary)

        operation = Operation(
            summary=self.summary,
            operationId=f"{tag_camel_case}_{summary_camel_case}",
            responses=self.get_responses(),
        )

        if tag := self.get_tag():
            operation.tags = [tag]
        if self.description:
            operation.description = self.description
        if parameters := self.get_parameters():
            operation.parameters = parameters
        if self.body:
            operation.requestBody = self.body.to_openapi()
        if self.auth:
            operation.security = [{self.auth.get_type(): []}]

        if self.url:
            operation.externalDocs = ExternalDocumentation(url=self.external_docs)

        return {method: operation}
