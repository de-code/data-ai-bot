# Mostly copied from smolagents examples

import logging
from typing import Mapping, Optional

import requests
import smolagents  # type: ignore


LOGGER = logging.getLogger(__name__)


def get_requests_session() -> requests.Session:
    return requests.Session()


class WebApiTool(smolagents.Tool):
    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        name: str,
        description: str,
        url: str,
        headers: Optional[Mapping[str, str]] = None,
        method: str = 'GET',
        output_type: str = 'string'
    ):
        super().__init__()
        self.name = name
        self.description = description
        self.output_type = output_type
        self.url = url
        self.method = method
        self.inputs: dict = {}
        self.headers = headers

    def forward(self):  # pylint: disable=arguments-differ
        session = get_requests_session()
        response = session.request(
            method=self.method,
            url=self.url,
            headers=self.headers
        )
        return response.json()
