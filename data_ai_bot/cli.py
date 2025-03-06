from dataclasses import dataclass
import logging
import os
from pathlib import Path
import traceback
from typing import Mapping, Optional

import slack_bolt
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.context.say import Say

from cachetools import TTLCache  # type: ignore
import smolagents  # type: ignore

from data_ai_bot.slack import (
    SlackMessageEvent,
    get_message_age_in_seconds_from_event_dict,
    get_slack_message_event_from_event_dict,
    get_slack_mrkdwn_for_markdown
)
from data_ai_bot.telemetry import configure_otlp_if_enabled
from data_ai_bot.tools.data_hub.docmap import DocMapTool
from data_ai_bot.tools.example.joke import get_joke


LOGGER = logging.getLogger(__name__)


def get_optional_env(key: str) -> Optional[str]:
    return os.getenv(key)


def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise KeyError(f'Missing environment variable: {key}')
    return value


def get_model(
    model_id: str,
    api_base: str,
    api_key: str
) -> smolagents.Model:
    LOGGER.info('model_id: %r', model_id)
    return smolagents.OpenAIServerModel(
        model_id=model_id,
        api_base=api_base,
        api_key=api_key
    )


def do_step_callback(step_log: smolagents.ActionStep):
    LOGGER.info('step_log: %r', step_log)
    if step_log.error:
        stacktrace_str = '\n'.join(traceback.format_exception(step_log.error))
        LOGGER.warning('Caught error: %s', stacktrace_str)


def get_agent(
    model: smolagents.Model,
    headers: Mapping[str, str]
) -> smolagents.MultiStepAgent:
    return smolagents.ToolCallingAgent(
        tools=[get_joke, DocMapTool(headers=headers)],
        model=model,
        step_callbacks=[do_step_callback],
        max_steps=3
    )


def get_system_prompt() -> str:
    return Path('data/system-prompt.txt').read_text(encoding='utf-8')


def get_agent_message(
    system_prompt: str,
    message_event: SlackMessageEvent
) -> str:
    prompt = system_prompt
    if message_event.previous_messages:
        flat_previous_messages = '\n\n'.join(message_event.previous_messages)
        prompt += f'\n\nPrevious messages:{flat_previous_messages}'
    prompt += f'\n\nUser query:\n{message_event.text}'
    return prompt


@dataclass(frozen=True)
class SlackChatApp:
    agent: smolagents.MultiStepAgent
    system_prompt: str
    slack_app: slack_bolt.App
    echo_message: bool = False

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
            response_message = self.agent.run(
                get_agent_message(
                    system_prompt=self.system_prompt,
                    message_event=message_event
                )
            )
            LOGGER.info('response_message: %r', response_message)
            response_message_mrkdwn = get_slack_mrkdwn_for_markdown(
                response_message
            )
            LOGGER.info('response_message_mrkdwn: %r', response_message_mrkdwn)
            LOGGER.info('responded to event: %r', event)
            self.slack_app.client.chat_postMessage(
                text=response_message,
                mrkdwn=True,
                blocks=[{
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': response_message_mrkdwn
                    }
                }],
                channel=message_event.channel,
                thread_ts=message_event.thread_ts
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            LOGGER.warning('Caught exception: %r', exc, exc_info=True)
            say(
                f'Failed to process request due to:\n> {repr(exc)}',
                thread_ts=event.get('ts')
            )


def create_bolt_app(
    agent: smolagents.MultiStepAgent,
    system_prompt: str,
    max_message_age_in_seconds: int = 600,
    echo_message: bool = False
):
    app = slack_bolt.App(
        token=get_required_env('SLACK_BOT_TOKEN'),
        signing_secret=get_required_env('SLACK_SIGNING_SECRET')
    )
    chat_app = SlackChatApp(
        agent=agent,
        system_prompt=system_prompt,
        slack_app=app,
        echo_message=echo_message
    )

    previous_messages: dict[str, bool] = TTLCache(maxsize=1000, ttl=600)

    @app.event('message')
    def message(event: dict, say: Say):
        LOGGER.info('event: %r', event)
        if event.get('channel_type') == 'im':
            chat_app.handle_message(event=event, say=say)

    @app.event('app_mention')
    def handle_app_mention(
        event: dict,
        say: Say,
        ack: slack_bolt.Ack,
        request: slack_bolt.BoltRequest
    ):
        retry_count = request.headers.get('x-slack-retry-num')
        retry_reason = request.headers.get('x-slack-retry-reason')
        message_age_in_seconds = get_message_age_in_seconds_from_event_dict(event)
        LOGGER.info(
            'event: %r (retry: %s, reason: %r, age: %.3fs)',
            event, retry_count, retry_reason, message_age_in_seconds
        )
        ack()
        ts = event['ts']
        if ts in previous_messages:
            LOGGER.info('Ignoring already processed message: %r', ts)
            return
        if message_age_in_seconds > max_message_age_in_seconds:
            LOGGER.info('Ignoring old message: %r', message_age_in_seconds)
            return
        previous_messages[ts] = True
        chat_app.handle_message(event=event, say=say)

    return app


def main():
    LOGGER.info('Initializing...')
    configure_otlp_if_enabled(get_optional_env('OTLP_ENDPOINT'))
    model = get_model(
        model_id=get_required_env('OPENAI_MODEL_ID'),
        api_base=get_required_env('OPENAI_BASE_URL'),
        api_key=get_required_env('OPENAI_API_KEY')
    )
    headers = {
        'User-Agent': get_optional_env('USER_AGENT') or 'Data-AI--Bot/1.0'
    }
    agent = get_agent(model=model, headers=headers)
    app = create_bolt_app(
        agent=agent,
        system_prompt=get_system_prompt()
    )
    handler = SocketModeHandler(
        app=app,
        app_token=get_required_env('SLACK_APP_TOKEN')
    )
    LOGGER.info('Starting...')
    handler.start()
