from dataclasses import dataclass, field
import logging
import os
from typing import Sequence

import smolagents  # type: ignore

from data_ai_bot.config import ModelConfig


LOGGER = logging.getLogger(__name__)


DEFAULT_MODEL_NAME = 'default'


def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise KeyError(f'Missing environment variable: {key}')
    return value


def get_model(
    model_id: str,
    api_base: str,
    api_key: str,
) -> smolagents.Model:
    LOGGER.info('model_id: %r', model_id)
    return smolagents.OpenAIServerModel(
        model_id=model_id,
        api_base=api_base,
        api_key=api_key
    )


def get_default_model_config() -> ModelConfig:
    return ModelConfig(
        model_name=get_required_env('OPENAI_MODEL_ID'),
        base_url=get_required_env('OPENAI_BASE_URL'),
        api_key=get_required_env('OPENAI_API_KEY')
    )


def get_model_for_config(model_config: ModelConfig) -> smolagents.Model:
    return get_model(
        model_id=model_config.model_name,
        api_base=model_config.base_url,
        api_key=model_config.api_key
    )


@dataclass(frozen=True)
class SmolAgentsModelRegistry:
    model_config_list: Sequence[ModelConfig]
    model_instance_by_model_name: dict[str, smolagents.Model] = field(default_factory=dict)

    def get_model_config(self, model_name: str) -> ModelConfig:
        for model_config in self.model_config_list:
            if model_config.model_name == model_name:
                return model_config
        if model_name == DEFAULT_MODEL_NAME:
            return get_default_model_config()
        raise ValueError(f'invalid model name: {model_name}')

    def get_model(self, model_name: str) -> smolagents.Model:
        model_instance = self.model_instance_by_model_name.get(model_name)
        if model_instance is not None:
            return model_instance
        model_config = self.get_model_config(model_name)
        model_instance = get_model_for_config(model_config)
        self.model_instance_by_model_name[model_name] = model_instance
        return model_instance

    def get_model_or_default_model(
        self,
        model_name: str | None
    ) -> smolagents.Model:
        if not model_name:
            return self.get_model(DEFAULT_MODEL_NAME)
        return self.get_model(model_name)
