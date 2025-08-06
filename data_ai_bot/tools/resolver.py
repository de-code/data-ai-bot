from abc import ABC, abstractmethod
from contextlib import ExitStack
from dataclasses import dataclass, field
import importlib
import inspect
import logging
from typing import Any, Mapping, Optional, Sequence

from smolagents import Tool, ToolCollection  # type: ignore

from data_ai_bot.config import (
    FromMcpConfig,
    FromPythonToolClassConfig,
    FromPythonToolInstanceConfig,
    ToolCollectionDefinitionsConfig,
    ToolDefinitionsConfig
)


LOGGER = logging.getLogger(__name__)


class ToolResolver(ABC):
    @abstractmethod
    def get_tool_by_name(self, tool_name: str) -> Tool:
        pass

    @abstractmethod
    def get_tools_by_collection_name(self, tool_collection_name: str) -> Sequence[Tool]:
        pass

    def get_tools_by_name(
        self,
        tool_names: Sequence[str],
        tool_collection_names: Optional[Sequence[str]] = None
    ) -> Sequence[Tool]:
        result = [
            self.get_tool_by_name(tool_name)
            for tool_name in tool_names
        ]
        if tool_collection_names:
            for tool_collection_name in tool_collection_names:
                result.extend(self.get_tools_by_collection_name(tool_collection_name))
        return result


class InvalidToolNameError(KeyError):
    pass


class InvalidToolCollectionNameError(KeyError):
    pass


def get_updated_tool(
    tool: Tool,
    tool_name: str,
    description: Optional[str] = None
) -> Tool:
    if tool.name != tool_name:
        LOGGER.info('Renaming tool: %r -> %r', tool.name, tool_name)
        tool.name = tool_name
    if description and tool.description != description:
        LOGGER.info('Updating tool description of %r: %r', tool_name, description)
        tool.description = description
    return tool


def get_tool_from_tool_class(
    tool_class: type[Tool],
    init_parameters: Mapping[str, Any],
    available_kwargs: Mapping[str, Any]
) -> Tool:
    parameters = inspect.signature(tool_class).parameters
    LOGGER.info('tool_class: %r, parameters: %r', tool_class, parameters)
    extra_kwargs = {
        key: value
        for key, value in available_kwargs.items()
        if key in parameters and key not in init_parameters
    }
    return tool_class(**init_parameters, **extra_kwargs)


def get_tool_from_python_tool_instance(
    config: FromPythonToolInstanceConfig
) -> Tool:
    tool_module = importlib.import_module(config.module)
    tool = getattr(tool_module, config.key)
    assert isinstance(tool, Tool)
    return get_updated_tool(tool, tool_name=config.name, description=config.description)


def get_tool_from_python_tool_class(
    config: FromPythonToolClassConfig,
    available_kwargs: Mapping[str, Any]
) -> Tool:
    tool_module = importlib.import_module(config.module)
    tool_class = getattr(tool_module, config.class_name)
    assert isinstance(tool_class, type)
    if config.description:
        available_kwargs = {
            **available_kwargs,
            'description': config.description
        }
    tool = get_tool_from_tool_class(
        tool_class,
        init_parameters=config.init_parameters,
        available_kwargs=available_kwargs
    )
    assert isinstance(tool, Tool)
    return get_updated_tool(tool, tool_name=config.name, description=config.description)


@dataclass(frozen=True)
class ConfigToolResolver(ToolResolver):
    tool_definitions_config: ToolDefinitionsConfig = (
        ToolDefinitionsConfig()
    )
    tool_collection_definitions_config: ToolCollectionDefinitionsConfig = (
        ToolCollectionDefinitionsConfig(from_mcp=[])
    )
    headers: Mapping[str, str] = field(default_factory=dict)
    exit_stack: ExitStack = field(default_factory=ExitStack)

    def __enter__(self):
        self.exit_stack.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit_stack.__exit__(exc_type, exc_val, exc_tb)
        return False

    def get_tool_by_name(self, tool_name: str) -> Tool:
        available_kwargs = {
            'name': tool_name,
            'headers': self.headers
        }
        for from_python_tool_instance_config in (
            self.tool_definitions_config.from_python_tool_instance
        ):
            if from_python_tool_instance_config.name == tool_name:
                return get_tool_from_python_tool_instance(from_python_tool_instance_config)
        for from_python_tool_class_config in (
            self.tool_definitions_config.from_python_tool_class
        ):
            if from_python_tool_class_config.name == tool_name:
                return get_tool_from_python_tool_class(
                    from_python_tool_class_config,
                    available_kwargs=available_kwargs
                )
        raise InvalidToolNameError(f'Unrecognised tool: {repr(tool_name)}')

    def _get_tools_from_mcp_config(
        self,
        from_mcp_config: FromMcpConfig
    ) -> Sequence[Tool]:
        tool_collection_cm = ToolCollection.from_mcp({
            'url': from_mcp_config.url,
            'transport': from_mcp_config.transport
        }, trust_remote_code=True)
        tool_collection = self.exit_stack.enter_context(tool_collection_cm)
        tools: Sequence[Tool] = tool_collection.tools
        if from_mcp_config.tools:
            tools = [
                tool
                for tool in tools
                if tool.name in from_mcp_config.tools
            ]
        return tools

    def get_tools_by_collection_name(self, tool_collection_name: str) -> Sequence[Tool]:
        for from_mcp in (
            self.tool_collection_definitions_config.from_mcp
        ):
            if from_mcp.name == tool_collection_name:
                return self._get_tools_from_mcp_config(from_mcp)
        raise InvalidToolCollectionNameError(f'Unrecognised tool: {repr(tool_collection_name)}')
