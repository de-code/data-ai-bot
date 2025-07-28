from dataclasses import dataclass
from io import BytesIO
import logging
from typing import Callable, Sequence, cast

import slack_bolt
from slack_bolt.context.say import Say

import smolagents  # type: ignore

from data_ai_bot.agent_session import SmolAgentsAgentSession
from data_ai_bot.slack import (
    SlackMessageEvent,
    get_slack_blocks_and_files_for_mrkdwn,
    get_slack_message_event_from_event_dict,
    get_slack_mrkdwn_for_markdown
)
from data_ai_bot.utils.dummy_text import DUMMY_TEXT_4K


LOGGER = logging.getLogger(__name__)


def get_agent_message(
    message_event: SlackMessageEvent
) -> str:
    return f'{message_event.text}'.strip() + '\n'


@dataclass(frozen=True)
class SlackChatApp:
    agent_factory: Callable[[], smolagents.MultiStepAgent]
    slack_app: slack_bolt.App
    echo_message: bool = False

    def get_agent_response_message(self, message_event: SlackMessageEvent) -> str:
        text = message_event.text
        last_word = text.rsplit(' ')[-1]
        if last_word == 'TEST_LONG_TEXT':
            return DUMMY_TEXT_4K
        if last_word == 'TEST_LONG_CODE':
            return f'```\n{DUMMY_TEXT_4K}\n```'
        agent_response = SmolAgentsAgentSession(self.agent_factory()).run(
            message=get_agent_message(
                message_event=message_event
            ),
            previous_messages=message_event.previous_messages
        )
        return agent_response.text

    def handle_message(self, event: dict, say: Say):
        try:
            message_event = get_slack_message_event_from_event_dict(
                app=self.slack_app,
                event=event
            )
            LOGGER.info('message_event: %r', message_event)

            self.slack_app.client.assistant_threads_setStatus(
                channel_id=message_event.channel,
                thread_ts=message_event.thread_ts,
                status=f'Processing request: {message_event.text}'
            )

            if self.echo_message:
                say(
                    f'Hi <@{message_event.user}>! You said: {message_event.text}',
                    thread_ts=message_event.thread_ts
                )
            response_message = self.get_agent_response_message(
                message_event=message_event
            )
            LOGGER.info('response_message: %r', response_message)
            response_message_mrkdwn = get_slack_mrkdwn_for_markdown(
                response_message
            )
            LOGGER.info('response_message_mrkdwn: %r', response_message_mrkdwn)
            LOGGER.info('responded to event: %r', event)
            blocks, files = get_slack_blocks_and_files_for_mrkdwn(
                response_message_mrkdwn
            )
            self.slack_app.client.chat_postMessage(
                text=response_message,
                mrkdwn=True,
                blocks=cast(Sequence[dict], blocks),
                channel=message_event.channel,
                thread_ts=message_event.thread_ts
            )
            if files:
                file_uploads = [
                    {
                        'filename': file_dict['filename'],
                        'title': file_dict['filename'],
                        'file': BytesIO(file_dict['content'])
                    }
                    for file_dict in files
                ]
                LOGGER.info('file_uploads: %r', file_uploads)
                self.slack_app.client.files_upload_v2(
                    channel=message_event.channel,
                    thread_ts=message_event.thread_ts,
                    file_uploads=file_uploads
                )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            LOGGER.warning('Caught exception: %r', exc, exc_info=True)
            say(
                f'Failed to process request due to:\n> {repr(exc)}',
                thread_ts=event.get('ts')
            )
