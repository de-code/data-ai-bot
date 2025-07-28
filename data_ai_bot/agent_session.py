from dataclasses import dataclass
from typing import Sequence

from data_ai_bot.agent_factory import SmolAgentsAgentFactory  # type: ignore


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
        text = self.agent_factory().run(
            message,
            additional_args={
                'previous_messages': previous_messages
            }
        )
        return AgentResponse(
            text=text
        )
