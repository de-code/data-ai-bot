from typing import Any, Mapping, NotRequired, Sequence, TypedDict


class FromPythonToolInstanceConfigDict(TypedDict):
    name: str
    module: str
    key: str
    description: NotRequired[str]


class FromPythonToolClassConfigDict(TypedDict):
    name: str
    module: str
    className: str
    initParameters: NotRequired[Mapping[str, Any]]
    description: NotRequired[str]


class ToolDefinitionsConfigDict(TypedDict):
    fromPythonToolInstance: NotRequired[Sequence[FromPythonToolInstanceConfigDict]]
    fromPythonToolClass: NotRequired[Sequence[FromPythonToolClassConfigDict]]


class FromMcpConfigDict(TypedDict):
    name: str
    url: str


class ToolCollectionDefinitionsConfigDict(TypedDict):
    fromMcp: NotRequired[Sequence[FromMcpConfigDict]]


class AgentConfigDict(TypedDict):
    tools: Sequence[str]
    toolCollections: NotRequired[Sequence[str]]
    systemPrompt: NotRequired[str]


class AppConfigDict(TypedDict):
    toolDefinitions: NotRequired[ToolDefinitionsConfigDict]
    toolCollectionDefinitions: NotRequired[ToolCollectionDefinitionsConfigDict]
    agent: AgentConfigDict
