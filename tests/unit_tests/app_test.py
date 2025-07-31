from unittest.mock import MagicMock
from data_ai_bot.agent_factory import ToolCall
from data_ai_bot.app import get_formatted_tool_args


class TestGetFormattedToolArgs:
    def test_should_return_empty_string_for_no_arguments(self):
        assert get_formatted_tool_args(ToolCall(
            tool_name='tool_1',
            tool=MagicMock(name='tool_1'),
            args=[],
            kwargs={}
        )) == ''

    def test_should_format_single_keyword_arguments(self):
        assert get_formatted_tool_args(ToolCall(
            tool_name='tool_1',
            tool=MagicMock(name='tool_1'),
            args=[],
            kwargs={'key_1': 'value_1'}
        )) == "key_1='value_1'"

    def test_should_format_multiple_keyword_arguments(self):
        assert get_formatted_tool_args(ToolCall(
            tool_name='tool_1',
            tool=MagicMock(name='tool_1'),
            args=[],
            kwargs={
                'key_1': 'value_1',
                'key_2': 'value_2'
            }
        )) == "key_1='value_1', key_2='value_2'"

    def test_should_ignore_arguments_with_empty_value(self):
        assert get_formatted_tool_args(ToolCall(
            tool_name='tool_1',
            tool=MagicMock(name='tool_1'),
            args=[],
            kwargs={'key_1': ''}
        )) == ''
