from dataclasses import dataclass, field
import logging
from typing import Sequence

import slack_bolt
from slack_bolt.context.say import Say

from data_ai_bot.agent_factory import SmolAgentsAgentFactory, ToolCall, ToolCallEvent
from data_ai_bot.agent_session import SmolAgentsAgentSession
from data_ai_bot.slack import (
    BlockTypedDict,
    ContextBlockTypedDict,
    SlackMessageClient,
    SlackMessageEvent,
    get_slack_blocks_and_files_for_mrkdwn,
    get_slack_message_event_from_event_dict,
    get_slack_mrkdwn_for_markdown
)
from data_ai_bot.utils.dummy_text import DUMMY_TEXT_4K
from data_ai_bot.utils.text import (
    get_markdown_for_agent_response_message,
    get_truncated_with_ellipsis
)


LOGGER = logging.getLogger(__name__)


ZERO_WIDTH_SPACE = '\u200B'


def get_agent_message(
    message_event: SlackMessageEvent
) -> str:
    return f'{message_event.text}'.strip() + '\n'


def get_formatted_tool_args(
    tool_call: ToolCall,
    mrkdwn: bool = False
) -> str:
    return ', '.join([
        f'_{key}_={repr(value)}'
        if mrkdwn
        else f'{key}={repr(value)}'
        for key, value in tool_call.kwargs.items()
        if value
    ])


def get_plain_text_formatted_tool_call(tool_call: ToolCall) -> str:
    tool_name = tool_call.tool_name
    formatted_args = get_formatted_tool_args(tool_call)
    return f'{tool_name}({formatted_args})'


def get_mrkdwn_formatted_tool_call(tool_call: ToolCall) -> str:
    tool_name = tool_call.tool_name
    formatted_args = get_formatted_tool_args(tool_call, mrkdwn=True)
    return f'*{tool_name}*{ZERO_WIDTH_SPACE}({formatted_args})'


@dataclass(frozen=True)
class SlackChatAppMessageSession:  # pylint: disable=too-many-instance-attributes
    agent_factory: SmolAgentsAgentFactory
    slack_app: slack_bolt.App
    message_event_dict: dict
    message_event: SlackMessageEvent
    message_client: SlackMessageClient
    say: Say
    echo_message: bool = False
    tool_call_str_list: list[str] = field(default_factory=list)

    def get_agent_response_message(self) -> str:
        text = self.message_event.text
        last_word = text.rsplit(' ')[-1]
        if last_word == 'TEST_LONG_TEXT':
            return DUMMY_TEXT_4K
        if last_word == 'TEST_LONG_CODE':
            return f'```\n{DUMMY_TEXT_4K}\n```'
        agent_response = SmolAgentsAgentSession(
            agent_factory=self.agent_factory
        ).run(
            message=get_agent_message(
                message_event=self.message_event
            ),
            previous_messages=self.message_event.previous_messages,
            tool_call_event_handler=self.on_tool_call_event
        )
        return agent_response.text

    def on_tool_call_event(self, tool_call_event: ToolCallEvent):
        LOGGER.info('Tool Call Event: %r', tool_call_event)
        plain_text_tool_call_str = get_plain_text_formatted_tool_call(tool_call_event.tool_call)
        mrkdwn_tool_call_str = get_mrkdwn_formatted_tool_call(tool_call_event.tool_call)
        if tool_call_event.event_name == 'before_call':
            self.message_client.set_status(
                f'Calling Tool: {plain_text_tool_call_str}'
            )
        if tool_call_event.event_name == 'success':
            self.message_client.set_status(
                f'Completed Tool: {plain_text_tool_call_str}'
            )
            self.tool_call_str_list.append(mrkdwn_tool_call_str)
        if tool_call_event.event_name == 'error':
            self.message_client.set_status(
                f'Failed Tool: {plain_text_tool_call_str}'
            )

    def get_tool_call_blocks(self) -> Sequence[ContextBlockTypedDict]:
        if not self.tool_call_str_list:
            return []
        return [{
            'type': 'context',
            'elements': [{
                'type': 'mrkdwn',
                'text': get_truncated_with_ellipsis(
                    'Called Tools: ' + ', '.join(self.tool_call_str_list),
                    max_length=3000
                )
            }]
        }]

    def handle_message(self):
        message_event = self.message_event
        LOGGER.info('message_event: %r', message_event)

        self.message_client.set_status(f'Processing request: {message_event.text}')

        if self.echo_message:
            self.say(
                f'Hi <@{message_event.user}>! You said: {message_event.text}',
                thread_ts=message_event.thread_ts
            )
        response_message = get_markdown_for_agent_response_message(
            self.get_agent_response_message()
        )
        LOGGER.info('response_message: %r', response_message)
        response_message_mrkdwn = get_slack_mrkdwn_for_markdown(
            response_message
        )
        LOGGER.info('response_message_mrkdwn: %r', response_message_mrkdwn)
        LOGGER.info('responded to event: %r', self.message_event_dict)
        tool_call_blocks = self.get_tool_call_blocks()
        blocks, files = get_slack_blocks_and_files_for_mrkdwn(
            response_message_mrkdwn
        )
        self.message_client.post_response_message(
            text=response_message,
            blocks=list[BlockTypedDict](tool_call_blocks) + list[BlockTypedDict](blocks)
        )
        self.message_client.upload_files(files)


@dataclass(frozen=True)
class SlackChatApp:
    agent_factory: SmolAgentsAgentFactory
    slack_app: slack_bolt.App
    echo_message: bool = False

    def handle_message(self, event: dict, say: Say):
        try:
            message_event = get_slack_message_event_from_event_dict(
                app=self.slack_app,
                event=event
            )
            SlackChatAppMessageSession(
                agent_factory=self.agent_factory,
                slack_app=self.slack_app,
                message_event_dict=event,
                message_event=message_event,
                message_client=SlackMessageClient(
                    slack_app=self.slack_app,
                    message_event=message_event
                ),
                say=say,
                echo_message=self.echo_message
            ).handle_message()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            LOGGER.warning('Caught exception: %r', exc, exc_info=True)
            say(
                f'Failed to process request due to:\n> {repr(exc)}',
                thread_ts=event.get('ts')
            )
