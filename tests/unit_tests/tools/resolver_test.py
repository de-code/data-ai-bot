import pytest

from data_ai_bot.config import (
    FromPythonToolClassConfig,
    FromPythonToolInstanceConfig,
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

DEFAULT_HEADERS = {'User-Agent': 'Agent-Bot/1.0'}

DEFAULT_CONFIG_TOOL_RESOLVER = ConfigToolResolver(
    headers=DEFAULT_HEADERS,
    tool_definitions_config=DEFAULT_TOOL_DEFINITIONS_CONFIG
)


class TestConfigToolResolver:
    def test_should_raise_error_if_unknown_tool_name(self):
        with pytest.raises(KeyError):
            DEFAULT_CONFIG_TOOL_RESOLVER.get_tool_by_name('unknown')

    def test_should_resolve_get_joke(self):
        tool = DEFAULT_CONFIG_TOOL_RESOLVER.get_tool_by_name('get_joke')
        assert tool == get_joke

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
                    module='data_ai_bot.tools.sources.static',
                    class_name='StaticContentTool',
                    init_parameters={
                        'description': 'Description 1',
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
        assert tool == get_joke
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
