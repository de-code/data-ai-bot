

from dataclasses import dataclass
from typing import Sequence, cast

import slack_bolt


@dataclass(frozen=True)
class SlackMessageEvent:
    user: str
    text: str
    thread_ts: str
    channel: str
    channel_type: str
    previous_messages: Sequence[str]


def get_slack_message_event_from_event_dict(
    app: slack_bolt.App,
    event: dict
) -> SlackMessageEvent:
    result = app.client.conversations_replies(
        channel=event['channel'],
        ts=event['thread_ts']
    )
    return SlackMessageEvent(
        user=event['user'],
        text=event['text'],
        thread_ts=event['ts'],
        channel=event['channel'],
        channel_type=event['channel_type'],
        previous_messages=[
            message['text']
            for message in cast(Sequence[dict], result.get('messages', []))
            if message['ts'] != event['ts']
        ]
    )
