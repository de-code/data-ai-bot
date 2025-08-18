from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import jinja2
import yaml

from data_ai_bot.config_typing import (
    AppConfigDict,
    BaseAgentConfigDict,
    FromMcpConfigDict,
    FromPythonToolClassConfigDict,
    FromPythonToolInstanceConfigDict,
    ManagedAgentConfigDict,
    ModelConfigDict,
    ToolCollectionDefinitionsConfigDict,
    ToolDefinitionsConfigDict
)


LOGGER = logging.getLogger(__name__)


class EnvironmentVariables:
    CONFIG_FILE = 'CONFIG_FILE'


def read_secret_from_env(var_name: str) -> str:
    path = os.environ[var_name]
    return Path(path).read_text(encoding='utf-8')


def get_evaluated_template(
    template: str,
    variables: Optional[Mapping[str, Any]] = None
) -> Any:
    env = jinja2.Environment()
    env.globals['env'] = dict(os.environ)
    env.globals['read_secret_from_env'] = read_secret_from_env
    compiled_template = env.from_string(template)
    return compiled_template.render(variables or {})


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
class ModelConfig:
    model_name: str
    base_url: str
    api_key: str = field(repr=False)

    @staticmethod
    def from_dict(model_config_dict: ModelConfigDict) -> 'ModelConfig':
        return ModelConfig(
            model_name=model_config_dict['model_name'],
            base_url=model_config_dict['base_url'],
            api_key=get_evaluated_template(model_config_dict['api_key'])
        )


@dataclass(frozen=True)
class BaseAgentConfig:
    tools: Sequence[str]
    tool_collections: Sequence[str]
    system_prompt: Optional[str] = None
    managed_agent_names: Sequence[str] = field(default_factory=list)
    model_name: Optional[str] = None

    @staticmethod
    def from_dict(agent_config_dict: BaseAgentConfigDict) -> 'BaseAgentConfig':
        return BaseAgentConfig(
            tools=agent_config_dict.get('tools', []),
            tool_collections=agent_config_dict.get('toolCollections', []),
            system_prompt=agent_config_dict.get('systemPrompt'),
            managed_agent_names=agent_config_dict.get('managedAgents', []),
            model_name=agent_config_dict.get('model')
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
            system_prompt=base_agent_config.system_prompt,
            model_name=base_agent_config.model_name
        )


@dataclass(frozen=True)
class AppConfig:
    tool_definitions: ToolDefinitionsConfig
    tool_collection_definitions: ToolCollectionDefinitionsConfig
    models: Sequence[ModelConfig]
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
            models=list(map(
                ModelConfig.from_dict,
                app_config_dict.get('models', [])
            )),
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
