import pytest

from data_ai_bot.config import (
    FromPythonToolClassConfig,
    FromPythonToolInstanceConfig,
    ToolDefinitionsConfig
)
from data_ai_bot.tools.data_hub.docmap import DocMapTool
from data_ai_bot.tools.example.joke import get_joke
from data_ai_bot.tools.resolver import ConfigToolResolver


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

DEFAULT_CONFIG_TOOL_RESOLVER = ConfigToolResolver(
    headers={'User-Agent': 'Agent-Bot/1.0'},
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
