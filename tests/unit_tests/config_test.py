from pathlib import Path

import yaml

from data_ai_bot.config import (
    BaseAgentConfig,
    AppConfig,
    EnvironmentVariables,
    FromMcpConfig,
    FromPythonToolClassConfig,
    FromPythonToolInstanceConfig,
    ManagedAgentConfig,
    ModelConfig,
    ToolCollectionDefinitionsConfig,
    ToolDefinitionsConfig,
    load_app_config
)
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


FROM_PYTHON_TOOL_INSTANCE_CONFIG_DICT_1: FromPythonToolInstanceConfigDict = {
    'name': 'tool_1',
    'module': 'tool_module_1',
    'key': 'tool_key_1'
}


FROM_PYTHON_TOOL_CLASS_CONFIG_DICT_1: FromPythonToolClassConfigDict = {
    'name': 'tool_1',
    'module': 'tool_module_1',
    'className': 'ToolClass1'
}


FROM_MCP_CONFIG_DICT_1: FromMcpConfigDict = {
    'name': 'mcp_1',
    'url': 'http://localhost:8080/sse'
}


TOOL_DEFINITIONS_CONFIG_DICT_1: ToolDefinitionsConfigDict = {
    'fromPythonToolInstance': [
        FROM_PYTHON_TOOL_INSTANCE_CONFIG_DICT_1
    ]
}

TOOL_COLLECTION_DEFINITIONS_CONFIG_DICT_1: ToolCollectionDefinitionsConfigDict = {
    'fromMcp': [
        FROM_MCP_CONFIG_DICT_1
    ]
}


MODEL_CONFIG_DICT_1: ModelConfigDict = {
    'model_name': 'model_1',
    'base_url': 'base_url_1',
    'api_key': 'api_key_1'
}


BASE_AGENT_CONFIG_DICT_1: BaseAgentConfigDict = {
}


MANAGED_AGENT_CONFIG_DICT_1: ManagedAgentConfigDict = {
    'name': 'managed_agent_1',
    'description': 'Managed Agent 1'
}


APP_CONFIG_DICT_1: AppConfigDict = {
    'agent': BASE_AGENT_CONFIG_DICT_1
}


class TestFromPythonToolInstanceConfig:
    def test_should_load_tool_config(self):
        tool_config = FromPythonToolInstanceConfig.from_dict(
            FROM_PYTHON_TOOL_INSTANCE_CONFIG_DICT_1
        )
        assert tool_config.name == FROM_PYTHON_TOOL_INSTANCE_CONFIG_DICT_1['name']
        assert tool_config.module == FROM_PYTHON_TOOL_INSTANCE_CONFIG_DICT_1['module']
        assert tool_config.key == FROM_PYTHON_TOOL_INSTANCE_CONFIG_DICT_1['key']

    def test_should_load_tool_description(self):
        tool_config = FromPythonToolInstanceConfig.from_dict({
            **FROM_PYTHON_TOOL_INSTANCE_CONFIG_DICT_1,
            'description': 'Description 1'
        })
        assert tool_config.description == 'Description 1'


class TestFromPythonToolClassConfig:
    def test_should_load_tool_config(self):
        tool_config = FromPythonToolClassConfig.from_dict(
            FROM_PYTHON_TOOL_CLASS_CONFIG_DICT_1
        )
        assert tool_config.name == FROM_PYTHON_TOOL_CLASS_CONFIG_DICT_1['name']
        assert tool_config.module == FROM_PYTHON_TOOL_CLASS_CONFIG_DICT_1['module']
        assert tool_config.class_name == FROM_PYTHON_TOOL_CLASS_CONFIG_DICT_1['className']

    def test_should_load_tool_init_parameters(self):
        tool_config = FromPythonToolClassConfig.from_dict({
            **FROM_PYTHON_TOOL_CLASS_CONFIG_DICT_1,
            'initParameters': {'init_key_1': 'init_value_1'}
        })
        assert tool_config.init_parameters == {'init_key_1': 'init_value_1'}

    def test_should_load_tool_description(self):
        tool_config = FromPythonToolClassConfig.from_dict({
            **FROM_PYTHON_TOOL_CLASS_CONFIG_DICT_1,
            'description': 'Description 1'
        })
        assert tool_config.description == 'Description 1'


class TestToolDefinitionsConfig:
    def test_should_be_falsy_if_empty(self):
        tool_config = ToolDefinitionsConfig.from_dict({
        })
        assert bool(tool_config) is False

    def test_should_load_tool_config(self):
        tool_config = ToolDefinitionsConfig.from_dict({
            'fromPythonToolInstance': [
                FROM_PYTHON_TOOL_INSTANCE_CONFIG_DICT_1
            ],
            'fromPythonToolClass': [
                FROM_PYTHON_TOOL_CLASS_CONFIG_DICT_1
            ]
        })
        assert tool_config.from_python_tool_instance == [
            FromPythonToolInstanceConfig.from_dict(
                FROM_PYTHON_TOOL_INSTANCE_CONFIG_DICT_1
            )
        ]
        assert tool_config.from_python_tool_class == [
            FromPythonToolClassConfig.from_dict(
                FROM_PYTHON_TOOL_CLASS_CONFIG_DICT_1
            )
        ]
        assert bool(tool_config) is True


class TestFromMcpConfig:
    def test_should_load_mcp_config(self):
        mcp_config = FromMcpConfig.from_dict(
            FROM_MCP_CONFIG_DICT_1
        )
        assert mcp_config.name == FROM_MCP_CONFIG_DICT_1['name']
        assert mcp_config.url == FROM_MCP_CONFIG_DICT_1['url']

    def test_should_load_mcp_config_with_tool_selection(self):
        mcp_config = FromMcpConfig.from_dict({
            **FROM_MCP_CONFIG_DICT_1,
            'tools': ['tool_1']
        })
        assert mcp_config.tools == ['tool_1']


class TestToolCollectionDefinitionsConfig:
    def test_should_be_falsy_if_empty(self):
        tool_config = ToolCollectionDefinitionsConfig.from_dict({
        })
        assert bool(tool_config) is False

    def test_should_load_tool_config(self):
        tool_config = ToolCollectionDefinitionsConfig.from_dict({
            'fromMcp': [
                FROM_MCP_CONFIG_DICT_1
            ]
        })
        assert tool_config.from_mcp == [
            FromMcpConfig.from_dict(
                FROM_MCP_CONFIG_DICT_1
            )
        ]
        assert bool(tool_config) is True


class TestModelConfig:
    def test_should_load_model_name_and_api_key(self):
        model_config = ModelConfig.from_dict(MODEL_CONFIG_DICT_1)
        assert model_config.model_name == MODEL_CONFIG_DICT_1['model_name']
        assert model_config.base_url == MODEL_CONFIG_DICT_1['base_url']
        assert model_config.api_key == MODEL_CONFIG_DICT_1['api_key']

    def test_should_not_include_api_key_in_str_or_repr(self):
        model_config = ModelConfig.from_dict(MODEL_CONFIG_DICT_1)
        assert MODEL_CONFIG_DICT_1['api_key'] not in str(model_config)
        assert MODEL_CONFIG_DICT_1['api_key'] not in repr(model_config)

    def test_should_read_read_api_key_from_env(
        self,
        mock_env: dict
    ):
        mock_env['API_KEY'] = 'api_key_1'
        model_config = ModelConfig.from_dict({
            **MODEL_CONFIG_DICT_1,
            'api_key': '{{ env["API_KEY"] }}'
        })
        assert model_config.api_key == 'api_key_1'


class TestBaseAgentConfig:
    def test_should_load_tools(self):
        tools = ['tool_1', 'tool_2']
        agent_config = BaseAgentConfig.from_dict({
            **BASE_AGENT_CONFIG_DICT_1,
            'tools': tools
        })
        assert agent_config.tools == tools

    def test_should_load_tool_collectionss(self):
        agent_config = BaseAgentConfig.from_dict({
            **BASE_AGENT_CONFIG_DICT_1,
            'toolCollections': ['tool_collection_1']
        })
        assert agent_config.tool_collections == ['tool_collection_1']

    def test_should_load_system_prompt(self):
        agent_config = BaseAgentConfig.from_dict({
            **BASE_AGENT_CONFIG_DICT_1,
            'systemPrompt': 'System prompt 1'
        })
        assert agent_config.system_prompt == 'System prompt 1'

    def test_should_load_managed_agent_names(self):
        agent_config = BaseAgentConfig.from_dict({
            **BASE_AGENT_CONFIG_DICT_1,
            'managedAgents': ['managed_agent_1']
        })
        assert agent_config.managed_agent_names == ['managed_agent_1']

    def test_should_model(self):
        agent_config = BaseAgentConfig.from_dict({
            **BASE_AGENT_CONFIG_DICT_1,
            'model': 'model_1'
        })
        assert agent_config.model_name == 'model_1'


class TestManagedAgentConfig:
    def test_should_load_name_and_description(self):
        agent_config = ManagedAgentConfig.from_dict(MANAGED_AGENT_CONFIG_DICT_1)
        assert agent_config.name == MANAGED_AGENT_CONFIG_DICT_1['name']
        assert agent_config.description == MANAGED_AGENT_CONFIG_DICT_1['description']

    def test_should_load_tools(self):
        tools = ['tool_1', 'tool_2']
        agent_config = ManagedAgentConfig.from_dict({
            **MANAGED_AGENT_CONFIG_DICT_1,
            'tools': tools
        })
        assert agent_config.tools == tools


class TestAppConfig:
    def test_should_load_agent(self):
        app_config = AppConfig.from_dict(APP_CONFIG_DICT_1)
        assert app_config.agent == BaseAgentConfig.from_dict(APP_CONFIG_DICT_1['agent'])

    def test_should_load_managed_agents(self):
        app_config = AppConfig.from_dict({
            **APP_CONFIG_DICT_1,
            'managedAgents': [MANAGED_AGENT_CONFIG_DICT_1]
        })
        assert app_config.managed_agents == [ManagedAgentConfig.from_dict(
            MANAGED_AGENT_CONFIG_DICT_1
        )]

    def test_should_load_tool_definitions(self):
        app_config = AppConfig.from_dict({
            **APP_CONFIG_DICT_1,
            'toolDefinitions': TOOL_DEFINITIONS_CONFIG_DICT_1
        })
        assert app_config.tool_definitions == ToolDefinitionsConfig.from_dict(
            TOOL_DEFINITIONS_CONFIG_DICT_1
        )

    def test_should_load_tool_collection_definitions(self):
        app_config = AppConfig.from_dict({
            **APP_CONFIG_DICT_1,
            'toolCollectionDefinitions': TOOL_COLLECTION_DEFINITIONS_CONFIG_DICT_1
        })
        assert app_config.tool_collection_definitions == ToolCollectionDefinitionsConfig.from_dict(
            TOOL_COLLECTION_DEFINITIONS_CONFIG_DICT_1
        )

    def test_should_load_models(self):
        app_config = AppConfig.from_dict({
            **APP_CONFIG_DICT_1,
            'models': [MODEL_CONFIG_DICT_1]
        })
        assert app_config.models == [ModelConfig.from_dict(
            MODEL_CONFIG_DICT_1
        )]


class TestLoadAppConfig:
    def test_should_load_app_config_from_file(self, mock_env: dict, tmp_path: Path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text(yaml.safe_dump(APP_CONFIG_DICT_1), encoding='utf-8')
        mock_env[EnvironmentVariables.CONFIG_FILE] = str(config_file)
        app_config = load_app_config()
        assert app_config == AppConfig.from_dict(APP_CONFIG_DICT_1)
