# Mostly copied from smolagents examples

import logging

import smolagents  # type: ignore


LOGGER = logging.getLogger(__name__)


class StaticContentTool(smolagents.Tool):
    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        output_type: str = 'string'
    ):
        super().__init__()
        self.name = name
        self.description = description
        self.output_type = output_type
        self.content = content
        self.inputs: dict = {}

    def forward(self):  # pylint: disable=arguments-differ
        return self.content
