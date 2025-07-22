

from dataclasses import dataclass
import textwrap
import time
from typing import Iterable, Optional, Sequence, cast

from markdown_to_mrkdwn import SlackMarkdownConverter  # type: ignore

import slack_bolt


DEFAULT_MAX_BLOCK_LENGTH = 3000


@dataclass(frozen=True)
class SlackMessageEvent:
    user: str
    text: str
    ts: str
    thread_ts: str
    channel: str
    previous_messages: Sequence[str]
    channel_type: Optional[str] = None


def get_slack_message_event_from_event_dict(
    app: slack_bolt.App,
    event: dict
) -> SlackMessageEvent:
    message = event.get('message', event)
    thread_ts = message.get('thread_ts')
    previous_message_dict_list: Sequence[dict] = []
    if thread_ts:
        result = app.client.conversations_replies(
            channel=event['channel'],
            ts=thread_ts
        )
        previous_message_dict_list = cast(Sequence[dict], result.get('messages', []))
    return SlackMessageEvent(
        user=message['user'],
        text=message['text'],
        ts=message['ts'],
        thread_ts=thread_ts or message['ts'],
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


def get_slack_mrkdwn_for_markdown(markdown: str) -> str:
    return SlackMarkdownConverter().convert(markdown)


def iter_split_mrkdwn(mrkdwn: str, max_length: int) -> Iterable[str]:
    return iter(textwrap.wrap(
        mrkdwn,
        width=max_length,
        break_long_words=False,
        replace_whitespace=False
    ))


def get_slack_blocks_for_mrkdwn(
    mrkdwn: str,
    max_block_length: int = DEFAULT_MAX_BLOCK_LENGTH
) -> Sequence[dict]:
    return [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': block_mrkdwn
            }
        }
        for block_mrkdwn in iter_split_mrkdwn(mrkdwn, max_length=max_block_length)
    ]
