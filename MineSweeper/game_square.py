##############################################################################################################################
# coding=utf-8
#
# game_square.py
#   -- MineSweeper game squares
#
# >> based on code by Martin Fitzpatrick
#    @ https://github.com/pythonguis/pythonguis-examples/tree/master/pyside6/demos/minesweeper
#
# Copyright (c) 2025 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-11-12"
__updated__ = "2025-11-19"

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QBrush, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QWidget, QMainWindow
from pyasn1_modules.rfc3280 import pds_name

from constants import *


# noinspection PyAttributeOutsideInit
class GameSquare(QWidget):
    expandable = Signal(int, int)
    clicked = Signal()
    ohno = Signal()

    def __init__(self, x, y, p_window:QMainWindow):
        super().__init__()

        self.setFixedSize(QSize(24, 24))
        self.x = x
        self.y = y
        self.main_window = p_window
        self.lgr = self.main_window.lgr

    def reset(self):
        self.is_start = False
        self.is_mine = False
        self.num_adjacent = 0
        self.is_revealed = False
        self.is_flagged = False
        self.bad_flag = False
        self.missing_flag = False
        self.update()

    def paintEvent(self, evt):
        pntr = QPainter(self)
        pntr.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = evt.rect()

        if self.is_revealed or self.is_flagged:
            color = self.palette().color(QPalette.ColorRole.Window)
            outer, inner = color, color
        else:
            outer, inner = QColor("paleturquoise"), QColor("peachpuff")

        pntr.fillRect(rect, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        pntr.setPen(pen)
        pntr.drawRect(rect)

        if self.is_revealed:
            if self.is_start:
                pntr.drawPixmap(rect, QPixmap(IMG_START))

            elif self.bad_flag:
                pntr.drawPixmap(rect, QPixmap(IMG_BAD_FLAG))

            elif self.missing_flag:
                pntr.drawPixmap(rect, QPixmap(IMG_MISSING_FLAG))

            elif self.is_mine:
                pntr.drawPixmap(rect, QPixmap(IMG_BOMB))

            elif self.num_adjacent > 0:
                pen = QPen(SQUARE_COLORS[self.num_adjacent])
                pntr.setPen(pen)
                f = pntr.font()
                f.setBold(True)
                pntr.setFont(f)
                pntr.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, str(self.num_adjacent))

        elif self.is_flagged:
            pntr.drawPixmap(rect, QPixmap(IMG_FLAG))

    def flag(self):
        """Set a new flag or remove the existing flag from this square."""
        if self.is_flagged:
            self.is_flagged = False
            self.main_window.total_flags -= 1
        else:
            self.is_flagged = True
            self.main_window.total_flags += 1
            self.clicked.emit()
        self.update()
        self.lgr.info(f"current num flags = {self.main_window.total_flags}")

    def reveal(self):
        self.is_revealed = True
        self.main_window.total_revealed += 1
        if self.main_window.status == Status.PLAYING:
            self.lgr.debug(f"current num revealed = {self.main_window.total_revealed}")
        self.update()

    def click(self):
        if not self.is_revealed:
            self.reveal()
            if self.num_adjacent == 0:
                self.expandable.emit(self.x, self.y)
        self.clicked.emit()

    def mouseReleaseEvent(self, evt):
        # set or remove flag
        if evt.button() == Qt.MouseButton.RightButton and not self.is_revealed:
            self.flag()
            self.main_window.mines.setText("%03d" % (self.main_window.num_mines - self.main_window.total_flags))

        # clear out adjacent squares
        elif evt.button() == Qt.MouseButton.RightButton and self.is_revealed:
            # make sure NO errors in adjacent squares
            if not self.main_window.clear_check(self.x, self.y):
                self.ohno.emit()
                return
            self.expandable.emit(self.x, self.y)
            self.clicked.emit()

        # reveal this square
        elif evt.button() == Qt.MouseButton.LeftButton:
            if self.is_flagged:
                self.is_flagged = False
                self.main_window.total_flags -= 1
            self.click()
            if self.is_mine:
                self.ohno.emit()
                return

        # see if the game is won
        if self.main_window.total_revealed == self.main_window.total_empty and self.main_window.total_flags == self.main_window.num_mines:
            self.main_window.game_win()
