import sys
from math import ceil

from clint.textui.cols import console_width

from mediakit.utils.format import len_ansi_safe
from .colors import colored, Colors


class ANSIConsoleExpressions:
    MOVE_CURSOR_ONE_LINE_UP = '\033[A'
    MOVE_CURSOR_TO_BEGGINING_OF_LINE = '\033[0G'
    CLEAR_CHARACTERS_TO_THE_RIGHT_OF_CURSOR = '\033[K'
    CLEAR_LINE = (
        MOVE_CURSOR_TO_BEGGINING_OF_LINE
        + CLEAR_CHARACTERS_TO_THE_RIGHT_OF_CURSOR
    )


class ContentCategories:
    NORMAL = 'NORMAL'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    USER_INPUT = 'USER_INPUT'


class Content:
    def __init__(self, index_on_screen, text, category):
        self.index_on_screen = index_on_screen

        if category == ContentCategories.NORMAL:
            self.category_label = ''
        elif category == ContentCategories.INFO:
            self.category_label = colored('info ', fore=Colors.fore.BLUE)
        elif category == ContentCategories.WARNING:
            self.category_label = colored('warning ', fore=Colors.fore.YELLOW)
        elif category == ContentCategories.ERROR:
            self.category_label = colored('error ', fore=Colors.fore.RED)
        elif category == ContentCategories.USER_INPUT:
            self.category_label = colored('? ', fore=Colors.fore.BLUE)

        self.update_inner_text(text)

    def update_inner_text(self, new_text):
        new_text_stripped_of_leading_newlines = new_text.lstrip('\n')
        number_of_leading_newlines = (
            len(new_text) - len(new_text_stripped_of_leading_newlines)
        )

        self.inner_text = (
            '\n' * number_of_leading_newlines
            + self.category_label
            + new_text_stripped_of_leading_newlines
        )

class Screen:
    def __init__(self):
        self.contents = []
        self.prompt_message = None

    def append_content(self, content_text, category=ContentCategories.NORMAL):
        index_on_screen = len(self.contents)

        new_content = Content(index_on_screen, content_text, category)

        self.contents.append(new_content)
        self._render_content(new_content)

        return new_content

    def update_content(self, content, new_content_text):
        self._clear_lines_starting_at(content)

        content.update_inner_text(new_content_text)

        self._render_contents_starting_at(content)

    def remove_content(self, content):
        index_to_remove_at = content.index_on_screen

        self._clear_lines_starting_at(content)
        self.contents.pop(index_to_remove_at)

        base_index = index_to_remove_at

        for index in range(base_index, len(self.contents)):
            self.contents[index].index_on_screen = index

        needs_to_rerender_contents = (
            len(self.contents) > 0
            and base_index < len(self.contents)
        )

        if needs_to_rerender_contents:
            self._render_contents_starting_at(self.contents[base_index])

    def clear_lines(self, number_of_lines_to_clear):
        clear_expression = (
            ANSIConsoleExpressions.MOVE_CURSOR_ONE_LINE_UP.join(
                [ANSIConsoleExpressions.CLEAR_LINE] * number_of_lines_to_clear
            )
        )

        print(clear_expression, end='', file=sys.stderr)

    def get_console_width(self):
        return console_width({})

    def prompt(
        self,
        message,
        valid_inputs=[],
        invalid_inputs=[],
        case_sensitive=False
    ):
        if not case_sensitive:
            for i in range(len(valid_inputs)):
                valid_inputs[i] = valid_inputs[i].lower()

        valid_inputs = set(valid_inputs)
        invalid_inputs = set(invalid_inputs)

        self.prompt_message = self.append_content(
            message,
            category=ContentCategories.USER_INPUT
        )

        while True:
            entry = input()

            if not case_sensitive:
                entry = entry.lower()

            valid_entry = (
                (entry in valid_inputs if len(valid_inputs) > 0 else True)
                and entry not in invalid_inputs
            )

            if valid_entry:
                return entry, self.prompt_message

            self.erase_prompt_entry(self.prompt_message)

    def erase_prompt_entry(self, prompt):
        lines_occupied_by_entry = 2 # <entry>\n<empty line> -> 2 lines to clear
        self.clear_lines(lines_occupied_by_entry)

        self._clear_lines_starting_at(prompt)
        self._render_contents_starting_at(prompt)

    def _render_content(self, content):
        print(content.inner_text, end='', file=sys.stderr)

    def _clear_lines_starting_at(self, content):
        current_console_width = self.get_console_width()

        texts_to_clear = map(
            lambda content_to_clear: content_to_clear.inner_text,
            self.contents[content.index_on_screen:]
        )

        lines_to_clear = self._count_lines_occupied_by(
            ''.join(texts_to_clear),
            current_console_width
        )

        self.clear_lines(lines_to_clear)

    def _render_contents_starting_at(self, content):
        for i in range(content.index_on_screen, len(self.contents)):
            self._render_content(self.contents[i])

    def _count_lines_occupied_by(self, text, current_console_width):
        lines = text.split('\n')

        lines_occupied = 0
        for i in range(len(lines)):
            line = lines[i]

            lines_occupied += max(
                ceil(len_ansi_safe(line) / current_console_width),
                1
            )

        return lines_occupied

screen = Screen()
