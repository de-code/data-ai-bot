from dataclasses import dataclass
from typing import Sequence

from data_ai_bot.agent_factory import (
    SmolAgentsAgentFactory,
    ToolCallEventHandler
)


@dataclass(frozen=True)
class AgentResponse:
    text: str


@dataclass(frozen=True)
class SmolAgentsAgentSession:
    agent_factory: SmolAgentsAgentFactory

    def run(
        self,
        message: str,
        previous_messages: Sequence[str],
        tool_call_event_handler: ToolCallEventHandler | None = None
    ) -> AgentResponse:
        text = self.agent_factory(
            tool_call_event_handler=tool_call_event_handler
        ).run(
            message,
            additional_args={
                'previous_messages': previous_messages
            }
        )
        return AgentResponse(
            text=text
        )
