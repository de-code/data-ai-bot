from typing import Sequence, TypedDict


class AgentConfigDict(TypedDict):
    tools: Sequence[str]


class AppConfigDict(TypedDict):
    agent: AgentConfigDict
