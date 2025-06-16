from pathlib import Path


def version() -> str:
    return (Path(__file__).parent / "version").read_text().strip()
