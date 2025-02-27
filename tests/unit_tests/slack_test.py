from unittest.mock import MagicMock

import pytest

from data_ai_bot.slack import SlackMessageEvent, get_slack_message_event_from_event_dict


MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1 = {
    'channel': 'channel_1',
    'user': 'user_1',
    'text': 'text_1',
    'ts': 'ts_1',
    'channel_type': 'channel_type_1'
}


@pytest.fixture(name='slack_client_mock')
def _slack_client_mock() -> MagicMock:
    return MagicMock(name='slack_client')


@pytest.fixture(name='conversations_replies_mock')
def _conversations_replies_mock(slack_client_mock: MagicMock) -> MagicMock:
    return slack_client_mock.conversations_replies


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
            thread_ts=MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1['ts'],
            channel=MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1['channel'],
            channel_type=MINIMAL_DIRECT_MESSAGE_SLACK_EVENT_DICT_1['channel_type'],
            previous_messages=[]
        )

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
