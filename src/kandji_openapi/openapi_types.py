from typing import Mapping, NotRequired, TypedDict

# No Nesting


class ContactObject(TypedDict):
    name: NotRequired[str]
    url: NotRequired[str]
    email: NotRequired[str]


class DiscriminatorObject(TypedDict):
    propertyName: str
    mapping: Mapping[str, str]


class ExternalDocumentationObject(TypedDict):
    url: str
    description: NotRequired[str]


class LicenseObject(TypedDict):
    name: str
    identifier: NotRequired[str]
    url: NotRequired[str]


class ServerVariableObject(TypedDict):
    default: str
    description: NotRequired[str]
    enum: NotRequired[list[str]]


class XMLObject(TypedDict):
    name: NotRequired[str]
    namespace: NotRequired[str]
    prefix: NotRequired[str]
    attribute: NotRequired[bool]
    wrapped: NotRequired[bool]


# Includes Nesting


class InfoObject(TypedDict):
    title: str
    version: str
    summary: NotRequired[str]
    description: NotRequired[str]
    termsOfService: NotRequired[str]
    contact: NotRequired[ContactObject]
    license: NotRequired[LicenseObject]


class ServerObject(TypedDict):
    url: str
    description: NotRequired[str]
    variables: NotRequired[Mapping[str, ServerVariableObject]]


class TagObject(TypedDict):
    name: str
    description: NotRequired[str]
    externalDocs: NotRequired[ExternalDocumentationObject]
