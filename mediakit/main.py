from .actions.main import get_command_actions


def main():
    for action in get_command_actions():
        action()
