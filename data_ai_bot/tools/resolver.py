from dataclasses import dataclass
from typing import Mapping, Sequence

from smolagents import Tool  # type: ignore

from data_ai_bot.tools.data_hub.docmap import DocMapTool
from data_ai_bot.tools.example.joke import get_joke  # type: ignore


@dataclass(frozen=True)
class DefaultToolResolver:
    headers: Mapping[str, str]

    def get_tool_by_name(self, tool_name: str) -> Tool:
        if tool_name == 'get_joke':
            return get_joke
        if tool_name == 'get_docmap_by_manuscript_id':
            return DocMapTool(headers=self.headers)
        raise KeyError(f'Unrecognised tool: {repr(tool_name)}')

    def get_tools_by_name(
        self,
        tool_names: Sequence[str]
    ) -> Sequence[Tool]:
        return [
            self.get_tool_by_name(tool_name)
            for tool_name in tool_names
        ]
