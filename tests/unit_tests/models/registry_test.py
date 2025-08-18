import pytest

import smolagents  # type: ignore[import-untyped]

from data_ai_bot.config import ModelConfig
from data_ai_bot.models.registry import SmolAgentsModelRegistry


MODEL_NAME_1 = 'model_1'
BASE_URL_1 = 'base_url_1'
API_KEY_1 = 'api_key_1'


MODEL_CONFIG_1 = ModelConfig(
    model_name=MODEL_NAME_1,
    base_url=BASE_URL_1,
    api_key=API_KEY_1
)


class TestSmolAgentsModelRegistry:
    def test_should_fail_for_invalid_model_name(self):
        registry = SmolAgentsModelRegistry(
            model_config_list=[MODEL_CONFIG_1]
        )
        with pytest.raises(ValueError):
            registry.get_model('invalid_model_name')

    def test_should_create_model(self):
        registry = SmolAgentsModelRegistry(
            model_config_list=[MODEL_CONFIG_1]
        )
        model = registry.get_model(MODEL_CONFIG_1.model_name)
        assert isinstance(model, smolagents.OpenAIServerModel)
        assert model.model_id == MODEL_CONFIG_1.model_name
        assert model.client_kwargs['base_url'] == MODEL_CONFIG_1.base_url
        assert model.client_kwargs['api_key'] == MODEL_CONFIG_1.api_key
