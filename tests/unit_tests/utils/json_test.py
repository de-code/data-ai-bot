import csv

from data_ai_bot.utils.json import get_json_as_csv_lines


class TestGetJsonAsCsvLines:
    def test_should_return_empty_response_for_empty_json_list(self):
        result = list(get_json_as_csv_lines([]))
        assert not result
        assert isinstance(result, list)

    def test_should_convert_simple_flat_json_list(self):
        simple_json_list = [{
            'col1': '1.1',
            'col2': '1.2'
        }, {
            'col1': '2.1',
            'col2': '2.2'
        }]
        result = list(get_json_as_csv_lines(simple_json_list))
        csv_as_json = list(csv.DictReader(result))
        assert csv_as_json == simple_json_list

    def test_should_add_keys_from_second_row(self):
        simple_json_list = [{
            'col1': '1.1'
        }, {
            'col1': '2.1',
            'col2': '2.2'
        }]
        result = list(get_json_as_csv_lines(simple_json_list))
        csv_as_json = list(csv.DictReader(result))
        assert csv_as_json == [{
            'col1': '1.1',
            'col2': ''
        }, {
            'col1': '2.1',
            'col2': '2.2'
        }]

    def test_should_ignore_missing_keys_in_second_row(self):
        simple_json_list = [{
            'col1': '1.1',
            'col2': '1.2'
        }, {
            'col1': '2.1'
        }]
        result = list(get_json_as_csv_lines(simple_json_list))
        csv_as_json = list(csv.DictReader(result))
        assert csv_as_json == [{
            'col1': '1.1',
            'col2': '1.2'
        }, {
            'col1': '2.1',
            'col2': ''
        }]

    def test_should_convert_nested_json_to_str(self):
        nested_json_list = [{
            'parent': {'nested': 'value'}
        }]
        result = list(get_json_as_csv_lines(nested_json_list))
        csv_as_json = list(csv.DictReader(result))
        assert csv_as_json == [{
            'parent': str({'nested': 'value'})
        }]
