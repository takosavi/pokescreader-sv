import sys
from importlib.resources import as_file, files

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget


def set_window_icon(widget: QWidget) -> None:
    if sys.platform != "win32":
        return
    with as_file(files("pkscrd.app.resources") / "pokescreader.ico") as path:
        widget.setWindowIcon(QIcon(str(path)))
