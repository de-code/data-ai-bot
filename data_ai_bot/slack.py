

from dataclasses import dataclass
import time
from typing import Optional, Sequence, cast

import slack_bolt


@dataclass(frozen=True)
class SlackMessageEvent:
    user: str
    text: str
    thread_ts: str
    channel: str
    previous_messages: Sequence[str]
    channel_type: Optional[str] = None


def get_slack_message_event_from_event_dict(
    app: slack_bolt.App,
    event: dict
) -> SlackMessageEvent:
    thread_ts = event.get('thread_ts')
    previous_message_dict_list: Sequence[dict] = []
    if thread_ts:
        result = app.client.conversations_replies(
            channel=event['channel'],
            ts=thread_ts
        )
        previous_message_dict_list = cast(Sequence[dict], result.get('messages', []))
    return SlackMessageEvent(
        user=event['user'],
        text=event['text'],
        thread_ts=thread_ts or event['ts'],
        channel=event['channel'],
        channel_type=event.get('channel_type'),
        previous_messages=[
            message['text']
            for message in previous_message_dict_list
            if message['ts'] != event['ts']
        ]
    )


def get_message_age_in_seconds_from_event_dict(
    event: dict
) -> float:
    return time.time() - float(event['ts'])
