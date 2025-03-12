from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import importlib
import inspect
import logging
from typing import Any, Mapping, Sequence

from smolagents import Tool  # type: ignore

from data_ai_bot.config import (
    FromPythonToolClassConfig,
    FromPythonToolInstanceConfig,
    ToolDefinitionsConfig
)


LOGGER = logging.getLogger(__name__)


class ToolResolver(ABC):
    @abstractmethod
    def get_tool_by_name(self, tool_name: str) -> Tool:
        pass

    def get_tools_by_name(
        self,
        tool_names: Sequence[str]
    ) -> Sequence[Tool]:
        return [
            self.get_tool_by_name(tool_name)
            for tool_name in tool_names
        ]


class InvalidToolNameError(KeyError):
    pass


def get_tool_with_name(tool: Tool, tool_name: str) -> Tool:
    if tool.name != tool_name:
        LOGGER.info('Renaming tool: %r -> %r', tool.name, tool_name)
        tool.name = tool_name
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
    return get_tool_with_name(tool, tool_name=config.name)


def get_tool_from_python_tool_class(
    config: FromPythonToolClassConfig,
    available_kwargs: Mapping[str, Any]
) -> Tool:
    tool_module = importlib.import_module(config.module)
    tool_class = getattr(tool_module, config.class_name)
    assert isinstance(tool_class, type)
    tool = get_tool_from_tool_class(
        tool_class,
        init_parameters=config.init_parameters,
        available_kwargs=available_kwargs
    )
    assert isinstance(tool, Tool)
    return get_tool_with_name(tool, tool_name=config.name)


@dataclass(frozen=True)
class ConfigToolResolver(ToolResolver):
    tool_definitions_config: ToolDefinitionsConfig
    headers: Mapping[str, str] = field(default_factory=dict)

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
