##############################################################################################################################
# coding=utf-8
#
# game_square.py
#   -- MineSweeper game squares
#
# >> based on code by Martin Fitzpatrick @ https://github.com/pythonguis/pythonguis-examples
#
# Copyright (c) 2025 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-11-12"
__updated__ = "2025-11-13"

from MineSweeper.constants import Status
# from MineSweeper.main import MainWindow
from constants import (
    IMG_BOMB,
    IMG_FLAG,
    IMG_START,
    NUM_COLORS,
)
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QPainter,
    QPalette,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QWidget, QMainWindow


# noinspection PyAttributeOutsideInit
class GameSquare(QWidget):
    expandable = Signal(int, int)
    clicked = Signal()
    ohno = Signal()

    def __init__(self, x, y, wid:QMainWindow):
        super().__init__()

        self.setFixedSize(QSize(20, 20))
        self.x = x
        self.y = y
        self.main_widget = wid

    def reset(self):
        self.is_start = False
        self.is_mine = False
        self.adjacent_n = 0

        self.is_revealed = False
        self.is_flagged = False

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        r = event.rect()

        if self.is_revealed:
            color = self.palette().color(QPalette.ColorRole.Window)
            outer, inner = color, color
        else:
            outer, inner = Qt.GlobalColor.gray, Qt.GlobalColor.lightGray

        p.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

        if self.is_revealed:
            if self.is_start:
                p.drawPixmap(r, QPixmap(IMG_START))

            elif self.is_mine:
                p.drawPixmap(r, QPixmap(IMG_BOMB))

            elif self.adjacent_n > 0:
                pen = QPen(NUM_COLORS[self.adjacent_n])
                p.setPen(pen)
                f = p.font()
                f.setBold(True)
                p.setFont(f)
                p.drawText(
                    r,
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                    str(self.adjacent_n),
                )

        elif self.is_flagged:
            p.drawPixmap(r, QPixmap(IMG_FLAG))

    def flag(self):
        self.is_flagged = True
        self.main_widget.total_flags += 1
        self.main_widget.lgr.info(f"current num flags = {self.main_widget.total_flags}")
        self.update()
        self.clicked.emit()

    def reveal(self):
        self.is_revealed = True
        self.main_widget.total_revealed += 1
        self.main_widget.lgr.info(f"current num revealed = {self.main_widget.total_revealed}")
        self.update()

    def click(self):
        if not self.is_revealed:
            self.reveal()
            if self.adjacent_n == 0:
                self.expandable.emit(self.x, self.y)

        self.clicked.emit()

    def mouseReleaseEvent(self, e):
        # set flag
        if e.button() == Qt.MouseButton.RightButton and not self.is_revealed and not self.is_flagged:
            self.flag()
            self.main_widget.mines.setText("%03d" % (self.main_widget.num_mines - self.main_widget.total_flags))

        # clear out adjacent squares
        elif e.button() == Qt.MouseButton.RightButton and self.is_revealed:
            # HAVE TO MAKE SURE NO ADJACENT SQUARES ARE ERRONEOUS FLAGS
            if not self.main_widget.clear_check(self.x, self.y):
                self.ohno.emit()
                return
            self.expandable.emit(self.x, self.y)
            self.clicked.emit()

        # reveal this square
        elif e.button() == Qt.MouseButton.LeftButton:
            self.click()
            if self.is_mine:
                self.ohno.emit()
                return

        # see if the game is won
        if self.main_widget.total_revealed == self.main_widget.total_empty and self.main_widget.total_flags == self.main_widget.num_mines:
            self.main_widget.update_status(Status.SUCCESS)
