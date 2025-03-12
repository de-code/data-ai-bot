from data_ai_bot.tools.sources.static import StaticContentTool


class TestStaticContentTool:
    def test_should_return_provided_content(self):
        tool = StaticContentTool(
            name='name_1',
            description='description_1',
            content='content_1',
            output_type='string'
        )
        assert tool.forward() == 'content_1'
