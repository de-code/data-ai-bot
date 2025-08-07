from typing import Iterator
from unittest.mock import MagicMock, call, patch

import pytest
import smolagents  # type: ignore

import data_ai_bot.agent_factory as agent_factory_module
from data_ai_bot.agent_factory import (
    SmolAgentsAgentFactory,
    SmolAgentsManagedAgentFactory,
    ToolCall,
    ToolCallEvent,
    get_chained_tool_call_event_handlers,
    get_wrapped_smolagents_tool,
    get_wrapped_smolagents_tools
)


TEST_TOOL_NAME = 'test_tool_1'


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
    tool_name=TEST_TOOL_NAME,
    tool=TestTool(),
    args=['arg_1'],
    kwargs={'kw_1': 'value_1'}
)


TOOL_CALL_EVENT_1 = ToolCallEvent(
    event_name='success',
    tool_call=TOOL_CALL_1
)


@pytest.fixture(name='test_tool')
def _tool_mock() -> TestTool:
    return TestTool()


@pytest.fixture(name='tool_call_event_handler_mock')
def _tool_event_call_handler_mock() -> MagicMock:
    return MagicMock(name='tool_call_event_handler_mock')


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
        tool_call_event_handler_mock: MagicMock
    ):
        original_forward_fn = test_tool.forward
        original_name = test_tool.name
        original_description = test_tool.description
        original_inputs = test_tool.inputs
        original_output_type = test_tool.output_type
        get_wrapped_smolagents_tool(
            test_tool,
            tool_call_event_handler=tool_call_event_handler_mock
        )
        assert test_tool.forward == original_forward_fn
        assert test_tool.name == original_name
        assert test_tool.description == original_description
        assert test_tool.inputs == original_inputs
        assert test_tool.output_type == original_output_type

    def test_should_pass_on_call_to_tool(
        self,
        test_tool: TestTool,
        tool_call_event_handler_mock: MagicMock
    ):
        wrapped = get_wrapped_smolagents_tool(
            test_tool,
            tool_call_event_handler=tool_call_event_handler_mock
        )
        wrapped('test', kw_1='value_1')
        test_tool.forward_mock.assert_called_with('test', kw_1='value_1')

    def test_should_emit_before_and_success_events(
        self,
        test_tool: TestTool,
        tool_call_event_handler_mock: MagicMock
    ):
        wrapped = get_wrapped_smolagents_tool(
            test_tool,
            tool_call_event_handler=tool_call_event_handler_mock
        )
        wrapped('test', kw_1='value_1')
        expected_tool_call = ToolCall(
            tool_name=test_tool.name,
            tool=test_tool,
            args=('test',),
            kwargs={'kw_1': 'value_1'}
        )
        tool_call_event_handler_mock.assert_has_calls([
            call(ToolCallEvent(event_name='before_call', tool_call=expected_tool_call)),
            call(ToolCallEvent(event_name='success', tool_call=expected_tool_call))
        ])

    def test_should_call_error_callback_if_forward_function_raises_exception(
        self,
        test_tool: TestTool,
        tool_call_event_handler_mock: MagicMock
    ):
        test_tool.forward_mock.side_effect = RuntimeError('test')
        wrapped = get_wrapped_smolagents_tool(
            test_tool,
            tool_call_event_handler=tool_call_event_handler_mock
        )
        with pytest.raises(RuntimeError):
            wrapped('test', kw_1='value_1')
        expected_tool_call = ToolCall(
            tool_name=test_tool.name,
            tool=test_tool,
            args=('test',),
            kwargs={'kw_1': 'value_1'}
        )
        tool_call_event_handler_mock.assert_has_calls([
            call(ToolCallEvent(event_name='before_call', tool_call=expected_tool_call)),
            call(ToolCallEvent(event_name='error', tool_call=expected_tool_call))
        ])


class TestGetWrappedSmolagentsTools:
    def test_should_return_wrapped_tools(
        self,
        test_tool: TestTool,
        tool_call_event_handler_mock: MagicMock,
        get_wrapped_smolagents_tool_mock: MagicMock
    ):
        wrapped = get_wrapped_smolagents_tools(
            [test_tool],
            tool_call_event_handler=tool_call_event_handler_mock
        )
        assert wrapped == [
            get_wrapped_smolagents_tool_mock.return_value
        ]
        get_wrapped_smolagents_tool_mock.assert_called_with(
            test_tool,
            tool_call_event_handler=tool_call_event_handler_mock
        )


class TestGetChainedToolCallEventHandlers:
    def test_should_call_multiple_handlers(self):
        handlers = [MagicMock(), MagicMock()]
        chained_handlers = get_chained_tool_call_event_handlers(handlers)
        chained_handlers(TOOL_CALL_EVENT_1)
        for handler in handlers:
            handler.assert_called_with(TOOL_CALL_EVENT_1)


class TestSmolAgentsAgentFactory:
    def test_should_create_simple_tool_agent(
        self,
        test_tool: TestTool
    ):
        agent_factory = SmolAgentsAgentFactory(
            model=MagicMock(name='model'),
            tools=[test_tool]
        )
        agent = agent_factory()
        assert agent is not None
        assert isinstance(agent, smolagents.ToolCallingAgent)
        assert agent.model == agent_factory.model
        assert agent.tools

    def test_should_create_agent_with_managed_agents(
        self,
        test_tool: TestTool
    ):
        managed_agent = MagicMock(name='managed_agent_1')
        managed_agent.name = 'managed_agent_1'
        managed_agent_factory = MagicMock(name='managed_agent_factory_1')
        managed_agent_factory.return_value = managed_agent
        tool_call_event_handler = MagicMock(name='tool_call_event_handler')
        agent_factory = SmolAgentsAgentFactory(
            model=MagicMock(name='model'),
            tools=[test_tool],
            managed_agent_factories=[managed_agent_factory]
        )
        agent = agent_factory(
            tool_call_event_handler=tool_call_event_handler
        )
        assert agent.managed_agents == {
            'managed_agent_1': managed_agent
        }
        managed_agent_factory.assert_called_once_with(
            tool_call_event_handler=tool_call_event_handler
        )


class TestSmolAgentsManagedAgentFactory:
    def test_should_create_simple_managed_tool_agent(
        self,
        test_tool: TestTool
    ):
        agent_factory = SmolAgentsManagedAgentFactory(
            name='managed_agent_1',
            description='Managed Agent 1',
            model=MagicMock(name='model'),
            tools=[test_tool]
        )
        agent = agent_factory()
        assert agent is not None
        assert isinstance(agent, smolagents.ToolCallingAgent)
        assert agent.name == 'managed_agent_1'
        assert agent.description == 'Managed Agent 1'
