from clint.textui.cols import console_width


class Content:
    def __init__(self, index_on_screen, inner_text=''):
        self.index_on_screen = index_on_screen
        self.inner_text = inner_text


class Screen:
    def __init__(self):
        self.contents = []

    def append_content(self, content_text):
        index_on_screen = len(self.contents)

        new_content = Content(index_on_screen, content_text)

        self.contents.append(new_content)
        self._render_content(new_content)

        return new_content

    def update_content(self, content, new_content_text):
        content.inner_text = new_content_text

        self._rerender_contents_starting_at(content)

    def clear_lines(self, number_of_lines_to_clear):
        clear_expression = (
            '\033[A'
            + ' ' * self.get_console_width()
            + '\033[A\n'
        )

        print(clear_expression * number_of_lines_to_clear, end='')

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

        self.prompt_message = self.append_content(message)

        while True:
            entry = input()

            if not case_sensitive:
                entry = entry.lower()

            valid_entry = (
                (entry in valid_inputs if len(valid_inputs) > 0 else True)
                and entry not in invalid_inputs
            )

            if valid_entry:
                return entry
            else:
                self._erase_prompt_entry()

    def _render_content(self, content):
        print(content.inner_text, end='')

    def _clear_lines_starting_at(self, content):
        lines_to_clear = 0
        for i in range(content.index_on_screen, len(self.contents)):
            content = self.contents[i]
            lines_occupied = content.inner_text.count('\n')
            lines_to_clear += lines_occupied

        self.clear_lines(lines_to_clear)

    def _rerender_contents_starting_at(self, content):
        self._clear_lines_starting_at(content)

        for i in range(content.index_on_screen, len(self.contents)):
            self._render_content(self.contents[i])

    def _erase_prompt_entry(self):
        self.clear_lines(1) # clear new line created by pressing enter on input()
        self._rerender_contents_starting_at(self.prompt_message)
