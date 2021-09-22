from .loop import run
from .config import Config


def main():
    config = Config()
    config.load()
    run(config)
