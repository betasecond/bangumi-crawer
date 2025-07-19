from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Info(BaseModel):
    title: str
    version: str
    description: Optional[str] = None


class Server(BaseModel):
    url: str
    description: Optional[str] = None


class Schema(BaseModel):
    type: Optional[str] = None
    format: Optional[str] = None
    ref: Optional[str] = Field(None, alias="$ref")
    properties: Optional[Dict[str, "Schema"]] = None
    required: Optional[List[str]] = None
    description: Optional[str] = None
    example: Any = None


class Parameter(BaseModel):
    name: str
    in_: str = Field(..., alias="in")
    description: Optional[str] = None
    required: bool = False
    schema_: Optional[Schema] = Field(None, alias="schema")


class Response(BaseModel):
    description: str
    content: Optional[Dict[str, Any]] = None


class Operation(BaseModel):
    summary: Optional[str] = None
    description: Optional[str] = None
    operation_id: Optional[str] = Field(None, alias="operationId")
    parameters: Optional[List[Parameter]] = None
    responses: Dict[str, Response]


class PathItem(BaseModel):
    get: Optional[Operation] = None
    post: Optional[Operation] = None
    put: Optional[Operation] = None
    delete: Optional[Operation] = None
    patch: Optional[Operation] = None


class Components(BaseModel):
    schemas: Optional[Dict[str, Schema]] = None
    security_schemes: Optional[Dict[str, Any]] = Field(
        None, alias="securitySchemes"
    )


class OpenAPI(BaseModel):
    openapi: str
    info: Info
    servers: List[Server]
    paths: Dict[str, PathItem]
    components: Components


Schema.model_rebuild() 