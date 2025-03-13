from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest

from data_ai_bot.tools.sources import bigquery
from data_ai_bot.tools.sources.bigquery import BigQueryTool


PROJECT_NAME_1 = 'project_name_1'

SQL_QUERY_1 = 'sql_query_1'

ROW_1 = {'column_1': 'value_1'}


@pytest.fixture(name='bigquery_mock', autouse=True)
def _bigquery_mock() -> Iterator[MagicMock]:
    with patch.object(bigquery, 'bigquery') as mock:
        yield mock


@pytest.fixture(name='iter_dict_from_bq_query_mock')
def _iter_dict_from_bq_query_mock() -> Iterator[MagicMock]:
    with patch.object(bigquery, 'iter_dict_from_bq_query') as mock:
        yield mock


class TestBigQueryTool:
    def test_should_call_iter_dict_from_bq_query(
        self,
        iter_dict_from_bq_query_mock: MagicMock
    ):
        tool = BigQueryTool(
            name='name_1',
            description='description_1',
            project_name=PROJECT_NAME_1,
            sql_query=SQL_QUERY_1
        )
        tool.forward()
        iter_dict_from_bq_query_mock.assert_called_with(
            project_name=PROJECT_NAME_1,
            query=SQL_QUERY_1
        )

    def test_should_return_query_results_as_json(
        self,
        iter_dict_from_bq_query_mock: MagicMock
    ):
        tool = BigQueryTool(
            name='name_1',
            description='description_1',
            project_name=PROJECT_NAME_1,
            sql_query=SQL_QUERY_1
        )
        iter_dict_from_bq_query_mock.return_value = iter([ROW_1])
        assert tool.forward() == [ROW_1]
