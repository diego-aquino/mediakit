import sys


class GlobalConfig:
    def __init__(self):
        self.answer_yes_to_all_questions = False
        self.ui_colors_disabled = not sys.stdin.isatty()
        self.batch_file = None
        self.max_downloads_in_parallel = 2


global_config = GlobalConfig()
