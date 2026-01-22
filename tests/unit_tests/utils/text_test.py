import textwrap

from data_ai_bot.utils.text import get_markdown_for_agent_response_message


class TestGetMarkdownForAgentResponseMessage:
    def test_preserve_passed_in_string(self):
        assert get_markdown_for_agent_response_message(
            'text'
        ) == 'text'

    def test_convert_list_of_strings_to_markdown_list(self):
        assert get_markdown_for_agent_response_message([
            'item 1',
            'item 2',
            'item 3'
        ]).strip() == textwrap.dedent(
            '''
            - item 1
            - item 2
            - item 3
            '''
        ).strip()

    def test_convert_list_of_dicts_to_markdown_list(self):
        assert get_markdown_for_agent_response_message([
            {'key': 'item 1'},
            {'key': 'item 2'},
            {'key': 'item 3'}
        ]).strip() == textwrap.dedent(
            '''
            - {'key': 'item 1'}
            - {'key': 'item 2'}
            - {'key': 'item 3'}
            '''
        ).strip()

    def test_convert_dict_to_string(self):
        assert get_markdown_for_agent_response_message(
            {'key': 'item 1'}
        ) == "{'key': 'item 1'}"
