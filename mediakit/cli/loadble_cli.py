from mediakit.cli.loadble_cli_store import LoadableCLIStore
from threading import Thread
from time import sleep

from mediakit.cli.screen import screen, ContentCategories


class LoadableCLI:
    def __init__(self, store: LoadableCLIStore):
        self.store = store

    def mark_as_loading(self, is_loading: bool):
        self.store.is_loading = is_loading

        if is_loading:
            self._show_loading_label()
        else:
            self._remove_loading_label()

    def _show_loading_label(self):
        self.store.loading_label = screen.append_content(
            "\nLoading video.\n\n", ContentCategories.INFO
        )

        def run_loading_animation():
            current_total_dots_displayed = 0

            while self.store.is_loading:
                current_total_dots_displayed = (current_total_dots_displayed + 1) % 4

                screen.update_content(
                    self.store.loading_label,
                    "\nLoading video" + "." * current_total_dots_displayed + "\n\n",
                )

                sleep(0.4)

        Thread(target=run_loading_animation).start()

    def _remove_loading_label(self):
        if self.store.loading_label is not None:
            screen.remove_content(self.store.loading_label)

        self.store.loading_label = None
        self.store.is_loading = False
