from dataclasses import dataclass
from typing import Sequence

import smolagents  # type: ignore

from data_ai_bot.config import ModelConfig


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
