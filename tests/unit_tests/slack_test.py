from unittest.mock import MagicMock

import pytest

from data_ai_bot.slack import get_slack_message_event_from_event_dict


@pytest.fixture(name='slack_client_mock')
def _slack_client_mock() -> MagicMock:
    return MagicMock(name='slack_client')


@pytest.fixture(name='slack_app_mock')
def _slack_app_mock(slack_client_mock: MagicMock) -> MagicMock:
    app = MagicMock(name='slack_app')
    app.client = slack_client_mock
    return app


class TestGetSlackMessageEventFromEventDict:
    def test_should_create_message_event_with_history(
        self,
        slack_app_mock: MagicMock,
        slack_client_mock: MagicMock
    ):
        get_slack_message_event_from_event_dict(
            app=slack_app_mock,
            event={
                'channel': 'channel_1',
                'thread_ts': 'thread_ts_1',
                'user': 'user_1',
                'text': 'text_1',
                'ts': 'ts_1',
                'channel_type': 'channel_type_1'
            }
        )
        slack_client_mock.conversations_replies.assert_called_with(
            channel='channel_1',
            ts='thread_ts_1'
        )
