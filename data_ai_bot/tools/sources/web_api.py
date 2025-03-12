# Mostly copied from smolagents examples

import logging
import re
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


def validate_tool_parameters(
    tool_parameters: Mapping[str, Any],
    inputs: Mapping[str, dict]
) -> Any:
    for key, value in tool_parameters.items():
        input_config = inputs[key]
        regex = input_config.get('regex')
        if regex:
            if not re.match(regex, value):
                raise ValueError(
                    f'Tool parameter value {repr(value)} for {repr(key)}'
                    f' does not match {repr(regex)}'
                )


def get_evaluated_query_parameters(
    query_parameters: Mapping[str, Any],
    variables: Mapping[str, Any]
) -> Mapping[str, Any]:
    return {
        key: get_evaluated_template(value, variables)
        for key, value in query_parameters.items()
    }


def get_query_parameters_without_empty_values(params: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        key: value
        for key, value in params.items()
        if value
    }


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
        remove_empty_query_parameters: bool = True,
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
        self.remove_empty_query_parameters = remove_empty_query_parameters
        self.skip_forward_signature_validation = True

    def forward(self, **kwargs):  # pylint: disable=arguments-differ
        validate_tool_parameters(kwargs, self.inputs)
        session = get_requests_session()
        url = get_evaluated_template(self.url, kwargs)
        params = get_evaluated_query_parameters(
            self.query_parameters,
            kwargs
        )
        if self.remove_empty_query_parameters:
            params = get_query_parameters_without_empty_values(params)
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
