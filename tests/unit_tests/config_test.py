from pathlib import Path

import yaml

from data_ai_bot.config import (
    AgentConfig,
    AppConfig,
    EnvironmentVariables,
    load_app_config
)
from data_ai_bot.config_typing import (
    AgentConfigDict,
    AppConfigDict
)


AGENT_CONFIG_DICT_1: AgentConfigDict = {
    'tools': ['tool_1', 'tool_2']
}


APP_CONFIG_DICT_1: AppConfigDict = {
    'agent': AGENT_CONFIG_DICT_1
}


class TestAgentConfig:
    def test_should_load_tools(self):
        agent_config = AgentConfig.from_dict(AGENT_CONFIG_DICT_1)
        assert agent_config.tools == AGENT_CONFIG_DICT_1['tools']


class TestAppConfig:
    def test_should_load_agent(self):
        app_config = AppConfig.from_dict(APP_CONFIG_DICT_1)
        assert app_config.agent == AgentConfig.from_dict(APP_CONFIG_DICT_1['agent'])


class TestLoadAppConfig:
    def test_should_load_app_config_from_file(self, mock_env: dict, tmp_path: Path):
        config_file = tmp_path / 'config.yaml'
        config_file.write_text(yaml.safe_dump(APP_CONFIG_DICT_1), encoding='utf-8')
        mock_env[EnvironmentVariables.CONFIG_FILE] = str(config_file)
        app_config = load_app_config()
        assert app_config == AppConfig.from_dict(APP_CONFIG_DICT_1)
