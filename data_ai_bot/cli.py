import logging
import os
from pathlib import Path
import traceback

import slack_bolt
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.context.say import Say

import smolagents  # type: ignore

from data_ai_bot.slack import (
    SlackMessageEvent,
    get_slack_message_event_from_event_dict
)


LOGGER = logging.getLogger(__name__)


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
    model: smolagents.Model
) -> smolagents.MultiStepAgent:
    return smolagents.ToolCallingAgent(
        tools=[],
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


def create_bolt_app(
    agent: smolagents.MultiStepAgent,
    system_prompt: str,
    echo_message: bool = False
):
    app = slack_bolt.App(
        token=get_required_env('SLACK_BOT_TOKEN'),
        signing_secret=get_required_env('SLACK_SIGNING_SECRET')
    )

    @app.event('message')
    def message(event: dict, say: Say):
        LOGGER.info('event: %r', event)
        if event.get('channel_type') == 'im':
            message_event = get_slack_message_event_from_event_dict(app=app, event=event)
            LOGGER.info('message_event: %r', message_event)

            if echo_message:
                say(
                    f'Hi <@{message_event.user}>! You said: {message_event.text}',
                    thread_ts=message_event.thread_ts
                )

            try:
                response_message = agent.run(
                    get_agent_message(
                        system_prompt=system_prompt,
                        message_event=message_event
                    )
                )
                say(response_message, thread_ts=message_event.thread_ts)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                LOGGER.warning('Caught exception: %r', exc, exc_info=True)
                say(
                    f'Failed to process request due to:\n> {repr(exc)}',
                    thread_ts=message_event.thread_ts
                )

    return app


def main():
    LOGGER.info('Initializing...')
    model = get_model(
        model_id=get_required_env('OPENAI_MODEL_ID'),
        api_base=get_required_env('OPENAI_BASE_URL'),
        api_key=get_required_env('OPENAI_API_KEY')
    )
    agent = get_agent(model=model)
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
