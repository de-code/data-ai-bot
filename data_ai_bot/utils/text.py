from typing import Any


def get_truncated_with_ellipsis(s: str, max_length: int) -> str:
    return s if len(s) <= max_length else s[:max_length - 3] + '...'


def get_markdown_for_agent_response_message(
    agent_response_message: Any
) -> str:
    if isinstance(agent_response_message, list):
        if not agent_response_message:
            return 'Empty list'
        return '\n'.join(f'- {str(item)}' for item in agent_response_message)
    text = str(agent_response_message)
    return text if text else 'Empty response'
