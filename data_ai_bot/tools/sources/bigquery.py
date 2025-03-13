# Mostly copied from smolagents examples

import logging
from typing import Any, Iterable, Mapping, Optional, Sequence

from google.cloud import bigquery
from google.cloud.bigquery.table import RowIterator

import smolagents  # type: ignore


LOGGER = logging.getLogger(__name__)


def get_bq_client(project_name: str) -> bigquery.Client:
    return bigquery.Client(project=project_name)


def get_bq_result_from_bq_query(
    project_name: str,
    query: str,
    query_parameters: Optional[Sequence[Any]] = tuple()
) -> RowIterator:
    client = get_bq_client(project_name=project_name)
    job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
    query_job = client.query(query, job_config=job_config)  # Make an API request.
    bq_result = query_job.result()  # Waits for query to finish
    LOGGER.debug('bq_result: %r', bq_result)
    return bq_result


def iter_dict_from_bq_query(
    project_name: str,
    query: str,
    query_parameters: Optional[Sequence[Any]] = tuple()
) -> Iterable[dict]:
    bq_result = get_bq_result_from_bq_query(
        project_name=project_name,
        query=query,
        query_parameters=query_parameters
    )
    for row in bq_result:
        LOGGER.debug('row: %r', row)
        yield dict(row.items())


class BigQueryTool(smolagents.Tool):  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        name: str,
        description: str,
        project_name: str,
        sql_query: str,
        output_type: str = 'string'
    ):
        super().__init__()
        self.name = name
        self.description = description
        self.output_type = output_type
        self.project_name = project_name
        self.sql_query = sql_query
        self.inputs: Mapping[str, dict] = {}
        self.skip_forward_signature_validation = True

    def forward(self):  # pylint: disable=arguments-differ
        result = list(iter_dict_from_bq_query(
            project_name=self.project_name,
            query=self.sql_query
        ))
        LOGGER.info('query results: %r', result)
        return result
