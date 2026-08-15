import os
import sys
from streamlit.web.cli import main


def resource_path(path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, path)

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)


if __name__ == "__main__":
    os.chdir(resource_path("."))

    sys.argv = [
        "streamlit",
        "run",
        resource_path("app.py"),
        "--global.developmentMode=false",
    ]

    main()