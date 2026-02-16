from geneci.cli.app import app
from geneci.config import HEADER
from rich import print


def main() -> None:
    print(HEADER)
    app()


if __name__ == "__main__":
    main()
