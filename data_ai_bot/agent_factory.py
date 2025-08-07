from copy import deepcopy
from dataclasses import dataclass, field
from functools import wraps
import logging
import traceback
from typing import Any, Callable, Literal, Mapping, Protocol, Sequence, TypeVar

import smolagents  # type: ignore
from smolagents import Tool


LOGGER = logging.getLogger(__name__)

ToolT = TypeVar('ToolT', bound=Callable)


def do_step_callback(step_log: smolagents.ActionStep):
    LOGGER.info('step_log: %r', step_log)
    if step_log.error:
        stacktrace_str = '\n'.join(traceback.format_exception(step_log.error))
        LOGGER.warning('Caught error: %s', stacktrace_str)


@dataclass(frozen=True)
class ToolCall[ToolT]:
    tool_name: str
    tool: ToolT
    args: Sequence[Any]
    kwargs: Mapping[str, Any]


@dataclass(frozen=True)
class ToolCallEvent[ToolT]:
    event_name: Literal['before_call', 'success', 'error']
    tool_call: ToolCall[ToolT]


class ToolCallEventHandler[ToolT](Protocol):
    def __call__(self, tool_call_event: ToolCallEvent[ToolT]) -> None:
        pass


def get_chained_tool_call_event_handlers(
    tool_call_event_handlers: Sequence[ToolCallEventHandler]
) -> ToolCallEventHandler:
    def wrapper(*args, **kwargs):
        for tool_call_event_handler in tool_call_event_handlers:
            tool_call_event_handler(*args, **kwargs)
    return wrapper


class LoggingToolCallEventHandler(ToolCallEventHandler[ToolT]):
    def __call__(self, tool_call_event: ToolCallEvent[ToolT]) -> None:
        LOGGER.info('Tool Event: %r', tool_call_event)


def get_wrapped_smolagents_tool(
    tool: Tool,
    tool_call_event_handler: ToolCallEventHandler | None = None
) -> Tool:
    if tool_call_event_handler is None:
        return tool

    orig_call = tool.forward

    @wraps(orig_call)
    def wrapped_call(*args, **kwargs):
        tool_call = ToolCall(
            tool_name=tool.name,
            tool=tool,
            args=args,
            kwargs=kwargs
        )
        tool_call_event_handler(ToolCallEvent(
            event_name='before_call',
            tool_call=tool_call
        ))
        try:
            result = orig_call(*args, **kwargs)
            tool_call_event_handler(ToolCallEvent(
                event_name='success',
                tool_call=tool_call
            ))
        except Exception:
            tool_call_event_handler(ToolCallEvent(
                event_name='error',
                tool_call=tool_call
            ))
            raise
        return result

    wrapped_tool = deepcopy(tool)
    wrapped_tool.forward = wrapped_call
    return wrapped_tool


def get_wrapped_smolagents_tools(
    tools: Sequence[Tool],
    tool_call_event_handler: ToolCallEventHandler | None = None
) -> Sequence[Tool]:
    if tool_call_event_handler is None:
        return tools
    return [
        get_wrapped_smolagents_tool(
            tool,
            tool_call_event_handler=tool_call_event_handler
        )
        for tool in tools
    ]


@dataclass(frozen=True, kw_only=True)
class SmolAgentsAgentFactory:
    model: smolagents.Model
    tools: Sequence[Tool]
    managed_agent_factories: Sequence['SmolAgentsManagedAgentFactory'] = field(
        default_factory=list
    )
    system_prompt: str | None = None
    name: str | None = None
    description: str | None = None

    def __call__(
        self,
        tool_call_event_handler: ToolCallEventHandler | None = None
    ) -> smolagents.MultiStepAgent:
        agent = smolagents.ToolCallingAgent(
            name=self.name,
            description=self.description,
            tools=get_wrapped_smolagents_tools(
                self.tools,
                tool_call_event_handler=tool_call_event_handler
            ),
            managed_agents=[
                managed_agent_factory(
                    tool_call_event_handler=tool_call_event_handler
                )
                for managed_agent_factory in self.managed_agent_factories
            ],
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
        return agent


@dataclass(frozen=True, kw_only=True)
class SmolAgentsManagedAgentFactory(SmolAgentsAgentFactory):
    name: str
    description: str

    def __post_init__(self):
        if self.name is None:
            raise TypeError('`name` required')
        if self.description is None:
            raise TypeError('`description` required')


def check_agent_factory(agent_factory: Callable[[], smolagents.MultiStepAgent]):
    agent = agent_factory()
    LOGGER.info('System Prompt:\n```text\n%s\n```', agent.system_prompt)
    assert agent is not None
