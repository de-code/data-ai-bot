# pylint: disable=duplicate-code
import dataclasses
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest

from smolagents import (  # type: ignore[import-untyped]
    ToolCollection,
    tool as smolagents_tool
)

from data_ai_bot.config import (
    FromMcpConfig,
    FromPythonToolClassConfig,
    FromPythonToolInstanceConfig,
    ToolCollectionDefinitionsConfig,
    ToolDefinitionsConfig
)
from data_ai_bot.tools.data_hub.docmap import DocMapTool
from data_ai_bot.tools.example.joke import get_joke
from data_ai_bot.tools.resolver import ConfigToolResolver
from data_ai_bot.tools.sources.static import StaticContentTool


DEFAULT_TOOL_DEFINITIONS_CONFIG: ToolDefinitionsConfig = ToolDefinitionsConfig(
    from_python_tool_instance=[
        FromPythonToolInstanceConfig(
            name='get_joke',
            module='data_ai_bot.tools.example.joke',
            key='get_joke'
        )
    ],
    from_python_tool_class=[
        FromPythonToolClassConfig(
            name='get_docmap_by_manuscript_id',
            module='data_ai_bot.tools.data_hub.docmap',
            class_name='DocMapTool'
        )
    ]
)

FROM_MCP_CONFIG_1: FromMcpConfig = FromMcpConfig(
    name='mcp_1',
    url='http://localhost:8080/mcp',
    transport='streamable-http'
)

TOOL_COLLECTION_DEFINITIONS_CONFIG_1: ToolCollectionDefinitionsConfig = (
    ToolCollectionDefinitionsConfig(
        from_mcp=[FROM_MCP_CONFIG_1]
    )
)

DEFAULT_HEADERS = {'User-Agent': 'Agent-Bot/1.0'}

DEFAULT_CONFIG_TOOL_RESOLVER = ConfigToolResolver(
    headers=DEFAULT_HEADERS,
    tool_definitions_config=DEFAULT_TOOL_DEFINITIONS_CONFIG,
    tool_collection_definitions_config=TOOL_COLLECTION_DEFINITIONS_CONFIG_1
)


@smolagents_tool
def _test_tool_1() -> str:
    """
    Test tool 1
    """
    return 'Tool 1'


@smolagents_tool
def _test_tool_2() -> str:
    """
    Test tool 2
    """
    return 'Tool 2'


@pytest.fixture(name='tool_collection_from_mcp_mock', autouse=True)
def _tool_collection_from_mcp_mock() -> Iterator[MagicMock]:
    with patch.object(ToolCollection, 'from_mcp') as mock:
        yield mock


@pytest.fixture(name='tool_collection_mock')
def _tool_collection_mock(
    tool_collection_from_mcp_mock: MagicMock
) -> MagicMock:
    return tool_collection_from_mcp_mock.return_value.__enter__.return_value


class TestConfigToolResolver:
    def test_should_raise_error_if_unknown_tool_name(self):
        with pytest.raises(KeyError):
            DEFAULT_CONFIG_TOOL_RESOLVER.get_tool_by_name('unknown')

    def test_should_resolve_get_joke(self):
        tool = DEFAULT_CONFIG_TOOL_RESOLVER.get_tool_by_name('get_joke')
        assert tool == get_joke  # pylint: disable=comparison-with-callable

    def test_should_resolve_get_docmap_by_manuscript_id(self):
        tool = DEFAULT_CONFIG_TOOL_RESOLVER.get_tool_by_name('get_docmap_by_manuscript_id')
        assert isinstance(tool, DocMapTool)
        assert tool.headers == DEFAULT_CONFIG_TOOL_RESOLVER.headers

    def test_should_resolve_tool_with_init_parameters(self):
        resolver = ConfigToolResolver(
            headers=DEFAULT_HEADERS,
            tool_definitions_config=ToolDefinitionsConfig(
                from_python_tool_class=[FromPythonToolClassConfig(
                    name='tool_1',
                    description='Description 1',
                    module='data_ai_bot.tools.sources.static',
                    class_name='StaticContentTool',
                    init_parameters={
                        'content': 'Content 1'
                    }
                )]
            )
        )
        tool = resolver.get_tool_by_name('tool_1')
        assert isinstance(tool, StaticContentTool)
        assert tool.name == 'tool_1'
        assert tool.description == 'Description 1'
        assert tool.content == 'Content 1'

    def test_should_be_able_to_rename_and_change_description_of_tool_instance(self):
        resolver = ConfigToolResolver(
            headers=DEFAULT_HEADERS,
            tool_definitions_config=ToolDefinitionsConfig(
                from_python_tool_instance=[FromPythonToolInstanceConfig(
                    name='new_name',
                    module='data_ai_bot.tools.example.joke',
                    key='get_joke',
                    description='New description'
                )]
            )
        )
        tool = resolver.get_tool_by_name('new_name')
        assert tool == get_joke  # pylint: disable=comparison-with-callable
        assert tool.name == 'new_name'
        assert tool.description == 'New description'

    def test_should_be_able_to_rename_and_change_description_of_tool_class(self):
        resolver = ConfigToolResolver(
            headers=DEFAULT_HEADERS,
            tool_definitions_config=ToolDefinitionsConfig(
                from_python_tool_class=[FromPythonToolClassConfig(
                    name='new_name',
                    module='data_ai_bot.tools.data_hub.docmap',
                    class_name='DocMapTool',
                    description='New description'
                )]
            )
        )
        tool = resolver.get_tool_by_name('new_name')
        assert isinstance(tool, DocMapTool)
        assert tool.name == 'new_name'
        assert tool.description == 'New description'

    def test_should_load_tools_from_collection(
        self,
        tool_collection_from_mcp_mock: MagicMock,
        tool_collection_mock: MagicMock
    ):
        resolver = ConfigToolResolver(
            headers=DEFAULT_HEADERS,
            tool_collection_definitions_config=ToolCollectionDefinitionsConfig(
                from_mcp=[FROM_MCP_CONFIG_1]
            )
        )
        tools = resolver.get_tools_by_collection_name(FROM_MCP_CONFIG_1.name)
        assert tools == tool_collection_mock.tools
        tool_collection_from_mcp_mock.assert_called_once_with(
            {
                'url': FROM_MCP_CONFIG_1.url,
                'transport': FROM_MCP_CONFIG_1.transport
            },
            trust_remote_code=True
        )

    def test_should_filter_tools_of_collection(
        self,
        tool_collection_mock: MagicMock
    ):
        resolver = ConfigToolResolver(
            headers=DEFAULT_HEADERS,
            tool_collection_definitions_config=ToolCollectionDefinitionsConfig(
                from_mcp=[
                    dataclasses.replace(
                        FROM_MCP_CONFIG_1,
                        tools=[_test_tool_1.name]
                    )
                ]
            )
        )
        tool_collection_mock.tools = [
            _test_tool_1,
            _test_tool_2
        ]
        tools = resolver.get_tools_by_collection_name(FROM_MCP_CONFIG_1.name)
        assert tools == [_test_tool_1]
