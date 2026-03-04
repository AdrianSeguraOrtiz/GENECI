from rich import print

from geneci.cli.app import app
from geneci.config import HEADER


def main() -> None:
    print(HEADER)
    app()


if __name__ == "__main__":
    main()
