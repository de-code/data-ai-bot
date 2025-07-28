from dataclasses import dataclass
import logging
import traceback
from typing import Callable, Sequence

import smolagents  # type: ignore
from smolagents import Tool


LOGGER = logging.getLogger(__name__)


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
        return agent


def check_agent_factory(agent_factory: Callable[[], smolagents.MultiStepAgent]):
    agent = agent_factory()
    LOGGER.info('System Prompt: %r', agent.system_prompt)
    assert agent is not None
