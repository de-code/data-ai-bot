from typing import Any, Mapping, NotRequired, Sequence, TypedDict


class FromPythonToolInstanceConfigDict(TypedDict):
    name: str
    module: str
    key: str


class FromPythonToolClassConfigDict(TypedDict):
    name: str
    module: str
    className: str
    initParameters: NotRequired[Mapping[str, Any]]


class ToolDefinitionsConfigDict(TypedDict):
    fromPythonToolInstance: NotRequired[Sequence[FromPythonToolInstanceConfigDict]]
    fromPythonToolClass: NotRequired[Sequence[FromPythonToolClassConfigDict]]


class AgentConfigDict(TypedDict):
    tools: Sequence[str]


class AppConfigDict(TypedDict):
    toolDefinitions: NotRequired[ToolDefinitionsConfigDict]
    agent: AgentConfigDict
