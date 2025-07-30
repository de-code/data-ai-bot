def get_truncated_with_ellipsis(s: str, max_length: int) -> str:
    return s if len(s) <= max_length else s[:max_length - 3] + '...'
