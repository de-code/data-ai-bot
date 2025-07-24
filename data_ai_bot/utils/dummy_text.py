import textwrap


# 447 characters
DUMMY_TEXT_1 = textwrap.dedent(
    '''
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
    ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco
    laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in
    voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat
    non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
    '''
).strip().replace('\n', ' ')


DUMMY_TEXT_4K = '\n\n'.join([DUMMY_TEXT_1] * 9)
