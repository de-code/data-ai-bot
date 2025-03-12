from typing import Iterator
from unittest.mock import ANY, MagicMock, patch

import pytest
import requests

from data_ai_bot.tools.sources import web_api
from data_ai_bot.tools.sources.web_api import WebApiTool


URL_1 = 'https://example/url_1'

HEADERS_1 = {'User-Agent': 'Test/1'}


@pytest.fixture(name='requests_response_mock')
def _requests_response_mock() -> MagicMock:
    return MagicMock(requests.Response)


@pytest.fixture(name='requests_session_mock')
def _requests_session_mock(requests_response_mock: MagicMock) -> MagicMock:
    session_mock = MagicMock(spec=requests.Session)
    session_mock.get.return_value = requests_response_mock
    session_mock.post.return_value = requests_response_mock
    session_mock.request.return_value = requests_response_mock
    return session_mock


@pytest.fixture(name='requests_request_fn_mock')
def _requests_request_fn_mock(requests_session_mock: MagicMock) -> MagicMock:
    return requests_session_mock.request


@pytest.fixture(name='requests_mock', autouse=True)
def _requests_mock(requests_session_mock: MagicMock) -> Iterator[MagicMock]:
    with patch.object(web_api, 'requests') as mock:
        mock.Session.return_value = requests_session_mock
        yield mock


class TestWebApiTool:
    def test_should_pass_method_url_and_headers_to_api(
        self,
        requests_request_fn_mock: MagicMock
    ):
        tool = WebApiTool(
            name='name_1',
            description='description_1',
            url=URL_1,
            method='POST',
            headers=HEADERS_1
        )
        tool.forward()
        requests_request_fn_mock.assert_called_with(
            method='POST',
            url=URL_1,
            params=ANY,
            headers=HEADERS_1
        )

    def test_should_replace_placeholders_in_url(
        self,
        requests_request_fn_mock: MagicMock
    ):
        tool = WebApiTool(
            name='name_1',
            description='description_1',
            inputs={
                'param_1': {
                    'type': 'string',
                    'description': 'Test param 1'
                }
            },
            url=r'https://example/url_1?param_1={{ param_1 }}',
        )
        tool.forward(param_1='value_1')
        requests_request_fn_mock.assert_called_with(
            method='GET',
            url=r'https://example/url_1?param_1=value_1',
            params=ANY,
            headers=ANY
        )

    def test_should_validate_parameters(
        self,
        requests_request_fn_mock: MagicMock
    ):
        tool = WebApiTool(
            name='name_1',
            description='description_1',
            inputs={
                'param_1': {
                    'type': 'string',
                    'description': 'Test param 1',
                    'regex': r'(valid)'
                }
            },
            url=r'https://example/url_1?param_1={{ param_1 }}',
        )
        with pytest.raises(ValueError):
            tool.forward(param_1='invalid')
        requests_request_fn_mock.assert_not_called()

    def test_should_replace_placeholders_in_query_parameters(
        self,
        requests_request_fn_mock: MagicMock
    ):
        tool = WebApiTool(
            name='name_1',
            description='description_1',
            inputs={
                'param_1': {
                    'type': 'string',
                    'description': 'Test param 1'
                }
            },
            url=r'https://example/url_1',
            query_parameters={
                'param_1': r'{{ param_1 }}'
            }
        )
        tool.forward(param_1='value_1')
        requests_request_fn_mock.assert_called_with(
            method='GET',
            url=r'https://example/url_1',
            params={'param_1': 'value_1'},
            headers=ANY
        )

    def test_should_remove_empty_query_parameters(
        self,
        requests_request_fn_mock: MagicMock
    ):
        tool = WebApiTool(
            name='name_1',
            description='description_1',
            inputs={
                'param_1': {
                    'type': 'string',
                    'description': 'Test param 1'
                }
            },
            url=r'https://example/url_1',
            query_parameters={
                'param_1': r'{{ param_1 }}'
            },
            remove_empty_query_parameters=True
        )
        tool.forward(param_1='')
        requests_request_fn_mock.assert_called_with(
            method='GET',
            url=r'https://example/url_1',
            params={},
            headers=ANY
        )

    def test_should_return_response_from_api(self, requests_response_mock: MagicMock):
        tool = WebApiTool(
            name='name_1',
            description='description_1',
            url=URL_1
        )
        assert tool.forward() == requests_response_mock.json.return_value
