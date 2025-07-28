from dataclasses import dataclass
from typing import Callable, Sequence

import smolagents  # type: ignore


@dataclass(frozen=True)
class AgentResponse:
    text: str


@dataclass(frozen=True)
class AgentSession:
    agent_factory: Callable[[], smolagents.MultiStepAgent]

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
