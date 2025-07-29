from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest
import smolagents  # type: ignore

import data_ai_bot.agent_factory as agent_factory_module
from data_ai_bot.agent_factory import (
    ToolCall,
    ToolCallbacks,
    get_chained_tool_callbacks,
    get_wrapped_smolagents_tool,
    get_wrapped_smolagents_tools
)


class TestTool(smolagents.Tool):
    __test__ = False

    skip_forward_signature_validation = True
    name = 'test_tool_1'
    description = 'This is test tool 1'
    inputs = {
        'param_1': {
            'type': 'string',
            'description': 'Param 1'
        }
    }
    output_type = 'string'

    def __init__(self):
        super().__init__()
        self.forward_mock = MagicMock(name='tool_forward_mock')

    def forward(self, *args, **kwargs):
        self.forward_mock(*args, **kwargs)


TOOL_CALL_1 = ToolCall(
    tool=TestTool(),
    args=['arg_1'],
    kwargs={'kw_1': 'value_1'}
)


@pytest.fixture(name='test_tool')
def _tool_mock() -> TestTool:
    return TestTool()


@pytest.fixture(name='on_before_call_mock')
def _on_before_call_mock() -> MagicMock:
    return MagicMock(name='on_before_call_mock')


@pytest.fixture(name='on_success_mock')
def _on_success_mock() -> MagicMock:
    return MagicMock(name='on_success_mock')


@pytest.fixture(name='on_error_mock')
def _on_error_mock() -> MagicMock:
    return MagicMock(name='on_error_mock')


@pytest.fixture(name='get_wrapped_smolagents_tool_mock')
def _get_wrapped_smolagents_tool_mock() -> Iterator[MagicMock]:
    with patch.object(agent_factory_module, 'get_wrapped_smolagents_tool') as mock:
        yield mock


class TestGetWrappedSmolagentsTool:
    def test_should_return_original_tool_if_no_callbacks(self, test_tool: TestTool):
        wrapped = get_wrapped_smolagents_tool(test_tool, None)
        assert wrapped is test_tool

    def test_should_not_modify_original_tool(
        self,
        test_tool: TestTool,
        on_before_call_mock: MagicMock
    ):
        original_forward_fn = test_tool.forward
        original_name = test_tool.name
        original_description = test_tool.description
        original_inputs = test_tool.inputs
        original_output_type = test_tool.output_type
        get_wrapped_smolagents_tool(test_tool, ToolCallbacks(
            on_before_call=on_before_call_mock
        ))
        assert test_tool.forward == original_forward_fn
        assert test_tool.name == original_name
        assert test_tool.description == original_description
        assert test_tool.inputs == original_inputs
        assert test_tool.output_type == original_output_type

    def test_should_pass_on_call_to_tool(
        self,
        test_tool: TestTool,
        on_before_call_mock: MagicMock
    ):
        wrapped = get_wrapped_smolagents_tool(test_tool, ToolCallbacks(
            on_before_call=on_before_call_mock
        ))
        wrapped('test', kw_1='value_1')
        test_tool.forward_mock.assert_called_with('test', kw_1='value_1')

    def test_should_call_before_and_success_callback(
        self,
        test_tool: TestTool,
        on_before_call_mock: MagicMock,
        on_success_mock: MagicMock,
        on_error_mock: MagicMock
    ):
        wrapped = get_wrapped_smolagents_tool(test_tool, ToolCallbacks(
            on_before_call=on_before_call_mock,
            on_success=on_success_mock,
            on_error=on_error_mock
        ))
        wrapped('test', kw_1='value_1')
        expected_tool_call = ToolCall(
            tool=test_tool,
            args=('test',),
            kwargs={'kw_1': 'value_1'}
        )
        on_before_call_mock.assert_called_with(expected_tool_call)
        on_success_mock.assert_called_with(expected_tool_call)
        on_error_mock.assert_not_called()

    def test_should_call_error_callback_if_forward_function_raises_exception(
        self,
        test_tool: TestTool,
        on_before_call_mock: MagicMock,
        on_success_mock: MagicMock,
        on_error_mock: MagicMock
    ):
        test_tool.forward_mock.side_effect = RuntimeError('test')
        wrapped = get_wrapped_smolagents_tool(test_tool, ToolCallbacks(
            on_before_call=on_before_call_mock,
            on_success=on_success_mock,
            on_error=on_error_mock
        ))
        with pytest.raises(RuntimeError):
            wrapped('test', kw_1='value_1')
        expected_tool_call = ToolCall(
            tool=test_tool,
            args=('test',),
            kwargs={'kw_1': 'value_1'}
        )
        on_before_call_mock.assert_called_with(expected_tool_call)
        on_success_mock.assert_not_called()
        on_error_mock.assert_called_with(expected_tool_call)


class TestGetWrappedSmolagentsTools:
    def test_should_return_wrapped_tools(
        self,
        test_tool: TestTool,
        on_before_call_mock: MagicMock,
        get_wrapped_smolagents_tool_mock: MagicMock
    ):
        tool_callbacks = ToolCallbacks(
            on_before_call=on_before_call_mock,
        )
        wrapped = get_wrapped_smolagents_tools([test_tool], tool_callbacks)
        assert wrapped == [
            get_wrapped_smolagents_tool_mock.return_value
        ]
        get_wrapped_smolagents_tool_mock.assert_called_with(
            test_tool,
            tool_callbacks=tool_callbacks
        )


class TestGetChainedToolCallbacks:
    def test_should_call_multiple_on_before_call_callbacks(self):
        callback_mocks = [MagicMock(), MagicMock()]
        chained_tool_callbacks = get_chained_tool_callbacks([
            ToolCallbacks(on_before_call=callback_mocks[0]),
            ToolCallbacks(on_before_call=callback_mocks[1]),
            ToolCallbacks()
        ])
        assert chained_tool_callbacks.on_before_call is not None
        chained_tool_callbacks.on_before_call(TOOL_CALL_1)
        for mock in callback_mocks:
            mock.assert_called()

    def test_should_call_multiple_on_success_callbacks(self):
        callback_mocks = [MagicMock(), MagicMock()]
        chained_tool_callbacks = get_chained_tool_callbacks([
            ToolCallbacks(on_success=callback_mocks[0]),
            ToolCallbacks(on_success=callback_mocks[1]),
            ToolCallbacks()
        ])
        assert chained_tool_callbacks.on_success is not None
        chained_tool_callbacks.on_success(TOOL_CALL_1)
        for mock in callback_mocks:
            mock.assert_called()

    def test_should_call_multiple_on_error_callbacks(self):
        callback_mocks = [MagicMock(), MagicMock()]
        chained_tool_callbacks = get_chained_tool_callbacks([
            ToolCallbacks(on_error=callback_mocks[0]),
            ToolCallbacks(on_error=callback_mocks[1]),
            ToolCallbacks()
        ])
        assert chained_tool_callbacks.on_error is not None
        chained_tool_callbacks.on_error(TOOL_CALL_1)
        for mock in callback_mocks:
            mock.assert_called()
