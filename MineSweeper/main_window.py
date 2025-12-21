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
__updated__ = "2025-12-15"

import random
import sys
import time
from sys import path
path.append("/home/marksa/git/Python/utils")
from mhsLogging import *
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from constants import *
from game_square import GameSquare


# noinspection PyAttributeOutsideInit
class MineSweeperUI(QMainWindow):
    def __init__(self, p_gridlen:int=DEFAULT_GRID_LEN, p_nmines:int=DEFAULT_NUM_MINES):
        super().__init__()
        self.status = Status.READY

        self.lgr = log_control.get_logger()
        self.lgr.info(f"Initializing {MineSweeperUI.__name__}({p_gridlen},{p_nmines})")
        # self.lgr.info("Available colors:")
        # for item in QColor.colorNames():
        #     self.lgr.info(f"\t{item}")

        if MIN_GRID_LEN <= p_gridlen <= MAX_GRID_LEN:
            self.grid_size = p_gridlen
        else:
            self.grid_size = DEFAULT_GRID_LEN
            self.lgr.info(f"Illegal grid size parameter '{p_gridlen}'! Using default grid size = {DEFAULT_GRID_LEN}")
        num_squares = self.grid_size**2
        if (num_squares // 3) >= p_nmines >= (num_squares // 8):
            self.num_mines = p_nmines
        else:
            self.num_mines = num_squares // 6
            self.lgr.info(f"Illegal number of mines parameter '{p_nmines}'! Using default number of mines = {self.num_mines}")

        self.mine_counter = QLabel()
        self.mine_counter.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        std_font = self.mine_counter.font()
        std_font.setPointSize(INFO_FONT_PTS)
        # std_font.setWeight(QFont.Weight.Thin)
        self.mine_counter.setFont(std_font)

        self.reset_button = QPushButton()
        self.reset_button.setFixedSize(QSize(DEFAULT_INFO_DIM, DEFAULT_INFO_DIM))
        self.reset_button.setIconSize(QSize(DEFAULT_INFO_DIM, DEFAULT_INFO_DIM))
        self.reset_button.setFlat(True)
        self.reset_button.pressed.connect(self.restart_game)

        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.clock.setFont(std_font)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000) # update each 1 second

        mine_pic = QLabel()
        mine_pic.setPixmap(QPixmap.fromImage(IMG_MINE))
        mine_pic.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.result = QLabel()
        self.result.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        info_layout = QHBoxLayout()
        info_layout.addWidget(mine_pic)
        info_layout.addWidget(self.mine_counter)
        info_layout.addWidget(self.reset_button)
        info_layout.addWidget(self.clock)
        info_layout.addWidget(self.result)

        main_layout = QVBoxLayout()
        main_layout.addLayout(info_layout)
        self.grid = QGridLayout()
        self.grid.setVerticalSpacing(DEFAULT_SPACING)
        self.grid.setHorizontalSpacing(DEFAULT_SPACING) # ?? does nothing unless main window width is modified
        main_layout.addLayout(self.grid)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.reset_game()
        self.init_map()
        self.reset_map()
        self.update_status(Status.READY)
        self.setWindowTitle(f"BugFinder Game:  {self.grid_size}x{self.grid_size} with {self.num_mines} mines.")

        # ?? only way to get the squares closer to each other seems to be to change the main window dimensions
        std_dim = self.grid_size * (DEFAULT_SQR_LEN + DEFAULT_SPACING)
        adj_wd = std_dim + self.grid_size
        adj_ht = std_dim + (DEFAULT_INFO_DIM * 2)
        self.setGeometry(300, 120, adj_wd, adj_ht)
        self.show()
        self.lgr.info(f"main window: width = {self.width()}, height = {self.height()}")

    def reset_game(self):
        self.lgr.info("\n\nStarting new Game!")
        self.total_empty = self.grid_size**2 - self.num_mines
        self.total_flags = 0
        self.total_revealed = 0
        self.lgr.info(f"grid size = {self.grid_size}, num mines = {self.num_mines}, empty squares = {self.total_empty}")
        self.mine_counter.setText("{:^3}".format(self.num_mines))
        self.clock.setText("0")
        self.result.setPixmap(QPixmap.fromImage(IMG_PLAY))

    def init_map(self):
        """Add GameSquares to the map"""
        for x in range(0, self.grid_size):
            for y in range(0, self.grid_size):
                sq = GameSquare(x, y, self)
                self.grid.addWidget(sq, y, x)
                sq.clicked.connect(self.start_game)
                # signal to handle expansion
                sq.expandable.connect(self.expand_reveal)
                # landed on a mine :(
                sq.ohno.connect(self.game_loss)

    def reset_map(self):
        # clear all previous mines
        for x in range(0, self.grid_size):
            for y in range(0, self.grid_size):
                self.grid.itemAtPosition(y,x).widget().reset()

        # add requested number of mines
        mine_posns = []
        while len(mine_posns) < self.num_mines:
            x,y = (
                random.randint(0, self.grid_size-1),
                random.randint(0, self.grid_size-1),
            )
            if (x,y) not in mine_posns:
                self.grid.itemAtPosition(y,x).widget().is_mine = True
                mine_posns.append((x,y))

        def get_num_adjacent(px, py):
            posns = self.get_surrounding(px,py)
            return sum(1 if ww.is_mine else 0 for ww in posns)

        # record number of adjacent mines for each square
        for x in range(0, self.grid_size):
            for y in range(0, self.grid_size):
                self.grid.itemAtPosition(y,x).widget().num_adjacent = get_num_adjacent(x,y)

        # place a random starting marker
        while True:
            x,y = (
                random.randint(0, self.grid_size-1),
                random.randint(0, self.grid_size-1),
            )
            # don't start on a mine
            if (x,y) not in mine_posns:
                self.grid.itemAtPosition(y,x).widget().is_start = True

                # reveal all squares around this where there are no mines
                for sq in self.get_surrounding(x,y):
                    if not sq.is_mine:
                        sq.click()
                break

    def get_surrounding(self, x, y):
        positions = []
        for xi in range(max(0, x-1), min(x+2, self.grid_size)):
            for yi in range(max(0, y-1), min(y+2, self.grid_size)):
                positions.append(self.grid.itemAtPosition(yi,xi).widget())
        return positions

    def restart_game(self):
        """Restart after a completed game."""
        if self.status == Status.SUCCESS or self.status == Status.FAILED:
            self.update_status(Status.READY)
            self.reset_game()
            self.reset_map()

    def reveal_map(self):
        for x in range(0, self.grid_size):
            for y in range(0, self.grid_size):
                self.grid.itemAtPosition(y,x).widget().reveal()

    def expand_reveal(self, x, y):
        for xi in range(max(0, x-1), min(x+2, self.grid_size)):
            for yi in range(max(0, y-1), min(y+2, self.grid_size)):
                sqw = self.grid.itemAtPosition(yi,xi).widget()
                if not sqw.is_mine:
                    sqw.click()

    def clear_check(self, x, y):
        """Make sure no adjacent squares are erroneous flags and all adjacent mines are flagged."""
        self.lgr.info(f"Clearing out around square[{x},{y}]")
        result = True
        for xi in range(max(0, x-1), min(x+2, self.grid_size)):
            for yi in range(max(0, y-1), min(y+2, self.grid_size)):
                sqw = self.grid.itemAtPosition(yi,xi).widget()
                if sqw.is_flagged and not sqw.is_mine:
                    self.lgr.info(f"ERRONEOUS flag at square[{xi},{yi}]!")
                    sqw.bad_flag = True
                    result = False
                if sqw.is_mine and not sqw.is_flagged:
                    self.lgr.info(f"MISSING flag at square[{xi},{yi}]!")
                    sqw.missing_flag = True
                    result = False
        return result

    def start_game(self):
        if self.status != Status.PLAYING:
            # first click
            self.update_status(Status.PLAYING)
            # start timer
            self.timer_start_numsecs = int(time.time())

    def update_status(self, p_status):
        self.status = p_status
        self.reset_button.setIcon(QIcon(STATUS_ICONS[self.status]))

    def update_clock(self):
        if self.status == Status.PLAYING:
            if self.isMinimized(): # pause the timer when minimized
                self.timer_start_numsecs += 1
            num_secs = int(time.time()) - self.timer_start_numsecs
            self.clock.setText("{:^5}".format(num_secs))

    def game_loss(self):
        self.update_status(Status.FAILED)
        self.result.setPixmap(QPixmap.fromImage(IMG_LOSE))
        self.reveal_map()
        self.lgr.info("FAILED :( \n\n")

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
