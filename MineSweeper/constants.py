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
__updated__ = "2025-11-25"

from enum import IntEnum
from PySide6.QtGui import QImage, QColor

IMG_MINE         = QImage("images/bug.png")
IMG_FLAG         = QImage("images/bomb.png")
IMG_BAD_FLAG     = QImage("images/mushroom.png")
IMG_MISSING_FLAG = QImage("images/hamburger.png")
IMG_START        = QImage("images/ice-cream-sprinkles.png")
IMG_PLAY         = QImage("images/fruit.png")
IMG_WIN          = QImage("images/cake.png")
IMG_LOSE         = QImage("images/cactus.png")

# for number of adjacent mines
SQUARE_COLORS = {
    1: QColor("tomato"),
    2: QColor("blue"),
    3: QColor("darkgreen"),
    4: QColor("magenta"),
    5: QColor("cyan"),
    6: QColor("darkgoldenrod"),
    7: QColor("darkgrey"),
    8: QColor("black")
}

# length of grid in number of squares
MIN_GRID_LEN     = 8
DEFAULT_GRID_LEN = 16
LARGE_GRID_LEN   = 24
MAX_GRID_LEN     = 32

DEFAULT_NUM_MINES = 66
DEFAULT_SQR_LEN   = 28
DEFAULT_INFO_DIM  = 32
INFO_FONT_PTS     = 24
NUM_ADJ_FONT_PTS  = 16
DEFAULT_SPACING   =  1

class Status(IntEnum):
    READY   = 0
    PLAYING = 1
    FAILED  = 2
    SUCCESS = 3


STATUS_ICONS = {
    Status.READY:   "images/plus.png",
    Status.PLAYING: "images/smiley.png",
    Status.FAILED:  "images/cross.png",
    Status.SUCCESS: "images/smiley-lol.png"
}
