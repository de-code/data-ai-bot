from dataclasses import dataclass
import inspect
import logging
from typing import Mapping, Sequence, Union

from smolagents import Tool  # type: ignore

from data_ai_bot.tools.data_hub.docmap import DocMapTool
from data_ai_bot.tools.example.joke import get_joke  # type: ignore


LOGGER = logging.getLogger(__name__)


ToolOrToolType = Union[Tool, type[Tool]]


DEFAULT_TOOL_MAPPING: Mapping[str, ToolOrToolType] = {
    'get_joke': get_joke,
    'get_docmap_by_manuscript_id': DocMapTool
}


@dataclass(frozen=True)
class DefaultToolResolver:
    headers: Mapping[str, str]

    def get_tool_by_name(self, tool_name: str) -> Tool:
        tool_or_tool_type = DEFAULT_TOOL_MAPPING.get(tool_name)
        if tool_or_tool_type is not None:
            tool = self.get_tool_by_instance_or_tool_type(tool_or_tool_type)
            if tool.name != tool_name:
                LOGGER.info('Renaming tool: %r -> %r', tool.name, tool_name)
                tool.name = tool_name
            return tool
        raise KeyError(f'Unrecognised tool: {repr(tool_name)}')

    def get_tool_by_instance_or_tool_type(self, tool_or_tool_type: ToolOrToolType) -> Tool:
        if isinstance(tool_or_tool_type, Tool):
            LOGGER.info('Already a tool instance: %r', tool_or_tool_type)
            return tool_or_tool_type
        return self.get_tool_by_type(tool_or_tool_type)

    def get_tool_by_type(self, tool_type: type[Tool]) -> Tool:
        parameters = inspect.signature(tool_type).parameters
        LOGGER.info('tool_type: %r, parameters: %r', tool_type, parameters)
        available_kwargs = {
            'headers': self.headers
        }
        kwargs = {
            key: value
            for key, value in available_kwargs.items()
            if key in parameters
        }
        return tool_type(**kwargs)

    def get_tools_by_name(
        self,
        tool_names: Sequence[str]
    ) -> Sequence[Tool]:
        return [
            self.get_tool_by_name(tool_name)
            for tool_name in tool_names
        ]
