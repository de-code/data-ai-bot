import logging
import os
from typing import Optional, Sequence

import slack_bolt
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.context.say import Say

from cachetools import TTLCache  # type: ignore

from data_ai_bot.agent_factory import (
    SmolAgentsAgentFactory,
    SmolAgentsManagedAgentFactory,
    check_agent_factory
)
from data_ai_bot.app import SlackChatApp
from data_ai_bot.config import (
    AppConfig,
    BaseAgentConfig,
    FromPythonToolClassConfig,
    FromPythonToolInstanceConfig,
    ManagedAgentConfig,
    ToolDefinitionsConfig,
    load_app_config
)
from data_ai_bot.models.registry import SmolAgentsModelRegistry
from data_ai_bot.slack import (
    get_message_age_in_seconds_from_event_dict
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


def create_bolt_app(
    agent_factory: SmolAgentsAgentFactory,
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


def get_managed_agent_factory_for_config(
    managed_agent_config: ManagedAgentConfig,
    tool_resolver: ConfigToolResolver,
    model_registry: SmolAgentsModelRegistry
) -> SmolAgentsManagedAgentFactory:
    LOGGER.info('managed_agent_config: %r', managed_agent_config)
    tools = tool_resolver.get_tools_by_name(
        tool_names=managed_agent_config.tools,
        tool_collection_names=managed_agent_config.tool_collections
    )
    LOGGER.info('Tools (Managed Agent: %s): %r', managed_agent_config.name, tools)
    model = model_registry.get_model_or_default_model(managed_agent_config.model_name)
    return SmolAgentsManagedAgentFactory(
        name=managed_agent_config.name,
        description=managed_agent_config.description,
        model=model,
        tools=tools,
        system_prompt=managed_agent_config.system_prompt
    )


def get_managed_agent_factory_by_name(
    name: str,
    tool_resolver: ConfigToolResolver,
    model_registry: SmolAgentsModelRegistry,
    app_config: AppConfig
) -> SmolAgentsManagedAgentFactory:
    for managed_agent_config in app_config.managed_agents:
        if managed_agent_config.name != name:
            continue
        return get_managed_agent_factory_for_config(
            managed_agent_config=managed_agent_config,
            tool_resolver=tool_resolver,
            model_registry=model_registry
        )
    raise ValueError(f'No managed agent config found for: {repr(name)}')


def get_managed_agent_factories(
    managed_agent_names: Sequence[str],
    tool_resolver: ConfigToolResolver,
    model_registry: SmolAgentsModelRegistry,
    app_config: AppConfig
) -> Sequence[SmolAgentsManagedAgentFactory]:
    return [
        get_managed_agent_factory_by_name(
            name=name,
            tool_resolver=tool_resolver,
            model_registry=model_registry,
            app_config=app_config
        )
        for name in managed_agent_names
    ]


def get_main_agent_factory_for_config(
    agent_config: BaseAgentConfig,
    tool_resolver: ConfigToolResolver,
    model_registry: SmolAgentsModelRegistry,
    app_config: AppConfig
) -> SmolAgentsAgentFactory:
    LOGGER.info('agent_config: %r', agent_config)
    tools = tool_resolver.get_tools_by_name(
        tool_names=agent_config.tools,
        tool_collection_names=agent_config.tool_collections
    )
    model = model_registry.get_model_or_default_model(agent_config.model_name)
    LOGGER.info('Tools (Main Agent): %r', tools)
    LOGGER.info('Managed Agents (Main Agent): %r', agent_config.managed_agent_names)
    return SmolAgentsAgentFactory(
        model=model,
        tools=tools,
        system_prompt=agent_config.system_prompt,
        managed_agent_factories=get_managed_agent_factories(
            managed_agent_names=agent_config.managed_agent_names,
            tool_resolver=tool_resolver,
            model_registry=model_registry,
            app_config=app_config
        )
    )


def main():
    LOGGER.info('Initializing...')
    app_config = load_app_config()
    LOGGER.info('app_config: %r', app_config)
    configure_otlp_if_enabled(get_optional_env('OTLP_ENDPOINT'))
    model_registry = SmolAgentsModelRegistry(
        app_config.models
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
        agent_factory = get_main_agent_factory_for_config(
            agent_config=app_config.agent,
            tool_resolver=tool_resolver,
            model_registry=model_registry,
            app_config=app_config
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
