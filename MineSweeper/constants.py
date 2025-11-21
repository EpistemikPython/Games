##############################################################################################################################
# coding=utf-8
#
# constants.py
#   -- MineSweeper game constants
#
# >> based on code by Martin Fitzpatrick
#    @ https://github.com/pythonguis/pythonguis-examples/tree/master/pyside6/demos/minesweeper
#
# Copyright (c) 2025 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-11-12"
__updated__ = "2025-11-20"

from enum import IntEnum
from PySide6.QtGui import QImage, QColor, QColorConstants

IMG_BOMB         = QImage("images/bug.png")
IMG_FLAG         = QImage("images/flag.png")
IMG_BAD_FLAG     = QImage("images/mushroom.png")
IMG_MISSING_FLAG = QImage("images/hamburger.png")
IMG_START        = QImage("images/ice-cream-sprinkles.png")
IMG_PLAY         = QImage("images/fruit.png")
IMG_WIN          = QImage("images/cake.png")
IMG_LOSE         = QImage("images/cactus.png")

SQUARE_COLORS = {
    1: QColor(QColorConstants.Red),
    2: QColor(QColorConstants.Blue),
    3: QColor(QColorConstants.DarkGreen),
    4: QColor(QColorConstants.Magenta),
    5: QColor(QColorConstants.Cyan),
    6: QColor(QColorConstants.DarkYellow),
    7: QColor(QColorConstants.Gray),
    8: QColor(QColorConstants.Black),
}

# length of grid in number of squares
MIN_GRID_LEN     = 8
DEFAULT_GRID_LEN = 16
LARGE_GRID_LEN   = 24
MAX_GRID_LEN     = 32

DEFAULT_NUM_MINES = 66

class Status(IntEnum):
    READY   = 0
    PLAYING = 1
    FAILED  = 2
    SUCCESS = 3


STATUS_ICONS = {
    Status.READY:   "images/plus.png",
    Status.PLAYING: "images/smiley.png",
    Status.FAILED:  "images/cross.png",
    Status.SUCCESS: "images/smiley-lol.png",
}
