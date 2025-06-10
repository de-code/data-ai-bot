from dataclasses import dataclass
import logging
import os
from pathlib import Path
import traceback
from typing import Callable, Optional, Sequence

import slack_bolt
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.context.say import Say

from cachetools import TTLCache  # type: ignore

import smolagents  # type: ignore
from smolagents import Tool

from data_ai_bot.config import (
    FromPythonToolClassConfig,
    FromPythonToolInstanceConfig,
    ToolDefinitionsConfig,
    load_app_config
)
from data_ai_bot.slack import (
    SlackMessageEvent,
    get_message_age_in_seconds_from_event_dict,
    get_slack_message_event_from_event_dict,
    get_slack_mrkdwn_for_markdown
)
from data_ai_bot.telemetry import configure_otlp_if_enabled
from data_ai_bot.tools.resolver import ConfigToolResolver


LOGGER = logging.getLogger(__name__)


DEFAULT_TOOL_DEFINITIONS_CONFIG: ToolDefinitionsConfig = ToolDefinitionsConfig(
    from_python_tool_instance=[
        FromPythonToolInstanceConfig(
            name='get_joke',
            module='data_ai_bot.tools.example.joke',
            key='get_joke'
        )
    ],
    from_python_tool_class=[
        FromPythonToolClassConfig(
            name='get_docmap_by_manuscript_id',
            module='data_ai_bot.tools.data_hub.docmap',
            class_name='DocMapTool'
        )
    ]
)


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
    api_key: str,
    temperature: float = 0.0
) -> smolagents.Model:
    LOGGER.info('model_id: %r', model_id)
    return smolagents.OpenAIServerModel(
        model_id=model_id,
        api_base=api_base,
        api_key=api_key,
        temperature=temperature
    )


def do_step_callback(step_log: smolagents.ActionStep):
    LOGGER.info('step_log: %r', step_log)
    if step_log.error:
        stacktrace_str = '\n'.join(traceback.format_exception(step_log.error))
        LOGGER.warning('Caught error: %s', stacktrace_str)


@dataclass(frozen=True)
class SmolAgentsAgentFactory:
    model: smolagents.Model
    tools: Sequence[Tool]
    system_prompt: str | None = None

    def __call__(self) -> smolagents.MultiStepAgent:
        agent = smolagents.ToolCallingAgent(
            tools=self.tools,
            model=self.model,
            step_callbacks=[do_step_callback],
            max_steps=3
        )
        if self.system_prompt:
            agent.prompt_templates['system_prompt'] = (
                agent.prompt_templates['system_prompt']
                + '\n\n'
                + self.system_prompt
            )
            agent.system_prompt = agent.initialize_system_prompt()
        return agent


def get_system_prompt() -> str:
    return Path('data/system-prompt.txt').read_text(encoding='utf-8')


def get_agent_message(
    message_event: SlackMessageEvent
) -> str:
    return f'User query:\n{message_event.text}'.strip() + '\n'


@dataclass(frozen=True)
class SlackChatApp:
    agent_factory: Callable[[], smolagents.MultiStepAgent]
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
            response_message = self.agent_factory().run(
                get_agent_message(
                    message_event=message_event
                ),
                additional_args={
                    'previous_messages': message_event.previous_messages
                }
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


def check_agent_factory(agent_factory: Callable[[], smolagents.MultiStepAgent]):
    agent = agent_factory()
    LOGGER.info('System Prompt: %r', agent.system_prompt)
    assert agent is not None


def create_bolt_app(
    agent_factory: Callable[[], smolagents.MultiStepAgent],
    max_message_age_in_seconds: int = 600,
    echo_message: bool = False
):
    check_agent_factory(agent_factory)
    app = slack_bolt.App(
        token=get_required_env('SLACK_BOT_TOKEN'),
        signing_secret=get_required_env('SLACK_SIGNING_SECRET')
    )
    chat_app = SlackChatApp(
        agent_factory=agent_factory,
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
    app_config = load_app_config()
    LOGGER.info('app_config: %r', app_config)
    configure_otlp_if_enabled(get_optional_env('OTLP_ENDPOINT'))
    model = get_model(
        model_id=get_required_env('OPENAI_MODEL_ID'),
        api_base=get_required_env('OPENAI_BASE_URL'),
        api_key=get_required_env('OPENAI_API_KEY')
    )
    headers = {
        'User-Agent': get_optional_env('USER_AGENT') or 'Data-AI-Bot/1.0'
    }
    with ConfigToolResolver(
        tool_definitions_config=(
            app_config.tool_definitions
            or DEFAULT_TOOL_DEFINITIONS_CONFIG
        ),
        tool_collection_definitions_config=(
            app_config.tool_collection_definitions
        ),
        headers=headers
    ) as tool_resolver:
        tools = tool_resolver.get_tools_by_name(
            app_config.agent.tools,
            tool_collection_names=app_config.agent.tool_collections
        )
        LOGGER.info('Tools: %r', tools)
        agent_factory = SmolAgentsAgentFactory(
            model=model,
            tools=tools,
            system_prompt=get_system_prompt()
        )
        app = create_bolt_app(
            agent_factory=agent_factory
        )
        handler = SocketModeHandler(
            app=app,
            app_token=get_required_env('SLACK_APP_TOKEN')
        )
        LOGGER.info('Starting...')
        handler.start()
