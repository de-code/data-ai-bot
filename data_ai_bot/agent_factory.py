from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
import logging
import traceback
from typing import Any, Callable, Mapping, Protocol, Sequence, TypeVar

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
    tool: ToolT
    args: Sequence[Any]
    kwargs: Mapping[str, Any]


class ToolCallback[ToolT](Protocol):
    def __call__(self, tool_call: ToolCall[ToolT]) -> None:
        pass


@dataclass(frozen=True)
class ToolCallbacks:
    on_before_call: ToolCallback | None = None
    on_success: ToolCallback | None = None
    on_error: ToolCallback | None = None


def get_chained_tool_callback_functions(
    callbacks: Sequence[ToolCallback]
) -> ToolCallback:
    def wrapper(*args, **kwargs):
        for callback in callbacks:
            callback(*args, **kwargs)
    return wrapper


def get_chained_tool_callbacks(
    tool_callbacks_list: Sequence[ToolCallbacks]
) -> ToolCallbacks:
    return ToolCallbacks(
        on_before_call=get_chained_tool_callback_functions([
            tc.on_before_call
            for tc in tool_callbacks_list
            if tc.on_before_call is not None
        ]),
        on_success=get_chained_tool_callback_functions([
            tc.on_success
            for tc in tool_callbacks_list
            if tc.on_success is not None
        ]),
        on_error=get_chained_tool_callback_functions([
            tc.on_error
            for tc in tool_callbacks_list
            if tc.on_error is not None
        ])
    )


class LoggingToolCallbacksWrapper(ToolCallbacks):
    def __init__(self):
        super().__init__(
            on_before_call=self._on_before_call,
            on_success=self._on_success,
            on_error=self._on_error
        )

    def _on_before_call(self, tool_call: ToolCall):
        LOGGER.info('on_before_call: %r', tool_call)

    def _on_success(self, tool_call: ToolCall):
        LOGGER.info('on_success: %r', tool_call)

    def _on_error(self, tool_call: ToolCall):
        LOGGER.info('on_error: %r', tool_call)


def get_wrapped_smolagents_tool(
    tool: Tool,
    tool_callbacks: ToolCallbacks | None = None
) -> Tool:
    if tool_callbacks is None:
        return tool

    orig_call = tool.forward

    @wraps(orig_call)
    def wrapped_call(*args, **kwargs):
        tool_call = ToolCall(tool, args=args, kwargs=kwargs)
        if tool_callbacks.on_before_call is not None:
            tool_callbacks.on_before_call(tool_call)
        try:
            result = orig_call(*args, **kwargs)
            if tool_callbacks.on_success is not None:
                tool_callbacks.on_success(tool_call)
        except Exception:
            if tool_callbacks.on_error is not None:
                tool_callbacks.on_error(tool_call)
            raise
        return result

    wrapped_tool = deepcopy(tool)
    wrapped_tool.forward = wrapped_call
    return wrapped_tool


def get_wrapped_smolagents_tools(
    tools: Sequence[Tool],
    tool_callbacks: ToolCallbacks | None = None
) -> Sequence[Tool]:
    if tool_callbacks is None:
        return tools
    return [
        get_wrapped_smolagents_tool(tool, tool_callbacks=tool_callbacks)
        for tool in tools
    ]


@dataclass(frozen=True)
class SmolAgentsAgentFactory:
    model: smolagents.Model
    tools: Sequence[Tool]
    system_prompt: str | None = None

    def __call__(
        self,
        tool_callbacks: ToolCallbacks | None = None
    ) -> smolagents.MultiStepAgent:
        agent = smolagents.ToolCallingAgent(
            tools=get_wrapped_smolagents_tools(
                self.tools,
                tool_callbacks=tool_callbacks
            ),
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


def check_agent_factory(agent_factory: Callable[[], smolagents.MultiStepAgent]):
    agent = agent_factory()
    LOGGER.info('System Prompt: %r', agent.system_prompt)
    assert agent is not None
