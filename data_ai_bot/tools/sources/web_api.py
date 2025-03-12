# Mostly copied from smolagents examples

import logging
from typing import Any, Mapping, Optional

import jinja2
import requests
import smolagents  # type: ignore


LOGGER = logging.getLogger(__name__)


def get_requests_session() -> requests.Session:
    return requests.Session()


def get_evaluated_template(template: str, variables: Mapping[str, Any]) -> Any:
    compiled_template = jinja2.Template(template)
    return compiled_template.render(variables)


class WebApiTool(smolagents.Tool):  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        name: str,
        description: str,
        url: str,
        query_parameters: Optional[Mapping[str, str]] = None,
        headers: Optional[Mapping[str, str]] = None,
        inputs: Optional[Mapping[str, dict]] = None,
        method: str = 'GET',
        output_type: str = 'string'
    ):
        super().__init__()
        self.name = name
        self.description = description
        self.output_type = output_type
        self.url = url
        self.method = method
        self.inputs: Mapping[str, dict] = inputs or {}
        self.query_parameters = query_parameters or {}
        self.headers = headers
        self.skip_forward_signature_validation = True

    def forward(self, **kwargs):  # pylint: disable=arguments-differ
        session = get_requests_session()
        url = get_evaluated_template(self.url, kwargs)
        params = {
            key: get_evaluated_template(value, kwargs)
            for key, value in self.query_parameters.items()
        }
        LOGGER.info('url: %r (method: %r, params: %r)', url, self.method, params)
        response = session.request(
            method=self.method,
            url=url,
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        response_json = response.json()
        LOGGER.info('response_json: %r', response_json)
        return response_json
