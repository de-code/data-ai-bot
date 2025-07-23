import logging
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest

import data_ai_bot.slack as slack_module
from data_ai_bot.slack import (
    DEFAULT_MAX_BLOCK_LENGTH,
    SlackMessageEvent,
    get_slack_blocks_and_files_for_mrkdwn,
    get_slack_blocks_for_mrkdwn,
    get_slack_message_event_from_event_dict,
    get_slack_mrkdwn_for_markdown,
    iter_split_mrkdwn,
    iter_split_mrkdwn_segments
)


LOGGER = logging.getLogger(__name__)


TEXT_1 = 'Text 1'
TEXT_2 = 'Text 2'


MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1 = {
    'channel': 'channel_1',
    'user': 'user_1',
    'text': 'text_1',
    'ts': 'ts_1'
}


@pytest.fixture(name='slack_client_mock')
def _slack_client_mock() -> MagicMock:
    return MagicMock(name='slack_client')


@pytest.fixture(name='conversations_replies_mock')
def _conversations_replies_mock(slack_client_mock: MagicMock) -> MagicMock:
    return slack_client_mock.conversations_replies


@pytest.fixture(name='iter_split_mrkdwn_mock')
def _iter_split_mrkdwn_mock() -> Iterator[MagicMock]:
    with patch.object(slack_module, 'iter_split_mrkdwn') as mock:
        yield mock


@pytest.fixture(name='slack_app_mock')
def _slack_app_mock(slack_client_mock: MagicMock) -> MagicMock:
    app = MagicMock(name='slack_app')
    app.client = slack_client_mock
    return app


class TestGetSlackMessageEventFromEventDict:
    def test_should_create_message_event_without_history(
        self,
        slack_app_mock: MagicMock
    ):
        message_event = get_slack_message_event_from_event_dict(
            app=slack_app_mock,
            event=MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1
        )
        assert message_event == SlackMessageEvent(
            user=MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1['user'],
            text=MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1['text'],
            ts=MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1['ts'],
            thread_ts=MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1['ts'],
            channel=MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1['channel'],
            channel_type=None,
            previous_messages=[]
        )

    def test_should_extract_channel_type(
        self,
        slack_app_mock: MagicMock
    ):
        message_event = get_slack_message_event_from_event_dict(
            app=slack_app_mock,
            event={
                **MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1,
                'channel_type': 'channel_type_1'
            }
        )
        assert message_event.channel_type == 'channel_type_1'

    def test_should_create_message_event_with_history(
        self,
        slack_app_mock: MagicMock,
        conversations_replies_mock: MagicMock
    ):
        conversations_replies_mock.return_value = {
            'messages': [{
                'ts': 'previous_ts_1',
                'text': 'previous_text_1'
            }]
        }
        message_event = get_slack_message_event_from_event_dict(
            app=slack_app_mock,
            event={
                **MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1,
                'thread_ts': 'thread_ts_1'
            }
        )
        conversations_replies_mock.assert_called_with(
            channel=MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1['channel'],
            ts='thread_ts_1'
        )
        assert message_event.previous_messages == ['previous_text_1']

    def test_should_extract_from_message_changed_event(
        self,
        slack_app_mock: MagicMock
    ):
        message_event = get_slack_message_event_from_event_dict(
            app=slack_app_mock,
            event={
                'ts': 'ts_1',
                'channel': 'channel_1',
                'channel_type': 'channel_type_1',
                'message': {
                    'ts': 'ts_2',
                    'thread_ts': 'thread_ts_1',
                    'user': 'user_1',
                    'text': 'text_1'
                }
            }
        )
        assert message_event.ts == 'ts_2'
        assert message_event.thread_ts == 'thread_ts_1'
        assert message_event.channel == 'channel_1'
        assert message_event.channel_type == 'channel_type_1'
        assert message_event.user == 'user_1'
        assert message_event.text == 'text_1'


class TestGetSlackMrkdwnForMarkdown:
    def test_should_not_convert_simple_text(self):
        assert get_slack_mrkdwn_for_markdown('Simple text') == 'Simple text'

    def test_should_convert_heading_1_to_slack_bold(self):
        assert get_slack_mrkdwn_for_markdown('# Heading 1') == '*Heading 1*'

    def test_should_convert_double_asterisk_to_slack_bold(self):
        assert get_slack_mrkdwn_for_markdown('**bold**') == '*bold*'

    def test_should_convert_markdown_link_to_slack_link(self):
        assert get_slack_mrkdwn_for_markdown('[Link Text](Link URL)') == '<Link URL|Link Text>'


class TestIterSplitMrkdwnSegments:
    def test_should_identify_code_chunks(self):
        mrkdwn = (
            'First paragraph\n'
            '```python\nprint("hello")\nprint("world")\n```'
            'Second paragraph'
        )
        LOGGER.debug('mrkdwn: %r', mrkdwn)
        result = list(iter_split_mrkdwn_segments(mrkdwn))
        LOGGER.debug('result: %r', result)
        assert result == [
            (False, 'First paragraph\n'),
            (True, '```python\nprint("hello")\nprint("world")\n```'),
            (False, 'Second paragraph')
        ]


class TestIterSplitMrkdwn:
    def test_should_split_at_word_boundaries(self):
        assert list(iter_split_mrkdwn('12345 12345', max_length=8)) == [
            '12345',
            '12345'
        ]

    def test_not_should_split_lines_if_within_max_length(self):
        assert list(iter_split_mrkdwn('12345\n12345 12345', max_length=100)) == [
            '12345\n12345 12345'
        ]

    def test_should_split_at_line_boundaries_if_necessary(self):
        assert list(iter_split_mrkdwn('12345\n12345 12345', max_length=12)) == [
            '12345',
            '12345 12345'
        ]

    def test_should_not_split_next_lines_before_hitting_max_length(self):
        assert list(iter_split_mrkdwn(
            '12345\n12345 12345\n12345 12345',
            max_length=12
        )) == [
            '12345',
            '12345 12345',
            '12345 12345'
        ]

    def test_should_prefer_splitting_at_paragraph_boundaries_if_necessary(self):
        assert list(iter_split_mrkdwn('12345\n12345\n\n12345', max_length=12)) == [
            '12345\n12345',
            '12345'
        ]

    def test_should_not_split_next_paragraphs_before_hitting_max_length(self):
        assert list(iter_split_mrkdwn(
            '12345\n12345\n\n12345\n\n12345',
            max_length=12
        )) == [
            '12345\n12345',
            '12345\n\n12345'
        ]

    def test_should_not_split_code_blocks_even_if_longer_than_max_length(self):
        mrkdwn = (
            'First paragraph\n'
            '```python\nprint("hello")\nprint("world")\n```'
            'Second paragraph'
        )
        LOGGER.debug('mrkdwn: %r', mrkdwn)
        result = list(iter_split_mrkdwn(mrkdwn, max_length=20))
        LOGGER.debug('result: %r', result)
        assert result == [
            'First paragraph',
            '```python\nprint("hello")\nprint("world")\n```',
            'Second paragraph'
        ]


class TestGetSlackBlocksForMrkdwn:
    def test_should_convert_simple_message(self):
        assert get_slack_blocks_for_mrkdwn(TEXT_1) == [{
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': TEXT_1
            }
        }]

    def test_should_split_long_text_into_separate_blocks(
        self,
        iter_split_mrkdwn_mock: MagicMock
    ):
        iter_split_mrkdwn_mock.return_value = iter([TEXT_1, TEXT_2])
        assert get_slack_blocks_for_mrkdwn(f'{TEXT_1} {TEXT_2}') == [{
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': TEXT_1
            }
        }, {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': TEXT_2
            }
        }]
        iter_split_mrkdwn_mock.assert_called_with(
            f'{TEXT_1} {TEXT_2}',
            max_length=DEFAULT_MAX_BLOCK_LENGTH
        )


class TestGetSlackBlocksAndFilesForMrkdwn:
    def test_should_convert_simple_message_without_files(self):
        assert get_slack_blocks_and_files_for_mrkdwn(TEXT_1) == (
            get_slack_blocks_for_mrkdwn(TEXT_1),
            []
        )

    def test_should_convert_long_code_block_to_file(self):
        blocks, files = get_slack_blocks_and_files_for_mrkdwn(
            '```python\nprint("hello")\nprint("world")\n```',
            max_block_length=10
        )
        assert blocks == [{
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': 'See file_1.py'
            }
        }]
        assert files == [{
            'filename': 'file_1.py',
            'content': b'print("hello")\nprint("world")\n'
        }]
