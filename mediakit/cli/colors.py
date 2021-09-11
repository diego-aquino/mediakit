import colorama

from mediakit.globals import global_config


class Colors():
    fore = colorama.Fore
    back = colorama.Back
    style = colorama.Style


class ColoredText():
    def __init__(self, text, fore, back, style):
        self.text = text
        self.fore = fore
        self.back = back
        self.style = style

    def __str__(self):
        return (
            f'{self.fore}{self.back}{self.style}'
            f'{self.text}'
            f'{Colors.style.RESET_ALL}'
        )


def colored(
    *values,
    fore=Colors.fore.RESET,
    back=Colors.back.RESET,
    style=Colors.style.NORMAL,
    sep=' '
):
    joined_text = sep.join(map(
        lambda value: str(value),
        values
    ))

    if global_config.ui_colors_disabled:
        return joined_text

    return str(ColoredText(joined_text, fore, back, style))
