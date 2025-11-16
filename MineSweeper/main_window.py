##############################################################################################################################
# coding=utf-8
#
# main_window.py
#   -- MineSweeper game main window
#
# >> based on code by Martin Fitzpatrick
#    @ https://github.com/pythonguis/pythonguis-examples/tree/master/pyside6/demos/minesweeper
#
# Copyright (c) 2025 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-11-12"
__updated__ = "2025-11-16"

import random
import sys
import time
from sys import path
path.append("/home/marksa/git/Python/utils")
from mhsLogging import *
from constants import *
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from game_square import GameSquare


# noinspection PyAttributeOutsideInit
class MineSweeperUI(QMainWindow):
    def __init__(self, p_gridlen:int=DEFAULT_GRID_LEN, p_nmines:int=DEFAULT_NUM_MINES):
        super().__init__()
        self.lgr = log_control.get_logger()
        self.lgr.info(f"Initializing {MineSweeperUI.__name__}")

        self.grid_size = p_gridlen if MIN_GRID_LEN <= p_gridlen <= MAX_GRID_LEN else DEFAULT_GRID_LEN
        num_squares = self.grid_size**2
        self.num_mines = p_nmines if (num_squares//3) >= p_nmines >= (num_squares//8) else (num_squares//6)
        self.lgr.info(f"Grid length = {self.grid_size}, num squares = {num_squares}, num mines = {self.num_mines}")

        main_widget = QWidget()
        self.status = Status.READY

        self.mines = QLabel()
        self.mines.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        f = self.mines.font()
        f.setPointSize(24)
        f.setWeight(QFont.Weight.Thin)
        self.mines.setFont(f)

        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.clock.setFont(f)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)  # 1 second timer

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

        self.result = QLabel()
        self.result.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        horiz_layout.addWidget(self.result)

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

        self.setWindowTitle("BugFinder Game")
        self.setGeometry(306, 170, self.width(), self.height())
        self.show()

    def reset_game(self):
        self.lgr.info("\n\nStarting new Game!")
        self.total_empty = self.grid_size**2 - self.num_mines
        self.total_flags = 0
        self.total_revealed = 0
        self.lgr.info(f"grid dim = {self.grid_size}, num mines = {self.num_mines}, empty squares = {self.total_empty}")
        self.mines.setText("%03d" % self.num_mines)
        self.clock.setText("000")
        self.result.setPixmap(QPixmap.fromImage(IMG_PLAY))

    def init_map(self):
        """Add PositionSquares to the map"""
        for x in range(0, self.grid_size):
            for y in range(0, self.grid_size):
                w = GameSquare(x, y, self)
                self.grid.addWidget(w, y, x)
                w.clicked.connect(self.start_game)
                # signal to handle expansion
                w.expandable.connect(self.expand_reveal)
                w.ohno.connect(self.game_loss)

    def reset_map(self):
        # clear all mines
        for x in range(0, self.grid_size):
            for y in range(0, self.grid_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.reset()

        # add mines
        positions = []
        while len(positions) < self.num_mines:
            x, y = (
                random.randint(0, self.grid_size-1),
                random.randint(0, self.grid_size-1),
            )
            if (x, y) not in positions:
                w = self.grid.itemAtPosition(y, x).widget()
                w.is_mine = True
                positions.append((x, y))

        def get_adjacency_n(px, py):
            posns = self.get_surrounding(px, py)
            n_mines = sum(1 if ww.is_mine else 0 for ww in posns)

            return n_mines

        # add adjacency values
        for x in range(0, self.grid_size):
            for y in range(0, self.grid_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.adjacent_n = get_adjacency_n(x, y)

        # place a starting marker
        while True:
            x, y = (
                random.randint(0, self.grid_size-1),
                random.randint(0, self.grid_size-1),
            )
            # don't start on a mine
            if (x, y) not in positions:
                w = self.grid.itemAtPosition(y, x).widget()
                w.is_start = True

                # reveal all positions around this if there are no mines
                for w in self.get_surrounding(x, y):
                    if not w.is_mine:
                        w.click()
                break

    def get_surrounding(self, x, y):
        positions = []
        for xi in range(max(0, x - 1), min(x + 2, self.grid_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.grid_size)):
                positions.append(self.grid.itemAtPosition(yi, xi).widget())
        return positions

    # restart after a completed game
    def button_pressed(self):
        if self.status == Status.SUCCESS or self.status == Status.FAILED:
            self.update_status(Status.READY)
            self.reset_game()
            self.reset_map()

    def reveal_map(self):
        for x in range(0, self.grid_size):
            for y in range(0, self.grid_size):
                self.grid.itemAtPosition(y, x).widget().reveal()

    def expand_reveal(self, x, y):
        for xi in range(max(0, x - 1), min(x + 2, self.grid_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.grid_size)):
                w = self.grid.itemAtPosition(yi, xi).widget()
                if not w.is_mine:
                    w.click()

    def clear_check(self, x, y):
        """Make sure no adjacent squares are erroneous flags and all adjacent mines are flagged."""
        for xi in range(max(0, x - 1), min(x + 2, self.grid_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.grid_size)):
                w = self.grid.itemAtPosition(yi, xi).widget()
                if w.is_flagged and not w.is_mine:
                    self.lgr.info(f"ERRONEOUS flag at square[{xi},{yi}]!")
                    w.bad_flag = True
                    return False
                if w.is_mine and not w.is_flagged:
                    self.lgr.info(f"MISSING flag at square[{xi},{yi}]!")
                    w.missing_flag = True
                    return False
        return True

    def start_game(self):
        if self.status != Status.PLAYING:
            # first click
            self.update_status(Status.PLAYING)
            # start timer
            self.timer_start_numsecs = int(time.time())

    def update_status(self, status):
        self.status = status
        self.button.setIcon(QIcon(STATUS_ICONS[self.status]))

    def update_clock(self):
        if self.status == Status.PLAYING:
            if self.isMinimized(): # pause the timer when minimized
                self.timer_start_numsecs += 1
            num_secs = int(time.time()) - self.timer_start_numsecs
            # self.lgr.info(f"num secs = {num_secs}")
            self.clock.setText("%03d" % num_secs)

    def game_loss(self):
        self.update_status(Status.FAILED)
        self.result.setPixmap(QPixmap.fromImage(IMG_LOSE))
        self.reveal_map()
        self.lgr.info("FAILED! :(\n\n")

    def game_win(self):
        self.update_status(Status.SUCCESS)
        self.result.setPixmap(QPixmap.fromImage(IMG_WIN))
        self.lgr.info("Victory!")

# END class MineSweeperUI


log_control = MhsLogger("MineSweeper", con_level = DEFAULT_LOG_LEVEL)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MineSweeperUI()
    app.exec()
    log_control.info("Exit game.")
