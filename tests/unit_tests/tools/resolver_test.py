import pytest
from data_ai_bot.tools.data_hub.docmap import DocMapTool
from data_ai_bot.tools.example.joke import get_joke
from data_ai_bot.tools.resolver import DefaultToolResolver


DEFAULT_TOOL_RESOLVER = DefaultToolResolver(
    headers={'User-Agent': 'Agent-Bot/1.0'}
)


class TestDefaultToolResolver:
    def test_should_raise_error_if_unknown_tool_name(self):
        with pytest.raises(KeyError):
            DEFAULT_TOOL_RESOLVER.get_tool_by_name('unknown')

    def test_should_resolve_get_joke(self):
        tool = DEFAULT_TOOL_RESOLVER.get_tool_by_name('get_joke')
        assert tool == get_joke

    def test_should_resolve_get_docmap_by_manuscript_id(self):
        tool = DEFAULT_TOOL_RESOLVER.get_tool_by_name('get_docmap_by_manuscript_id')
        assert isinstance(tool, DocMapTool)
        assert tool.headers == DEFAULT_TOOL_RESOLVER.headers
