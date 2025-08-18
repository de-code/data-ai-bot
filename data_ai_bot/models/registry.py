from dataclasses import dataclass
import logging
from typing import Sequence

import smolagents  # type: ignore

from data_ai_bot.config import ModelConfig


LOGGER = logging.getLogger(__name__)


def get_default_model(
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


@dataclass(frozen=True)
class SmolAgentsModelRegistry:
    model_config_list: Sequence[ModelConfig]

    def get_model_config(self, model_name) -> ModelConfig:
        for model_config in self.model_config_list:
            if model_config.model_name == model_name:
                return model_config
        raise ValueError(f'invalid model name: {model_name}')

    def get_model(self, model_name) -> smolagents.Model:
        model_config = self.get_model_config(model_name)
        return smolagents.OpenAIServerModel(
            model_id=model_config.model_name,
            api_base=model_config.base_url,
            api_key=model_config.api_key
        )
