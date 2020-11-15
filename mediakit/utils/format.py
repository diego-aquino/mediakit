import re

def limit_text_length(text, limit_of_caracters):
    if len(text) > limit_of_caracters:
        partial_text_with_ellipsis = f'{text[:limit_of_caracters - 3]}...'

        return partial_text_with_ellipsis

    return text

def len_ansi_safe(string):
    ansi_escape_codes_regex = r'\x1b\[[;\d]*[A-Za-z]'

    string_striped_of_ansi_codes = re.sub(
        ansi_escape_codes_regex,
        '',
        string
    )

    return len(string_striped_of_ansi_codes)
