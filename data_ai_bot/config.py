from dataclasses import dataclass
import logging
import os
from typing import Sequence

import yaml

from data_ai_bot.config_typing import (
    AgentConfigDict,
    AppConfigDict
)


LOGGER = logging.getLogger(__name__)


class EnvironmentVariables:
    CONFIG_FILE = 'CONFIG_FILE'


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
    agent: AgentConfig

    @staticmethod
    def from_dict(app_config_dict: AppConfigDict) -> 'AppConfig':
        return AppConfig(
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
