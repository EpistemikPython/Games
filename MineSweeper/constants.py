##############################################################################################################################
# coding=utf-8
#
# constants.py
#   -- MineSweeper game constants
#
# >> based on code by Martin Fitzpatrick @ https://github.com/pythonguis/pythonguis-examples
#
# Copyright (c) 2025 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-11-12"
__updated__ = "2025-11-13"

from enum import IntEnum
from PySide6.QtGui import (QColor, QImage)

IMG_BOMB = QImage("./images/bug.png")
IMG_FLAG = QImage("./images/flag.png")
IMG_START = QImage("./images/rocket.png")
IMG_CLOCK = QImage("./images/clock-select.png")

NUM_COLORS = {
    1: QColor("#f44336"),
    2: QColor("#9C27B0"),
    3: QColor("#3F51B5"),
    4: QColor("#03A9F4"),
    5: QColor("#00BCD4"),
    6: QColor("#4CAF50"),
    7: QColor("#E91E63"),
    8: QColor("#FF9800"),
}

LEVELS = [(8, 10), (16, 40), (24, 99)]


class Status(IntEnum):
    READY = 0
    PLAYING = 1
    FAILED = 2
    SUCCESS = 3


STATUS_ICONS = {
    Status.READY: "./images/plus.png",
    Status.PLAYING: "./images/smiley.png",
    Status.FAILED: "./images/cross.png",
    Status.SUCCESS: "./images/smiley-lol.png",
}
