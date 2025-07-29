from dataclasses import dataclass
from typing import Sequence

from data_ai_bot.agent_factory import (
    LoggingToolCallbacksWrapper,
    SmolAgentsAgentFactory
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
        previous_messages: Sequence[str]
    ) -> AgentResponse:
        text = self.agent_factory(
            tool_callbacks=LoggingToolCallbacksWrapper()
        ).run(
            message,
            additional_args={
                'previous_messages': previous_messages
            }
        )
        return AgentResponse(
            text=text
        )
