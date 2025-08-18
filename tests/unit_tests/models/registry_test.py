from typing import Iterator
from unittest.mock import MagicMock, patch
import pytest

import smolagents  # type: ignore[import-untyped]

from data_ai_bot.config import ModelConfig
import data_ai_bot.models.registry as registry_model
from data_ai_bot.models.registry import SmolAgentsModelRegistry


MODEL_NAME_1 = 'model_1'
BASE_URL_1 = 'base_url_1'
API_KEY_1 = 'api_key_1'


MODEL_CONFIG_1 = ModelConfig(
    model_name=MODEL_NAME_1,
    base_url=BASE_URL_1,
    api_key=API_KEY_1
)


@pytest.fixture(name='get_default_model_mock')
def _get_default_model_mock() -> Iterator[MagicMock]:
    with patch.object(registry_model, 'get_default_model') as mock:
        yield mock


class TestSmolAgentsModelRegistry:
    class TestGetModel:
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

        def test_should_return_same_model_instance(self):
            registry = SmolAgentsModelRegistry(
                model_config_list=[MODEL_CONFIG_1]
            )
            model_1 = registry.get_model(MODEL_CONFIG_1.model_name)
            model_2 = registry.get_model(MODEL_CONFIG_1.model_name)
            assert id(model_1) == id(model_2)

    class TestGetModelOrDefaultModel:
        def test_should_return_default_model(
            self,
            get_default_model_mock: MagicMock
        ):
            registry = SmolAgentsModelRegistry(
                model_config_list=[MODEL_CONFIG_1]
            )
            model = registry.get_model_or_default_model(None)
            assert model == get_default_model_mock.return_value

        def test_should_return_model_by_name(self):
            registry = SmolAgentsModelRegistry(
                model_config_list=[MODEL_CONFIG_1]
            )
            model = registry.get_model_or_default_model(MODEL_CONFIG_1.model_name)
            assert model.model_id == MODEL_CONFIG_1.model_name
