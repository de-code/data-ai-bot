from dataclasses import dataclass, field
import logging
import os
from typing import Any, Mapping, Sequence

import yaml

from data_ai_bot.config_typing import (
    AgentConfigDict,
    AppConfigDict,
    FromPythonToolClassConfigDict,
    FromPythonToolInstanceConfigDict,
    ToolDefinitionsConfigDict
)


LOGGER = logging.getLogger(__name__)


class EnvironmentVariables:
    CONFIG_FILE = 'CONFIG_FILE'


@dataclass(frozen=True)
class FromPythonToolInstanceConfig:
    name: str
    module: str
    key: str

    @staticmethod
    def from_dict(
        from_python_tool_instance_config_dict: FromPythonToolInstanceConfigDict
    ) -> 'FromPythonToolInstanceConfig':
        return FromPythonToolInstanceConfig(
            name=from_python_tool_instance_config_dict['name'],
            module=from_python_tool_instance_config_dict['module'],
            key=from_python_tool_instance_config_dict['key']
        )


@dataclass(frozen=True)
class FromPythonToolClassConfig:
    name: str
    module: str
    class_name: str
    init_parameters: Mapping[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(
        from_python_tool_class_config_dict: FromPythonToolClassConfigDict
    ) -> 'FromPythonToolClassConfig':
        return FromPythonToolClassConfig(
            name=from_python_tool_class_config_dict['name'],
            module=from_python_tool_class_config_dict['module'],
            class_name=from_python_tool_class_config_dict['className'],
            init_parameters=from_python_tool_class_config_dict.get('initParameters', {})
        )


@dataclass(frozen=True)
class ToolDefinitionsConfig:
    from_python_tool_instance: Sequence[FromPythonToolInstanceConfig] = field(default_factory=list)
    from_python_tool_class: Sequence[FromPythonToolClassConfig] = field(default_factory=list)

    @staticmethod
    def from_dict(
        tool_definitions_config_dict: ToolDefinitionsConfigDict
    ) -> 'ToolDefinitionsConfig':
        return ToolDefinitionsConfig(
            from_python_tool_instance=list(map(
                FromPythonToolInstanceConfig.from_dict,
                tool_definitions_config_dict.get('fromPythonToolInstance', [])
            )),
            from_python_tool_class=list(map(
                FromPythonToolClassConfig.from_dict,
                tool_definitions_config_dict.get('fromPythonToolClass', [])
            ))
        )

    def __bool__(self) -> bool:
        return bool(
            self.from_python_tool_instance
            or self.from_python_tool_class
        )


@dataclass(frozen=True)
class AgentConfig:
    tools: Sequence[str]

    @staticmethod
    def from_dict(agent_config_dict: AgentConfigDict) -> 'AgentConfig':
        return AgentConfig(
            tools=agent_config_dict['tools']
        )


@dataclass(frozen=True)
class AppConfig:
    tool_definitions: ToolDefinitionsConfig
    agent: AgentConfig

    @staticmethod
    def from_dict(app_config_dict: AppConfigDict) -> 'AppConfig':
        return AppConfig(
            tool_definitions=ToolDefinitionsConfig.from_dict(
                app_config_dict.get('toolDefinitions', {})
            ),
            agent=AgentConfig.from_dict(app_config_dict['agent'])
        )


def get_app_config_file() -> str:
    return os.environ[EnvironmentVariables.CONFIG_FILE]


def load_app_config_from_file(config_file: str) -> AppConfig:
    LOGGER.info('Loading config from: %r', config_file)
    with open(config_file, 'r', encoding='utf-8') as config_fp:
        return AppConfig.from_dict(
            yaml.safe_load(config_fp)
        )


def load_app_config() -> AppConfig:
    return load_app_config_from_file(get_app_config_file())
