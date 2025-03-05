# Mostly copied from smolagents examples

import json
import logging
import re
from typing import Mapping

import requests

import smolagents  # type: ignore


LOGGER = logging.getLogger(__name__)


class DocMapTool(smolagents.Tool):
    name = 'data_hub_docmap'
    description = 'Fetches a DocMap as JSON from the Data Hub DocMaps API.'
    inputs = {
        'manuscript_id': {
            'type': 'string',
            'description': 'The 5 or 6 digit eLife manuscript id'
        }
    }
    output_type = 'string'

    def __init__(self, headers: Mapping[str, str], timeout: int = 30):
        super().__init__()
        self.headers = headers
        self.timeout = timeout

    def forward(self, manuscript_id: str):  # pylint: disable=arguments-differ
        try:
            if not re.match(r'\d{5,6}', manuscript_id):
                return r'Invalid manuscript id (must be 5 or 6 digits): {manuscript_id}'
            url = (
                'https://data-hub-api.elifesciences.org/enhanced-preprints/docmaps'
                f'/v2/by-publisher/elife/get-by-manuscript-id?manuscript_id={manuscript_id}'
            )
            LOGGER.info('url: %r', url)

            response = requests.get(url, timeout=self.timeout, headers=self.headers)
            response.raise_for_status()

            docmap_json = response.json()
            LOGGER.info('docmap_json: %r', docmap_json)

            return json.dumps(docmap_json)
        except Exception as e:  # pylint: disable=broad-exception-caught
            return f'Error fetching DocMap: {str(e)}'
