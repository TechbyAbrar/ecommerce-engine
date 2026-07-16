from urllib.request import urlopen
from urllib.error import URLError
import sys

HEALTH_URL = "http://127.0.0.1:8000/health"


def main() -> None:
    try:
        response = urlopen(HEALTH_URL, timeout=5)

        if response.status == 200:
            sys.exit(0)

    except URLError:
        pass
    except Exception:
        pass

    sys.exit(1)


if __name__ == "__main__":
    main()