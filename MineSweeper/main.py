##############################################################################################################################
# coding=utf-8
#
# main.py
#   -- MineSweeper game main window
#
# >> based on code by Martin Fitzpatrick @ https://github.com/pythonguis/pythonguis-examples
#
# Copyright (c) 2025 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-11-12"
__updated__ = "2025-11-13"

import random
import sys
import time
from sys import path
path.append("/home/marksa/git/Python/utils")
from mhsLogging import *
from constants import (
    IMG_BOMB,
    IMG_CLOCK,
    LEVELS,
    STATUS_ICONS,
    Status,
)
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from widgets import PositionSquare


# noinspection PyAttributeOutsideInit
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lgr = log_control.get_logger()
        self.lgr.info("Initializing MainWindow")

        self.b_size, self.num_mines = LEVELS[1]

        main_widget = QWidget()
        self.status = Status.READY

        self.mines = QLabel()
        self.mines.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        f = self.mines.font()
        f.setPointSize(24)
        f.setWeight(QFont.Weight.Thin)
        self.mines.setFont(f)
        self.clock.setFont(f)

        self._timer = QTimer()
        self._timer.timeout.connect(self.update_timer)
        self._timer.start(1000)  # 1 second timer

        self.button = QPushButton()
        self.button.setFixedSize(QSize(32, 32))
        self.button.setIconSize(QSize(32, 32))
        self.button.setIcon(QIcon("./images/smiley.png"))
        self.button.setFlat(True)
        self.button.pressed.connect(self.button_pressed)

        horiz_layout = QHBoxLayout()
        label = QLabel()
        label.setPixmap(QPixmap.fromImage(IMG_BOMB))
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        horiz_layout.addWidget(label)

        horiz_layout.addWidget(self.mines)
        horiz_layout.addWidget(self.button)
        horiz_layout.addWidget(self.clock)

        label = QLabel()
        label.setPixmap(QPixmap.fromImage(IMG_CLOCK))
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        horiz_layout.addWidget(label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(horiz_layout)

        self.grid = QGridLayout()
        self.grid.setSpacing(5)

        main_layout.addLayout(self.grid)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.reset_game()
        self.init_map()
        self.reset_map()
        self.update_status(Status.READY)

        self.setWindowTitle("MoonSweeper")
        self.show()

    def reset_game(self):
        self.lgr.info("\n\nStarting new Game!")
        self.total_empty = self.b_size**2 - self.num_mines
        self.total_flags = 0
        self.total_revealed = 0
        self.lgr.info(f"grid dim = {self.b_size}, num mines = {self.num_mines}, empty squares = {self.total_empty}")
        self.mines.setText("%03d" % self.num_mines)
        self.clock.setText("000")

    def init_map(self):
        """Add PositionSquares to the map"""
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = PositionSquare(x, y, self)
                self.grid.addWidget(w, y, x)
                # Connect signal to handle expansion.
                w.clicked.connect(self.trigger_start)
                w.expandable.connect(self.expand_reveal)
                w.ohno.connect(self.game_over)

    def reset_map(self):
        # Clear all mine positions
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.reset()

        # Add mines to the positions
        positions = []
        while len(positions) < self.num_mines:
            x, y = (
                random.randint(0, self.b_size - 1),
                random.randint(0, self.b_size - 1),
            )
            if (x, y) not in positions:
                w = self.grid.itemAtPosition(y, x).widget()
                w.is_mine = True
                positions.append((x, y))

        def get_adjacency_n(px, py):
            posns = self.get_surrounding(px, py)
            n_mines = sum(1 if ww.is_mine else 0 for ww in posns)

            return n_mines

        # Add adjacencies to the positions
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.adjacent_n = get_adjacency_n(x, y)

        # Place starting marker
        while True:
            x, y = (
                random.randint(0, self.b_size - 1),
                random.randint(0, self.b_size - 1),
            )
            # We don't want to start on a mine.
            if (x, y) not in positions:
                w = self.grid.itemAtPosition(y, x).widget()
                w.is_start = True

                # Reveal all positions around this, if they are not mines either.
                for w in self.get_surrounding(x, y):
                    if not w.is_mine:
                        w.click()
                break

    def get_surrounding(self, x, y):
        positions = []
        for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
                positions.append(self.grid.itemAtPosition(yi, xi).widget())
        return positions

    # restart the game
    def button_pressed(self):
        if self.status == Status.SUCCESS or self.status == Status.FAILED:
            self.update_status(Status.READY)
            self.reset_game()
            self.reset_map()

    def reveal_map(self):
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.reveal()

    def expand_reveal(self, x, y):
        for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
                w = self.grid.itemAtPosition(yi, xi).widget()
                if not w.is_mine:
                    w.click()

    def clear_check(self, x, y):
        for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
                w = self.grid.itemAtPosition(yi, xi).widget()
                if w.is_flagged and not w.is_mine:
                    self.lgr.info(f"Erroneous flag at square[{x},{y}]!")
                    return False
        return True

    def trigger_start(self):
        if self.status != Status.PLAYING:
            # First click.
            self.update_status(Status.PLAYING)
            # Start timer.
            self._timer_start_nsecs = int(time.time())

    def update_status(self, status):
        self.status = status
        self.button.setIcon(QIcon(STATUS_ICONS[self.status]))

    def update_timer(self):
        if self.status == Status.PLAYING:
            n_secs = int(time.time()) - self._timer_start_nsecs
            self.clock.setText("%03d" % n_secs)

    def game_over(self):
        self.reveal_map()
        self.update_status(Status.FAILED)


if __name__ == "__main__":
    log_control = MhsLogger("MineSweeperLogger", con_level = DEFAULT_LOG_LEVEL)
    app = QApplication(sys.argv)
    window = MainWindow()
    app.exec()
    log_control.info("Exit game.")
