

from dataclasses import dataclass
import logging
import re
import textwrap
import time
from typing import Iterable, Mapping, Optional, Sequence, TypedDict, cast

from markdown_to_mrkdwn import SlackMarkdownConverter  # type: ignore

import slack_bolt


LOGGER = logging.getLogger(__name__)


DEFAULT_MAX_BLOCK_LENGTH = 3000


CODE_BLOCK_RE = re.compile(
    r'(```([^\n]*)\n(.*?\n)```)',
    re.DOTALL
)


class BlockTextTypedDict(TypedDict):
    type: str  # e.g. 'mrkdwn'
    text: str


class BlockTypedDict(TypedDict):
    type: str  # e.g. 'section'
    text: BlockTextTypedDict


@dataclass(frozen=True)
class SlackMessageEvent:
    user: str
    text: str
    ts: str
    thread_ts: str
    channel: str
    previous_messages: Sequence[str]
    channel_type: Optional[str] = None


def get_slack_message_event_from_event_dict(
    app: slack_bolt.App,
    event: dict
) -> SlackMessageEvent:
    message = event.get('message', event)
    thread_ts = message.get('thread_ts')
    previous_message_dict_list: Sequence[dict] = []
    if thread_ts:
        result = app.client.conversations_replies(
            channel=event['channel'],
            ts=thread_ts
        )
        previous_message_dict_list = cast(Sequence[dict], result.get('messages', []))
    return SlackMessageEvent(
        user=message['user'],
        text=message['text'],
        ts=message['ts'],
        thread_ts=thread_ts or message['ts'],
        channel=event['channel'],
        channel_type=event.get('channel_type'),
        previous_messages=[
            message['text']
            for message in previous_message_dict_list
            if message['ts'] != event['ts']
        ]
    )


def get_message_age_in_seconds_from_event_dict(
    event: dict
) -> float:
    return time.time() - float(event['ts'])


def get_slack_mrkdwn_for_markdown(markdown: str) -> str:
    return SlackMarkdownConverter().convert(markdown)


def iter_split_long_line(text: str, max_length: int) -> Iterable[str]:
    if len(text) <= max_length:
        yield text
    else:
        yield from textwrap.wrap(
            text,
            width=max_length,
            break_long_words=False,
            replace_whitespace=False
        )


def iter_split_long_paragraph(paragraph: str, max_length: int) -> Iterable[str]:
    lines = paragraph.split('\n')
    chunk = ''
    for line in lines:
        sep = '\n' if chunk else ''
        new_chunk = chunk + sep + line if chunk else line
        if len(new_chunk) <= max_length:
            chunk = new_chunk
        else:
            if chunk:
                yield chunk
            if len(line) <= max_length:
                chunk = line
            else:
                yield from iter_split_long_line(line, max_length)
                chunk = ''
    if chunk:
        yield chunk


def iter_split_noncode_mrkdwn(noncode: str, max_length: int) -> Iterable[str]:
    # Greedy chunk at paragraph level, fallback to lines, fallback to words
    if len(noncode) <= max_length:
        yield noncode
        return
    paragraphs = noncode.split('\n\n')
    chunk = ''
    for para in paragraphs:
        sep = '\n\n' if chunk else ''
        new_chunk = chunk + sep + para if chunk else para
        if len(new_chunk) <= max_length:
            chunk = new_chunk
        else:
            if chunk:
                yield chunk
            if len(para) > max_length:
                yield from iter_split_long_paragraph(para, max_length)
                chunk = ''
            else:
                chunk = para
    if chunk:
        yield chunk


def iter_split_mrkdwn_segments(mrkdwn: str) -> Iterable[tuple[bool, str]]:
    '''
    Yield tuples: (is_code_block: bool, content: str)
    '''
    pos = 0
    for match in CODE_BLOCK_RE.finditer(mrkdwn):
        LOGGER.debug('match: %r', match)
        start, end = match.span()
        if start > pos:
            yield (False, mrkdwn[pos:start])
        yield (True, match.group(0))
        pos = end
    if pos < len(mrkdwn):
        yield (False, mrkdwn[pos:])


def iter_split_mrkdwn(mrkdwn: str, max_length: int) -> Iterable[str]:
    '''
    Yields chunks of mrkdwn text, never splitting code blocks.
    '''
    current_chunk = ''
    for is_code, segment in iter_split_mrkdwn_segments(mrkdwn):
        if is_code:
            if current_chunk:
                yield from iter_split_noncode_mrkdwn(current_chunk, max_length)
                current_chunk = ''
            yield segment
        else:
            current_chunk += segment.rstrip()
    if current_chunk:
        yield from iter_split_noncode_mrkdwn(current_chunk, max_length)


def get_slack_blocks_for_mrkdwn(
    mrkdwn: str,
    max_block_length: int = DEFAULT_MAX_BLOCK_LENGTH
) -> Sequence[BlockTypedDict]:
    return [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': block_mrkdwn
            }
        }
        for block_mrkdwn in iter_split_mrkdwn(mrkdwn, max_length=max_block_length)
    ]


class FileTypedDict(TypedDict):
    filename: str
    content: bytes


FILE_EXT_BY_LANGUAGE: Mapping[str, str] = {
    'python': 'py',
    'text': 'txt'
}


def get_file_dict_from_code_block(
    code_block: str,
    file_no: int
) -> FileTypedDict:
    match = re.match(CODE_BLOCK_RE, code_block)
    if match is None:
        raise ValueError(f'Invalid code block: {repr(code_block)}')
    code_language = match.group(2)
    code_content = match.group(3)
    file_ext = FILE_EXT_BY_LANGUAGE.get(code_language or 'text', code_language)
    file_dict: FileTypedDict = {
        'filename': f'file_{file_no}.{file_ext}',
        'content': code_content.encode('utf-8')
    }
    return file_dict


def get_replacement_block_and_file_for_too_long_code_block(
    too_long_code_block: str,
    file_no: int
) -> tuple[BlockTypedDict, FileTypedDict]:
    file_dict: FileTypedDict = get_file_dict_from_code_block(
        too_long_code_block,
        file_no=file_no
    )
    filename = file_dict['filename']
    block: BlockTypedDict = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': f'See `{filename}`'
        }
    }
    return block, file_dict


def get_slack_blocks_and_files_for_mrkdwn(
    mrkdwn: str,
    max_block_length: int = DEFAULT_MAX_BLOCK_LENGTH
) -> tuple[Sequence[BlockTypedDict], Sequence[FileTypedDict]]:
    candidate_blocks = get_slack_blocks_for_mrkdwn(mrkdwn, max_block_length=max_block_length)
    files: list[FileTypedDict] = []
    final_blocks = []
    for block in candidate_blocks:
        block_text = block['text']['text']
        if len(block_text) >= max_block_length:
            final_block, file = get_replacement_block_and_file_for_too_long_code_block(
                block_text,
                1 + len(files)
            )
            final_blocks.append(final_block)
            files.append(file)
        else:
            final_blocks.append(block)
    return final_blocks, files
