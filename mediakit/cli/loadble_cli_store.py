from mediakit.cli.screen import Content


class LoadableCLIStore:
    def __init__(self):
        self.LOADING_UI_UPDATE_INTERVAL = 0.4

        self.is_loading: bool = False
        self.loading_label: Content = None

    def reset(self):
        self.is_loading: bool = False
        self.loading_label: Content = None
