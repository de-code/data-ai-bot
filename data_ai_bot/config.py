from dataclasses import dataclass, field
import logging
import os
from typing import Any, Mapping, Optional, Sequence

import yaml

from data_ai_bot.config_typing import (
    AppConfigDict,
    BaseAgentConfigDict,
    FromMcpConfigDict,
    FromPythonToolClassConfigDict,
    FromPythonToolInstanceConfigDict,
    ManagedAgentConfigDict,
    ToolCollectionDefinitionsConfigDict,
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
    description: Optional[str] = None

    @staticmethod
    def from_dict(
        from_python_tool_instance_config_dict: FromPythonToolInstanceConfigDict
    ) -> 'FromPythonToolInstanceConfig':
        return FromPythonToolInstanceConfig(
            name=from_python_tool_instance_config_dict['name'],
            module=from_python_tool_instance_config_dict['module'],
            key=from_python_tool_instance_config_dict['key'],
            description=from_python_tool_instance_config_dict.get('description')
        )


@dataclass(frozen=True)
class FromPythonToolClassConfig:
    name: str
    module: str
    class_name: str
    init_parameters: Mapping[str, Any] = field(default_factory=dict)
    description: Optional[str] = None

    @staticmethod
    def from_dict(
        from_python_tool_class_config_dict: FromPythonToolClassConfigDict
    ) -> 'FromPythonToolClassConfig':
        return FromPythonToolClassConfig(
            name=from_python_tool_class_config_dict['name'],
            module=from_python_tool_class_config_dict['module'],
            class_name=from_python_tool_class_config_dict['className'],
            init_parameters=from_python_tool_class_config_dict.get('initParameters', {}),
            description=from_python_tool_class_config_dict.get('description')
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
class FromMcpConfig:
    name: str
    url: str
    transport: str
    tools: Sequence[str] = field(default_factory=list)

    @staticmethod
    def from_dict(
        from_mcp_config_dict: FromMcpConfigDict
    ) -> 'FromMcpConfig':
        return FromMcpConfig(
            name=from_mcp_config_dict['name'],
            url=from_mcp_config_dict['url'],
            transport=from_mcp_config_dict.get('transport', 'streamable-http'),
            tools=from_mcp_config_dict.get('tools', [])
        )


@dataclass(frozen=True)
class ToolCollectionDefinitionsConfig:
    from_mcp: Sequence[FromMcpConfig] = field(default_factory=list)

    @staticmethod
    def from_dict(
        tool_collection_definitions_config_dict: ToolCollectionDefinitionsConfigDict
    ) -> 'ToolCollectionDefinitionsConfig':
        return ToolCollectionDefinitionsConfig(
            from_mcp=list(map(
                FromMcpConfig.from_dict,
                tool_collection_definitions_config_dict.get('fromMcp', [])
            )),
        )

    def __bool__(self) -> bool:
        return bool(self.from_mcp)


@dataclass(frozen=True)
class BaseAgentConfig:
    tools: Sequence[str]
    tool_collections: Sequence[str]
    system_prompt: Optional[str] = None

    @staticmethod
    def from_dict(agent_config_dict: BaseAgentConfigDict) -> 'BaseAgentConfig':
        return BaseAgentConfig(
            tools=agent_config_dict['tools'],
            tool_collections=agent_config_dict.get('toolCollections', []),
            system_prompt=agent_config_dict.get('systemPrompt')
        )


@dataclass(frozen=True, kw_only=True)
class ManagedAgentConfig(BaseAgentConfig):
    name: str
    description: str

    @staticmethod
    def from_dict(
        agent_config_dict: ManagedAgentConfigDict  # type: ignore[override]
    ) -> 'ManagedAgentConfig':
        base_agent_config = BaseAgentConfig.from_dict(agent_config_dict)
        return ManagedAgentConfig(
            name=agent_config_dict['name'],
            description=agent_config_dict['description'],
            tools=base_agent_config.tools,
            tool_collections=base_agent_config.tool_collections,
            system_prompt=base_agent_config.system_prompt
        )


@dataclass(frozen=True)
class AppConfig:
    tool_definitions: ToolDefinitionsConfig
    tool_collection_definitions: ToolCollectionDefinitionsConfig
    agent: BaseAgentConfig
    managed_agents: Sequence[ManagedAgentConfig]

    @staticmethod
    def from_dict(app_config_dict: AppConfigDict) -> 'AppConfig':
        return AppConfig(
            tool_definitions=ToolDefinitionsConfig.from_dict(
                app_config_dict.get('toolDefinitions', {})
            ),
            tool_collection_definitions=ToolCollectionDefinitionsConfig.from_dict(
                app_config_dict.get('toolCollectionDefinitions', {})
            ),
            agent=BaseAgentConfig.from_dict(app_config_dict['agent']),
            managed_agents=list(map(
                ManagedAgentConfig.from_dict,
                app_config_dict.get('managedAgents', [])
            ))
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
